"""
向量数据库服务测试
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from src.services.vector_service import (
    VectorService, VectorDocument, VectorSearchResult, vector_service
)
from qdrant_client.http.models import Distance


class TestVectorDocument:
    """向量文档测试类"""
    
    def test_create_document(self):
        """测试创建向量文档"""
        metadata = {"category": "test", "author": "张三"}
        doc = VectorDocument(
            id="doc1",
            content="这是测试内容",
            metadata=metadata
        )
        
        assert doc.id == "doc1"
        assert doc.content == "这是测试内容"
        assert doc.metadata == metadata
        assert doc.embedding is None
        assert isinstance(doc.created_at, datetime)
    
    def test_create_document_with_embedding(self):
        """测试创建带嵌入向量的文档"""
        embedding = np.array([0.1, 0.2, 0.3])
        doc = VectorDocument(
            id="doc1",
            content="测试内容",
            metadata={},
            embedding=embedding
        )
        
        assert np.array_equal(doc.embedding, embedding)


class TestVectorSearchResult:
    """向量搜索结果测试类"""
    
    def test_create_result(self):
        """测试创建搜索结果"""
        doc = VectorDocument("doc1", "内容", {"title": "标题"})
        result = VectorSearchResult(doc, 0.95, 0.05)
        
        assert result.document == doc
        assert result.score == 0.95
        assert result.distance == 0.05


class TestVectorService:
    """向量数据库服务测试类"""
    
    @pytest.fixture
    def service(self):
        """创建向量服务实例"""
        return VectorService()
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """模拟Qdrant客户端"""
        client = Mock()
        client.get_collections.return_value = Mock(collections=[])
        return client
    
    @pytest.fixture
    def sample_documents(self):
        """示例文档"""
        return [
            VectorDocument("doc1", "这是第一个文档", {"category": "tech"}),
            VectorDocument("doc2", "这是第二个文档", {"category": "business"}),
            VectorDocument("doc3", "这是第三个文档", {"category": "research"})
        ]
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, service):
        """测试成功初始化"""
        with patch('src.services.vector_service.QdrantClient') as mock_client_class:
            with patch('src.services.embedding_service.embedding_service') as mock_embedding:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.get_collections.return_value = Mock(collections=[])
                
                mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
                
                with patch.object(service, 'create_collection', return_value=True):
                    await service.initialize()
                
                assert service.client is not None
                assert service.embedding_dimension == 1024
    
    @pytest.mark.asyncio
    async def test_initialize_with_api_key(self, service):
        """测试使用API密钥初始化"""
        with patch('src.core.config.settings') as mock_settings:
            mock_settings.QDRANT_API_KEY = "hicrm"
            mock_settings.QDRANT_URL = "http://localhost:6333"
            
            with patch('src.services.vector_service.QdrantClient') as mock_client_class:
                with patch('src.services.embedding_service.embedding_service') as mock_embedding:
                    mock_client = Mock()
                    mock_client_class.return_value = mock_client
                    mock_client.get_collections.return_value = Mock(collections=[])
                    
                    mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
                    
                    with patch.object(service, 'create_collection', return_value=True):
                        await service.initialize()
                    
                    # 验证使用API密钥创建客户端
                    mock_client_class.assert_called_with(
                        url="http://localhost:6333",
                        api_key="hicrm",
                        timeout=30
                    )
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, service):
        """测试初始化失败"""
        with patch('src.services.vector_service.QdrantClient') as mock_client_class:
            mock_client_class.side_effect = Exception("连接失败")
            
            with pytest.raises(Exception, match="连接失败"):
                await service.initialize()
    
    @pytest.mark.asyncio
    async def test_create_collection_success(self, service, mock_qdrant_client):
        """测试成功创建集合"""
        service.client = mock_qdrant_client
        service.embedding_dimension = 1024
        
        # 模拟集合不存在
        mock_qdrant_client.get_collections.return_value = Mock(collections=[])
        mock_qdrant_client.create_collection = Mock()
        
        result = await service.create_collection("test_collection")
        
        assert result is True
        assert "test_collection" in service.collections
        mock_qdrant_client.create_collection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_collection_already_exists(self, service, mock_qdrant_client):
        """测试集合已存在"""
        service.client = mock_qdrant_client
        
        # 模拟集合已存在
        existing_collection = Mock()
        existing_collection.name = "test_collection"
        mock_qdrant_client.get_collections.return_value = Mock(collections=[existing_collection])
        
        result = await service.create_collection("test_collection")
        
        assert result is True
        assert "test_collection" in service.collections
    
    @pytest.mark.asyncio
    async def test_create_collection_recreate(self, service, mock_qdrant_client):
        """测试重新创建集合"""
        service.client = mock_qdrant_client
        service.embedding_dimension = 1024
        
        # 模拟集合已存在
        existing_collection = Mock()
        existing_collection.name = "test_collection"
        mock_qdrant_client.get_collections.return_value = Mock(collections=[existing_collection])
        mock_qdrant_client.delete_collection = Mock()
        mock_qdrant_client.create_collection = Mock()
        
        result = await service.create_collection("test_collection", recreate=True)
        
        assert result is True
        mock_qdrant_client.delete_collection.assert_called_once_with("test_collection")
        mock_qdrant_client.create_collection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_documents_success(self, service, sample_documents, mock_qdrant_client):
        """测试成功添加文档"""
        service.client = mock_qdrant_client
        service.collections["test_collection"] = {"vector_size": 1024}
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            # 模拟嵌入服务返回向量
            embeddings = [np.array([0.1] * 1024) for _ in sample_documents]
            mock_embedding.encode = AsyncMock(return_value=embeddings)
            
            mock_qdrant_client.upsert = Mock()
            
            result = await service.add_documents(sample_documents, "test_collection")
            
            assert result is True
            mock_embedding.encode.assert_called_once()
            mock_qdrant_client.upsert.assert_called()
    
    @pytest.mark.asyncio
    async def test_add_documents_empty_list(self, service):
        """测试添加空文档列表"""
        result = await service.add_documents([])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_add_documents_create_collection(self, service, sample_documents, mock_qdrant_client):
        """测试添加文档时自动创建集合"""
        service.client = mock_qdrant_client
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            with patch.object(service, 'create_collection', return_value=True) as mock_create:
                embeddings = [np.array([0.1] * 1024) for _ in sample_documents]
                mock_embedding.encode = AsyncMock(return_value=embeddings)
                mock_qdrant_client.upsert = Mock()
                
                result = await service.add_documents(sample_documents)
                
                assert result is True
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_documents_failure(self, service, sample_documents, mock_qdrant_client):
        """测试添加文档失败"""
        service.client = mock_qdrant_client
        service.collections["test_collection"] = {"vector_size": 1024}
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.encode = AsyncMock(side_effect=Exception("嵌入失败"))
            
            result = await service.add_documents(sample_documents, "test_collection")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_search_success(self, service, mock_qdrant_client):
        """测试成功搜索"""
        service.client = mock_qdrant_client
        
        # 模拟搜索结果
        mock_point = Mock()
        mock_point.id = "doc1"
        mock_point.score = 0.95
        mock_point.payload = {
            "content": "测试内容",
            "created_at": "2023-01-01T00:00:00",
            "category": "test"
        }
        
        mock_qdrant_client.search.return_value = [mock_point]
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
            
            results = await service.search("测试查询")
            
            assert len(results) == 1
            assert results[0].document.id == "doc1"
            assert results[0].score == 0.95
            assert results[0].document.content == "测试内容"
            
            mock_embedding.encode.assert_called_once_with("测试查询")
            mock_qdrant_client.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, service, mock_qdrant_client):
        """测试带过滤条件的搜索"""
        service.client = mock_qdrant_client
        mock_qdrant_client.search.return_value = []
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
            
            filters = {"category": "tech"}
            await service.search("测试查询", filters=filters)
            
            # 验证过滤器被正确传递
            call_args = mock_qdrant_client.search.call_args
            assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_search_by_vector(self, service, mock_qdrant_client):
        """测试通过向量搜索"""
        service.client = mock_qdrant_client
        
        mock_point = Mock()
        mock_point.id = "doc1"
        mock_point.score = 0.9
        mock_point.payload = {"content": "内容", "created_at": "2023-01-01T00:00:00"}
        
        mock_qdrant_client.search.return_value = [mock_point]
        
        query_vector = np.array([0.1] * 1024)
        results = await service.search_by_vector(query_vector)
        
        assert len(results) == 1
        assert results[0].score == 0.9
        mock_qdrant_client.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_failure(self, service, mock_qdrant_client):
        """测试搜索失败"""
        service.client = mock_qdrant_client
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.encode = AsyncMock(side_effect=Exception("嵌入失败"))
            
            results = await service.search("测试查询")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_delete_documents_success(self, service, mock_qdrant_client):
        """测试成功删除文档"""
        service.client = mock_qdrant_client
        mock_qdrant_client.delete = Mock()
        
        document_ids = ["doc1", "doc2", "doc3"]
        result = await service.delete_documents(document_ids)
        
        assert result is True
        mock_qdrant_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_documents_failure(self, service, mock_qdrant_client):
        """测试删除文档失败"""
        service.client = mock_qdrant_client
        mock_qdrant_client.delete = Mock(side_effect=Exception("删除失败"))
        
        result = await service.delete_documents(["doc1"])
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_document_success(self, service, mock_qdrant_client):
        """测试成功更新文档"""
        service.client = mock_qdrant_client
        mock_qdrant_client.upsert = Mock()
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.encode = AsyncMock(return_value=np.array([0.1] * 1024))
            
            doc = VectorDocument("doc1", "更新内容", {"category": "updated"})
            result = await service.update_document(doc)
            
            assert result is True
            mock_embedding.encode.assert_called_once_with("更新内容")
            mock_qdrant_client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_document_failure(self, service, mock_qdrant_client):
        """测试更新文档失败"""
        service.client = mock_qdrant_client
        
        with patch('src.services.embedding_service.embedding_service') as mock_embedding:
            mock_embedding.encode = AsyncMock(side_effect=Exception("嵌入失败"))
            
            doc = VectorDocument("doc1", "内容", {})
            result = await service.update_document(doc)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_collection_info(self, service, mock_qdrant_client):
        """测试获取集合信息"""
        service.client = mock_qdrant_client
        
        mock_info = Mock()
        mock_info.vectors_count = 100
        mock_info.indexed_vectors_count = 95
        mock_info.points_count = 100
        mock_info.segments_count = 2
        mock_info.config.params.vectors.size = 1024
        mock_info.config.params.vectors.distance.value = "Cosine"
        mock_info.status.value = "green"
        
        mock_qdrant_client.get_collection.return_value = mock_info
        
        info = await service.get_collection_info("test_collection")
        
        assert info["vectors_count"] == 100
        assert info["config"]["vector_size"] == 1024
        assert info["status"] == "green"
    
    @pytest.mark.asyncio
    async def test_get_collection_info_failure(self, service, mock_qdrant_client):
        """测试获取集合信息失败"""
        service.client = mock_qdrant_client
        mock_qdrant_client.get_collection = Mock(side_effect=Exception("获取失败"))
        
        info = await service.get_collection_info("test_collection")
        
        assert info == {}
    
    @pytest.mark.asyncio
    async def test_list_collections(self, service, mock_qdrant_client):
        """测试列出集合"""
        service.client = mock_qdrant_client
        
        mock_col1 = Mock()
        mock_col1.name = "collection1"
        mock_col2 = Mock()
        mock_col2.name = "collection2"
        
        mock_qdrant_client.get_collections.return_value = Mock(collections=[mock_col1, mock_col2])
        
        collections = await service.list_collections()
        
        assert collections == ["collection1", "collection2"]
    
    @pytest.mark.asyncio
    async def test_list_collections_failure(self, service, mock_qdrant_client):
        """测试列出集合失败"""
        service.client = mock_qdrant_client
        mock_qdrant_client.get_collections = Mock(side_effect=Exception("列出失败"))
        
        collections = await service.list_collections()
        
        assert collections == []
    
    @pytest.mark.asyncio
    async def test_delete_collection_success(self, service, mock_qdrant_client):
        """测试成功删除集合"""
        service.client = mock_qdrant_client
        service.collections["test_collection"] = {}
        mock_qdrant_client.delete_collection = Mock()
        
        result = await service.delete_collection("test_collection")
        
        assert result is True
        assert "test_collection" not in service.collections
        mock_qdrant_client.delete_collection.assert_called_once_with("test_collection")
    
    @pytest.mark.asyncio
    async def test_delete_collection_failure(self, service, mock_qdrant_client):
        """测试删除集合失败"""
        service.client = mock_qdrant_client
        mock_qdrant_client.delete_collection = Mock(side_effect=Exception("删除失败"))
        
        result = await service.delete_collection("test_collection")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_stats(self, service):
        """测试获取统计信息"""
        with patch.object(service, 'list_collections', return_value=["col1", "col2"]):
            with patch.object(service, 'get_collection_info') as mock_get_info:
                mock_get_info.side_effect = [
                    {"name": "col1", "vectors_count": 100},
                    {"name": "col2", "vectors_count": 200}
                ]
                
                stats = await service.get_stats()
                
                assert stats["total_collections"] == 2
                assert "col1" in stats["collections"]
                assert "col2" in stats["collections"]
    
    @pytest.mark.asyncio
    async def test_get_stats_failure(self, service):
        """测试获取统计信息失败"""
        with patch.object(service, 'list_collections', side_effect=Exception("获取失败")):
            stats = await service.get_stats()
            assert stats == {}
    
    def test_build_filter(self, service):
        """测试构建过滤器"""
        filters = {
            "category": "tech",
            "author": "张三",
            "score": 0.8,
            "published": True
        }
        
        filter_obj = service._build_filter(filters)
        
        assert filter_obj is not None
        assert len(filter_obj.must) == 4
    
    def test_build_filter_empty(self, service):
        """测试构建空过滤器"""
        filter_obj = service._build_filter({})
        assert filter_obj is None
    
    @pytest.mark.asyncio
    async def test_close(self, service):
        """测试关闭服务"""
        service.client = Mock()
        
        await service.close()
        
        assert service.client is None


class TestGlobalService:
    """全局服务实例测试"""
    
    def test_global_service_instance(self):
        """测试全局服务实例"""
        assert vector_service is not None
        assert isinstance(vector_service, VectorService)
        assert vector_service.default_collection == "hicrm_knowledge"
        assert vector_service.embedding_dimension == 1024