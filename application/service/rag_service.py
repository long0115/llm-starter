"""
RAG 服务实现

    - RAG 查询服务
    - 文档入库服务
"""

import os
import json
import hashlib
from typing import List, Dict
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from infra.prompt.prompt_manager import prompt_manager
from infra.retriever.retriever import retriever_manager
from infra.document.loader import document_loader
from infra.document.splitter import document_splitter
from infra.document.cleaner import document_cleaner
from infra.settings import settings
from infra.utils.log_util import logger
from application.adapter.openai_adapter import openai_adapter
from application.adapter.chroma_adapter import chroma_adapter
from api.schemas.rag import RagResponse
from functools import lru_cache


class RAGService:

    def __init__(self):
        self.chain = None
        self.retriever = None
        self.index_meta_file = os.path.join(settings.CHROMA_STORE_DIR, "index_meta.json")

    def _init_retriever(self, use_rerank: bool = False):
        """
        初始化检索器
        """

        if self.retriever is not None:
            return

        if use_rerank:
            self.retriever = retriever_manager.create_rerank_retriever()
        else:
            self.retriever = retriever_manager.create_hybrid_retriever()
        
        return self.retriever

    def _init_prompt(self, prompt_name: str, prompt_version: str) -> ChatPromptTemplate:
        """
        初始化 Prompt 模板
        """

        try:
            return prompt_manager.load_prompt(name=prompt_name, version=prompt_version)
        except Exception as e:
            logger.error(f"加载 Prompt 模板 {prompt_name}_{prompt_version} 失败，降级到默认模板: {e}")
            return ChatPromptTemplate.from_messages([
                ("system", "你是专业的问答助手。你的任务是根据用户提供的上下文信息，准确地回答用户的问题。\n\n上下文：\n{context}"),
                ("human", "{question}")
            ])

    def _rewrite_query(self, question: str) -> str:
        """
        问题改写：将口语化问题转为规范的检索问题
        """

        # 初始化 Prompt 模板
        rewrite_prompt = self._init_prompt("rag_rewrite", "v1")
        # 构建链
        chain = rewrite_prompt | openai_adapter.client | StrOutputParser()

        return chain.invoke({"question": question})

    def query(self, question: str, use_rerank: bool = False) -> RagResponse:
        """
        执行 RAG 查询

        Args:
            question: 用户问题
            use_rerank: 是否使用 rerank 模型
        """

        # 初始化检索器
        self._init_retriever(use_rerank)

        # 问题改写，只用来检索，不用来回答
        rewritten_query = self._rewrite_query(question)
        logger.info(f"问题改写: {question} → {rewritten_query}")

        # Step 1: 执行检索
        docs = self.retriever.invoke(rewritten_query)

        # Step 2: 格式化上下文
        context = format_docs(docs)
        
        # Step 3: 构建Prompt并调用LLM，注意这里仍使用改写前的问题
        base_prompt = self._init_prompt("rag_base", "v1")
        prompt_input = {
            "context": context,
            "question": question
        }
        prompt = base_prompt.format_messages(**prompt_input)

        # Step 4: 调用LLM获取回答
        response = openai_adapter.client.invoke(prompt)
        answer = response.content

        # Step 5: 提取引用来源
        sources = extract_sources(docs)

        return RagResponse(
            content=answer,
            sources=sources
        )


    def ingest_documents(self, file_path: str, incremental: bool = True):
        """
        入库文档

        Args:
            file_path: 文档文件路径
            incremental: 是否增量更新，默认 True
        """
        
        docs = document_loader.load(file_path)

        if not docs:
            logger.info("没有有效文档，终止入库！")
            return
        
        logger.info(f"共加载 {len(docs)} 个文档")
        clean_docs = document_cleaner.clean(docs)
        logger.info(f"清洗后 {len(clean_docs)} 个有效文档")
        chunks = document_splitter.split(clean_docs, doc_type="general")
        logger.info(f"切分为 {len(chunks)} 个切片")

        if incremental:
            index_meta = {}
            # 加载索引索引元数据
            if os.path.exists(self.index_meta_file):
                with open(self.index_meta_file, "r", encoding="utf-8") as f:
                    index_meta = json.load(f)

            new_chunks = []
            for chunk in chunks:
                chunk_id = get_chunk_id(chunk)
                
                if chunk_id in index_meta:
                    continue
                
                index_meta[chunk_id] = {
                    "file_path": chunk.metadata.get("file_path", ""),
                    "file_name": chunk.metadata.get("file_name", ""),
                    "page": chunk.metadata.get("page", None)
                }
                new_chunks.append(chunk)
            
            if new_chunks:
                logger.info(f"增量更新: {len(new_chunks)} 个需要更新的切片")
                chroma_adapter.add_documents(new_chunks)
            else:
                logger.info("增量更新: 没有需要更新的切片") 
            
            # 保存索引索引元数据
            os.makedirs(os.path.dirname(self.index_meta_file), exist_ok=True)
            with open(self.index_meta_file, "w", encoding="utf-8") as f:
                json.dump(index_meta, f, ensure_ascii=False, indent=2)
        else:
            logger.info("全量更新: 清空覆盖向量库...")
            chroma_adapter.clear()
            chroma_adapter.add_documents(chunks)


@lru_cache()
def get_rag_service() -> RAGService:
    return RAGService()

rag_service = get_rag_service()


def format_docs(docs) -> str:
    """
    格式化文档列表为字符串
    
    Args:
        docs: 文档列表
    
    Returns:
        str: 格式化后的文档字符串
    """
    formatted = []
    for i, doc in enumerate(docs, 1):
        file_name = doc.metadata.get("file_name", "未知来源")
        formatted.append(f"[{i}] {doc.page_content}\n【来源：{file_name}】")
    return "\n\n".join(formatted)

def extract_sources(docs: List[Document]) -> List[Dict]:
    """
    从检索到的文档列表中提取引用来源信息
    
    Args:
        docs: 检索到的文档列表

    Returns:
        List[Dict]: 引用来源列表，每个元素包含 file_name、file_path、 page 字段
    """
    sources = []
    seen = set()  # 去重
    
    for doc in docs:
        file_name = doc.metadata.get("file_name", "未知来源")
        file_path = doc.metadata.get("file_path", "")
        page = doc.metadata.get("page", None)
        
        # 按文件+页码去重
        key = f"{file_name}_{page}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "file_name": file_name,
                "file_path": file_path,
                "page": page
            })
    
    return sources

def get_chunk_id(chunk) -> str:
        """
        获取 chunk ID
        
        Args:
            chunk: 文档 chunk
        
        Returns:
            str: chunk ID
        """
        content = chunk.page_content
        file_path = chunk.metadata.get("file_path", "")
        page = chunk.metadata.get("page", "")
        
        hash_str = f"{file_path}|{page}|{content[:500]}"
        return hashlib.md5(hash_str.encode("utf-8")).hexdigest()