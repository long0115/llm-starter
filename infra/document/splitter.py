"""
DocumentSplitter - 文档切分器

负责将文档切分为合适大小的 chunks。
"""

from typing import List
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter
)
from langchain_core.documents import Document
from functools import lru_cache
from application.ports.document_port import DocumentSplitterPort


class DocumentSplitter(DocumentSplitterPort):

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size        # 每个 chunk 的最大字符数
        self.chunk_overlap = chunk_overlap  # 相邻 chunk 之间的重叠字符数

    def split(self, docs: List[Document], doc_type: str = "general") -> List[Document]:
        """
        切分文档
        
        Args:
            docs: 文档列表
            doc_type: 文档类型（general/markdown）
        
        Returns:
            切分后的文档 chunk 列表
        """
        if not docs:
            return []
        
        all_chunks = []
    
        for doc in docs:
            # Step 1: 根据文档类型选择切分方式
            if doc_type == "markdown":
                chunks = self._split_markdown(doc)
            else:
                chunks = self._split_general(doc)
            
            # Step 2: 为每个 chunk 添加位置信息
            for j, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = j
                chunk.metadata["char_count"] = len(chunk.page_content)
                chunk.metadata["token_count"] = len(chunk.page_content) // 4 # 每个字符平均 4 个 token
            
            all_chunks.extend(chunks)
        
        return all_chunks

    def _split_markdown(self, doc: Document) -> List[Document]:
        """
        Markdown 文档切分
        
        按标题进行切分，保留 metadata
        """
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "一级标题"),
                ("##", "二级标题"),
                ("###", "三级标题"),
                ("####", "四级标题"),
            ]
        )
        
        # split_text 返回的是 List[Document]，需要合并 metadata
        texts = splitter.split_text(doc.page_content)

        chunks = []
        for text in texts:
            # split_text 返回的可能是 Document 对象或字符串
            if isinstance(text, Document):
                chunk_content = text.page_content
                header_metadata = text.metadata
            else:
                chunk_content = text
                header_metadata = {}

            # 合并原始 metadata 和标题 metadata
            merged_metadata = doc.metadata.copy()
            merged_metadata.update(header_metadata)

            chunk = Document(
                page_content=chunk_content,
                metadata=merged_metadata
            )
            chunks.append(chunk)
        
        return chunks


    def _split_general(self, doc: Document) -> List[Document]:
        """
        通用文档切分
        
        按段落、句子等进行切分，metadata 会自动继承
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " "]
        )
        
        # split_documents 会自动继承 metadata
        chunks = splitter.split_documents([doc])
        
        return chunks


@lru_cache()
def get_document_splitter() -> DocumentSplitter:
    return DocumentSplitter()

document_splitter = get_document_splitter()
