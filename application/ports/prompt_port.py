"""
Prompt 管理端口（抽象接口）
"""

from abc import ABC, abstractmethod
from langchain_core.prompts import ChatPromptTemplate


class PromptPort(ABC):
    """Prompt 管理端口"""
    
    @abstractmethod
    def load_prompt(self, name: str, version: str = "v1") -> ChatPromptTemplate:
        """加载 Prompt 模板"""
        pass