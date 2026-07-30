from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from infra.tools.calculator import calculate
from infra.tools.time_tool import get_current_time
from infra.tools.weather import get_weather
from functools import lru_cache
from textwrap import dedent
from pydantic import BaseModel
from application.adapter.openai_adapter import openai_adapter
from application.service.rag_service import rag_service
from infra.utils.log_util import logger


# 定义 Agent 状态类型（TypedDict）
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    task_type: Annotated[str, "任务类型：chat | rag | tool"]


class AgentService:

    def __init__(self):
        # graph 实例，初始化为 None，等待懒加载
        self.graph = None
        # MemorySaver 用于保存对话历史，支持多会话（通过 thread_id 区分）
        self.memory = None
        # 注册可用工具列表
        self.tools = [calculate, get_current_time, get_weather]

    def _ensure_initialized(self):
        """
        懒加载初始化 graph 和 memory
        """
        if self.graph is None:
            self.graph = self._build_graph()
        if self.memory is None:
            self.memory = MemorySaver()

    def _build_graph(self):
        """
        构建 Agent Graph 图。

        流程：
            - add_node：添加节点（Node）：每个节点是一个处理函数
            - set_entry_point：设置入口点
            - add_conditional_edges：添加条件边，根据函数返回值决定下一个节点
            - 
        """

        # 创建 StateGraph，指定状态类型为 AgentState
        workflow = StateGraph(AgentState)

        # 意图识别节点（入口）
        workflow.add_node("identify_intent", self._identify_intent)
        # 普通对话节点
        workflow.add_node("chat_handler", self._chat_handler)
        # RAG 知识库问答节点
        workflow.add_node("rag_handler", self._rag_handler)
        # 工具调用节点
        workflow.add_node("tool_handler", self._tool_handler)
        # tools: 使用 ToolNode 执行工具调用（LangGraph 预构建的工具执行节点）
        workflow.add_node("tools", ToolNode(self.tools))
        
        # 设置入口点：从 identify_intent 开始执行
        workflow.set_entry_point("identify_intent")
        
        # 添加条件边：根据 _route_task 的返回值决定下一个节点
        workflow.add_conditional_edges("identify_intent", self._route_task)
        
        # 添加终止边：普通对话和 RAG 知识库问答完成后指向 END
        workflow.add_edge("chat_handler", END)
        workflow.add_edge("rag_handler", END)
        
        # 添加条件边：工具调用完成后根据结果判断是否继续调用工具
        workflow.add_conditional_edges(
            "tool_handler",
            self._should_continue,
            {
                "continue": "tools",  # 继续调用工具
                "end": END            # 结束流程
            }
        )

        # 添加循环边：工具执行完成后返回 tools 继续调用工具
        workflow.add_edge("tools", "tool_handler")

        # 编译图，传入 checkpointer 以支持对话记忆
        return workflow.compile(checkpointer=self.memory)

    def _identify_intent(self, state: AgentState) -> AgentState:
        """
        意图识别节点，根据用户问题判断任务类型。
        """

        # 获取用户问题
        question = state["messages"][-1].content

        # 定义结构化输出的 Schema
        class TaskType(BaseModel):
            type: Literal["chat", "rag", "tool"]   # 任务类型
            reason: str   # 判断原因，用于调试和日志

        # 使用结构化输出判断任务类型，自动构建符合 Schema 的输出
        result = openai_adapter.invoke_with_structure(
            question=question,
            system_content=dedent("""
            你是一个智能助手，请根据用户的问题来判断任务类型进行后续处理。

            任务类型：
                - chat: 普通对话，直接回答
                - rag: 知识库问答，需要查询知识库文档
                - tool: 工具调用，需要调用工具返回结果
            """),
            messages=state["messages"],
            schema=TaskType
        )

        # 记录意图识别结果日志
        logger.info(f"意图识别结果: {result.type}, 原因: {result.reason}")
        
        # 返回更新后的状态（只更新 task_type）
        return {"task_type": result.type}

    def _chat_handler(self, state: AgentState) -> AgentState:
        """
        普通对话节点，根据用户问题进行普通对话。
        """

        # 获取用户问题
        question = state["messages"][-1].content
        logger.info(f"路由到普通对话，问题：{question}")
        
        # 调用 LLM 进行普通对话
        result = openai_adapter.invoke(question, messages=state["messages"])
        
        return {"messages": [result]}

    def _rag_handler(self, state: AgentState) -> AgentState:
        """
        RAG 知识库问答节点，根据用户问题查询知识库。
        """

        # 获取用户问题
        question = state["messages"][-1].content
        logger.info(f"路由到知识库问答，问题：{question}")
        
        # 调用 RAG 服务查询知识库
        result = rag_service.query(
            question=question,
            prompt_name="rag_base",
            prompt_version="v1",
            use_rerank=False
        )
        
        return {"messages": [result]}

    def _tool_handler(self, state: AgentState) -> AgentState:
        """
        工具调用节点，根据用户问题调用工具。
        """

        # 获取用户问题
        question = state["messages"][-1].content
        logger.info(f"路由到工具调用，问题：{question}")

        # 系统提示词，定义 Agent 的角色和可用工具
        system_prompt = dedent("""
        你是一个智能助手，可以使用工具来回答问题。
        
        可用工具：
            - calculate: 数学计算，参数为数学表达式
            - get_current_time: 获取当前时间，无需参数
            - get_weather: 获取当前天气，参数为城市名称

        请根据问题判断是否需要使用工具，如果需要，请调用相应的工具并根据工具返回的结果给出最终答案。
        如果不需要工具，可以直接回答。
        """)

        # 调用 LLM 获取响应，使用 invoke_with_tools 绑定工具
        response = openai_adapter.invoke_with_tools(
            question=question,
            system_content=system_prompt,
            messages=state["messages"],
            tools=self.tools
        )
        
        return {"messages": [response]}

    def _route_task(self, state: AgentState) -> str:
        """
        路由节点，根据任务类型选择合适的处理节点。
        """
        task_type = state["task_type"]
        if task_type == "chat":
            return "chat_handler"
        elif task_type == "rag":
            return "rag_handler"
        elif task_type == "tool":
            return "tool_handler"
        else:
            return "chat_handler"

    def _should_continue(self, state: AgentState) -> str:
        """
        决定是否继续调用工具节点或结束流程
        """

        # 获取最后一条用户消息
        last_message = state["messages"][-1]
        
        # 检查消息中是否包含工具调用
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.info(f"检测到工具调用: {last_message.tool_calls}")
            return "continue"
        
        # 没有工具调用，返回 "end"，结束流程
        return "end"

    def run(self, question: str, thread_id: str = "default") -> str:
        """
        运行 LangGraphAgent，处理用户问题

        Args:
            question: 用户问题
            thread_id: 会话 ID，用于区分不同会话的记忆（默认 "default"）

        Returns: Agent 的最终回答   
        """
        try:
            # 确保 graph 已初始化
            self._ensure_initialized()

            # 调用 graph，传入初始状态，thread_id 用于区分不同会话的记忆
            result = self.graph.invoke(
                {"messages": [HumanMessage(content=question)]},
                config={"configurable": {"thread_id": thread_id}}
            )
            
            # 返回最后一条消息的内容（即 Agent 的最终回答）
            return result["messages"][-1].content
            
        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            # 返回错误信息给用户
            return f"Agent 执行失败：{str(e)}"


@lru_cache()
def get_agent_service() -> AgentService:
    return AgentService()

agent_service = get_agent_service()