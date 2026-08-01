"""
文档格式化工具

提供文档格式化、来源提取、chunk ID 生成等工具方法
"""

import hashlib
from typing import List, Dict
from langchain_core.documents import Document


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
        List[Dict]: 引用来源列表，每个元素包含 file_name、file_path、page 字段
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
