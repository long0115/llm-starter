"""
RAG 服务实现

    - RAG 查询服务
    - 文档入库服务
"""

import os
import json
from langchain_core.output_parsers import StrOutputParser
from api.schemas.rag import RagResponse
from application.ports.document_port import DocumentLoaderPort, DocumentCleanerPort, DocumentSplitterPort
from application.ports.retriever_port import RetrieverPort
from application.ports.prompt_port import PromptPort
from application.ports.llm_client_port import LlmClientPort
from application.ports.vector_store_port import VectorStorePort
from infra.settings import settings
from infra.utils.log_util import logger
from infra.document.formatter import format_docs, extract_sources, get_chunk_id
from infra.storage.session_storage import SessionStorage
from sqlalchemy.orm import Session


class RAGService:

    def __init__(
        self,
        loader: DocumentLoaderPort,
        cleaner: DocumentCleanerPort,
        splitter: DocumentSplitterPort,
        prompt_port: PromptPort,
        retriever_port: RetrieverPort,
        vector_adapter: VectorStorePort,
        llm_adapter: LlmClientPort,
        session_storage: SessionStorage, 
        database: Session
    ):
        self.loader = loader
        self.cleaner = cleaner
        self.splitter = splitter
        self.retriever_port = retriever_port
        self.prompt_port = prompt_port
        self.session_storage = session_storage
        self.database = database
        self.vector_adapter = vector_adapter
        self.llm_adapter = llm_adapter
        self.retriever = None
        self.index_meta_file = os.path.join(settings.CHROMA_STORE_DIR, "index_meta.json")

    async def query(self, question: str, session_id: str = None, use_rerank: bool = False) -> RagResponse:
        """
        执行 RAG 查询

        Args:
            question: 用户问题
            use_rerank: 是否使用 rerank 模型
        """

        # 如果没有会话ID，创建新会话
        if not session_id:
            session_id = self.session_storage.create_session(self.database, session_type="rag")

        # 保存用户消息
        self.session_storage.save_message(self.database, session_id, "user", question)

        # 初始化检索器
        if self.retriever is None:
            self.retriever = self.retriever_port.create_hybrid_retriever()
            # 如果使用 rerank 模型，创建重排序检索器
            if use_rerank:
                    self.retriever = self.retriever_port.create_rerank_retriever(self.retriever)

        # Step 1: 问题改写，只用来检索，不用来回答
        rewritten_query = await self._rewrite_query(question)
        logger.info(f"问题改写: {question} → {rewritten_query}")

        # Step 2: 执行检索
        docs = await self.retriever.ainvoke(rewritten_query)

        # Step 3: 格式化上下文
        context = format_docs(docs)
        
        # Step 4: 构建Prompt并调用LLM，注意这里仍使用改写前的问题
        base_prompt = self.prompt_port.load_prompt(name="rag_base", version="v1")
        prompt = base_prompt.format_messages(context=context, question=question)

        # Step 5: 调用LLM获取回答
        response = await self.llm_adapter.client.ainvoke(prompt)
        answer = response.content

        # 保存AI回复
        self.session_storage.save_message(
            self.database,
            session_id, 
            "assistant", 
            answer,
            token_count=0
        )

        # Step 6: 提取引用来源
        sources = extract_sources(docs)

        return RagResponse(
            content=answer,
            sources=sources
        )

    async def _rewrite_query(self, question: str) -> str:
        """
        问题改写：将口语化问题转为规范的检索问题
        """

        # 初始化 Prompt 模板
        rewrite_prompt = self.prompt_port.load_prompt(name="rag_rewrite", version="v1")
        # 构建链
        chain = rewrite_prompt | self.llm_adapter.client | StrOutputParser()

        return chain.invoke({"question": question})

    def ingest_documents(self, file_path: str, incremental: bool = True):
        """
        入库文档

        Args:
            file_path: 文档文件路径
            incremental: 是否增量更新，默认 True
        """
        
        docs = self.loader.load(file_path)

        if not docs:
            logger.info("没有有效文档，终止入库！")
            return
        
        logger.info(f"共加载 {len(docs)} 个文档")
        clean_docs = self.cleaner.clean(docs)
        logger.info(f"清洗后 {len(clean_docs)} 个有效文档")
        chunks = self.splitter.split(clean_docs, doc_type="general")
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
                self.vector_adapter.add_documents(new_chunks)
            else:
                logger.info("增量更新: 没有需要更新的切片") 
            
            # 保存索引索引元数据
            os.makedirs(os.path.dirname(self.index_meta_file), exist_ok=True)
            with open(self.index_meta_file, "w", encoding="utf-8") as f:
                json.dump(index_meta, f, ensure_ascii=False, indent=2)
        else:
            logger.info("全量更新: 清空覆盖向量库...")
            self.vector_adapter.clear()
            self.vector_adapter.add_documents(chunks)