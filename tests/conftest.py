"""
公共测试 fixtures

提供测试中可复用的 mock 对象和测试数据
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from langchain_core.documents import Document
from langchain_core.messages import AIMessage


@pytest.fixture
def sample_docs():
    """创建测试用文档列表"""
    return [
        Document(
            page_content="员工手册：公司实行标准工时制，上班时间为 09:00，下班时间为 18:00。",
            metadata={"file_name": "员工手册.md", "file_path": "/docs/员工手册.md", "page": 1, "file_type": ".md"},
        ),
        Document(
            page_content="考勤制度：迟到超过规定上班时间未到岗，当月累计 3 次以内口头警告。",
            metadata={"file_name": "考勤制度.md", "file_path": "/docs/考勤制度.md", "page": 1, "file_type": ".md"},
        ),
        Document(
            page_content="请假制度：年休假根据累计工作年限，1-10 年为 5 天，10-20 年为 10 天。",
            metadata={"file_name": "请假制度.md", "file_path": "/docs/请假制度.md", "page": 1, "file_type": ".md"},
        ),
    ]


@pytest.fixture
def mock_llm_adapter():
    """创建 mock LLM 适配器"""
    adapter = MagicMock()
    adapter.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="根据员工手册，公司实行标准工时制，上班时间为 09:00。",
            response_metadata={
                "finish_reason": "stop",
                "token_usage": {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50},
            },
        )
    )
    adapter.astream = AsyncMock()
    return adapter


@pytest.fixture
def mock_session_storage():
    """创建 mock 会话存储"""
    storage = MagicMock()
    storage.create_session.return_value = "test-session-id-123"
    storage.save_message.return_value = None
    storage.get_messages_as_langchain.return_value = []
    return storage


@pytest.fixture
def mock_db():
    """创建 mock 数据库 session"""
    return MagicMock()
