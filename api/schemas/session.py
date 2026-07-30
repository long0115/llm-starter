"""
Session 相关的数据模型（DTO）

定义请求/响应的数据结构，使用 Pydantic 进行自动校验和文档生成。

模型：
    - SessionRequest: 会话创建请求模型
    - SessionResponse: 会话创建响应模型
    - MessageRequest: 消息查询请求模型
    - MessageResponse: 消息查询响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional


class SessionRequest(BaseModel):
    session_type: str = Field("chat", description="会话类型 (chat/rag/agent)")
    title: Optional[str] = Field(None, description="会话标题（可选）")
    limit: int = Field(50, description="返回的消息数量（默认 50）")


class SessionResponse(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    title: str = Field(..., description="会话标题")
    session_type: str = Field(..., description="会话类型 (chat/rag/agent)")
    is_active: bool = Field(..., description="会话是否活跃")
    created_at: Optional[str] = Field(None, description="会话创建时间")
    updated_at: Optional[str] = Field(None, description="会话更新时间")


class MessageRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    limit: int = Field(50, description="返回的消息数量（默认 50）")


class MessageResponse(BaseModel):
    id: int = Field(..., description="消息 ID")
    role: str = Field(..., description="消息角色 (user/assistant/system)")
    content: str = Field(..., description="消息内容")
    token_count: int = Field(0, description="消息 token 数量")
    meta_data: dict = Field({}, description="消息元数据")
    created_at: Optional[str] = Field(None, description="消息创建时间")
