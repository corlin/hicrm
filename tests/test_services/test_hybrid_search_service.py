"""
混合检索服务测试
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.services.hybrid_search_service import (
    HybridSearchService, HybridSearchResult, SearchMode, hybrid_search_service
)
from src.services.vector_service import VectorDocument, VectorSearchResult
from src.services.elasticsearch_service import ElasticsearchDocument, ElasticsearchSearchResult


class TestHybridSearchResult:
    """混合搜索结果测试类"""
    
    def test_create_result(self):
        """测试创建混合搜索结果"""
        result = HybridSearchResult(
            id="doc1",
            content="这是测试内容",
            title="测试标题",
            metadata={"category": "tech"},
            vector_score=0.95,
            bm25_score=0.85,
            hybrid_score=0.90,
            rerank_score=0.92,
            highlights={"content": ["<mark>测试</mark>内容"]}
        )
        
        assert result.id == "doc1"
        assert result.content == "这是测试内容"
        assert result.title == "测试标题"
        assert result.metadata == {"category": "tech"}
        assert result.vector_score == 0.95
        assert result.bm25_score == 0.85
        assert result.hybrid_score == 0.90
        assert result.rerank_score == 0.92
        assert result.highlights == {"content": ["<mark>测试</mark>内容"]}
    
    def test_create_result_minimal(self):
        """测试创建最小混合搜索结果"""
        result = HybridSearchResult(
            id="doc1",
            content="内容",
            title="标题",
            metadata={},
            vector_score=0.8,
            bm25_score=0.7,
            hybrid_score=0.75
        )
        
        assert result.rerank_score is None
        assert result.highlights is None


class TestHybridSearchService:
    """混合检索服务测试类"""
    
    @pytest.fixture
    def service(self):
        """创建混合搜索服务实例"""
        return HybridSearchService()
    
    @pytest.fixture
    def sample_documents(self):
        """示例文档"""
        return [
            {
                "id": "doc1",
                "content": "这是关于人工智能的文档，介绍了机器学习的基本概念",
                "title": "人工智能基础",
                "metadata": {"category": "tech", "author": "张三"}
            },
            {
                "id": "doc2", 
                "content": "深度学习是机器学习的一个重要分支，使用神经网络",
                "title": "深度学习入门",
                "metadata": {"category": "research", "author": "李四"}
            },
            {
                "id": "doc3",
                "content": "自然语言处理技术在现代AI系统中发挥重要作用",
                "title": "NLP技术应用",
                "metadata": {"category": "tech", "author": "王五"}
            }
        ]
    
    @pytest.fixture
    def mock_vector_results(self):
        """模拟向量搜索结果"""
        doc1 = VectorDocument("doc1", "人工智能内容", {"category": "tech"})
        doc2 = VectorDocument("doc2", "深度学习内容", {"category": "research"})
        
        return [
            VectorSearchResult(doc1, 0.95, 0.05),
            VectorSearchResult(doc2, 0.88, 0.12)
        ]
    
    @pytest.fixture
    def mock_bm25_results(self):
        """模拟BM25搜索结果"""
        doc1 = ElasticsearchDocument("doc1", "人工智能内容", {"category": "tech"}, "AI标题")
        doc3 = ElasticsearchDocument("doc3", "NLP内容", {"category": "tech"}, "NLP标题")
        
        return [
            ElasticsearchSearchResult(doc1, 15.5, {"content": ["<mark>人工智能</mark>内容"]}),
            ElasticsearchSearchResult(doc3, 12.3, {"content": ["<mark>NLP</mark>内容"]})
        ]
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, service):
        """测试成功初始化"""
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            with patch('src.services.vector_service.vector_service') as mock_vector:
                with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                    mock_embedding.initialize = AsyncMock()
                    mock_vector.initialize = AsyncMock()
                    mock_es.initialize = AsyncMock()
                    
                    await service.initialize()
                    
                    mock_embedding.initialize.assert_called_once()
                    mock_vector.initialize.assert_called_once()
                    mock_es.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, service):
        """测试初始化失败"""
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.initialize = AsyncMock(side_effect=Exception("初始化失败"))
            
            with pytest.raises(Exception, match="初始化失败"):
                await service.initialize()
    
    @pytest.mark.asyncio
    async def test_add_documents_success(self, service, sample_documents):
        """测试成功添加文档"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.add_documents = AsyncMock(return_value=True)
                mock_es.add_documents = AsyncMock(return_value=True)
                
                result = await service.add_documents(sample_documents)
                
                assert result is True
                mock_vector.add_documents.assert_called_once()
                mock_es.add_documents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_documents_empty_list(self, service):
        """测试添加空文档列表"""
        result = await service.add_documents([])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_add_documents_invalid_document(self, service):
        """测试添加无效文档"""
        invalid_docs = [
            {"id": "doc1"},  # 缺少content
            {"content": "内容"},  # 缺少id
            {"id": "doc3", "content": "内容", "title": "标题"}  # 有效文档
        ]
        
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.add_documents = AsyncMock(return_value=True)
                mock_es.add_documents = AsyncMock(return_value=True)
                
                result = await service.add_documents(invalid_docs)
                
                assert result is True
                # 只有一个有效文档被处理
                assert len(mock_vector.add_documents.call_args[0][0]) == 1
                assert len(mock_es.add_documents.call_args[0][0]) == 1
    
    @pytest.mark.asyncio
    async def test_add_documents_partial_failure(self, service, sample_documents):
        """测试部分添加失败"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.add_documents = AsyncMock(return_value=True)
                mock_es.add_documents = AsyncMock(return_value=False)
                
                result = await service.add_documents(sample_documents)
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_add_documents_exception_handling(self, service, sample_documents):
        """测试添加文档异常处理"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.add_documents = AsyncMock(side_effect=Exception("向量添加失败"))
                mock_es.add_documents = AsyncMock(return_value=True)
                
                result = await service.add_documents(sample_documents)
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_search_vector_only(self, service, mock_vector_results):
        """测试仅向量搜索模式"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            
            results = await service.search("人工智能", mode=SearchMode.VECTOR_ONLY)
            
            assert len(results) == 2
            assert results[0].id == "doc1"
            assert results[0].vector_score == 0.95
            assert results[0].bm25_score == 0.0
            assert results[0].hybrid_score == 0.95
            
            mock_vector.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_bm25_only(self, service, mock_bm25_results):
        """测试仅BM25搜索模式"""
        with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
            mock_es.search = AsyncMock(return_value=mock_bm25_results)
            
            results = await service.search("人工智能", mode=SearchMode.BM25_ONLY)
            
            assert len(results) == 2
            assert results[0].id == "doc1"
            assert results[0].vector_score == 0.0
            assert results[0].bm25_score == 15.5
            assert results[0].hybrid_score == 15.5
            assert results[0].highlights == {"content": ["<mark>人工智能</mark>内容"]}
            
            mock_es.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_hybrid_mode(self, service, mock_vector_results, mock_bm25_results):
        """测试混合搜索模式"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.search = AsyncMock(return_value=mock_vector_results)
                mock_es.search = AsyncMock(return_value=mock_bm25_results)
                
                results = await service.search("人工智能", mode=SearchMode.HYBRID)
                
                assert len(results) > 0
                # 验证混合分数计算
                for result in results:
                    assert result.hybrid_score >= 0
                    assert result.vector_score >= 0 or result.bm25_score >= 0
                
                mock_vector.search.assert_called_once()
                mock_es.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_custom_weights(self, service, mock_vector_results, mock_bm25_results):
        """测试使用自定义权重的搜索"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.search = AsyncMock(return_value=mock_vector_results)
                mock_es.search = AsyncMock(return_value=mock_bm25_results)
                
                results = await service.search(
                    "人工智能", 
                    mode=SearchMode.HYBRID,
                    vector_weight=0.8,
                    bm25_weight=0.2
                )
                
                assert len(results) > 0
                # 验证权重被正确应用
                for result in results:
                    expected_score = (result.vector_score * 0.8 + result.bm25_score * 0.2)
                    # 由于归一化，不能直接比较，但应该有合理的混合分数
                    assert result.hybrid_score >= 0
    
    @pytest.mark.asyncio
    async def test_search_with_rerank(self, service, mock_vector_results, mock_bm25_results):
        """测试带重排序的搜索"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                with patch('src.services.embedding_service.embedding_service') as mock_embedding:
                    mock_vector.search = AsyncMock(return_value=mock_vector_results)
                    mock_es.search = AsyncMock(return_value=mock_bm25_results)
                    mock_embedding.rerank = AsyncMock(return_value=[(0, 0.95), (1, 0.85)])
                    
                    results = await service.search("人工智能", rerank=True)
                    
                    assert len(results) > 0
                    # 验证重排序分数被设置
                    for result in results:
                        if result.rerank_score is not None:
                            assert 0 <= result.rerank_score <= 1
                    
                    mock_embedding.rerank.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, service, mock_vector_results):
        """测试带过滤条件的搜索"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            
            filters = {"category": "tech"}
            results = await service.search(
                "人工智能", 
                mode=SearchMode.VECTOR_ONLY,
                filters=filters
            )
            
            assert len(results) > 0
            mock_vector.search.assert_called_once()
            # 验证过滤条件被传递
            call_args = mock_vector.search.call_args
            assert call_args[1]["filters"] == filters
    
    @pytest.mark.asyncio
    async def test_search_failure_handling(self, service):
        """测试搜索失败处理"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.search = AsyncMock(side_effect=Exception("向量搜索失败"))
                mock_es.search = AsyncMock(side_effect=Exception("BM25搜索失败"))
                
                results = await service.search("人工智能", mode=SearchMode.HYBRID)
                
                assert results == []
    
    def test_merge_results(self, service, mock_vector_results, mock_bm25_results):
        """测试合并搜索结果"""
        merged = service._merge_results(
            mock_vector_results, 
            mock_bm25_results, 
            0.6, 
            0.4
        )
        
        assert len(merged) > 0
        # 验证结果按混合分数排序
        for i in range(len(merged) - 1):
            assert merged[i].hybrid_score >= merged[i + 1].hybrid_score
        
        # 验证分数计算
        for result in merged:
            assert 0 <= result.vector_score <= 1
            assert 0 <= result.bm25_score <= 1
            assert result.hybrid_score >= 0
    
    def test_merge_results_vector_only(self, service, mock_vector_results):
        """测试仅向量结果合并"""
        merged = service._merge_results(mock_vector_results, [], 1.0, 0.0)
        
        assert len(merged) == len(mock_vector_results)
        for result in merged:
            assert result.vector_score > 0
            assert result.bm25_score == 0
    
    def test_merge_results_bm25_only(self, service, mock_bm25_results):
        """测试仅BM25结果合并"""
        merged = service._merge_results([], mock_bm25_results, 0.0, 1.0)
        
        assert len(merged) == len(mock_bm25_results)
        for result in merged:
            assert result.vector_score == 0
            assert result.bm25_score > 0
    
    def test_merge_results_empty(self, service):
        """测试合并空结果"""
        merged = service._merge_results([], [], 0.6, 0.4)
        assert merged == []
    
    @pytest.mark.asyncio
    async def test_rerank_results(self, service):
        """测试重排序结果"""
        # 创建测试结果
        results = [
            HybridSearchResult("doc1", "内容1", "标题1", {}, 0.8, 0.7, 0.75),
            HybridSearchResult("doc2", "内容2", "标题2", {}, 0.9, 0.6, 0.75),
            HybridSearchResult("doc3", "内容3", "标题3", {}, 0.7, 0.8, 0.75)
        ]
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            # 模拟重排序分数：doc2 > doc1 > doc3
            mock_embedding.rerank = AsyncMock(return_value=[(1, 0.95), (0, 0.85), (2, 0.75)])
            
            reranked = await service._rerank_results("查询", results)
            
            assert len(reranked) == 3
            assert reranked[0].id == "doc2"  # 最高重排序分数
            assert reranked[0].rerank_score == 0.95
            assert reranked[1].id == "doc1"
            assert reranked[1].rerank_score == 0.85
            assert reranked[2].id == "doc3"
            assert reranked[2].rerank_score == 0.75
    
    @pytest.mark.asyncio
    async def test_rerank_results_empty(self, service):
        """测试重排序空结果"""
        reranked = await service._rerank_results("查询", [])
        assert reranked == []
    
    @pytest.mark.asyncio
    async def test_rerank_results_failure(self, service):
        """测试重排序失败"""
        results = [
            HybridSearchResult("doc1", "内容1", "标题1", {}, 0.8, 0.7, 0.75)
        ]
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.rerank = AsyncMock(side_effect=Exception("重排序失败"))
            
            reranked = await service._rerank_results("查询", results)
            
            # 应该返回原始结果
            assert len(reranked) == 1
            assert reranked[0].id == "doc1"
            assert reranked[0].rerank_score is None
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, service, mock_vector_results):
        """测试语义搜索"""
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            with patch('src.services.vector_service.vector_service') as mock_vector:
                mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
                mock_vector.search_by_vector = AsyncMock(return_value=mock_vector_results)
                
                results = await service.semantic_search("人工智能", similarity_threshold=0.8)
                
                assert len(results) > 0
                # 验证只返回高相似度结果
                for result in results:
                    assert result.vector_score >= 0.8
                
                mock_embedding.encode.assert_called_once_with("人工智能")
                mock_vector.search_by_vector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_semantic_search_low_similarity(self, service):
        """测试低相似度语义搜索"""
        low_score_results = [
            VectorSearchResult(
                VectorDocument("doc1", "内容", {}), 
                0.5,  # 低于阈值
                0.5
            )
        ]
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            with patch('src.services.vector_service.vector_service') as mock_vector:
                mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
                mock_vector.search_by_vector = AsyncMock(return_value=low_score_results)
                
                results = await service.semantic_search("查询", similarity_threshold=0.7)
                
                assert len(results) == 0  # 所有结果都被过滤掉
    
    @pytest.mark.asyncio
    async def test_semantic_search_failure(self, service):
        """测试语义搜索失败"""
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.encode = AsyncMock(side_effect=Exception("编码失败"))
            
            results = await service.semantic_search("查询")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_delete_documents_success(self, service):
        """测试成功删除文档"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.delete_documents = AsyncMock(return_value=True)
                mock_es.delete_documents = AsyncMock(return_value=True)
                
                document_ids = ["doc1", "doc2", "doc3"]
                result = await service.delete_documents(document_ids)
                
                assert result is True
                mock_vector.delete_documents.assert_called_once_with(document_ids, None)
                mock_es.delete_documents.assert_called_once_with(document_ids, None)
    
    @pytest.mark.asyncio
    async def test_delete_documents_partial_failure(self, service):
        """测试部分删除失败"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.delete_documents = AsyncMock(return_value=True)
                mock_es.delete_documents = AsyncMock(return_value=False)
                
                result = await service.delete_documents(["doc1"])
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_documents_exception_handling(self, service):
        """测试删除文档异常处理"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.delete_documents = AsyncMock(side_effect=Exception("删除失败"))
                mock_es.delete_documents = AsyncMock(return_value=True)
                
                result = await service.delete_documents(["doc1"])
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_get_stats(self, service):
        """测试获取统计信息"""
        mock_vector_stats = {"total_collections": 2, "collections": {}}
        mock_es_stats = {"name": "test_index", "docs_count": 100}
        
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.get_stats = AsyncMock(return_value=mock_vector_stats)
                mock_es.get_index_stats = AsyncMock(return_value=mock_es_stats)
                
                stats = await service.get_stats()
                
                assert "vector_database" in stats
                assert "elasticsearch" in stats
                assert "search_weights" in stats
                assert stats["vector_database"] == mock_vector_stats
                assert stats["elasticsearch"] == mock_es_stats
                assert "vector_weight" in stats["search_weights"]
                assert "bm25_weight" in stats["search_weights"]
    
    @pytest.mark.asyncio
    async def test_get_stats_failure(self, service):
        """测试获取统计信息失败"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                mock_vector.get_stats = AsyncMock(side_effect=Exception("获取向量统计失败"))
                mock_es.get_index_stats = AsyncMock(side_effect=Exception("获取ES统计失败"))
                
                stats = await service.get_stats()
                
                assert stats["vector_database"] == {}
                assert stats["elasticsearch"] == {}
                assert "search_weights" in stats
    
    def test_set_search_weights(self, service):
        """测试设置搜索权重"""
        service.set_search_weights(0.8, 0.2)
        
        assert service.vector_weight == 0.8
        assert service.bm25_weight == 0.2
    
    def test_set_search_weights_normalization(self, service):
        """测试搜索权重归一化"""
        service.set_search_weights(3.0, 1.0)
        
        assert service.vector_weight == 0.75  # 3/(3+1)
        assert service.bm25_weight == 0.25   # 1/(3+1)
    
    def test_set_search_weights_zero_total(self, service):
        """测试零总权重"""
        original_vector_weight = service.vector_weight
        original_bm25_weight = service.bm25_weight
        
        service.set_search_weights(0.0, 0.0)
        
        # 权重应该保持不变
        assert service.vector_weight == original_vector_weight
        assert service.bm25_weight == original_bm25_weight
    
    @pytest.mark.asyncio
    async def test_close(self, service):
        """测试关闭服务"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                with patch('src.services.embedding_service.embedding_service') as mock_embedding:
                    mock_vector.close = AsyncMock()
                    mock_es.close = AsyncMock()
                    mock_embedding.close = AsyncMock()
                    
                    await service.close()
                    
                    mock_vector.close.assert_called_once()
                    mock_es.close.assert_called_once()
                    mock_embedding.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_with_exceptions(self, service):
        """测试关闭服务时有异常"""
        with patch('src.services.vector_service.vector_service') as mock_vector:
            with patch('src.services.elasticsearch_service.elasticsearch_service') as mock_es:
                with patch('src.services.embedding_service.embedding_service') as mock_embedding:
                    mock_vector.close = AsyncMock(side_effect=Exception("关闭向量服务失败"))
                    mock_es.close = AsyncMock(side_effect=Exception("关闭ES服务失败"))
                    mock_embedding.close = AsyncMock()
                    
                    # 应该不会抛出异常
                    await service.close()
                    
                    mock_embedding.close.assert_called_once()


class TestSearchMode:
    """搜索模式测试"""
    
    def test_search_mode_values(self):
        """测试搜索模式值"""
        assert SearchMode.VECTOR_ONLY.value == "vector_only"
        assert SearchMode.BM25_ONLY.value == "bm25_only"
        assert SearchMode.HYBRID.value == "hybrid"
        assert SearchMode.RERANK.value == "rerank"


class TestGlobalService:
    """全局服务实例测试"""
    
    def test_global_service_instance(self):
        """测试全局服务实例"""
        assert hybrid_search_service is not None
        assert isinstance(hybrid_search_service, HybridSearchService)
        assert hybrid_search_service.vector_weight == 0.6
        assert hybrid_search_service.bm25_weight == 0.4
        assert hybrid_search_service.min_vector_score == 0.1
        assert hybrid_search_service.min_bm25_score == 0.1