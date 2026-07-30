from pydantic import BaseModel, Field
from typing import Optional

class AgentRequest(BaseModel):
    """
    Agent 请求模型

    Fields:
        question: 用户问题（必填）
        thread_id: 会话 ID（默认 default）
    """
    question: str = Field(..., description="用户问题")
    thread_id: Optional[str] = Field("default", description="会话 ID")

class AgentResponse(BaseModel):
    """
    Agent 响应模型

    Fields:
        content: 回答内容
    """
    content: str = Field(..., description="回答内容")