"""
ChatService 单元测试

使用 mock 对象隔离外部依赖（LLM、数据库），只测试业务逻辑
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, call
from langchain_core.messages import AIMessage
from application.service.chat_service import ChatService


class TestChatServiceChat:
    """测试 chat 方法"""

    @pytest.mark.asyncio
    async def test_chat_new_session(self, mock_llm_adapter, mock_session_storage, mock_db):
        """测试新建会话的对话流程"""
        service = ChatService(mock_llm_adapter, mock_session_storage, mock_db)

        result = await service.chat("你好")

        # 验证创建了新会话
        mock_session_storage.create_session.assert_called_once_with(mock_db, session_type="chat")

        # 验证保存了用户消息
        mock_session_storage.save_message.assert_any_call(
            mock_db, "test-session-id-123", "user", "你好"
        )

        # 验证调用了 LLM
        mock_llm_adapter.ainvoke.assert_called_once()

        # 验证保存了 AI 回复
        assert mock_session_storage.save_message.call_count == 2

        # 验证返回结果
        assert "content" in result
        assert "finish_reason" in result
        assert "token_usage" in result
        assert result["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_chat_existing_session(self, mock_llm_adapter, mock_session_storage, mock_db):
        """测试使用已有会话 ID 的对话"""
        service = ChatService(mock_llm_adapter, mock_session_storage, mock_db)

        result = await service.chat("继续聊", session_id="existing-session-456")

        # 不应创建新会话
        mock_session_storage.create_session.assert_not_called()

        # 应使用传入的 session_id
        mock_session_storage.save_message.assert_any_call(
            mock_db, "existing-session-456", "user", "继续聊"
        )

    @pytest.mark.asyncio
    async def test_chat_with_system_content(self, mock_llm_adapter, mock_session_storage, mock_db):
        """测试带系统提示词的对话"""
        service = ChatService(mock_llm_adapter, mock_session_storage, mock_db)

        await service.chat("你好", system_content="你是一个助手")

        # 验证 system_content 被传递给 LLM
        call_kwargs = mock_llm_adapter.ainvoke.call_args[1]
        assert call_kwargs["system_content"] == "你是一个助手"

    @pytest.mark.asyncio
    async def test_chat_saves_token_count(self, mock_llm_adapter, mock_session_storage, mock_db):
        """测试保存 token 使用量"""
        service = ChatService(mock_llm_adapter, mock_session_storage, mock_db)

        await service.chat("你好")

        # 验证第二次 save_message 调用包含 token_count
        save_calls = mock_session_storage.save_message.call_args_list
        last_call = save_calls[-1]
        assert last_call[1]["token_count"] == 150


class TestChatServiceStreamChat:
    """测试 stream_chat 方法"""

    @pytest.mark.asyncio
    async def test_stream_chat(self, mock_llm_adapter, mock_session_storage, mock_db):
        """测试流式对话"""
        # 设置 stream 返回模拟数据
        async def mock_stream(**kwargs):
            for chunk in ["你好", "，", "我是", "助手"]:
                yield chunk

        mock_llm_adapter.astream = mock_stream

        service = ChatService(mock_llm_adapter, mock_session_storage, mock_db)

        chunks = []
        async for chunk in service.stream_chat("你好"):
            chunks.append(chunk)

        assert chunks == ["你好", "，", "我是", "助手"]
        assert len(chunks) == 4
