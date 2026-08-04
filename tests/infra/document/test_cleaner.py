"""
文档清洗器测试

测试 DocumentCleaner 的清洗、去短文档、去重功能
"""

import pytest
from langchain_core.documents import Document
from infra.document.cleaner import DocumentCleaner


@pytest.fixture
def cleaner():
    return DocumentCleaner()


class TestClean:
    """测试 clean 方法"""

    def test_clean_basic(self, cleaner):
        """测试基本清洗"""
        docs = [
            Document(
                page_content="  公司实行标准工时制\r\n\r\n\r\n上班时间为 09:00  ",
                metadata={"file_type": ".txt"},
            )
        ]
        result = cleaner.clean(docs)
        assert len(result) == 1
        # 多余空行被清理
        assert "\r\n" not in result[0].page_content
        assert "\n\n\n" not in result[0].page_content
        # 首尾空白被清理
        assert result[0].page_content.startswith("公司")

    def test_clean_markdown(self, cleaner):
        """测试 Markdown 文件清洗"""
        docs = [
            Document(
                page_content="# 标题\n\n## 子标题\n\n正文内容",
                metadata={"file_type": ".md"},
            )
        ]
        result = cleaner.clean(docs)
        assert len(result) == 1
        # Markdown 标记被保留
        assert "# 标题" in result[0].page_content
        assert "## 子标题" in result[0].page_content

    def test_clean_empty_content(self, cleaner):
        """测试空内容文档被过滤"""
        docs = [
            Document(page_content="", metadata={"file_type": ".txt"}),
            Document(page_content="   ", metadata={"file_type": ".txt"}),
        ]
        result = cleaner.clean(docs)
        assert len(result) == 0  # 空内容被过滤

    def test_clean_preserves_metadata(self, cleaner):
        """测试清洗后 metadata 被保留"""
        docs = [
            Document(
                page_content="  测试内容  ",
                metadata={"file_name": "test.md", "file_type": ".md", "page": 1},
            )
        ]
        result = cleaner.clean(docs)
        assert result[0].metadata["file_name"] == "test.md"
        assert result[0].metadata["page"] == 1


class TestRemoveShortDocuments:
    """测试 remove_short_documents 方法"""

    def test_remove_short(self, cleaner):
        """测试移除过短文档"""
        docs = [
            Document(page_content="短", metadata={}),
            Document(page_content="这是一段足够长的内容，超过默认最小长度50", metadata={}),
        ]
        result = cleaner.remove_short_documents(docs, min_length=10)
        assert len(result) == 1
        assert "足够长" in result[0].page_content

    def test_custom_min_length(self, cleaner):
        """测试自定义最小长度"""
        docs = [
            Document(page_content="abc", metadata={}),
            Document(page_content="abcdef", metadata={}),
        ]
        result = cleaner.remove_short_documents(docs, min_length=5)
        assert len(result) == 1
        assert result[0].page_content == "abcdef"


class TestRemoveDuplicates:
    """测试 remove_duplicates 方法"""

    def test_remove_duplicates(self, cleaner):
        """测试移除重复文档"""
        docs = [
            Document(page_content="相同内容", metadata={"file_name": "a.md"}),
            Document(page_content="相同内容", metadata={"file_name": "b.md"}),
            Document(page_content="不同内容", metadata={"file_name": "c.md"}),
        ]
        result = cleaner.remove_duplicates(docs)
        assert len(result) == 2  # 去重后 2 条

    def test_no_duplicates(self, cleaner):
        """测试无重复文档"""
        docs = [
            Document(page_content="内容一", metadata={}),
            Document(page_content="内容二", metadata={}),
        ]
        result = cleaner.remove_duplicates(docs)
        assert len(result) == 2
