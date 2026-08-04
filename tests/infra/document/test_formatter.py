"""
文档格式化工具测试

测试 format_docs、extract_sources、get_chunk_id 三个工具函数
"""

import pytest
from langchain_core.documents import Document
from infra.document.formatter import format_docs, extract_sources, get_chunk_id


class TestFormatDocs:
    """测试 format_docs 函数"""

    def test_format_single_doc(self):
        """测试单个文档格式化"""
        docs = [
            Document(
                page_content="公司实行标准工时制",
                metadata={"file_name": "员工手册.md"},
            )
        ]
        result = format_docs(docs)
        assert "[1]" in result
        assert "公司实行标准工时制" in result
        assert "【来源：员工手册.md】" in result

    def test_format_multiple_docs(self):
        """测试多个文档格式化"""
        docs = [
            Document(page_content="内容一", metadata={"file_name": "文件1.md"}),
            Document(page_content="内容二", metadata={"file_name": "文件2.md"}),
        ]
        result = format_docs(docs)
        assert "[1]" in result
        assert "[2]" in result
        assert "内容一" in result
        assert "内容二" in result
        # 多个文档之间用双换行分隔
        assert "\n\n" in result

    def test_format_empty_docs(self):
        """测试空文档列表"""
        result = format_docs([])
        assert result == ""

    def test_format_missing_file_name(self):
        """测试缺少 file_name 的文档"""
        docs = [Document(page_content="内容", metadata={})]
        result = format_docs(docs)
        assert "未知来源" in result


class TestExtractSources:
    """测试 extract_sources 函数"""

    def test_extract_single_source(self):
        """测试提取单个来源"""
        docs = [
            Document(
                page_content="内容",
                metadata={
                    "file_name": "员工手册.md",
                    "file_path": "/docs/员工手册.md",
                    "page": 1,
                },
            )
        ]
        result = extract_sources(docs)
        assert len(result) == 1
        assert result[0]["file_name"] == "员工手册.md"
        assert result[0]["file_path"] == "/docs/员工手册.md"
        assert result[0]["page"] == 1

    def test_extract_dedup_same_file_page(self):
        """测试同文件同页码去重"""
        docs = [
            Document(
                page_content="内容一",
                metadata={"file_name": "员工手册.md", "file_path": "/docs/员工手册.md", "page": 1},
            ),
            Document(
                page_content="内容二",
                metadata={"file_name": "员工手册.md", "file_path": "/docs/员工手册.md", "page": 1},
            ),
        ]
        result = extract_sources(docs)
        assert len(result) == 1  # 去重后只有 1 条

    def test_extract_different_pages(self):
        """测试不同页码不去重"""
        docs = [
            Document(
                page_content="内容一",
                metadata={"file_name": "员工手册.md", "file_path": "/docs/员工手册.md", "page": 1},
            ),
            Document(
                page_content="内容二",
                metadata={"file_name": "员工手册.md", "file_path": "/docs/员工手册.md", "page": 2},
            ),
        ]
        result = extract_sources(docs)
        assert len(result) == 2  # 不同页码，不去重

    def test_extract_empty_docs(self):
        """测试空文档列表"""
        result = extract_sources([])
        assert result == []

    def test_extract_missing_metadata(self):
        """测试缺少 metadata 字段"""
        docs = [Document(page_content="内容", metadata={})]
        result = extract_sources(docs)
        assert len(result) == 1
        assert result[0]["file_name"] == "未知来源"
        assert result[0]["file_path"] == ""
        assert result[0]["page"] is None


class TestGetChunkId:
    """测试 get_chunk_id 函数"""

    def test_get_chunk_id_basic(self):
        """测试基本 chunk ID 生成"""
        chunk = Document(
            page_content="这是一段测试内容",
            metadata={"file_path": "/docs/test.md", "page": 1},
        )
        chunk_id = get_chunk_id(chunk)
        assert isinstance(chunk_id, str)
        assert len(chunk_id) == 32  # MD5 hex digest 长度

    def test_same_content_same_id(self):
        """测试相同内容生成相同 ID"""
        chunk1 = Document(
            page_content="相同内容",
            metadata={"file_path": "/docs/test.md", "page": 1},
        )
        chunk2 = Document(
            page_content="相同内容",
            metadata={"file_path": "/docs/test.md", "page": 1},
        )
        assert get_chunk_id(chunk1) == get_chunk_id(chunk2)

    def test_different_content_different_id(self):
        """测试不同内容生成不同 ID"""
        chunk1 = Document(
            page_content="内容一",
            metadata={"file_path": "/docs/test.md", "page": 1},
        )
        chunk2 = Document(
            page_content="内容二",
            metadata={"file_path": "/docs/test.md", "page": 1},
        )
        assert get_chunk_id(chunk1) != get_chunk_id(chunk2)

    def test_different_page_different_id(self):
        """测试不同页码生成不同 ID"""
        chunk1 = Document(
            page_content="相同内容",
            metadata={"file_path": "/docs/test.md", "page": 1},
        )
        chunk2 = Document(
            page_content="相同内容",
            metadata={"file_path": "/docs/test.md", "page": 2},
        )
        assert get_chunk_id(chunk1) != get_chunk_id(chunk2)

    def test_long_content_truncated(self):
        """测试长内容只取前 500 字符"""
        long_content = "a" * 1000
        chunk = Document(
            page_content=long_content,
            metadata={"file_path": "/docs/test.md", "page": 1},
        )
        chunk_id = get_chunk_id(chunk)
        assert isinstance(chunk_id, str)
        assert len(chunk_id) == 32
