"""
DocumentLoader - 文档加载器

负责从文件系统加载各种格式的文档。
"""

import os
from typing import List
from datetime import datetime
from langchain_community.document_loaders import TextLoader, UnstructuredFileLoader
from langchain_core.documents import Document
from infra.utils.log_util import logger
from application.ports.document_port import DocumentLoaderPort
from functools import lru_cache


class DocumentLoader(DocumentLoaderPort):

    def load(self, file_path: str) -> List[Document]:
        """
        加载单个文档文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            文档列表
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return []

        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        docs = []
        try:
            if file_ext == ".txt" or file_ext == ".md":
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                loader = UnstructuredFileLoader(file_path)
            
            docs = loader.load()
        
        except Exception as e:
            logger.error(f"文档解析失败: {file_path}, 降级为普通文本加载: {str(e)}")
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()

        # 为每个文档添加元数据
        for i, doc in enumerate(docs):
            doc.metadata["file_path"] = os.path.abspath(file_path)
            doc.metadata["file_name"] = file_name
            doc.metadata["file_type"] = file_ext
            doc.metadata["page"] = i + 1
            doc.metadata["created_at"] = datetime.now().isoformat()
            
        return docs
        

    def load_directory(self, directory: str, extensions: List[str] = None) -> List[Document]:
        """
        加载目录下的所有文档
        
        Args:
            directory: 目录路径
            extensions: 要加载的文件扩展名列表（可选）
        
        Returns:
            文档列表
        """
        all_docs = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if extensions and ext not in extensions:
                    continue
                
                docs = self.load(file_path)
                all_docs.extend(docs)
        
        return all_docs


@lru_cache()
def get_document_loader() -> DocumentLoader:
    return DocumentLoader()

document_loader = get_document_loader()
