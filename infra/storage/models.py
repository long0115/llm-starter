"""
数据模型定义

定义会话、消息、Agent状态等持久化数据的结构。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from infra.storage.database import Base


class Session(Base):
    """
    会话表
    
    存储用户会话的基本信息。
    """
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True, comment="会话唯一ID")
    title = Column(String(200), default="新会话", comment="会话标题（取第一条消息作为标题）")
    session_type = Column(String(20), default="chat", comment="会话类型: chat/rag/agent")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 关联消息（一对多）
    messages = None  # 通过 relationship 定义，在 SessionStorage 中使用


class Message(Base):
    """
    消息表
    
    存储会话中的每条消息（用户输入和AI回复）。
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True, comment="关联的会话ID")
    role = Column(String(20), nullable=False, comment="角色: user/assistant/system")
    content = Column(Text, nullable=False, comment="消息内容")
    token_count = Column(Integer, default=0, comment="Token数量")
    meta_data = Column(Text, default="{}", comment="扩展元数据（JSON格式）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 创建索引以加速按会话ID查询
    __table_args__ = (
        Index("ix_messages_session_created", "session_id", "created_at"),
    )


class AgentState(Base):
    """
    Agent状态表
    
    存储Agent的对话状态，支持跨会话恢复。
    """
    __tablename__ = "agent_states"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True, comment="会话ID")
    state_data = Column(Text, nullable=False, comment="Agent状态数据（JSON序列化）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")