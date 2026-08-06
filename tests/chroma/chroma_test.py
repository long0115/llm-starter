"""
ChromaDB 向量数据库查询测试

功能：
    - 查询 ChromaDB 中存储的所有切片内容
    - 按关键词相似度检索切片
    - 查看切片的 metadata 信息

运行方式：
    python -m pytest tests/chroma/chroma_test.py -v -s
"""

import pytest
from infra.adapter.chroma_adapter import chroma_adapter


class TestChromaQuery:
    """测试 ChromaDB 查询"""

    def test_get_all_documents(self):
        """查询所有切片内容"""
        results = chroma_adapter.get_documents()

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])

        print(f"\n===== ChromaDB 切片统计 =====")
        print(f"集合名称: {chroma_adapter.collection_name}")
        print(f"存储目录: {chroma_adapter.persist_directory}")
        print(f"切片总数: {len(documents)}")
        print(f"{'=' * 40}")

        assert len(documents) > 0, "向量库中没有数据"

        # 打印前 5 条切片
        for i in range(min(5, len(documents))):
            print(f"\n--- 切片 {i + 1} ---")
            print(f"ID: {ids[i]}")
            print(f"内容: {documents[i][:100]}...")
            print(f"来源: {metadatas[i].get('file_name', '未知')}")
            print(f"页码: {metadatas[i].get('page', 'N/A')}")

    def test_similarity_search(self):
        """按关键词相似度检索切片"""
        query = "年假"
        top_k = 3

        print(f"\n===== 相似度检索: '{query}' =====")

        # 使用 Chroma 原生相似度搜索
        results = chroma_adapter.chroma.similarity_search(query, k=top_k)

        assert len(results) > 0, f"未检索到与 '{query}' 相关的切片"

        for i, doc in enumerate(results, 1):
            print(f"\n--- 结果 {i} (相似度排名) ---")
            print(f"内容: {doc.page_content[:150]}...")
            print(f"来源: {doc.metadata.get('file_name', '未知')}")
            print(f"页码: {doc.metadata.get('page', 'N/A')}")

    def test_similarity_search_with_score(self):
        """按关键词检索并返回相似度分数"""
        query = "考勤"
        top_k = 3

        print(f"\n===== 带分数检索: '{query}' =====")

        results = chroma_adapter.chroma.similarity_search_with_score(query, k=top_k)

        for i, (doc, score) in enumerate(results, 1):
            print(f"\n--- 结果 {i} ---")
            print(f"相似度分数: {score:.4f} (越小越相似)")
            print(f"内容: {doc.page_content[:150]}...")
            print(f"来源: {doc.metadata.get('file_name', '未知')}")

    def test_search_by_metadata_filter(self):
        """按 metadata 过滤检索"""
        query = "制度"
        file_name = "考勤制度.md"

        print(f"\n===== 按来源过滤检索 =====")
        print(f"关键词: '{query}', 来源: '{file_name}'")

        results = chroma_adapter.chroma.similarity_search(
            query,
            k=3,
            filter={"file_name": file_name}
        )

        for i, doc in enumerate(results, 1):
            print(f"\n--- 结果 {i} ---")
            print(f"内容: {doc.page_content[:150]}...")
            print(f"来源: {doc.metadata.get('file_name', '未知')}")

        # 验证结果都来自指定文件
        for doc in results:
            assert doc.metadata.get("file_name") == file_name

    def test_collection_info(self):
        """查看集合基本信息"""
        collection = chroma_adapter.chroma._collection

        print(f"\n===== 集合信息 =====")
        print(f"集合名称: {collection.name}")
        count = collection.count()
        print(f"文档数量: {count}")
        print(f"{'=' * 40}")

        assert count > 0, "集合为空"
