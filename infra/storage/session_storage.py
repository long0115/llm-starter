"""
会话存储服务

提供会话和消息的CRUD操作，基于SQLite实现持久化。
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from infra.storage.database import init_db
from infra.storage.models import Session, Message, AgentState
from infra.utils.log_util import logger
from functools import lru_cache


class SessionStorage:
    """
    会话存储服务
    
    提供：
        - 会话管理：创建、查询、更新、删除会话
        - 消息管理：保存、查询会话消息
        - Agent状态：保存、恢复Agent对话状态
    """
    
    def __init__(self):
        init_db()
    
    # ========== 会话操作 ==========
    
    def create_session(self, db: Session, session_type: str = "chat", title: str = "新会话") -> str:
        """
        创建新会话
        
        Args:
            session_type: 会话类型 (chat/rag/agent)
            title: 会话标题
            
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        try:
            session = Session(
                session_id=session_id,
                title=title,
                session_type=session_type,
                created_at=datetime.now()
            )
            db.add(session)
            db.commit()
            logger.info(f"创建会话: {session_id} ({session_type})")
            return session_id
        except Exception as e:
            db.rollback()
            logger.error(f"创建会话失败: {e}")
            raise

    def get_session(self, db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息字典，不存在返回None
        """
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            return {
                "session_id": session.session_id,
                "title": session.title,
                "session_type": session.session_type,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None
            }
        return None

    def list_sessions(self, db: Session, session_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取会话列表
        
        Args:
            session_type: 按类型过滤（可选）
            limit: 返回数量限制
            
        Returns:
            会话列表
        """
        query = db.query(Session).filter(Session.is_active == True)
        if session_type:
            query = query.filter(Session.session_type == session_type)
        sessions = query.order_by(Session.created_at.desc()).limit(limit).all()
        return [{
            "session_id": s.session_id,
            "title": s.title,
            "session_type": s.session_type,
            "created_at": s.created_at.isoformat() if s.created_at else None
        } for s in sessions]

    def update_session_title(self, db: Session, session_id: str, title: str):
        """
        更新会话标题
        
        Args:
            session_id: 会话ID
            title: 新标题
        """
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            session.title = title
            db.commit()

    def delete_session(self, db: Session, session_id: str):
        """
        删除会话（软删除）
        
        Args:
            session_id: 会话ID
        """
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            session.is_active = False
            db.commit()
            logger.info(f"删除会话: {session_id}")

    # ========== 消息操作 ==========
    
    def save_message(self, db: Session, session_id: str, role: str, content: str, 
                     token_count: int = 0, meta_data: Optional[Dict] = None) -> int:
        """
        保存消息到会话
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            token_count: Token数量
            meta_data: 扩展元数据
            
        Returns:
            消息ID
        """
        try:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                token_count=token_count,
                meta_data=json.dumps(meta_data or {}, ensure_ascii=False)
            )
            db.add(message)
            db.commit()
            
            # 如果是第一条用户消息，自动设置会话标题
            if role == "user":
                msg_count = db.query(Message).filter(
                    Message.session_id == session_id
                ).count()
                if msg_count <= 1:
                    # 截取前20个字符作为标题
                    title = content[:20] + "..." if len(content) > 20 else content
                    session = db.query(Session).filter(Session.session_id == session_id).first()
                    if session and session.title == "新会话":
                        session.title = title
                        db.commit()
            
            return message.id
        except Exception as e:
            db.rollback()
            logger.error(f"保存消息失败: {e}")
            raise

    def get_messages(self, db: Session, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取会话的消息历史
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            
        Returns:
            消息列表（按时间正序）
        """
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).limit(limit).all()
        
        return [{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "token_count": m.token_count,
            "meta_data": json.loads(m.meta_data) if m.meta_data else {},
            "created_at": m.created_at.isoformat() if m.created_at else None
        } for m in messages]

    def get_messages_as_langchain(self, db: Session, session_id: str, limit: int = 20) -> List[BaseMessage]:
        """
        获取会话消息历史（转换为LangChain格式）
        
        用于传递给LLM进行多轮对话。
        
        Args:
            session_id: 会话ID
            limit: 返回最近N条消息
            
        Returns:
            LangChain BaseMessage 列表
        """
        
        messages_data = self.get_messages(db, session_id, limit=limit)
        lc_messages = []
        
        for msg in messages_data:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
        
        return lc_messages
    
    # ========== Agent状态操作 ==========
    
    def save_agent_state(self, db: Session, session_id: str, state_data: Dict[str, Any]):
        """
        保存Agent状态
        
        Args:
            session_id: 会话ID
            state_data: 状态数据
        """
        try:
            state = db.query(AgentState).filter(AgentState.session_id == session_id).first()
            if state:
                state.state_data = json.dumps(state_data, ensure_ascii=False)
            else:
                state = AgentState(
                    session_id=session_id,
                    state_data=json.dumps(state_data, ensure_ascii=False)
                )
                db.add(state)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"保存Agent状态失败: {e}")
            raise

    def get_agent_state(self, db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取Agent状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            状态数据，不存在返回None
        """
        state = db.query(AgentState).filter(AgentState.session_id == session_id).first()
        if state:
            return json.loads(state.state_data)
        return None

    def delete_agent_state(self, db: Session, session_id: str):
        """
        删除Agent状态
        
        Args:
            session_id: 会话ID
        """
        state = db.query(AgentState).filter(AgentState.session_id == session_id).first()
        if state:
            db.delete(state)
            db.commit()


@lru_cache()
def get_session_storage() -> SessionStorage:
    return SessionStorage()

session_storage = get_session_storage()