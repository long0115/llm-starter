"""
RAG 相关的数据模型（DTO）

定义请求/响应的数据结构，使用 Pydantic 进行自动校验和文档生成。

模型：
    - RagRequest: RAG 查询请求模型
    - RagResponse: RAG 查询响应模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict


class RagRequest(BaseModel):
    """
    RAG 查询请求模型
    
    Fields:
        question: 用户问题（必填）
    """
    question: str = Field(..., description="用户问题")


class RagResponse(BaseModel):
    """
    RAG 查询响应模型
    
    Fields:
        content: 回答内容
        sources: 引用来源列表
    """
    content: str = Field(..., description="回答内容")
    sources: List[Dict] = Field([], description="引用来源列表")
