"""
多 Agent 协作 - Supervisor 模式

采用"协调者 + 专家"架构：
- Supervisor（协调者）：分析用户意图，分发任务给专业 Agent，汇总结果
- Specialist Agents（专家）：各自负责特定领域（RAG 知识库、工具调用、普通对话）

流程：
    用户输入 → Supervisor 分析意图 → 路由到对应专家 Agent → 专家处理 → Supervisor 汇总 → 返回结果

类比 Java：类似于 Spring 的 @Service 分层，Supervisor 是 Facade 门面模式，
对外统一接口，内部委托给不同的 Service 实现。
"""

from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from application.ports.llm_client_port import LlmClientPort
from application.service.rag_service import RAGService
from application.tools.calculator import calculate
from application.tools.time_tool import get_current_time
from application.tools.weather import get_weather
from infra.utils.log_util import logger
from textwrap import dedent
from pydantic import BaseModel


# 定义多 Agent 协作状态
class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # 当前由哪个 Agent 处理
    next_agent: str
    # 各 Agent 的处理结果
    agent_results: dict
    # 最终汇总结果
    final_response: str


class SupervisorAgent:
    """
    多 Agent 协作协调者

    负责：
        1. 分析用户意图，决定路由到哪个专家 Agent
        2. 协调多个 Agent 的执行顺序
        3. 汇总各 Agent 的结果，生成最终回复
    """

    def __init__(self, llm_adapter: LlmClientPort, rag_service: RAGService):
        self.llm_adapter = llm_adapter
        self.rag_service = rag_service
        self.graph = None
        self.checkpointer = None
        # 工具列表（供 Tool Agent 使用）
        self.tools = [calculate, get_current_time, get_weather]

    def build(self):
        """
        构建多 Agent 协作图

        节点：
            - supervisor: 协调者，分析意图并路由
            - rag_agent: RAG 知识库专家
            - tool_agent: 工具调用专家
            - chat_agent: 普通对话专家
            - summarizer: 汇总节点，整合结果
        """

        if self.checkpointer is None:
            self.checkpointer = InMemorySaver()

        if self.graph is None:
            workflow = StateGraph(SupervisorState)

            # 添加节点
            workflow.add_node("supervisor", self._supervisor_node)
            workflow.add_node("rag_agent", self._rag_agent_node)
            workflow.add_node("tool_agent", self._tool_agent_node)
            workflow.add_node("chat_agent", self._chat_agent_node)
            workflow.add_node("summarizer", self._summarizer_node)

            # 设置入口：从 supervisor 开始
            workflow.add_edge(START, "supervisor")

            # supervisor 根据意图路由到对应专家
            workflow.add_conditional_edges(
                "supervisor",
                self._route_to_agent,
                {
                    "rag_agent": "rag_agent",
                    "tool_agent": "tool_agent",
                    "chat_agent": "chat_agent",
                    "end": END
                }
            )

            # 各专家处理完后到汇总节点
            workflow.add_edge("rag_agent", "summarizer")
            workflow.add_edge("tool_agent", "summarizer")
            workflow.add_edge("chat_agent", "summarizer")

            # 汇总后结束
            workflow.add_edge("summarizer", END)

            self.graph = workflow.compile(checkpointer=self.checkpointer)

        return self.graph

    def _supervisor_node(self, state: SupervisorState) -> SupervisorState:
        """
        协调者节点：分析用户意图，决定路由到哪个专家 Agent
        """

        question = state["messages"][-1].content
        logger.info(f"Supervisor 分析意图: {question[:50]}...")

        # 定义路由决策的 Schema
        class RoutingDecision(BaseModel):
            next_agent: Literal["rag_agent", "tool_agent", "chat_agent"]
            reason: str

        # 使用结构化输出进行路由决策
        decision = self.llm_adapter.invoke_with_structure(
            question=question,
            system_content=dedent("""
            你是一个任务协调者（Supervisor），负责分析用户问题并决定由哪个专家 Agent 处理。

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
            schema=RoutingDecision
        )

        logger.info(f"路由决策: {decision.next_agent}, 原因: {decision.reason}")

        return {
            "next_agent": decision.next_agent,
            "agent_results": {}
        }

    async def _rag_agent_node(self, state: SupervisorState) -> SupervisorState:
        """
        RAG 知识库专家节点：查询知识库并返回结果
        """

        question = state["messages"][-1].content
        logger.info(f"RAG Agent 处理: {question[:50]}...")

        try:
            # 调用 RAG 服务查询知识库（异步）
            result = await self.rag_service.query(
                question=question,
                use_rerank=False
            )

            return {
                "agent_results": {
                    "rag_agent": {
                        "status": "success",
                        "response": result.content if hasattr(result, 'content') else str(result)
                    }
                }
            }
        except Exception as e:
            logger.error(f"RAG Agent 处理失败: {e}")
            return {
                "agent_results": {
                    "rag_agent": {
                        "status": "error",
                        "response": f"知识库查询失败: {str(e)}"
                    }
                }
            }

    def _tool_agent_node(self, state: SupervisorState) -> SupervisorState:
        """
        工具调用专家节点：使用工具解决问题
        """

        question = state["messages"][-1].content
        logger.info(f"Tool Agent 处理: {question[:50]}...")

        try:
            # 使用工具调用 LLM
            response = self.llm_adapter.invoke_with_tools(
                question=question,
                system_content=dedent("""
                你是一个工具调用专家，可以使用以下工具来回答问题：
                - calculate: 数学计算
                - get_current_time: 获取当前时间
                - get_weather: 获取天气信息

                请根据用户问题选择合适的工具，并根据工具返回结果给出答案。
                """),
                messages=state["messages"],
                tools=self.tools
            )

            return {
                "agent_results": {
                    "tool_agent": {
                        "status": "success",
                        "response": response.content
                    }
                }
            }
        except Exception as e:
            logger.error(f"Tool Agent 处理失败: {e}")
            return {
                "agent_results": {
                    "tool_agent": {
                        "status": "error",
                        "response": f"工具调用失败: {str(e)}"
                    }
                }
            }

    def _chat_agent_node(self, state: SupervisorState) -> SupervisorState:
        """
        普通对话专家节点：直接回答用户问题
        """

        question = state["messages"][-1].content
        logger.info(f"Chat Agent 处理: {question[:50]}...")

        try:
            response = self.llm_adapter.invoke(
                question=question,
                messages=state["messages"]
            )

            return {
                "agent_results": {
                    "chat_agent": {
                        "status": "success",
                        "response": response.content
                    }
                }
            }
        except Exception as e:
            logger.error(f"Chat Agent 处理失败: {e}")
            return {
                "agent_results": {
                    "chat_agent": {
                        "status": "error",
                        "response": f"对话处理失败: {str(e)}"
                    }
                }
            }

    def _summarizer_node(self, state: SupervisorState) -> SupervisorState:
        """
        汇总节点：整合各 Agent 的结果，生成最终回复
        """

        agent_results = state.get("agent_results", {})
        next_agent = state.get("next_agent", "unknown")

        logger.info(f"汇总节点: 处理来自 {next_agent} 的结果")

        # 获取对应 Agent 的结果
        result = agent_results.get(next_agent, {})
        response_text = result.get("response", "抱歉，未能处理您的问题。")
        status = result.get("status", "error")

        # 如果成功，直接返回结果；如果失败，尝试让 LLM 生成友好回复
        if status == "success":
            final_response = response_text
        else:
            # 失败时让 LLM 生成友好的错误提示
            final_response = self._generate_friendly_error(response_text)

        return {"final_response": final_response}

    def _generate_friendly_error(self, error_msg: str) -> str:
        """生成友好的错误提示"""
        try:
            response = self.llm_adapter.invoke(
                question=f"系统遇到了问题：{error_msg}，请用友好的语气告知用户",
                system_content="你是一个友好的助手，需要用温和的语气告知用户系统遇到了问题。"
            )
            return response.content
        except Exception:
            return "抱歉，系统暂时无法处理您的问题，请稍后再试。"

    def _route_to_agent(self, state: SupervisorState) -> str:
        """根据 supervisor 的决策路由到对应 Agent"""
        return state.get("next_agent", "chat_agent")
