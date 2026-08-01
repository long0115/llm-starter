"""
文档处理端口（抽象接口）

定义文档加载、清洗、切分的抽象接口。
Service 层只依赖此接口，具体实现由 Infra 层提供。
类比 Java：类似于定义一个 DocumentService 接口，然后由 DocumentServiceImpl 实现。
"""

from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document


class DocumentLoaderPort(ABC):
    """文档加载端口"""
    
    @abstractmethod
    def load(self, file_path: str) -> List[Document]:
        """加载单个文件"""
        pass

    @abstractmethod
    def load_directory(self, directory: str, extensions: List[str] = None) -> List[Document]:
        """加载目录下所有文件"""
        pass


class DocumentCleanerPort(ABC):
    """文档清洗端口"""
    
    @abstractmethod
    def clean(self, docs: List[Document]) -> List[Document]:
        """清洗文档列表"""
        pass


class DocumentSplitterPort(ABC):
    """文档切分端口"""
    
    @abstractmethod
    def split(self, docs: List[Document], doc_type: str = "general") -> List[Document]:
        """切分文档"""
        pass