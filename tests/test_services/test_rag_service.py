"""
RAG服务单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
from langchain.schema import Document

from src.services.rag_service import (
    RAGService, RAGConfig, RAGMode, RAGResult, RetrievalResult,
    ChineseTextSplitter, ContextWindowManager, ResultFusion
)
from src.services.vector_service import VectorDocument, VectorSearchResult


class TestChineseTextSplitter:
    """中文文本分割器测试"""
    
    def test_init(self):
        """测试初始化"""
        splitter = ChineseTextSplitter(chunk_size=100, chunk_overlap=20)
        assert splitter.chunk_size == 100
        assert splitter.chunk_overlap == 20
        assert '。' in splitter.sentence_separators
        assert '\n\n' in splitter.paragraph_separators
    
    def test_split_empty_text(self):
        """测试空文本分割"""
        splitter = ChineseTextSplitter()
        result = splitter.split_text("")
        assert result == []
        
        result = splitter.split_text("   ")
        assert result == []
    
    def test_split_short_text(self):
        """测试短文本分割"""
        splitter = ChineseTextSplitter(chunk_size=100)
        text = "这是一个简短的测试文本。"
        result = splitter.split_text(text)
        assert len(result) == 1
        assert result[0] == text
    
    def test_split_long_text(self):
        """测试长文本分割"""
        splitter = ChineseTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "这是第一句话。这是第二句话，内容比较长一些。这是第三句话。这是第四句话，也比较长。这是第五句话。"
        result = splitter.split_text(text)
        
        assert len(result) > 1
        # 检查重叠
        if len(result) > 1:
            # 应该有一些重叠内容
            assert len(result[0]) <= 60  # chunk_size + 一些容差
    
    def test_split_with_paragraphs(self):
        """测试段落分割"""
        splitter = ChineseTextSplitter(chunk_size=100)
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        result = splitter.split_text(text)
        
        assert len(result) >= 1
        # 检查是否保留了段落结构
        for chunk in result:
            assert chunk.strip()
    
    def test_split_by_separators(self):
        """测试分隔符分割"""
        splitter = ChineseTextSplitter()
        text = "句子一。句子二！句子三？"
        separators = ['。', '！', '？']
        result = splitter._split_by_separators(text, separators)
        
        assert len(result) == 3
        assert "句子一。" in result
        assert "句子二！" in result
        assert "句子三？" in result


class TestContextWindowManager:
    """上下文窗口管理器测试"""
    
    def test_init(self):
        """测试初始化"""
        manager = ContextWindowManager(max_tokens=1000)
        assert manager.max_tokens == 1000
    
    def test_manage_context_empty_docs(self):
        """测试空文档管理"""
        manager = ContextWindowManager(max_tokens=1000)
        query = "测试查询"
        documents = []
        
        result_query, result_docs = manager.manage_context(query, documents)
        assert result_query == query
        assert result_docs == []
    
    def test_manage_context_sufficient_space(self):
        """测试充足空间的上下文管理"""
        manager = ContextWindowManager(max_tokens=1000)
        query = "测试查询"
        documents = [
            Document(page_content="短文档内容", metadata={'score': 0.9}),
            Document(page_content="另一个短文档", metadata={'score': 0.8})
        ]
        
        result_query, result_docs = manager.manage_context(query, documents)
        assert result_query == query
        assert len(result_docs) == 2
    
    def test_manage_context_insufficient_space(self):
        """测试空间不足的上下文管理"""
        manager = ContextWindowManager(max_tokens=50)
        query = "测试查询"
        long_content = "这是一个非常长的文档内容" * 20
        documents = [
            Document(page_content=long_content, metadata={'score': 0.9})
        ]
        
        result_query, result_docs = manager.manage_context(query, documents)
        assert result_query == query
        # 应该截断或排除文档
        if result_docs:
            assert len(result_docs[0].page_content) < len(long_content)
    
    def test_sort_documents_by_importance(self):
        """测试文档重要性排序"""
        manager = ContextWindowManager()
        documents = [
            Document(page_content="文档1", metadata={'score': 0.5}),
            Document(page_content="文档2", metadata={'score': 0.9}),
            Document(page_content="文档3", metadata={'score': 0.7})
        ]
        
        sorted_docs = manager._sort_documents_by_importance(documents)
        scores = [doc.metadata.get('score', 0) for doc in sorted_docs]
        assert scores == [0.9, 0.7, 0.5]


class TestResultFusion:
    """结果融合器测试"""
    
    def setup_method(self):
        """测试设置"""
        self.fusion = ResultFusion()
        
        # 创建模拟的搜索结果
        self.mock_results_1 = [
            Mock(document=Mock(id="doc1"), score=0.9),
            Mock(document=Mock(id="doc2"), score=0.8),
            Mock(document=Mock(id="doc3"), score=0.7)
        ]
        
        self.mock_results_2 = [
            Mock(document=Mock(id="doc2"), score=0.85),
            Mock(document=Mock(id="doc1"), score=0.75),
            Mock(document=Mock(id="doc4"), score=0.6)
        ]
    
    def test_fuse_results_empty(self):
        """测试空结果融合"""
        result = self.fusion.fuse_results([])
        assert result == []
        
        result = self.fusion.fuse_results([[]])
        assert result == []
    
    def test_reciprocal_rank_fusion(self):
        """测试倒数排名融合"""
        results_list = [self.mock_results_1, self.mock_results_2]
        fused = self.fusion._reciprocal_rank_fusion(results_list)
        
        assert len(fused) == 4  # doc1, doc2, doc3, doc4
        # doc2应该排在前面，因为在两个结果中都有较好的排名
        doc_ids = [result.document.id for result in fused]
        assert "doc2" in doc_ids[:2]  # doc2应该在前两位
    
    def test_weighted_fusion(self):
        """测试加权融合"""
        results_list = [self.mock_results_1, self.mock_results_2]
        fused = self.fusion._weighted_fusion(results_list)
        
        assert len(fused) == 4
        # 检查分数是否被正确加权
        for result in fused:
            assert hasattr(result, 'score')
    
    def test_max_fusion(self):
        """测试最大值融合"""
        results_list = [self.mock_results_1, self.mock_results_2]
        fused = self.fusion._max_fusion(results_list)
        
        assert len(fused) == 4
        # 检查每个文档是否保留了最高分数
        doc_scores = {result.document.id: result.score for result in fused}
        assert doc_scores["doc1"] == 0.9  # 第一个结果中的分数更高
        assert doc_scores["doc2"] == 0.85  # 第二个结果中的分数更高


class TestRAGService:
    """RAG服务测试"""
    
    @pytest.fixture
    def rag_config(self):
        """RAG配置fixture"""
        return RAGConfig(
            chunk_size=100,
            chunk_overlap=20,
            top_k=5,
            similarity_threshold=0.7,
            rerank_top_k=3,
            context_window_size=1000,
            enable_reranking=True,
            enable_fusion=True
        )
    
    @pytest.fixture
    def rag_service(self, rag_config):
        """RAG服务fixture"""
        return RAGService(rag_config)
    
    @pytest.fixture
    def mock_vector_results(self):
        """模拟向量搜索结果"""
        return [
            VectorSearchResult(
                document=VectorDocument(
                    id="doc1",
                    content="这是第一个测试文档的内容",
                    metadata={'title': '文档1', 'score': 0.9}
                ),
                score=0.9,
                distance=0.1
            ),
            VectorSearchResult(
                document=VectorDocument(
                    id="doc2", 
                    content="这是第二个测试文档的内容",
                    metadata={'title': '文档2', 'score': 0.8}
                ),
                score=0.8,
                distance=0.2
            )
        ]
    
    def test_init(self, rag_config):
        """测试RAG服务初始化"""
        service = RAGService(rag_config)
        assert service.config == rag_config
        assert service.text_splitter.chunk_size == rag_config.chunk_size
        assert service.context_manager.max_tokens == rag_config.context_window_size
        assert isinstance(service.result_fusion, ResultFusion)
    
    def test_init_default_config(self):
        """测试默认配置初始化"""
        service = RAGService()
        assert isinstance(service.config, RAGConfig)
        assert service.config.chunk_size == 512
        assert service.config.top_k == 10
    
    @pytest.mark.asyncio
    async def test_initialize(self, rag_service):
        """测试服务初始化"""
        with patch('src.services.rag_service.vector_service') as mock_vector, \
             patch('src.services.rag_service.embedding_service') as mock_embedding:
            
            mock_vector.client = None
            mock_vector.initialize = AsyncMock()
            mock_embedding._model_loaded = False
            mock_embedding._reranker_loaded = False
            mock_embedding.initialize = AsyncMock()
            mock_embedding.initialize_reranker = AsyncMock()
            
            await rag_service.initialize()
            
            mock_vector.initialize.assert_called_once()
            mock_embedding.initialize.assert_called_once()
            mock_embedding.initialize_reranker.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_documents(self, rag_service):
        """测试添加文档"""
        documents = [
            {
                'id': 'test_doc_1',
                'content': '这是一个测试文档的内容，用于验证文档添加功能。',
                'metadata': {'title': '测试文档1', 'category': 'test'}
            }
        ]
        
        with patch('src.services.rag_service.vector_service') as mock_vector:
            mock_vector.add_documents = AsyncMock(return_value=True)
            
            result = await rag_service.add_documents(documents)
            
            assert result is True
            mock_vector.add_documents.assert_called_once()
            
            # 检查调用参数
            call_args = mock_vector.add_documents.call_args
            processed_docs = call_args[0][0]
            assert len(processed_docs) >= 1  # 至少有一个文档块
            assert all(hasattr(doc, 'id') for doc in processed_docs)
            assert all(hasattr(doc, 'content') for doc in processed_docs)
    
    @pytest.mark.asyncio
    async def test_simple_retrieve(self, rag_service, mock_vector_results):
        """测试简单检索"""
        with patch('src.services.rag_service.vector_service') as mock_vector:
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            
            results = await rag_service._simple_retrieve("测试查询", "test_collection")
            
            assert len(results) == 2
            assert results[0].score == 0.9
            assert results[1].score == 0.8
            mock_vector.search.assert_called_once_with(
                query="测试查询",
                collection_name="test_collection",
                limit=rag_service.config.top_k,
                score_threshold=rag_service.config.similarity_threshold
            )
    
    @pytest.mark.asyncio
    async def test_rerank_retrieve(self, rag_service, mock_vector_results):
        """测试重排序检索"""
        with patch('src.services.rag_service.vector_service') as mock_vector, \
             patch('src.services.rag_service.embedding_service') as mock_embedding:
            
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            mock_embedding.rerank = AsyncMock(return_value=[(1, 0.95), (0, 0.85)])
            
            results = await rag_service._rerank_retrieve("测试查询", "test_collection")
            
            assert len(results) == 2
            # 检查重排序后的分数
            assert results[0].score == 0.95
            assert results[1].score == 0.85
            
            mock_embedding.rerank.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve(self, rag_service, mock_vector_results):
        """测试检索方法"""
        with patch('src.services.rag_service.vector_service') as mock_vector:
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            
            result = await rag_service.retrieve("测试查询", RAGMode.SIMPLE)
            
            assert isinstance(result, RetrievalResult)
            assert len(result.documents) == 2
            assert len(result.scores) == 2
            assert result.retrieval_time > 0
            assert result.metadata['mode'] == 'simple'
            
            # 检查文档转换
            for doc in result.documents:
                assert isinstance(doc, Document)
                assert hasattr(doc, 'page_content')
                assert hasattr(doc, 'metadata')
    
    @pytest.mark.asyncio
    async def test_generate(self, rag_service):
        """测试生成回答"""
        documents = [
            Document(
                page_content="这是相关的文档内容",
                metadata={'score': 0.9}
            )
        ]
        
        with patch('src.services.rag_service.llm_service') as mock_llm:
            mock_llm.generate_response = AsyncMock(
                return_value={'content': '基于提供的文档，这是生成的回答。'}
            )
            
            answer = await rag_service.generate("测试问题", documents)
            
            assert isinstance(answer, str)
            assert len(answer) > 0
            assert "生成的回答" in answer
            
            mock_llm.generate_response.assert_called_once()
            
            # 检查调用参数
            call_args = mock_llm.generate_response.call_args
            prompt = call_args[1]['prompt']
            assert "测试问题" in prompt
            assert "相关的文档内容" in prompt
    
    @pytest.mark.asyncio
    async def test_query_complete_flow(self, rag_service, mock_vector_results):
        """测试完整查询流程"""
        with patch('src.services.rag_service.vector_service') as mock_vector, \
             patch('src.services.rag_service.llm_service') as mock_llm:
            
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            mock_llm.generate_response = AsyncMock(
                return_value={'content': '这是完整的RAG回答。'}
            )
            
            result = await rag_service.query("什么是RAG？", RAGMode.SIMPLE)
            
            assert isinstance(result, RAGResult)
            assert result.answer == '这是完整的RAG回答。'
            assert len(result.sources) == 2
            assert result.confidence > 0
            assert result.retrieval_time > 0
            assert result.generation_time > 0
            assert result.total_time > 0
            assert result.mode == RAGMode.SIMPLE
            
            # 检查源信息
            for source in result.sources:
                assert 'index' in source
                assert 'content' in source
                assert 'metadata' in source
                assert 'score' in source
    
    @pytest.mark.asyncio
    async def test_query_error_handling(self, rag_service):
        """测试查询错误处理"""
        with patch('src.services.rag_service.vector_service') as mock_vector:
            mock_vector.search = AsyncMock(side_effect=Exception("搜索失败"))
            
            result = await rag_service.query("测试问题")
            
            assert isinstance(result, RAGResult)
            assert "错误" in result.answer
            assert result.confidence == 0.0
            assert len(result.sources) == 0
            assert 'error' in result.metadata
    
    def test_calculate_confidence(self, rag_service):
        """测试置信度计算"""
        # 高分数，多文档
        scores = [0.9, 0.8, 0.7]
        confidence = rag_service._calculate_confidence(scores, 3)
        assert 0.5 < confidence <= 1.0
        
        # 低分数
        scores = [0.3, 0.2, 0.1]
        confidence = rag_service._calculate_confidence(scores, 3)
        assert 0.0 <= confidence < 0.5
        
        # 空分数
        confidence = rag_service._calculate_confidence([], 0)
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_update_config(self, rag_service):
        """测试配置更新"""
        new_config = RAGConfig(
            chunk_size=256,
            chunk_overlap=30,
            top_k=15,
            context_window_size=2000
        )
        
        await rag_service.update_config(new_config)
        
        assert rag_service.config == new_config
        assert rag_service.text_splitter.chunk_size == 256
        assert rag_service.text_splitter.chunk_overlap == 30
        assert rag_service.context_manager.max_tokens == 2000
    
    @pytest.mark.asyncio
    async def test_get_stats(self, rag_service):
        """测试获取统计信息"""
        with patch('src.services.rag_service.vector_service') as mock_vector, \
             patch('src.services.rag_service.embedding_service') as mock_embedding:
            
            mock_vector.get_stats = AsyncMock(return_value={'total_collections': 1})
            mock_embedding.get_model_info = AsyncMock(return_value={'model': 'BGE-M3'})
            
            stats = await rag_service.get_stats()
            
            assert 'config' in stats
            assert 'vector_service' in stats
            assert 'embedding_service' in stats
            assert 'llama_index_available' in stats
            
            # 检查配置信息
            config_stats = stats['config']
            assert config_stats['chunk_size'] == rag_service.config.chunk_size
            assert config_stats['top_k'] == rag_service.config.top_k
    
    @pytest.mark.asyncio
    async def test_fusion_retrieve(self, rag_service, mock_vector_results):
        """测试融合检索"""
        with patch('src.services.rag_service.vector_service') as mock_vector:
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            
            results = await rag_service._fusion_retrieve("测试查询", "test_collection")
            
            # 应该调用多次搜索（不同的查询变体）
            assert mock_vector.search.call_count >= 2
            assert len(results) >= 0  # 融合后的结果
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieve(self, rag_service, mock_vector_results):
        """测试混合检索"""
        with patch('src.services.rag_service.vector_service') as mock_vector, \
             patch('src.services.rag_service.embedding_service') as mock_embedding:
            
            mock_vector.search = AsyncMock(return_value=mock_vector_results)
            mock_embedding.rerank = AsyncMock(return_value=[(1, 0.95), (0, 0.85)])
            
            results = await rag_service._hybrid_retrieve("测试查询", "test_collection")
            
            assert len(results) <= rag_service.config.rerank_top_k
            # 如果启用重排序且结果足够多，应该调用重排序
            if rag_service.config.enable_reranking and len(mock_vector_results) > rag_service.config.rerank_top_k:
                mock_embedding.rerank.assert_called_once()


class TestRAGIntegration:
    """RAG服务集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        config = RAGConfig(
            chunk_size=100,
            top_k=3,
            enable_reranking=False,  # 简化测试
            enable_fusion=False
        )
        service = RAGService(config)
        
        # 模拟所有依赖服务
        with patch('src.services.rag_service.vector_service') as mock_vector, \
             patch('src.services.rag_service.embedding_service') as mock_embedding, \
             patch('src.services.rag_service.llm_service') as mock_llm:
            
            # 设置模拟
            mock_vector.client = Mock()
            mock_vector.initialize = AsyncMock()
            mock_vector.add_documents = AsyncMock(return_value=True)
            mock_vector.search = AsyncMock(return_value=[
                VectorSearchResult(
                    document=VectorDocument(
                        id="test_doc",
                        content="RAG是检索增强生成技术",
                        metadata={'title': 'RAG介绍'}
                    ),
                    score=0.9,
                    distance=0.1
                )
            ])
            
            mock_embedding._model_loaded = True
            mock_embedding._reranker_loaded = True
            mock_embedding.initialize = AsyncMock()
            mock_embedding.initialize_reranker = AsyncMock()
            
            mock_llm.generate_response = AsyncMock(
                return_value={'content': 'RAG是一种结合检索和生成的AI技术。'}
            )
            
            # 执行完整流程
            await service.initialize()
            
            # 添加文档
            documents = [{
                'id': 'doc1',
                'content': 'RAG（检索增强生成）是一种先进的AI技术，它结合了信息检索和文本生成的能力。',
                'metadata': {'title': 'RAG技术介绍'}
            }]
            
            add_result = await service.add_documents(documents)
            assert add_result is True
            
            # 执行查询
            query_result = await service.query("什么是RAG技术？")
            
            assert isinstance(query_result, RAGResult)
            assert len(query_result.answer) > 0
            assert query_result.confidence > 0
            assert len(query_result.sources) > 0
            assert query_result.total_time > 0
    
    @pytest.mark.asyncio
    async def test_chinese_text_processing(self):
        """测试中文文本处理"""
        service = RAGService()
        
        # 测试中文文本分割
        chinese_text = "人工智能是计算机科学的一个分支。它致力于创建能够执行通常需要人类智能的任务的系统。机器学习是人工智能的一个重要子领域。深度学习又是机器学习的一个分支。"
        
        chunks = service.text_splitter.split_text(chinese_text)
        assert len(chunks) >= 1
        
        # 检查中文字符处理
        for chunk in chunks:
            assert len(chunk) > 0
            # 确保包含中文字符
            assert any('\u4e00' <= char <= '\u9fff' for char in chunk)
    
    @pytest.mark.asyncio 
    async def test_error_recovery(self):
        """测试错误恢复"""
        service = RAGService()
        
        with patch('src.services.rag_service.vector_service') as mock_vector:
            # 模拟向量服务失败
            mock_vector.search = AsyncMock(side_effect=Exception("向量搜索失败"))
            
            result = await service.query("测试问题")
            
            # 应该返回错误结果而不是抛出异常
            assert isinstance(result, RAGResult)
            assert "错误" in result.answer
            assert result.confidence == 0.0
            assert 'error' in result.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])