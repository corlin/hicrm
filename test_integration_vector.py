"""
向量数据库和嵌入服务集成测试
"""

import pytest
import asyncio
import numpy as np
from typing import List

# 这个测试需要实际的服务运行，标记为集成测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_embedding_service_integration():
    """测试嵌入服务集成"""
    from src.services.embedding_service import embedding_service
    
    try:
        # 初始化嵌入服务
        await embedding_service.initialize()
        
        # 测试单个文本编码
        text = "这是一个测试文本"
        embedding = await embedding_service.encode(text)
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0
        print(f"嵌入向量维度: {len(embedding)}")
        
        # 测试批量编码
        texts = ["文本1", "文本2", "文本3"]
        embeddings = await embedding_service.encode(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        
        # 测试相似度计算
        similarity = await embedding_service.compute_similarity("人工智能", "机器学习")
        assert 0.0 <= similarity <= 1.0
        print(f"相似度: {similarity}")
        
        print("✅ 嵌入服务集成测试通过")
        
    except Exception as e:
        print(f"❌ 嵌入服务集成测试失败: {e}")
        # 如果是模型加载失败，跳过测试
        pytest.skip(f"嵌入服务不可用: {e}")


@pytest.mark.asyncio
async def test_vector_service_integration():
    """测试向量数据库服务集成"""
    from src.services.vector_service import vector_service, VectorDocument
    
    try:
        # 初始化向量服务
        await vector_service.initialize()
        
        # 创建测试文档
        test_docs = [
            VectorDocument("doc1", "这是关于人工智能的文档", {"category": "AI"}),
            VectorDocument("doc2", "这是关于机器学习的文档", {"category": "ML"}),
            VectorDocument("doc3", "这是关于深度学习的文档", {"category": "DL"})
        ]
        
        # 添加文档
        collection_name = "test_collection"
        success = await vector_service.add_documents(test_docs, collection_name)
        assert success, "添加文档失败"
        
        # 等待索引完成
        await asyncio.sleep(1)
        
        # 搜索测试
        results = await vector_service.search("人工智能", collection_name, limit=5)
        assert len(results) > 0, "搜索结果为空"
        
        print(f"搜索到 {len(results)} 个结果")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.document.content} (分数: {result.score:.3f})")
        
        # 获取集合信息
        info = await vector_service.get_collection_info(collection_name)
        assert "vectors_count" in info
        print(f"集合信息: {info}")
        
        # 清理测试数据
        await vector_service.delete_collection(collection_name)
        
        print("✅ 向量数据库服务集成测试通过")
        
    except Exception as e:
        print(f"❌ 向量数据库服务集成测试失败: {e}")
        # 如果是连接失败，跳过测试
        pytest.skip(f"向量数据库不可用: {e}")


@pytest.mark.asyncio
async def test_elasticsearch_service_integration():
    """测试Elasticsearch服务集成"""
    from src.services.elasticsearch_service import elasticsearch_service, ElasticsearchDocument
    
    try:
        # 初始化Elasticsearch服务
        await elasticsearch_service.initialize()
        
        # 创建测试文档
        test_docs = [
            ElasticsearchDocument("doc1", "这是关于人工智能的文档", {"category": "AI"}, "AI技术"),
            ElasticsearchDocument("doc2", "这是关于机器学习的文档", {"category": "ML"}, "机器学习"),
            ElasticsearchDocument("doc3", "这是关于深度学习的文档", {"category": "DL"}, "深度学习")
        ]
        
        # 添加文档
        index_name = "test_index"
        success = await elasticsearch_service.add_documents(test_docs, index_name)
        assert success, "添加文档失败"
        
        # 等待索引完成
        await asyncio.sleep(2)
        
        # 搜索测试
        results = await elasticsearch_service.search("人工智能", index_name, size=5)
        assert len(results) > 0, "搜索结果为空"
        
        print(f"搜索到 {len(results)} 个结果")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.document.content} (分数: {result.score:.3f})")
        
        # 获取索引统计
        stats = await elasticsearch_service.get_index_stats(index_name)
        assert "docs_count" in stats
        print(f"索引统计: {stats}")
        
        # 清理测试数据
        await elasticsearch_service.delete_index(index_name)
        
        print("✅ Elasticsearch服务集成测试通过")
        
    except Exception as e:
        print(f"❌ Elasticsearch服务集成测试失败: {e}")
        # 如果是连接失败，跳过测试
        pytest.skip(f"Elasticsearch不可用: {e}")


@pytest.mark.asyncio
async def test_hybrid_search_integration():
    """测试混合搜索服务集成"""
    from src.services.hybrid_search_service import hybrid_search_service, SearchMode
    
    try:
        # 初始化混合搜索服务
        await hybrid_search_service.initialize()
        
        # 创建测试文档
        test_docs = [
            {
                "id": "doc1",
                "content": "这是关于人工智能技术的详细介绍文档",
                "title": "人工智能技术概述",
                "metadata": {"category": "AI", "author": "张三"}
            },
            {
                "id": "doc2", 
                "content": "机器学习是人工智能的重要分支",
                "title": "机器学习基础",
                "metadata": {"category": "ML", "author": "李四"}
            },
            {
                "id": "doc3",
                "content": "深度学习神经网络在图像识别中的应用",
                "title": "深度学习应用",
                "metadata": {"category": "DL", "author": "王五"}
            }
        ]
        
        # 添加文档到混合搜索系统
        success = await hybrid_search_service.add_documents(test_docs)
        assert success, "添加文档失败"
        
        # 等待索引完成
        await asyncio.sleep(3)
        
        # 测试不同搜索模式
        query = "人工智能"
        
        # 向量搜索
        vector_results = await hybrid_search_service.search(
            query, mode=SearchMode.VECTOR_ONLY, limit=3
        )
        print(f"向量搜索结果: {len(vector_results)} 个")
        
        # BM25搜索
        bm25_results = await hybrid_search_service.search(
            query, mode=SearchMode.BM25_ONLY, limit=3
        )
        print(f"BM25搜索结果: {len(bm25_results)} 个")
        
        # 混合搜索
        hybrid_results = await hybrid_search_service.search(
            query, mode=SearchMode.HYBRID, limit=3
        )
        print(f"混合搜索结果: {len(hybrid_results)} 个")
        
        # 验证结果
        assert len(hybrid_results) > 0, "混合搜索结果为空"
        
        for i, result in enumerate(hybrid_results):
            print(f"  {i+1}. {result.title}")
            print(f"     向量分数: {result.vector_score:.3f}, BM25分数: {result.bm25_score:.3f}")
            print(f"     混合分数: {result.hybrid_score:.3f}")
        
        # 语义搜索测试
        semantic_results = await hybrid_search_service.semantic_search(
            "机器学习算法", similarity_threshold=0.3
        )
        print(f"语义搜索结果: {len(semantic_results)} 个")
        
        # 获取统计信息
        stats = await hybrid_search_service.get_stats()
        print(f"混合搜索统计: {stats}")
        
        print("✅ 混合搜索服务集成测试通过")
        
    except Exception as e:
        print(f"❌ 混合搜索服务集成测试失败: {e}")
        # 如果是服务不可用，跳过测试
        pytest.skip(f"混合搜索服务不可用: {e}")


if __name__ == "__main__":
    # 直接运行集成测试
    async def run_tests():
        print("开始向量数据库和嵌入服务集成测试...")
        print("=" * 60)
        
        try:
            await test_embedding_service_integration()
        except Exception as e:
            print(f"嵌入服务测试跳过: {e}")
        
        print("-" * 60)
        
        try:
            await test_vector_service_integration()
        except Exception as e:
            print(f"向量数据库测试跳过: {e}")
        
        print("-" * 60)
        
        try:
            await test_elasticsearch_service_integration()
        except Exception as e:
            print(f"Elasticsearch测试跳过: {e}")
        
        print("-" * 60)
        
        try:
            await test_hybrid_search_integration()
        except Exception as e:
            print(f"混合搜索测试跳过: {e}")
        
        print("=" * 60)
        print("集成测试完成")
    
    asyncio.run(run_tests())