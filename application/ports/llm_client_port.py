"""
LLM 模型端口（抽象接口）

定义 LLM 调用的标准接口，Service 层只依赖此端口，
具体实现由 Infra 层的 OpenAIAdapter 提供。
"""

from abc import ABC, abstractmethod
from typing import List, AsyncIterator
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, AIMessage
from pydantic import BaseModel


class LlmClientPort(ABC):

    @property
    @abstractmethod
    def client(self):
        """
        获取 LLM 客户端实例（懒加载）
        """
        pass

    @property
    @abstractmethod
    def embedding(self):
        """
        获取 Embedding 向量模型实例（懒加载）
        """
        pass

    @abstractmethod
    def invoke(self, question: str, system_content: str = None, messages: List[BaseMessage] = None) -> AIMessage:
        """
        同步对话接口
        
        Args:
            question: 用户输入
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
        
        Returns:
            LLM 返回的消息
        """
        pass

    @abstractmethod
    async def ainvoke(self, question: str, system_content: str = None, messages: List[BaseMessage] = None) -> AIMessage:
        """
        异步对话接口
        
        Args:
            question: 用户输入
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
        
        Returns:
            LLM 返回的消息
        """
        pass

    @abstractmethod
    def astream(self, question: str, system_content: str = None, messages: List[BaseMessage] = None) -> AsyncIterator[str]:
        """
        异步流式对话接口
        
        Args:
            question: 用户输入
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
        
        Returns:
            异步迭代器，每次返回一个文本块
        """
        pass

    @abstractmethod
    def invoke_with_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """
        使用消息列表调用 LLM
        
        Args:
            messages: 消息列表
        
        Returns:
            LLM 返回的消息
        """
        pass

    @abstractmethod
    def invoke_with_structure(self, question: str, system_content: str, messages: List[BaseMessage], schema: type[BaseModel]) -> BaseModel:
        """
        调用 LLM 并返回结构化输出
        
        Args:
            question: 用户输入
            system_content: 系统提示词
            messages: 历史消息列表（可选）
            schema: 结构化输出的 Pydantic 模型
        
        Returns:
            符合 schema 的结构化输出
        """
        pass

    @abstractmethod
    def invoke_with_tools(self, question: str, system_content: str, messages: List[BaseMessage], tools: List[BaseTool]) -> AIMessage:
        """
        调用 LLM 并绑定工具
        
        Args:
            question: 用户输入
            system_content: 系统提示词
            messages: 历史消息列表（可选）
            tools: 可用工具列表
        
        Returns:
            LLM 返回的消息（可能包含工具调用指令）
        """
        pass
