"""
嵌入服务测试
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from concurrent.futures import ThreadPoolExecutor

from src.services.embedding_service import EmbeddingService, embedding_service


class TestEmbeddingService:
    """嵌入服务测试类"""
    
    @pytest.fixture
    def service(self):
        """创建嵌入服务实例"""
        return EmbeddingService()
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """模拟SentenceTransformer模型"""
        model = Mock()
        model.eval = Mock()
        model.encode = Mock(return_value=np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]))
        model.predict = Mock(return_value=[0.8, 0.6])
        return model
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, service):
        """测试成功初始化"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_model.eval = Mock()
            mock_st.return_value = mock_model
            
            await service.initialize()
            
            assert service._model_loaded is True
            assert service.model is not None
            mock_model.eval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, service):
        """测试初始化失败"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            mock_st.side_effect = Exception("模型加载失败")
            
            with pytest.raises(Exception, match="模型加载失败"):
                await service.initialize()
    
    @pytest.mark.asyncio
    async def test_initialize_reranker_success(self, service):
        """测试成功初始化重排序模型"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_model.eval = Mock()
            mock_st.return_value = mock_model
            
            await service.initialize_reranker()
            
            assert service._reranker_loaded is True
            assert service.reranker_model is not None
    
    @pytest.mark.asyncio
    async def test_initialize_reranker_failure(self, service):
        """测试重排序模型初始化失败"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            mock_st.side_effect = Exception("重排序模型加载失败")
            
            with pytest.raises(Exception, match="重排序模型加载失败"):
                await service.initialize_reranker()
    
    def test_get_cache_key(self, service):
        """测试生成缓存键"""
        key1 = service._get_cache_key("测试文本", True)
        key2 = service._get_cache_key("测试文本", True)
        key3 = service._get_cache_key("测试文本", False)
        
        assert key1 == key2  # 相同参数应该生成相同的键
        assert key1 != key3  # 不同参数应该生成不同的键
        assert len(key1) == 32  # MD5哈希长度
    
    def test_manage_cache(self, service):
        """测试缓存管理"""
        service.max_cache_size = 3
        
        # 填充缓存超过最大大小
        for i in range(5):
            service.cache[f"key{i}"] = np.array([i])
        
        service._manage_cache()
        
        # 缓存大小应该被控制在合理范围内
        assert len(service.cache) <= service.max_cache_size
    
    @pytest.mark.asyncio
    async def test_encode_single_text(self, service, mock_sentence_transformer):
        """测试编码单个文本"""
        service.model = mock_sentence_transformer
        service._model_loaded = True
        
        # 模拟编码结果
        mock_sentence_transformer.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        
        result = await service.encode("测试文本")
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.allclose(result, [0.1, 0.2, 0.3])
    
    @pytest.mark.asyncio
    async def test_encode_multiple_texts(self, service, mock_sentence_transformer):
        """测试编码多个文本"""
        service.model = mock_sentence_transformer
        service._model_loaded = True
        
        texts = ["文本1", "文本2"]
        mock_sentence_transformer.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        
        results = await service.encode(texts)
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(r, np.ndarray) for r in results)
    
    @pytest.mark.asyncio
    async def test_encode_with_cache(self, service, mock_sentence_transformer):
        """测试使用缓存的编码"""
        service.model = mock_sentence_transformer
        service._model_loaded = True
        
        text = "测试文本"
        expected_result = np.array([0.1, 0.2, 0.3])
        
        # 第一次调用
        mock_sentence_transformer.encode.return_value = np.array([expected_result])
        result1 = await service.encode(text)
        
        # 第二次调用应该使用缓存
        result2 = await service.encode(text)
        
        assert np.allclose(result1, result2)
        # 模型的encode方法应该只被调用一次
        assert mock_sentence_transformer.encode.call_count == 1
    
    @pytest.mark.asyncio
    async def test_encode_auto_initialize(self, service):
        """测试自动初始化"""
        service._model_loaded = False
        
        with patch.object(service, 'initialize', new_callable=AsyncMock) as mock_init:
            with patch.object(service, '_encode_batch', return_value=[np.array([0.1, 0.2, 0.3])]):
                await service.encode("测试文本")
                mock_init.assert_called_once()
    
    def test_encode_batch(self, service, mock_sentence_transformer):
        """测试批量编码"""
        service.model = mock_sentence_transformer
        
        texts = ["文本1", "文本2"]
        mock_sentence_transformer.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        
        results = service._encode_batch(texts)
        
        assert len(results) == 2
        assert all(r.dtype == np.float32 for r in results)
        mock_sentence_transformer.encode.assert_called_once()
    
    def test_preprocess_text(self, service):
        """测试文本预处理"""
        # 测试正常文本
        text1 = "  这是测试文本  "
        result1 = service._preprocess_text(text1)
        assert result1 == "这是测试文本"
        
        # 测试长文本截断
        long_text = "a" * 7000
        result2 = service._preprocess_text(long_text)
        assert len(result2) <= 6003  # 6000 + "..."
        assert result2.endswith("...")
    
    @pytest.mark.asyncio
    async def test_compute_similarity(self, service):
        """测试计算相似度"""
        with patch.object(service, 'encode') as mock_encode:
            # 模拟两个相似的向量
            mock_encode.return_value = [
                np.array([1.0, 0.0, 0.0]),  # 归一化向量
                np.array([0.8, 0.6, 0.0])   # 归一化向量
            ]
            
            similarity = await service.compute_similarity("文本1", "文本2")
            
            assert 0.0 <= similarity <= 1.0
            mock_encode.assert_called_once_with(["文本1", "文本2"], normalize=True)
    
    @pytest.mark.asyncio
    async def test_compute_similarity_without_normalization(self, service):
        """测试不归一化的相似度计算"""
        with patch.object(service, 'encode') as mock_encode:
            mock_encode.return_value = [
                np.array([2.0, 0.0, 0.0]),  # 未归一化向量
                np.array([1.0, 0.0, 0.0])   # 未归一化向量
            ]
            
            similarity = await service.compute_similarity("文本1", "文本2", normalize=False)
            
            assert 0.0 <= similarity <= 1.0
            mock_encode.assert_called_once_with(["文本1", "文本2"], normalize=False)
    
    @pytest.mark.asyncio
    async def test_compute_similarities(self, service):
        """测试计算多个相似度"""
        with patch.object(service, 'encode') as mock_encode:
            # 查询向量 + 3个文档向量
            mock_encode.return_value = [
                np.array([1.0, 0.0, 0.0]),  # 查询向量
                np.array([0.9, 0.1, 0.0]),  # 文档1
                np.array([0.5, 0.5, 0.0]),  # 文档2
                np.array([0.0, 1.0, 0.0])   # 文档3
            ]
            
            similarities = await service.compute_similarities("查询", ["文档1", "文档2", "文档3"])
            
            assert len(similarities) == 3
            assert all(0.0 <= s <= 1.0 for s in similarities)
            # 第一个文档应该最相似
            assert similarities[0] > similarities[1] > similarities[2]
    
    @pytest.mark.asyncio
    async def test_rerank_success(self, service, mock_sentence_transformer):
        """测试成功重排序"""
        service.reranker_model = mock_sentence_transformer
        service._reranker_loaded = True
        
        query = "查询文本"
        documents = ["文档1", "文档2", "文档3"]
        
        # 模拟重排序分数
        mock_sentence_transformer.predict.return_value = [0.9, 0.7, 0.8]
        
        results = await service.rerank(query, documents)
        
        assert len(results) == 3
        # 结果应该按分数降序排列
        assert results[0][1] >= results[1][1] >= results[2][1]
        # 第一个结果应该是分数最高的文档
        assert results[0] == (0, 0.9)  # 文档0，分数0.9
    
    @pytest.mark.asyncio
    async def test_rerank_with_top_k(self, service, mock_sentence_transformer):
        """测试带top_k的重排序"""
        service.reranker_model = mock_sentence_transformer
        service._reranker_loaded = True
        
        documents = ["文档1", "文档2", "文档3"]
        mock_sentence_transformer.predict.return_value = [0.9, 0.7, 0.8]
        
        results = await service.rerank("查询", documents, top_k=2)
        
        assert len(results) == 2
        assert results[0][1] >= results[1][1]
    
    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self, service):
        """测试重排序空文档列表"""
        results = await service.rerank("查询", [])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_rerank_auto_initialize(self, service):
        """测试重排序自动初始化"""
        service._reranker_loaded = False
        
        with patch.object(service, 'initialize_reranker', new_callable=AsyncMock) as mock_init:
            with patch.object(service, '_rerank_batch', return_value=[0.8]):
                await service.rerank("查询", ["文档"])
                mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rerank_failure(self, service, mock_sentence_transformer):
        """测试重排序失败"""
        service.reranker_model = mock_sentence_transformer
        service._reranker_loaded = True
        
        mock_sentence_transformer.predict.side_effect = Exception("重排序失败")
        
        documents = ["文档1", "文档2"]
        results = await service.rerank("查询", documents)
        
        # 应该返回默认分数
        assert len(results) == 2
        assert all(score == 0.5 for _, score in results)
    
    def test_rerank_batch(self, service, mock_sentence_transformer):
        """测试批量重排序"""
        service.reranker_model = mock_sentence_transformer
        
        query = "查询"
        documents = ["文档1", "文档2"]
        
        mock_sentence_transformer.predict.return_value = np.array([0.8, 0.6])
        
        scores = service._rerank_batch(query, documents)
        
        assert scores == [0.8, 0.6]
        # 验证输入格式
        expected_pairs = [["查询", "文档1"], ["查询", "文档2"]]
        mock_sentence_transformer.predict.assert_called_once_with(expected_pairs)
    
    def test_rerank_batch_failure(self, service, mock_sentence_transformer):
        """测试批量重排序失败"""
        service.reranker_model = mock_sentence_transformer
        mock_sentence_transformer.predict.side_effect = Exception("批量重排序失败")
        
        scores = service._rerank_batch("查询", ["文档1", "文档2"])
        
        assert scores == [0.5, 0.5]  # 默认分数
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, service):
        """测试获取模型信息"""
        service._model_loaded = True
        service.model = Mock()  # Ensure service.model is not None
        service._reranker_loaded = False
        service.cache = {"key1": np.array([1, 2, 3])}
        
        with patch.object(service, 'encode', return_value=np.array([0.1, 0.2, 0.3])):
            info = await service.get_model_info()
        
        assert info["embedding_model_loaded"] is True
        assert info["reranker_model_loaded"] is False
        assert info["cache_size"] == 1
        assert info["embedding_dimension"] == 3
    
    @pytest.mark.asyncio
    async def test_get_model_info_embedding_error(self, service):
        """测试获取模型信息时嵌入维度获取失败"""
        service._model_loaded = True
        service.model = Mock()  # Ensure service.model is not None
        
        with patch.object(service, 'encode', side_effect=Exception("获取维度失败")):
            info = await service.get_model_info()
        
        assert info["embedding_dimension"] == "unknown"
    
    def test_clear_cache(self, service):
        """测试清空缓存"""
        service.cache = {"key1": np.array([1, 2, 3]), "key2": np.array([4, 5, 6])}
        
        service.clear_cache()
        
        assert len(service.cache) == 0
    
    @pytest.mark.asyncio
    async def test_close(self, service):
        """测试关闭服务"""
        service.cache = {"key1": np.array([1, 2, 3])}
        service.executor = Mock()
        service.executor.shutdown = Mock()
        
        await service.close()
        
        assert len(service.cache) == 0
        service.executor.shutdown.assert_called_once_with(wait=True)
    
    def test_load_embedding_model(self, service):
        """测试加载嵌入模型"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            with patch('src.services.embedding_service.settings') as mock_settings: # Patch settings where it's used
                mock_settings.BGE_MODEL_NAME = "test-model"
                mock_settings.BGE_DEVICE = "cpu"
                
                mock_model = Mock()
                mock_model.eval = Mock()
                mock_st.return_value = mock_model
                
                result = service._load_embedding_model()
                
                assert result == mock_model
                mock_st.assert_called_once_with("test-model", device="cpu")
                mock_model.eval.assert_called_once()
    
    def test_load_embedding_model_failure(self, service):
        """测试加载嵌入模型失败"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            mock_st.side_effect = Exception("模型加载失败")
            
            with pytest.raises(Exception, match="模型加载失败"):
                service._load_embedding_model()
    
    def test_load_reranker_model(self, service):
        """测试加载重排序模型"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            with patch('src.services.embedding_service.settings') as mock_settings: # Patch settings where it's used
                mock_settings.BGE_RERANKER_MODEL = "test-reranker"
                mock_settings.BGE_DEVICE = "cpu"
                
                mock_model = Mock()
                mock_model.eval = Mock()
                mock_st.return_value = mock_model
                
                result = service._load_reranker_model()
                
                assert result == mock_model
                mock_st.assert_called_once_with("test-reranker", device="cpu")
                mock_model.eval.assert_called_once()
    
    def test_load_reranker_model_failure(self, service):
        """测试加载重排序模型失败"""
        with patch('src.services.embedding_service.SentenceTransformer') as mock_st:
            mock_st.side_effect = Exception("重排序模型加载失败")
            
            with pytest.raises(Exception, match="重排序模型加载失败"):
                service._load_reranker_model()


class TestGlobalService:
    """全局服务实例测试"""
    
    def test_global_service_instance(self):
        """测试全局服务实例"""
        assert embedding_service is not None
        assert isinstance(embedding_service, EmbeddingService)
        assert embedding_service.max_cache_size == 1000
        assert isinstance(embedding_service.executor, ThreadPoolExecutor)
    
    def test_global_service_initial_state(self):
        """测试全局服务初始状态"""
        assert embedding_service._model_loaded is False
        assert embedding_service._reranker_loaded is False
        assert embedding_service.model is None
        assert embedding_service.reranker_model is None
        assert len(embedding_service.cache) == 0
