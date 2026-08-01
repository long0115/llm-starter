"""
Sessions 路由

接口：
    - POST /session/create: 创建新会话
    - GET /session/list: 获取会话列表
    - GET /session/{session_id}: 获取会话详情
    - GET /session/{session_id}/messages: 获取会话消息列表
    - DELETE /session/{session_id}: 删除会话
    
"""

from typing import List
from fastapi import APIRouter, HTTPException, Path
from infra.exceptions import NotFoundException
from api.schemas.session import SessionRequest, SessionResponse, MessageResponse
from infra.storage.session_storage import session_storage
from infra.utils.log_util import logger
from infra.storage.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/create", response_model=SessionResponse)
async def create_session(request: SessionRequest, db: Session = Depends(get_db)):
    """
    创建新会话
    
    - session_type: 会话类型 (chat/rag/agent)
    - title: 会话标题（可选）
    """
    try:
        title = request.title or f"{request.session_type} 会话"
        session_id = session_storage.create_session(
            db=db,
            session_type=request.session_type,
            title=title
        )
        session_info = session_storage.get_session(db, session_id)
        return SessionResponse(**session_info)
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[SessionResponse])
async def list_sessions(db: Session = Depends(get_db), session_type: str = "chat", limit: int = 50):
    """
    获取会话列表
    
    - session_type: 按类型过滤（可选）
    - limit: 返回数量限制
    """
    try:
        sessions = session_storage.list_sessions(
            db=db,
            session_type=session_type,
            limit=limit
        )
        return [SessionResponse(**s) for s in sessions]
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(db: Session = Depends(get_db), session_id: str = Path(...)):
    """
    获取会话信息
    """
    try:
        session = session_storage.get_session(db, session_id)
        if not session:
            raise NotFoundException("会话不存在")

        return SessionResponse(**session)
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, db: Session = Depends(get_db), limit: int = 50):
    """
    获取会话的消息历史
    
    - limit: 返回数量限制
    """
    try:
        # 检查会话是否存在
        session = session_storage.get_session(db, session_id)
        if not session:
            raise NotFoundException("会话不存在")
        
        messages = session_storage.get_messages(db, session_id, limit=limit)
        return [MessageResponse(**m) for m in messages]
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"获取消息历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(db: Session = Depends(get_db), session_id: str = Path(...)):
    """
    删除会话（软删除）
    """
    try:
        session = session_storage.get_session(db, session_id)
        if not session:
            raise NotFoundException("会话不存在")
        
        session_storage.delete_session(db, session_id)
        return {"message": "会话已删除"}
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))