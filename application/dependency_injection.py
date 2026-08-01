"""
依赖注入容器

负责将所有端口实现组装好，提供 FastAPI Depends 使用的工厂函数
"""

from application.service.chat_service import ChatService
from application.service.rag_service import RAGService
from application.service.agent_service import AgentService
from application.agents.flow_agent import FlowAgent
from application.agents.simple_agent import SimpleAgent
from infra.adapter.openai_adapter import openai_adapter
from infra.adapter.chroma_adapter import chroma_adapter
from infra.document.loader import document_loader
from infra.document.cleaner import document_cleaner
from infra.document.splitter import document_splitter
from infra.retriever.retriever import retriever_manager
from infra.prompt.prompt_manager import prompt_manager
from infra.storage.session_storage import session_storage
from fastapi import Depends
from sqlalchemy.orm import Session
from infra.storage.database import get_db


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    """获取 ChatService 实例（依赖注入用）

    FastAPI 会自动解析 db 依赖：请求结束时自动关闭 Session。
    """
    return ChatService(
        llm_adapter=openai_adapter,
        session_storage=session_storage,
        database=db
    )


def get_rag_service() -> RAGService:
    """获取 RAGService 实例（依赖注入用）"""
    return RAGService(
        loader=document_loader,
        cleaner=document_cleaner,
        splitter=document_splitter,
        prompt_port=prompt_manager,
        retriever_port=retriever_manager,
        vector_adapter=chroma_adapter,
        llm_adapter=openai_adapter
    )


def get_agent_service() -> AgentService:
    """获取 AgentService 实例（依赖注入用）"""
    return AgentService(
        flow_agent=get_flow_agent(),
        simple_agent=get_simple_agent()
    )


def get_flow_agent() -> FlowAgent:
    """获取 FlowAgent 实例（依赖注入用）"""
    return FlowAgent(
        llm_adapter=openai_adapter,
        rag_service=get_rag_service()
    )


def get_simple_agent() -> SimpleAgent:
    """获取 SimpleAgent 实例（依赖注入用）"""
    return SimpleAgent(
        llm_adapter=openai_adapter
    )
