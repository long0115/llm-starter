from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from langgraph.graph.message import add_messages
import asyncio
from application.ports.llm_client_port import LlmClientPort
from application.service.rag_service import RAGService
from application.tools.calculator import calculate
from application.tools.time_tool import get_current_time
from application.tools.weather import get_weather
from infra.utils.log_util import logger
from textwrap import dedent
from pydantic import BaseModel


# 需要人工干预的工具列表（类比 Java 中的配置常量）
HUMAN_APPROVAL_TOOLS = {"get_weather"}

# 定义 Agent 状态类型（TypedDict）
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    agent_type: Annotated[str, "agent类型：chat_agent | rag_agent | tool_agent"]
    agent_status: Annotated[dict[str, str], "agent状态：success | error"] = {"status": "success", "response": ""}
    human_approved: Annotated[bool, "人工干预结果：是否同意本次操作"] = False
    pending_tool_calls: Annotated[list, "待审批的工具调用列表"] = []


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
            workflow.add_node("identify_intent", self._identify_intent_node)
            # 普通对话节点
            workflow.add_node("chat_agent", self._chat_agent_node)
            # RAG 知识库问答节点
            workflow.add_node("rag_agent", self._rag_agent_node)
            # 工具调用选择节点
            workflow.add_node("tool_agent", self._tool_agent_node)
            # 人工干预节点
            workflow.add_node("human_approval", self._human_approval_node)   
            # 最终总结节点
            workflow.add_node("final_summary", self._final_summary_node)
            # 各工具节点
            workflow.add_node("tools", ToolNode(self.tools))
            
            # 设置入口点：从 identify_intent 开始执行
            workflow.add_edge(START, "identify_intent")
            
            # 意图识别节点：根据模型返回结果决定执行哪个 Agent
            workflow.add_conditional_edges(
                "identify_intent", 
                lambda state: state.get("agent_type", "chat_agent")
            )

            # 普通对话完成后指向 END
            workflow.add_edge("chat_agent", "final_summary")
            # RAG 知识库问答完成后指向 END
            workflow.add_edge("rag_agent", "final_summary")
            # 工具调用选择节点：根据模型返回结果决定是否需要人工干预
            workflow.add_conditional_edges(
                "tool_agent",
                self._check_need_human,
                {
                    "need_human": "human_approval",
                    "execute": "tools",
                    "end": "final_summary"
                }
            )

            # 人工干预节点：批准则执行工具，否则结束流程
            workflow.add_conditional_edges(
                "human_approval",
                lambda state: "tools" if state.get("human_approved") else "final_summary"
            )

            # 最终总结节点
            workflow.add_edge("final_summary", END)

            # 编译图，传入 checkpointer 以支持对话记忆
            self.graph = workflow.compile(checkpointer=self.checkpoint)

        return self.graph
    
    def _identify_intent_node(self, state: AgentState) -> AgentState:
        """
        意图识别节点，根据用户问题判断任务类型。
        """

        # 获取用户问题
        question = state["messages"][-1].content

        # 定义结构化输出的 Schema
        class TaskType(BaseModel):
            type: Literal["chat_agent", "rag_agent", "tool_agent"]   # 任务类型
            reason: str   # 判断原因，用于调试和日志

        # 使用结构化输出判断任务类型，自动构建符合 Schema 的输出
        response = self.llm_adapter.invoke_with_structure(
            question=question,
            system_content=dedent("""
            你是一个任务协调者，负责分析用户问题并决定由哪个专家 Agent 处理。

            专家 Agent 列表：
                - rag_agent: RAG 知识库专家，处理需要查询文档/知识库的问题（如公司制度、员工手册等）
                - tool_agent: 工具调用专家，处理需要计算、查天气、查时间等工具操作的问题
                - chat_agent: 普通对话专家，处理闲聊、问候、简单问答等

            判断规则：
                - 如果问题涉及公司内部制度、政策、流程等，路由到 rag_agent
                - 如果问题需要计算、查询实时信息（天气、时间），路由到 tool_agent
                - 其他情况路由到 chat_agent
            """),
            messages=state["messages"],
            schema=TaskType
        )

        # 记录意图识别结果日志
        logger.info(f"路由决策: {response.type}, 原因: {response.reason}")
        
        # 返回更新后的状态（只更新 agent_type
        return {"agent_type": response.type}

    def _chat_agent_node(self, state: AgentState) -> AgentState:
        """
        普通对话节点，根据用户问题进行普通对话。
        """

        # 获取用户问题
        question = state["messages"][-1].content
        logger.info(f"Chat Agent 处理: {question}")
        
        try:
            # 调用 LLM 进行普通对话
            response = self.llm_adapter.invoke(question, messages=state["messages"])
        
            return {"messages": [response], "agent_status": {"status": "success", "response": response.content}}
        except Exception as e:
            logger.error(f"Chat Agent 处理失败: {e}")
            return {"agent_status": {"status": "error", "response": f"对话处理失败: {str(e)}"}}

    def _rag_agent_node(self, state: AgentState) -> AgentState:
        """
        RAG 知识库问答节点，根据用户问题查询知识库。
        """

        # 获取用户问题
        question = state["messages"][-1].content
        logger.info(f"RAG Agent 处理: {question}")

        try:
            # 用 asyncio 包装异步调用
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(
                self.rag_service.query(question=question, use_rerank=False)
            )
            loop.close()

            aiMessage = AIMessage(content=response.content)

            return {"messages": [aiMessage], "agent_status": {"status": "success", "response": response.content}}
        except Exception as e:
            logger.error(f"RAG Agent 处理失败: {e}")
            return {"agent_status": {"status": "error", "response": f"知识库查询失败: {str(e)}"}}

    def _tool_agent_node(self, state: AgentState) -> AgentState:
        """
        工具调用节点，根据用户问题调用工具。
        """

        # 获取用户问题
        question = state["messages"][-1].content
        logger.info(f"Tool Agent 处理: {question}")

        # 系统提示词，定义 Agent 的角色和可用工具
        system_prompt = dedent("""
        你是一个工具调用专家，可以使用以下工具来回答问题：
            - calculate: 数学计算，参数为数学表达式
            - get_current_time: 获取当前时间，无需参数
            - get_weather: 获取当前天气，参数为城市名称

        请根据问题判断是否需要使用工具，如果需要，请调用相应的工具。
        如果不需要工具，可以直接回答。
        """)

        try:
            # 调用 LLM 获取响应，使用 invoke_with_tools 绑定工具
            response = self.llm_adapter.invoke_with_tools(
                question=question,
                system_content=system_prompt,
                messages=state["messages"],
                tools=self.tools
            )

            # 提取 LLM 决定调用的工具名
            tool_calls = getattr(response, "tool_calls", []) or []
            tool_names = [tc["name"] for tc in tool_calls] if tool_calls else []
            logger.info(f"Tool Agent 选择工具: {tool_names}")

            return {
                "messages": [response],
                "agent_status": {"status": "success", "response": response.content},
                "pending_tool_calls": tool_names
            }
        except Exception as e:
            logger.error(f"Tool Agent 处理失败: {e}")
            return {"agent_status": {"status": "error", "response": f"工具调用失败: {str(e)}"}}

    def _human_approval_node(self, state: AgentState) -> AgentState:
        """
        人工干预节点，根据人工干预结果继续流程。
        """
        
        approved = interrupt({
            "question": "是否同意本次操作？"
        })

        # 处理人工干预结果
        if approved == True:
            return {"human_approved": True}
        else:
            return {"human_approved": False}

    def _final_summary_node(self, state: AgentState) -> AgentState:
        """
        最终总结节点，根据用户问题进行最终总结。
        """

        agent_status = state.get("agent_status", {})

        if agent_status.get("status") == "success":
            return {}
        else:
            error_msg = agent_status.get("response", "抱歉，未能处理您的问题。")
            response = self.llm_adapter.invoke(
                question=f"系统遇到了问题：{error_msg}，请用友好的语气告知用户",
                system_content="你是一个友好的助手，需要用温和的语气告知用户系统遇到了问题。"
            )
            return {"messages": [response]}

    def _check_need_human(self, state: AgentState) -> str:
        """
        检查待调用的工具是否需要人工干预。

        规则：如果待调用工具中有任一工具在 HUMAN_APPROVAL_TOOLS 列表中，
        则走人工干预节点；否则直接执行。
        """
        pending_tools = state.get("pending_tool_calls", [])

        # 没有工具调用，说明 LLM 直接回答了，结束流程
        if not pending_tools:
            logger.info("无需工具调用，直接结束")
            return "end"

        # 检查是否有需要人工审批的工具
        need_approval = set(pending_tools) & HUMAN_APPROVAL_TOOLS
        if need_approval:
            logger.info(f"工具 {need_approval} 需要人工审批")
            return "need_human"

        logger.info(f"工具 {pending_tools} 无需审批，直接执行")
        return "execute"
