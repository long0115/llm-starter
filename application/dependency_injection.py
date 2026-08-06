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
from infra.adapter.mcp_adapter import McpAdapter
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


def _create_rag_service(db: Session) -> RAGService:
    """创建 RAGService 实例（内部工厂，不依赖 FastAPI）"""
    return RAGService(
        loader=document_loader,
        cleaner=document_cleaner,
        splitter=document_splitter,
        prompt_port=prompt_manager,
        retriever_port=retriever_manager,
        vector_adapter=chroma_adapter,
        llm_adapter=openai_adapter,
        session_storage=session_storage,
        database=db
    )


def get_rag_service(db: Session = Depends(get_db)) -> RAGService:
    """获取 RAGService 实例（FastAPI 依赖注入用）"""
    return _create_rag_service(db)


def get_agent_service(db: Session = Depends(get_db)) -> AgentService:
    """获取 AgentService 实例（依赖注入用）"""
    return AgentService(
        simple_agent=_create_simple_agent(),
        flow_agent=_create_flow_agent(db),
        session_storage=session_storage,
        database=db
    )


def _create_flow_agent(db: Session) -> FlowAgent:
    """创建 FlowAgent 实例（内部工厂）"""
    return FlowAgent(
        llm_adapter=openai_adapter,
        rag_service=_create_rag_service(db)
    )


def _create_simple_agent() -> SimpleAgent:
    """获取 SimpleAgent 实例（依赖注入用）"""
    return SimpleAgent(
        llm_adapter=openai_adapter,
        mcp_adapter=None # McpAdapter()
    )

