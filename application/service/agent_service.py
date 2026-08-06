from langchain_core.messages import HumanMessage
from langgraph.types import Command
from pydantic import config
from application.agents.flow_agent import FlowAgent
from application.agents.simple_agent import SimpleAgent
from infra.utils.log_util import logger
from infra.storage.session_storage import SessionStorage
from sqlalchemy.orm import Session


class AgentService:

    def __init__(self, flow_agent: FlowAgent, simple_agent: SimpleAgent, session_storage: SessionStorage = None, database: Session = None):
        self.graph = None
        self.flow_agent = flow_agent
        self.simple_agent = simple_agent
        self.session_storage = session_storage
        self.database = database

    async def run_by_simple(self, question: str, thread_id: str = "default") -> str:
        """
        运行 simple_agent，处理用户问题

        Args:
            question: 用户问题
            thread_id: 会话 ID，用于区分不同会话的记忆（默认 "default"）

        Returns: Agent 的最终回答
        """

        # 如果没有会话ID，创建新会话
        if not thread_id:
            thread_id = self.session_storage.create_session(self.database, session_type="agent")

        # 保存用户消息
        self.session_storage.save_message(self.database, thread_id, "user", question)

        try:
            self.graph = await self.simple_agent.build()

            # 调用 graph，传入初始状态，thread_id 用于区分不同会话的记忆
            result = self.graph.invoke(
                input={"messages": [HumanMessage(content=question)]},
                config={"configurable": {"thread_id": thread_id}},
                version="v2"
            )

            # 检查是否有中断
            if hasattr(result, 'interrupts') and result.interrupts:
                # 有中断，需要人工干预
                interrupt_info = result.interrupts[0]
                logger.info(f"触发中断: {interrupt_info}")

                # 人工干预结果，当前默认同意，后续可以根据业务返回结果动态调整
                approved = "approve"
                logger.info(f"人工干预结果: 同意")

                # 继续执行
                result = self.graph.invoke(
                    Command(resume={"decisions": [{"type": approved}]}),
                    config={"configurable": {"thread_id": thread_id}},
                    version="v2"
                )

            # 保存AI回复
            self.session_storage.save_message(
                self.database,
                thread_id, 
                "assistant", 
                result["messages"][-1].content,
                token_count=0
            )
            
            # 返回最后一条消息的内容（即 Agent 的最终回答）
            return result["messages"][-1].content
            
        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            # 返回错误信息给用户
            return f"Agent 执行失败：{str(e)}"

    def run_by_flow(self, question: str, thread_id: str = "default") -> str:
        """
        运行 flow_agent，处理用户问题

        Args:
            question: 用户问题
            thread_id: 会话 ID，用于区分不同会话的记忆（默认 "default"）

        Returns: Agent 的最终回答   
        """

        # 如果没有会话ID，创建新会话
        if not thread_id:
            thread_id = self.session_storage.create_session(self.database, session_type="agent")

        # 保存用户消息
        self.session_storage.save_message(self.database, thread_id, "user", question)

        try:
            self.graph = self.flow_agent.build()

            # 调用 graph，传入初始状态，thread_id 用于区分不同会话的记忆
            result = self.graph.invoke(
                input={"messages": [HumanMessage(content=question)]},
                config={"configurable": {"thread_id": thread_id}},
                version="v2"
            )

            # 检查是否有中断
            if hasattr(result, 'interrupts') and result.interrupts:
                # 有中断，需要人工干预
                interrupt_info = result.interrupts[0]
                logger.info(f"触发中断: {interrupt_info}")

                # 人工干预结果，当前默认同意，后续可以根据业务返回结果动态调整
                approved = True
                logger.info(f"人工干预结果: 同意")

                # 继续执行
                result = self.graph.invoke(
                    Command(resume=approved),
                    config={"configurable": {"thread_id": thread_id}},
                    version="v2"
                )

            # 保存AI回复
            self.session_storage.save_message(
                self.database,
                thread_id, 
                "assistant", 
                result["messages"][-1].content,
                token_count=0
            )
            
            # 返回最后一条消息的内容（即 Agent 的最终回答）
            return result["messages"][-1].content
            
        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            # 返回错误信息给用户
            return f"Agent 执行失败：{str(e)}"