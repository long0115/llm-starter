"""
基础对话服务实现

    - 基础对话服务
    - 流式对话服务
"""

from api.schemas.chat import ChatResponse
from application.ports.llm_client_port import LlmClientPort
from infra.storage.session_storage import SessionStorage
from sqlalchemy.orm import Session


class ChatService:

    def __init__(self, llm_adapter: LlmClientPort, session_storage: SessionStorage, database: Session):
        self.llm_adapter = llm_adapter
        self.session_storage = session_storage
        self.database = database

    async def chat(self, message: str, session_id: str = None) -> ChatResponse:
        """
        对话服务实现
        
        Args:
            message: 用户输入的消息
            session_id: 会话 ID（可选）
        
        Returns:
            ChatResponse: 包含回复内容、完成原因和 token 使用信息的响应
        """

        # 如果没有会话ID，创建新会话
        if not session_id:
            session_id = self.session_storage.create_session(self.database, session_type="chat")

        # 保存用户消息
        self.session_storage.save_message(self.database, session_id, "user", message)

        # 获取历史消息（用于多轮对话）
        history_messages = self.session_storage.get_messages_as_langchain(self.database, session_id)
        
        response = await self.llm_adapter.ainvoke(
            question=message,
            messages=history_messages
        )

        # 保存AI回复
        self.session_storage.save_message(
            self.database,
            session_id, 
            "assistant", 
            response.content,
            token_count=response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        )
    
        return {
            "content": response.content,
            "finish_reason": response.response_metadata["finish_reason"],
            "token_usage": response.response_metadata["token_usage"],
            "session_id": session_id
        }
    
    async def stream_chat(self, message: str, session_id: str = None):
        """
        流式对话服务实现
        
        Args:
            message: 用户输入的消息
            session_id: 会话 ID（可选）
        
        Returns:
            ChatResponse: 包含回复内容、完成原因和 token 使用信息的响应
        """

        # 如果没有会话ID，创建新会话
        if not session_id:
            session_id = self.session_storage.create_session(self.database, session_type="chat")

        # 保存用户消息
        self.session_storage.save_message(self.database, session_id, "user", message)

        # 获取历史消息（用于多轮对话）
        history_messages = self.session_storage.get_messages_as_langchain(self.database, session_id)
        
        # 🆕 创建缓冲区用于累积流式内容
        content_buffer = []

        async for chunk in self.llm_adapter.astream(
            question=message,
            messages=history_messages
        ):
            content_buffer.append(chunk)
            yield chunk

        full_content = "".join(content_buffer)

        # 保存AI回复
        self.session_storage.save_message(
            self.database,
            session_id, 
            "assistant", 
            full_content,
            token_count=0
        )
