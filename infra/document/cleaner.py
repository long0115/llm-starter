"""
DocumentCleaner - 文档清洗器

负责清洗文档内容，去除无用信息。
"""

import re
from typing import List
from langchain_core.documents import Document
from application.ports.document_port import DocumentCleanerPort
from functools import lru_cache


class DocumentCleaner(DocumentCleanerPort):

    def clean(self, docs: List[Document]) -> List[Document]:
        """
        清洗文档列表
        
        Args:
            docs: 文档列表
        
        Returns:
            清洗后的文档列表
        """
        cleaned_docs = []
        
        for doc in docs:
            file_type = doc.metadata.get("file_type", "")
            cleaned_content = self._clean_content(doc.page_content, file_type)
            
            if cleaned_content.strip():
                cleaned_doc = Document(
                    page_content=cleaned_content,
                    metadata=doc.metadata
                )
                cleaned_docs.append(cleaned_doc)
        
        return cleaned_docs

    def _clean_content(self, content: str, file_type: str = "") -> str:
        """
        清洗文档内容
        
        Args:
            content: 原始内容
            file_type: 文件类型（md/txt/pdf等），用于差异化清洗
        """
        if not content:
            return ""
        
        # 统一换行符
        content = content.replace("\r\n", "\n")
        
        # 去除多余空行
        content = re.sub(r"\n{3,}", "\n\n", content)
        
        # 根据文件类型进行差异化清洗
        if file_type == ".md":
            # Markdown 文件：保留标题、列表、代码块标记
            content = self._clean_markdown(content)
        else:
            # 其他文件：通用清洗
            content = self._clean_generic(content)
        
        # 去除首尾空白
        content = content.strip()
        
        return content
    
    def _clean_markdown(self, content: str) -> str:
        """
        Markdown 文件专用清洗
        
        保留：
        - # 标题标记
        - - 列表标记
        - * 强调标记
        - ` 代码标记
        - | 表格标记
        """
        # 保留 Markdown 常用符号
        content = re.sub(r"[^\w\u4e00-\u9fa5\s\n.,，。！？!?'\"()（）<>《》【】\-\—:：;；#*`|]", "", content)
        
        # 清理行内多余空格（保留代码块内的空格）
        lines = content.split("\n")
        cleaned_lines = []
        for line in lines:
            if not line.strip().startswith("```"):  # 代码块不清理
                line = re.sub(r" {2,}", " ", line)
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)

    def _clean_generic(self, content: str) -> str:
        """
        通用清洗（非 Markdown 文件）
        """
        # 去除特殊字符
        content = re.sub(r"[^\w\u4e00-\u9fa5\s\n.,，。！？!?'\"()（）<>《》【】\-\—:：;；]", "", content)
        content = re.sub(r"\s{2,}", " ", content)
        
        return content

    def remove_short_documents(self, docs: List[Document], min_length: int = 50) -> List[Document]:
        """
        移除过短的文档
        
        Args:
            docs: 文档列表
            min_length: 最小长度（默认 50）
        
        Returns:
            过滤后的文档列表
        """
        filtered = [doc for doc in docs if len(doc.page_content) >= min_length]
        return filtered

    def remove_duplicates(self, docs: List[Document]) -> List[Document]:
        """
        移除重复文档
        
        Args:
            docs: 文档列表
        
        Returns:
            去重后的文档列表
        """
        seen = set()
        unique_docs = []
        
        for doc in docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen:
                seen.add(content_hash)
                unique_docs.append(doc)
        
        return unique_docs


@lru_cache()
def get_document_cleaner() -> DocumentCleaner:
    return DocumentCleaner()

document_cleaner = get_document_cleaner()