from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from application.ports.llm_client_port import LlmClientPort
from application.service.rag_service import RAGService
from application.tools.calculator import calculate
from application.tools.time_tool import get_current_time
from application.tools.weather import get_weather
from infra.utils.log_util import logger
from textwrap import dedent
from pydantic import BaseModel


# 定义 Agent 状态类型（TypedDict）
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    task_type: Annotated[str, "任务类型：chat | rag | tool"]


class FlowAgent:
    def __init__(self, llm_adapter: LlmClientPort, rag_service: RAGService):
        # graph 实例，初始化为 None，等待懒加载
        self.graph = None
        # MemorySaver 用于保存对话历史，支持多会话（通过 thread_id 区分）
        self.checkpoint = None
        # 注册可用工具列表
        self.tools = [calculate, get_current_time, get_weather]
        # 依赖注入
        self.llm_adapter = llm_adapter
        self.rag_service = rag_service
        

    def build(self):
        """
        构建 Agent Graph 图。

        流程：
            - add_node：添加节点（Node）：每个节点是一个处理函数
            - add_edge：添加边，指定节点之间的连接
            - add_conditional_edges：添加条件分支边，根据函数返回值决定下一个节点
        """

        if self.checkpoint is None:
            self.checkpoint = InMemorySaver()

        if self.graph is None:
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
            # 使用 ToolNode 执行工具调用（LangGraph 预构建的工具执行节点）
            workflow.add_node("tools", ToolNode(self.tools))
            
            # 设置入口点：从 identify_intent 开始执行
            workflow.add_edge(START, "identify_intent")
            
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
            self.graph = workflow.compile(checkpointer=self.checkpoint)

        return self.graph
    
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
        result = self.llm_adapter.invoke_with_structure(
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
        result = self.llm_adapter.invoke(question, messages=state["messages"])
        
        return {"messages": [result]}

    def _rag_handler(self, state: AgentState) -> AgentState:
        """
        RAG 知识库问答节点，根据用户问题查询知识库。
        """

        # 获取用户问题
        question = state["messages"][-1].content
        logger.info(f"路由到知识库问答，问题：{question}")
        
        # 调用 RAG 服务查询知识库
        result = self.rag_service.query(
            question=question,
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
        response = self.llm_adapter.invoke_with_tools(
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
