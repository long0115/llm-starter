"""
向量存储端口（抽象接口）

定义向量存储操作的标准接口，Service 层只依赖此端口，
具体实现由 Infra 层的 ChromaAdapter 提供。
"""

from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document


class VectorStorePort(ABC):

    @property
    @abstractmethod
    def chroma(self):
        """
        获取 Chroma 数据库客户端实例（懒加载）
        """
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Document], batch_size: int = 10):
        """添加文档到向量库"""
        pass

    @abstractmethod
    def clear(self):
        """清空向量库"""
        pass

    @abstractmethod
    def get_documents(self):
        """获取所有文档"""
        pass

    @abstractmethod
    def get_retriever(self):
        """获取向量检索器"""
        pass