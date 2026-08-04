"""
文档切分器测试

测试 DocumentSplitter 的切分功能
"""

import pytest
from langchain_core.documents import Document
from infra.document.splitter import DocumentSplitter


@pytest.fixture
def splitter():
    return DocumentSplitter(chunk_size=100, chunk_overlap=10)


class TestSplitGeneral:
    """测试通用文档切分"""

    def test_split_short_doc(self, splitter):
        """测试短文档（不超过 chunk_size）"""
        docs = [Document(page_content="这是一段很短的内容", metadata={"file_name": "test.txt"})]
        result = splitter.split(docs, doc_type="general")
        assert len(result) >= 1

    def test_split_long_doc(self, splitter):
        """测试长文档被切分为多个 chunk"""
        long_text = "这是一段测试内容。" * 50  # 约 500 字符
        docs = [Document(page_content=long_text, metadata={"file_name": "test.txt"})]
        result = splitter.split(docs, doc_type="general")
        assert len(result) > 1  # 长文档应被切分为多个 chunk

    def test_split_empty_docs(self, splitter):
        """测试空文档列表"""
        result = splitter.split([], doc_type="general")
        assert result == []

    def test_split_metadata_inherited(self, splitter):
        """测试切分后 metadata 被继承"""
        docs = [
            Document(
                page_content="测试内容 " * 30,
                metadata={"file_name": "test.txt", "file_path": "/docs/test.txt"},
            )
        ]
        result = splitter.split(docs, doc_type="general")
        for chunk in result:
            assert chunk.metadata["file_name"] == "test.txt"
            assert chunk.metadata["file_path"] == "/docs/test.txt"

    def test_split_chunk_metadata(self, splitter):
        """测试 chunk 位置信息"""
        docs = [Document(page_content="测试内容 " * 30, metadata={})]
        result = splitter.split(docs, doc_type="general")
        for chunk in result:
            assert "chunk_index" in chunk.metadata
            assert "char_count" in chunk.metadata
            assert "token_count" in chunk.metadata


class TestSplitMarkdown:
    """测试 Markdown 文档切分"""

    def test_split_markdown_by_headers(self, splitter):
        """测试按标题切分 Markdown"""
        md_content = """# 第一章

第一章的内容，这里有很多文字描述。

## 1.1 小节

小节的具体内容。

## 1.2 小节

另一个小节的内容。
"""
        docs = [Document(page_content=md_content, metadata={"file_name": "test.md"})]
        result = splitter.split(docs, doc_type="markdown")
        assert len(result) >= 2  # 至少按标题切出 2 个 chunk

    def test_split_markdown_metadata(self, splitter):
        """测试 Markdown 切分后 metadata 继承"""
        md_content = "# 标题\n\n标题下的内容。"
        docs = [Document(
            page_content=md_content,
            metadata={"file_name": "test.md", "file_path": "/docs/test.md"},
        )]
        result = splitter.split(docs, doc_type="markdown")
        for chunk in result:
            assert chunk.metadata["file_name"] == "test.md"
