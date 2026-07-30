import logging
from infra.settings import settings
from application.adapter.chroma_adapter import chroma_adapter


if __name__ == "__main__":
    results = chroma_adapter.chroma._collection.get(
        include=['documents', 'metadatas']
    )

    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
        print(f"\n【第 {i+1} 条】")
        print(f"元数据: {meta}")
        print(f"内容预览: {doc[:200]}...")
        print("-" * 50)
    
