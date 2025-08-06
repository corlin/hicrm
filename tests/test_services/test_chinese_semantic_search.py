"""
中文语义搜索服务测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.services.chinese_semantic_search import (
    ChineseSemanticSearchService, ChineseSearchResult, chinese_search_service
)
from src.services.hybrid_search_service import HybridSearchResult


class TestChineseSearchResult:
    """中文搜索结果测试类"""
    
    def test_create_result(self):
        """测试创建中文搜索结果"""
        chinese_features = {
            'content_keywords': ['人工智能', '机器学习'],
            'keyword_overlap': 2,
            'semantic_similarity': 0.85
        }
        
        result = ChineseSearchResult(
            id="doc1",
            content="这是关于人工智能和机器学习的文档",
            title="AI技术介绍",
            metadata={"category": "tech"},
            semantic_score=0.9,
            keyword_score=0.8,
            combined_score=0.85,
            highlights={"content": ["<mark>人工智能</mark>"]},
            chinese_features=chinese_features
        )
        
        assert result.id == "doc1"
        assert result.content == "这是关于人工智能和机器学习的文档"
        assert result.title == "AI技术介绍"
        assert result.semantic_score == 0.9
        assert result.keyword_score == 0.8
        assert result.combined_score == 0.85
        assert result.chinese_features == chinese_features


class TestChineseSemanticSearchService:
    """中文语义搜索服务测试类"""
    
    @pytest.fixture
    def service(self):
        """创建中文语义搜索服务实例"""
        return ChineseSemanticSearchService()
    
    @pytest.fixture
    def mock_hybrid_results(self):
        """模拟混合搜索结果"""
        return [
            HybridSearchResult(
                id="doc1",
                content="这是关于人工智能的文档",
                title="AI技术",
                metadata={"category": "tech"},
                vector_score=0.9,
                bm25_score=0.8,
                hybrid_score=0.85,
                highlights={"content": ["<mark>人工智能</mark>"]}
            ),
            HybridSearchResult(
                id="doc2",
                content="机器学习是AI的重要分支",
                title="机器学习",
                metadata={"category": "research"},
                vector_score=0.85,
                bm25_score=0.75,
                hybrid_score=0.8
            )
        ]
    
    def test_load_chinese_stopwords(self, service):
        """测试加载中文停用词"""
        stopwords = service.chinese_stopwords
        
        assert isinstance(stopwords, set)
        assert len(stopwords) > 0
        assert '的' in stopwords
        assert '了' in stopwords
        assert '是' in stopwords
    
    def test_load_chinese_synonyms(self, service):
        """测试加载中文同义词"""
        synonyms = service.chinese_synonyms
        
        assert isinstance(synonyms, dict)
        assert len(synonyms) > 0
        assert '人工智能' in synonyms
        assert 'AI' in synonyms['人工智能']
        assert '机器学习' in synonyms
    
    def test_preprocess_chinese_text(self, service):
        """测试预处理中文文本"""
        # 测试基本预处理
        text1 = "  这是一个   测试文本  "
        result1 = service._preprocess_chinese_text(text1)
        assert result1 == "这是一个 测试文本"
        
        # 测试特殊字符处理
        text2 = "这是测试@#$%文本！！！"
        result2 = service._preprocess_chinese_text(text2)
        assert "@#$%" not in result2
        
        # 测试中文标点标准化
        text3 = "这是测试，文本。"
        result3 = service._preprocess_chinese_text(text3)
        assert "," in result3 and "." in result3
    
    def test_extract_chinese_keywords(self, service):
        """测试提取中文关键词"""
        text = "人工智能和机器学习是现代科技的重要组成部分"
        keywords = service._extract_chinese_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # 应该包含一些有意义的词汇
        meaningful_words = ['人工智能', '机器学习', '现代科技', '重要', '组成部分']
        found_words = [word for word in meaningful_words if word in keywords]
        assert len(found_words) > 0
    
    def test_extract_chinese_keywords_empty(self, service):
        """测试提取空文本的关键词"""
        keywords = service._extract_chinese_keywords("")
        assert keywords == []
    
    def test_is_valid_chinese_word(self, service):
        """测试判断有效中文词汇"""
        # 有效的中文词汇
        assert service._is_valid_chinese_word("人工智能") is True
        assert service._is_valid_chinese_word("机器学习") is True
        
        # 无效的词汇
        assert service._is_valid_chinese_word("a") is False
        assert service._is_valid_chinese_word("的") is False  # 太短
        assert service._is_valid_chinese_word("abc123") is False
    
    def test_expand_query_with_synonyms(self, service):
        """测试同义词扩展查询"""
        query = "人工智能的应用"
        expanded = service._expand_query_with_synonyms(query)
        
        assert isinstance(expanded, list)
        assert query in expanded  # 原查询应该在结果中
        assert len(expanded) > 1  # 应该有扩展的查询
        
        # 检查是否包含同义词扩展
        ai_synonyms = service.chinese_synonyms.get('人工智能', [])
        if ai_synonyms:
            synonym_found = any(synonym in ' '.join(expanded) for synonym in ai_synonyms)
            assert synonym_found
    
    def test_expand_query_no_synonyms(self, service):
        """测试没有同义词的查询扩展"""
        query = "这是一个没有同义词的查询"
        expanded = service._expand_query_with_synonyms(query)
        
        assert expanded == [query]
    
    @pytest.mark.asyncio
    async def test_search_success(self, service, mock_hybrid_results):
        """测试成功的中文搜索"""
        with patch('src.services.hybrid_search_service.hybrid_search_service') as mock_hybrid:
            with patch.object(service, '_extract_chinese_features') as mock_features:
                mock_hybrid.search = AsyncMock(return_value=mock_hybrid_results)
                mock_features.return_value = {
                    'content_keywords': ['人工智能'],
                    'keyword_overlap': 1,
                    'semantic_similarity': 0.85
                }
                
                results = await service.search("人工智能技术")
                
                assert len(results) > 0
                assert isinstance(results[0], ChineseSearchResult)
                assert results[0].id == "doc1"
                assert results[0].chinese_features is not None
                
                mock_hybrid.search.assert_called()
                mock_features.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_with_synonym_expansion(self, service, mock_hybrid_results):
        """测试使用同义词扩展的搜索"""
        with patch('src.services.hybrid_search_service.hybrid_search_service') as mock_hybrid:
            with patch.object(service, '_extract_chinese_features') as mock_features:
                mock_hybrid.search = AsyncMock(return_value=mock_hybrid_results)
                mock_features.return_value = {}
                
                results = await service.search("人工智能", use_synonym_expansion=True)
                
                # 应该调用多次搜索（原查询 + 同义词扩展）
                assert mock_hybrid.search.call_count > 1
    
    @pytest.mark.asyncio
    async def test_search_without_synonym_expansion(self, service, mock_hybrid_results):
        """测试不使用同义词扩展的搜索"""
        with patch('src.services.hybrid_search_service.hybrid_search_service') as mock_hybrid:
            with patch.object(service, '_extract_chinese_features') as mock_features:
                mock_hybrid.search = AsyncMock(return_value=mock_hybrid_results)
                mock_features.return_value = {}
                
                results = await service.search("人工智能", use_synonym_expansion=False)
                
                # 应该只调用一次搜索
                assert mock_hybrid.search.call_count == 1
    
    @pytest.mark.asyncio
    async def test_search_with_custom_weights(self, service, mock_hybrid_results):
        """测试使用自定义权重的搜索"""
        with patch('src.services.hybrid_search_service.hybrid_search_service') as mock_hybrid:
            with patch.object(service, '_extract_chinese_features') as mock_features:
                mock_hybrid.search = AsyncMock(return_value=mock_hybrid_results)
                mock_features.return_value = {}
                
                await service.search(
                    "测试查询",
                    semantic_weight=0.8,
                    keyword_weight=0.2
                )
                
                # 验证权重被正确传递
                call_args = mock_hybrid.search.call_args
                assert call_args[1]['vector_weight'] == 0.8
                assert call_args[1]['bm25_weight'] == 0.2
    
    @pytest.mark.asyncio
    async def test_search_failure(self, service):
        """测试搜索失败"""
        with patch('src.services.hybrid_search_service.hybrid_search_service') as mock_hybrid:
            mock_hybrid.search = AsyncMock(side_effect=Exception("搜索失败"))
            
            results = await service.search("测试查询")
            
            assert results == []
    
    def test_deduplicate_results(self, service, mock_hybrid_results):
        """测试去重搜索结果"""
        # 创建重复结果
        duplicate_results = mock_hybrid_results + [mock_hybrid_results[0]]
        
        unique_results = service._deduplicate_results(duplicate_results)
        
        assert len(unique_results) == len(mock_hybrid_results)
        assert unique_results[0].id == "doc1"
        assert unique_results[1].id == "doc2"
    
    def test_deduplicate_results_empty(self, service):
        """测试去重空结果"""
        unique_results = service._deduplicate_results([])
        assert unique_results == []
    
    @pytest.mark.asyncio
    async def test_extract_chinese_features(self, service):
        """测试提取中文特征"""
        content = "这是关于人工智能和机器学习的技术文档"
        query = "人工智能技术"
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.compute_similarity = AsyncMock(return_value=0.85)
            
            features = await service._extract_chinese_features(content, query)
            
            assert isinstance(features, dict)
            assert 'content_keywords' in features
            assert 'keyword_overlap' in features
            assert 'keyword_overlap_ratio' in features
            assert 'content_length' in features
            assert 'chinese_char_ratio' in features
            assert 'semantic_similarity' in features
            
            assert features['semantic_similarity'] == 0.85
            assert features['content_length'] == len(content)
            assert 0 <= features['chinese_char_ratio'] <= 1
    
    @pytest.mark.asyncio
    async def test_extract_chinese_features_failure(self, service):
        """测试提取中文特征失败"""
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.compute_similarity = AsyncMock(side_effect=Exception("计算失败"))
            
            features = await service._extract_chinese_features("内容", "查询")
            
            assert features == {}
    
    @pytest.mark.asyncio
    async def test_compute_chinese_similarity(self, service):
        """测试计算中文相似度"""
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.compute_similarity = AsyncMock(return_value=0.9)
            
            similarity = await service._compute_chinese_similarity("文本1", "文本2")
            
            assert similarity == 0.9
            mock_embedding.compute_similarity.assert_called_once_with("文本1", "文本2")
    
    @pytest.mark.asyncio
    async def test_compute_chinese_similarity_failure(self, service):
        """测试计算中文相似度失败"""
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.compute_similarity = AsyncMock(side_effect=Exception("计算失败"))
            
            similarity = await service._compute_chinese_similarity("文本1", "文本2")
            
            assert similarity == 0.0
    
    def test_rerank_by_chinese_features(self, service):
        """测试基于中文特征重排序"""
        results = [
            ChineseSearchResult(
                id="doc1", content="内容1", title="标题1", metadata={},
                semantic_score=0.8, keyword_score=0.7, combined_score=0.75,
                chinese_features={
                    'keyword_overlap_ratio': 0.5,
                    'semantic_similarity': 0.8,
                    'chinese_char_ratio': 0.9
                }
            ),
            ChineseSearchResult(
                id="doc2", content="内容2", title="标题2", metadata={},
                semantic_score=0.7, keyword_score=0.8, combined_score=0.75,
                chinese_features={
                    'keyword_overlap_ratio': 0.8,
                    'semantic_similarity': 0.9,
                    'chinese_char_ratio': 0.95
                }
            )
        ]
        
        reranked = service._rerank_by_chinese_features(results, "查询")
        
        assert len(reranked) == 2
        # 第二个结果应该排在前面（更好的中文特征）
        assert reranked[0].id == "doc2"
        assert reranked[1].id == "doc1"
    
    def test_rerank_by_chinese_features_no_features(self, service):
        """测试没有中文特征的重排序"""
        results = [
            ChineseSearchResult(
                id="doc1", content="内容1", title="标题1", metadata={},
                semantic_score=0.8, keyword_score=0.7, combined_score=0.75
            )
        ]
        
        reranked = service._rerank_by_chinese_features(results, "查询")
        
        assert len(reranked) == 1
        assert reranked[0].id == "doc1"
    
    def test_rerank_by_chinese_features_failure(self, service):
        """测试重排序失败"""
        results = [
            ChineseSearchResult(
                id="doc1", content="内容1", title="标题1", metadata={},
                semantic_score=0.8, keyword_score=0.7, combined_score=0.75,
                chinese_features=None  # 这会导致错误
            )
        ]
        
        # 应该不会抛出异常，返回原始结果
        reranked = service._rerank_by_chinese_features(results, "查询")
        
        assert len(reranked) == 1
        assert reranked[0].id == "doc1"
    
    @pytest.mark.asyncio
    async def test_find_similar_documents(self, service, mock_hybrid_results):
        """测试查找相似文档"""
        with patch('src.services.hybrid_search_service.hybrid_search_service') as mock_hybrid:
            with patch.object(service, '_extract_chinese_features') as mock_features:
                mock_hybrid.semantic_search = AsyncMock(return_value=mock_hybrid_results)
                mock_features.return_value = {'semantic_similarity': 0.85}
                
                results = await service.find_similar_documents(
                    "这是关于人工智能技术的文档内容"
                )
                
                assert len(results) > 0
                assert isinstance(results[0], ChineseSearchResult)
                
                mock_hybrid.semantic_search.assert_called_once()
                mock_features.assert_called()
    
    @pytest.mark.asyncio
    async def test_find_similar_documents_no_keywords(self, service):
        """测试查找相似文档但没有关键词"""
        with patch.object(service, '_extract_chinese_keywords', return_value=[]):
            results = await service.find_similar_documents("abc123")
            assert results == []
    
    @pytest.mark.asyncio
    async def test_find_similar_documents_failure(self, service):
        """测试查找相似文档失败"""
        with patch('src.services.hybrid_search_service.hybrid_search_service') as mock_hybrid:
            mock_hybrid.semantic_search = AsyncMock(side_effect=Exception("搜索失败"))
            
            results = await service.find_similar_documents("测试文档")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, service):
        """测试获取搜索建议"""
        suggestions = await service.get_search_suggestions("人工")
        
        assert isinstance(suggestions, list)
        # 应该包含相关的建议
        if suggestions:
            assert any('人工智能' in suggestion for suggestion in suggestions)
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions_no_match(self, service):
        """测试获取搜索建议但没有匹配"""
        suggestions = await service.get_search_suggestions("xyz123")
        
        assert isinstance(suggestions, list)
        # 可能为空或包含少量建议
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions_failure(self, service):
        """测试获取搜索建议失败"""
        with patch.object(service, 'chinese_synonyms', side_effect=Exception("获取失败")):
            suggestions = await service.get_search_suggestions("测试")
            assert suggestions == []
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent_search(self, service):
        """测试分析搜索意图"""
        query = "搜索人工智能相关的文档"
        intent = await service.analyze_query_intent(query)
        
        assert isinstance(intent, dict)
        assert 'primary_intent' in intent
        assert 'keywords' in intent
        assert 'processed_query' in intent
        assert intent['primary_intent'] == 'search'
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent_compare(self, service):
        """测试分析比较意图"""
        query = "比较深度学习和机器学习的区别"
        intent = await service.analyze_query_intent(query)
        
        assert intent['primary_intent'] == 'compare'
        assert 'intent_scores' in intent
        assert 'compare' in intent['intent_scores']
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent_explain(self, service):
        """测试分析解释意图"""
        query = "解释什么是自然语言处理"
        intent = await service.analyze_query_intent(query)
        
        assert intent['primary_intent'] == 'explain'
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent_no_specific_intent(self, service):
        """测试分析没有特定意图的查询"""
        query = "人工智能技术发展"
        intent = await service.analyze_query_intent(query)
        
        assert intent['primary_intent'] == 'search'  # 默认意图
        assert len(intent['keywords']) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent_failure(self, service):
        """测试分析查询意图失败"""
        with patch.object(service, '_preprocess_chinese_text', side_effect=Exception("处理失败")):
            intent = await service.analyze_query_intent("测试查询")
            
            assert intent['primary_intent'] == 'search'
            assert intent['keywords'] == []


class TestGlobalService:
    """全局服务实例测试"""
    
    def test_global_service_instance(self):
        """测试全局服务实例"""
        assert chinese_search_service is not None
        assert isinstance(chinese_search_service, ChineseSemanticSearchService)
        assert len(chinese_search_service.chinese_stopwords) > 0
        assert len(chinese_search_service.chinese_synonyms) > 0
    
    def test_global_service_stopwords(self):
        """测试全局服务停用词"""
        stopwords = chinese_search_service.chinese_stopwords
        common_stopwords = ['的', '了', '在', '是', '我', '有']
        for word in common_stopwords:
            assert word in stopwords
    
    def test_global_service_synonyms(self):
        """测试全局服务同义词"""
        synonyms = chinese_search_service.chinese_synonyms
        assert '人工智能' in synonyms
        assert '机器学习' in synonyms
        assert 'AI' in synonyms['人工智能']