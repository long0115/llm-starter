"""
检索器端口（抽象接口）
"""

from abc import ABC, abstractmethod
from typing import List
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever


class RetrieverPort(ABC):
    """检索器端口"""
    
    @abstractmethod
    def create_hybrid_retriever(self) -> EnsembleRetriever:
        """创建混合检索器"""
        pass

    @abstractmethod
    def create_rerank_retriever(self) -> ContextualCompressionRetriever:
        """创建重排序检索器"""
        pass