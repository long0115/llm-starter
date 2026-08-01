"""
对话路由

接口：
    - POST /chat/base: 同步对话
    - POST /chat/stream: 流式对话
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from api.schemas.chat import ChatRequest, ChatResponse
from application.service.chat_service import ChatService
from application.dependency_injection import get_chat_service
from infra.utils.log_util import logger

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/base", response_model=ChatResponse)
async def chat(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    """
    同步对话接口
    
    Args:
        request: ChatRequest 请求模型
        chat_service: ChatService 实例（依赖注入）
    
    Returns:
        ChatResponse: 响应模型
    """
    try:
        logger.info(f"收到对话请求: {request.message[:50]}...")
        
        result = await chat_service.chat(
            message=request.message,
            system_content=request.system_content,
            session_id=request.session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    """
    流式对话接口（Server-Sent Events）
    
    Args:
        request: ChatRequest 请求模型
    
    Returns:
        StreamingResponse: 流式响应
    """
    try:
        logger.info(f"收到流式对话请求: {request.message[:50]}...")
        
        async def generate():
            try:
                async for chunk in chat_service.stream_chat(
                    message=request.message,
                    system_content=request.system_content,
                ):
                    yield f"data: {chunk}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"流式对话请求失败: {e}", exc_info=True)
                yield f"error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except Exception as e:
        logger.error(f"流式对话初始化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
