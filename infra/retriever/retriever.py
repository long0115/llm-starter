"""
检索器管理类

    - 向量检索器（基于向量相似度）
    - BM25 检索器（关键词匹配）
    - 混合检索器（向量 + BM25）
"""

from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.documents import Document
from infra.adapter.chroma_adapter import chroma_adapter
from infra.utils.log_util import logger
from infra.settings import settings
from functools import lru_cache
from application.ports.retriever_port import RetrieverPort


class RetrieverManager(RetrieverPort):
    
    def __init__(self):
        self.vector_retriever = None
        self.bm25_retriever = None

    def _init_vector_retriever(self):
        """
        初始化向量检索器（向量相似度）
        """

        if self.vector_retriever is not None:
            return

        self.vector_retriever = chroma_adapter.get_retriever()

    def _init_bm25_retriever(self):
        """
        初始化 BM25 检索器（关键词匹配）
        """

        if self.bm25_retriever is not None:
            return

        try:
            # 从向量数据库中获取所有文档
            results = chroma_adapter.get_documents()
            if not results['documents']:
                raise ValueError("向量库中没有数据，无法初始化 BM25")

            documents = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(results['documents'], results['metadatas'])
            ]
            self.bm25_retriever = BM25Retriever.from_documents(documents)
            self.bm25_retriever.k = settings.RAG_BM25_TOP_K
            logger.info(f"BM25 初始化完成，文档数: {len(documents)}")
        except Exception as e:
            raise ValueError(f"无法初始化 BM25: {str(e)}")
    
    def create_hybrid_retriever(self):
        """
        创建混合检索器（向量 + BM25）
        """

        self._init_vector_retriever()
        self._init_bm25_retriever()

        return EnsembleRetriever(
            retrievers=[self.vector_retriever, self.bm25_retriever],
            weights=settings.RAG_HYBRID_WEIGHTS,    # 混合权重 [向量权重, BM25 权重]
        )
    
    def create_rerank_retriever(self, base_retriever: EnsembleRetriever = None):
        """
        创建重排序检索器
        
        Args:
            base_retriever: 基础检索器，默认使用混合检索器
        """

        model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
        compressor = CrossEncoderReranker(model=model, top_n=settings.RAG_RERANK_TOP_K)
        
        return ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever
        )
    

@lru_cache()
def get_retriever_manager() -> RetrieverManager:
    return RetrieverManager()

retriever_manager = get_retriever_manager()