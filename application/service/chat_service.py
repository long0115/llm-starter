"""
基础对话服务实现

    - 基础对话服务
    - 流式对话服务
"""

from api.schemas.chat import ChatResponse
from application.adapter.openai_adapter import openai_adapter
from infra.storage.session_storage import session_storage
from infra.utils.log_util import logger
from functools import lru_cache


class ChatService:

    def __init__(self):
        pass

    async def chat(self, message: str, system_content: str = None, session_id: str = None) -> ChatResponse:
        """
        对话服务实现
        
        Args:
            message: 用户输入的消息
            system_content: 系统提示（可选）
            session_id: 会话 ID（可选）
        
        Returns:
            ChatResponse: 包含回复内容、完成原因和 token 使用信息的响应
        """

        # 如果没有会话ID，创建新会话
        if not session_id:
            session_id = session_storage.create_session(session_type="chat")

        # 保存用户消息
        session_storage.save_message(session_id, "user", message)

        # 获取历史消息（用于多轮对话）
        history_messages = session_storage.get_messages_as_langchain(session_id)
        
        response = await openai_adapter.ainvoke(
            question=message,
            system_content=system_content,
            messages=history_messages
        )

        # 保存AI回复
        session_storage.save_message(
            session_id, "assistant", response.content,
            token_count=response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        )
    
        return {
            "content": response.content,
            "finish_reason": response.response_metadata["finish_reason"],
            "token_usage": response.response_metadata["token_usage"]
        }
    
    async def stream_chat(self, message: str, system_content: str = None):
        """
        流式对话服务实现
        
        Args:
            message: 用户输入的消息
            system_content: 系统提示（可选）
        
        Returns:
            ChatResponse: 包含回复内容、完成原因和 token 使用信息的响应
        """
        
        async for chunk in openai_adapter.astream(
            question=message,
            system_content=system_content
        ):
            yield chunk
    

@lru_cache()
def get_chat_service() -> ChatService:
    return ChatService()

chat_service = get_chat_service()
