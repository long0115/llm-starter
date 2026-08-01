"""
ChromaDB 适配器

    - 初始化 ChromaDB 客户端
    - add_documents 方法：添加文档到向量数据库
    - get_documents 方法：获取所有文档
    - clear 方法：清空向量数据库
    - get_retriever 方法：获取检索器
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from functools import lru_cache
from application.ports.vector_store_port import VectorStorePort
from infra.adapter.openai_adapter import openai_adapter
from infra.utils.log_util import logger
from infra.settings import settings


class ChromaAdapter(VectorStorePort):

    def __init__(self):
        self._chroma = None
        self._embedding = None
        self.collection_name = settings.CHROMA_STORE_COLLECTION
        self.persist_directory = settings.CHROMA_STORE_DIR

    @property
    def chroma(self):
        """
        初始化 ChromaDB 客户端实例
        """
        if self._chroma is None:
            self._chroma = Chroma(
                collection_name=self.collection_name,
                embedding_function=openai_adapter.embedding,
                persist_directory=self.persist_directory
            )
            logger.info(f"ChromaDB 客户端初始化完成: {self.collection_name}")
        return self._chroma

    def add_documents(self, documents: list[Document], batch_size: int = 10):
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表
            batch_size: 每次入库的文档数量，默认 10
        """
        if not documents:
            logger.info("没有文档需要入库")
            return
        # 分批入库，避免单次请求过大
        total = len(documents)
        for i in range(0, total, batch_size):
            batch = documents[i : i + batch_size]
            self.chroma.add_documents(batch)
            logger.info(f"入库进度: {min(i + batch_size, total)}/{total}")

    def get_documents(self):
        """
        获取所有文档
        
        Returns:
            所有文档的元组
        """
        return self.chroma.get(include=['documents', 'metadatas'])

    def clear(self):
        """
        清空向量数据库
        """
        self.chroma._client.delete_collection(name=self.collection_name)

    def get_retriever(self):
        """
        获取向量数据库的检索器
        
        Args:
            top_k: 检索结果返回的文档数量，默认 10
        Returns:
            检索器实例
        """
        return self.chroma.as_retriever(
            search_type="similarity",                           # 相似度检索
            search_kwargs={"k": settings.RAG_VECTOR_TOP_K}      # 返回 top_k 个最相似的文档
        )
    

@lru_cache()
def get_chroma_adapter() -> ChromaAdapter:
    return ChromaAdapter()

chroma_adapter = get_chroma_adapter()
