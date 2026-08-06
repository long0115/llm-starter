"""
对话相关的数据模型（DTO）

定义请求/响应的数据结构，使用 Pydantic 进行自动校验和文档生成。

模型：
    - ChatRequest: 对话请求模型
    - ChatResponse: 对话响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """
    对话请求模型
    
    Fields:
        message: 用户消息（必填）
        system_content: 系统提示词（可选）
        temperature: 温度参数（可选）
    """
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")


class ChatResponse(BaseModel):
    """
    对话响应模型
    
    Fields:
        content: 回复内容
        finish_reason: 结束原因
        token_usage: Token 使用情况
    """
    content: str = Field(..., description="回复内容")
    finish_reason: Optional[str] = Field("stop", description="结束原因")
    token_usage: Optional[dict] = Field(None, description="Token 使用情况")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")

