"""
向量服务简单测试
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

# 测试向量服务的基本功能
def test_vector_service_import():
    """测试向量服务导入"""
    from src.services.vector_service import VectorService, VectorDocument
    service = VectorService()
    assert service is not None
    
    doc = VectorDocument("test", "content", {})
    assert doc.id == "test"
    assert doc.content == "content"

def test_embedding_service_import():
    """测试嵌入服务导入"""
    from src.services.embedding_service import EmbeddingService
    service = EmbeddingService()
    assert service is not None

def test_elasticsearch_service_import():
    """测试Elasticsearch服务导入"""
    from src.services.elasticsearch_service import ElasticsearchService
    service = ElasticsearchService()
    assert service is not None

def test_hybrid_search_service_import():
    """测试混合搜索服务导入"""
    from src.services.hybrid_search_service import HybridSearchService, SearchMode
    service = HybridSearchService()
    assert service is not None
    assert SearchMode.HYBRID.value == "hybrid"

class TestVectorServiceBasic:
    """向量服务基础测试"""
    
    def test_create_service(self):
        """测试创建服务"""
        from src.services.vector_service import VectorService
        service = VectorService()
        assert service.default_collection == "hicrm_knowledge"
        assert service.embedding_dimension == 1024
    
    @pytest.mark.asyncio
    async def test_mock_initialize(self):
        """测试模拟初始化"""
        from src.services.vector_service import VectorService
        
        service = VectorService()
        
        with patch('src.services.vector_service.QdrantClient') as mock_client_class:
            with patch('src.services.embedding_service.embedding_service') as mock_embedding:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.get_collections.return_value = Mock(collections=[])
                
                mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
                
                with patch.object(service, 'create_collection', return_value=True):
                    await service.initialize()
                
                assert service.client is not None