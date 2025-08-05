"""
Elasticsearch服务测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.services.elasticsearch_service import (
    ElasticsearchService, ElasticsearchDocument, ElasticsearchSearchResult, elasticsearch_service
)


class TestElasticsearchDocument:
    """Elasticsearch文档测试类"""
    
    def test_create_document(self):
        """测试创建Elasticsearch文档"""
        metadata = {"category": "tech", "author": "张三"}
        doc = ElasticsearchDocument(
            id="doc1",
            content="这是测试内容",
            metadata=metadata,
            title="测试标题"
        )
        
        assert doc.id == "doc1"
        assert doc.content == "这是测试内容"
        assert doc.metadata == metadata
        assert doc.title == "测试标题"
        assert isinstance(doc.created_at, datetime)
    
    def test_create_document_without_title(self):
        """测试创建没有标题的文档"""
        doc = ElasticsearchDocument(
            id="doc1",
            content="内容",
            metadata={}
        )
        
        assert doc.title == ""


class TestElasticsearchSearchResult:
    """Elasticsearch搜索结果测试类"""
    
    def test_create_result(self):
        """测试创建搜索结果"""
        doc = ElasticsearchDocument("doc1", "内容", {}, "标题")
        highlights = {"content": ["<mark>内容</mark>"]}
        result = ElasticsearchSearchResult(doc, 15.5, highlights)
        
        assert result.document == doc
        assert result.score == 15.5
        assert result.highlights == highlights
    
    def test_create_result_without_highlights(self):
        """测试创建没有高亮的搜索结果"""
        doc = ElasticsearchDocument("doc1", "内容", {}, "标题")
        result = ElasticsearchSearchResult(doc, 10.0)
        
        assert result.highlights == {}


class TestElasticsearchService:
    """Elasticsearch服务测试类"""
    
    @pytest.fixture
    def service(self):
        """创建Elasticsearch服务实例"""
        return ElasticsearchService()
    
    @pytest.fixture
    def mock_es_client(self):
        """模拟Elasticsearch客户端"""
        client = Mock()
        client.info = AsyncMock(return_value={"version": {"number": "8.11.0"}})
        client.indices.exists = AsyncMock(return_value=False)
        client.indices.create = AsyncMock()
        client.indices.delete = AsyncMock()
        client.indices.get_alias = AsyncMock(return_value={"index1": {}, "index2": {}})
        client.indices.stats = AsyncMock()
        client.bulk = AsyncMock(return_value={"errors": False, "items": []})
        client.search = AsyncMock()
        client.index = AsyncMock()
        client.close = AsyncMock()
        return client
    
    @pytest.fixture
    def sample_documents(self):
        """示例文档"""
        return [
            ElasticsearchDocument("doc1", "这是第一个关于人工智能的文档", {"category": "tech"}, "AI技术"),
            ElasticsearchDocument("doc2", "这是第二个关于机器学习的文档", {"category": "tech"}, "机器学习"),
            ElasticsearchDocument("doc3", "这是第三个关于深度学习的文档", {"category": "research"}, "深度学习")
        ]
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, service):
        """测试成功初始化"""
        with patch('src.services.elasticsearch_service.AsyncElasticsearch') as mock_es_class:
            mock_client = Mock()
            mock_client.info = AsyncMock(return_value={"version": {"number": "8.11.0"}})
            mock_es_class.return_value = mock_client
            
            with patch.object(service, 'create_index', return_value=True):
                await service.initialize()
            
            assert service.client is not None
            mock_client.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_with_auth(self, service):
        """测试使用认证初始化"""
        with patch('src.core.config.settings') as mock_settings:
            mock_settings.ELASTICSEARCH_URL = "http://localhost:9200"
            mock_settings.ELASTICSEARCH_USERNAME = "elastic"
            mock_settings.ELASTICSEARCH_PASSWORD = "password"
            
            with patch('src.services.elasticsearch_service.AsyncElasticsearch') as mock_es_class:
                mock_client = Mock()
                mock_client.info = AsyncMock(return_value={"version": {"number": "8.11.0"}})
                mock_es_class.return_value = mock_client
                
                with patch.object(service, 'create_index', return_value=True):
                    await service.initialize()
                
                # 验证使用认证信息创建客户端
                call_args = mock_es_class.call_args[1]
                assert "basic_auth" in call_args
                assert call_args["basic_auth"] == ("elastic", "password")
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, service):
        """测试初始化失败"""
        with patch('src.services.elasticsearch_service.AsyncElasticsearch') as mock_es_class:
            mock_es_class.side_effect = Exception("连接失败")
            
            with pytest.raises(Exception, match="连接失败"):
                await service.initialize()
    
    @pytest.mark.asyncio
    async def test_create_index_success(self, service, mock_es_client):
        """测试成功创建索引"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = False
        
        result = await service.create_index("test_index")
        
        assert result is True
        assert "test_index" in service.indices
        mock_es_client.indices.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_index_already_exists(self, service, mock_es_client):
        """测试索引已存在"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = True
        
        result = await service.create_index("test_index")
        
        assert result is True
        mock_es_client.indices.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_index_recreate(self, service, mock_es_client):
        """测试重新创建索引"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = True
        
        result = await service.create_index("test_index", recreate=True)
        
        assert result is True
        mock_es_client.indices.delete.assert_called_once_with(index="test_index")
        mock_es_client.indices.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_index_without_ik_analyzer(self, service, mock_es_client):
        """测试在没有IK分词器时创建索引"""
        from elasticsearch.exceptions import RequestError
        
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = False
        
        # 第一次调用失败（没有IK分词器）
        mock_es_client.indices.create.side_effect = [
            RequestError(400, "unknown_tokenizer", {}),
            None  # 第二次调用成功
        ]
        
        result = await service.create_index("test_index")
        
        assert result is True
        assert mock_es_client.indices.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_index_failure(self, service, mock_es_client):
        """测试创建索引失败"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = False
        mock_es_client.indices.create.side_effect = Exception("创建失败")
        
        result = await service.create_index("test_index")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_documents_success(self, service, sample_documents, mock_es_client):
        """测试成功添加文档"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = True
        mock_es_client.bulk.return_value = {"errors": False, "items": []}
        
        result = await service.add_documents(sample_documents, "test_index")
        
        assert result is True
        mock_es_client.bulk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_documents_empty_list(self, service):
        """测试添加空文档列表"""
        result = await service.add_documents([])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_add_documents_create_index(self, service, sample_documents, mock_es_client):
        """测试添加文档时自动创建索引"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = False
        
        with patch.object(service, 'create_index', return_value=True) as mock_create:
            result = await service.add_documents(sample_documents, "test_index")
            mock_create.assert_called_once_with("test_index")
    
    @pytest.mark.asyncio
    async def test_add_documents_with_errors(self, service, sample_documents, mock_es_client):
        """测试添加文档时有错误"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = True
        mock_es_client.bulk.return_value = {
            "errors": True,
            "items": [
                {"index": {"error": {"type": "version_conflict_engine_exception"}}},
                {"index": {"_id": "doc2", "result": "created"}}
            ]
        }
        
        result = await service.add_documents(sample_documents, "test_index")
        
        assert result is True  # 仍然返回True，但会记录警告
    
    @pytest.mark.asyncio
    async def test_add_documents_failure(self, service, sample_documents, mock_es_client):
        """测试添加文档失败"""
        service.client = mock_es_client
        mock_es_client.indices.exists.return_value = True
        mock_es_client.bulk.side_effect = Exception("批量操作失败")
        
        result = await service.add_documents(sample_documents, "test_index")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_search_success(self, service, mock_es_client):
        """测试成功搜索"""
        service.client = mock_es_client
        
        # 模拟搜索结果
        mock_response = {
            "hits": {
                "hits": [
                    {
                        "_id": "doc1",
                        "_score": 15.5,
                        "_source": {
                            "content": "这是关于人工智能的文档",
                            "title": "AI技术",
                            "metadata": {"category": "tech"},
                            "created_at": "2023-01-01T00:00:00"
                        },
                        "highlight": {
                            "content": ["这是关于<mark>人工智能</mark>的文档"]
                        }
                    }
                ]
            }
        }
        mock_es_client.search.return_value = mock_response
        
        results = await service.search("人工智能", "test_index")
        
        assert len(results) == 1
        assert results[0].document.id == "doc1"
        assert results[0].score == 15.5
        assert results[0].document.content == "这是关于人工智能的文档"
        assert "content" in results[0].highlights
        
        mock_es_client.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, service, mock_es_client):
        """测试带过滤条件的搜索"""
        service.client = mock_es_client
        mock_es_client.search.return_value = {"hits": {"hits": []}}
        
        filters = {"category": "tech", "author": "张三"}
        await service.search("测试查询", filters=filters)
        
        # 验证过滤条件被正确添加
        call_args = mock_es_client.search.call_args[1]
        search_body = call_args["body"]
        assert "filter" in search_body["query"]["bool"]
    
    @pytest.mark.asyncio
    async def test_search_without_highlight(self, service, mock_es_client):
        """测试不使用高亮的搜索"""
        service.client = mock_es_client
        mock_es_client.search.return_value = {"hits": {"hits": []}}
        
        await service.search("测试查询", highlight=False)
        
        call_args = mock_es_client.search.call_args[1]
        search_body = call_args["body"]
        assert "highlight" not in search_body
    
    @pytest.mark.asyncio
    async def test_search_failure(self, service, mock_es_client):
        """测试搜索失败"""
        service.client = mock_es_client
        mock_es_client.search.side_effect = Exception("搜索失败")
        
        results = await service.search("测试查询")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_multi_match_search(self, service, mock_es_client):
        """测试多字段匹配搜索"""
        service.client = mock_es_client
        mock_es_client.search.return_value = {"hits": {"hits": []}}
        
        fields = ["content", "title"]
        await service.multi_match_search("测试查询", fields)
        
        call_args = mock_es_client.search.call_args[1]
        search_body = call_args["body"]
        assert search_body["query"]["multi_match"]["fields"] == fields
        assert search_body["query"]["multi_match"]["fuzziness"] == "AUTO"
    
    @pytest.mark.asyncio
    async def test_multi_match_search_failure(self, service, mock_es_client):
        """测试多字段搜索失败"""
        service.client = mock_es_client
        mock_es_client.search.side_effect = Exception("多字段搜索失败")
        
        results = await service.multi_match_search("查询", ["content"])
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_delete_documents_success(self, service, mock_es_client):
        """测试成功删除文档"""
        service.client = mock_es_client
        mock_es_client.bulk.return_value = {"errors": False, "items": []}
        
        document_ids = ["doc1", "doc2", "doc3"]
        result = await service.delete_documents(document_ids, "test_index")
        
        assert result is True
        mock_es_client.bulk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_documents_with_errors(self, service, mock_es_client):
        """测试删除文档时有错误"""
        service.client = mock_es_client
        mock_es_client.bulk.return_value = {
            "errors": True,
            "items": [
                {"delete": {"error": {"type": "not_found_exception"}}},
                {"delete": {"_id": "doc2", "result": "deleted"}}
            ]
        }
        
        result = await service.delete_documents(["doc1", "doc2"], "test_index")
        
        assert result is True  # 仍然返回True，但会记录警告
    
    @pytest.mark.asyncio
    async def test_delete_documents_failure(self, service, mock_es_client):
        """测试删除文档失败"""
        service.client = mock_es_client
        mock_es_client.bulk.side_effect = Exception("删除失败")
        
        result = await service.delete_documents(["doc1"], "test_index")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_document_success(self, service, mock_es_client):
        """测试成功更新文档"""
        service.client = mock_es_client
        mock_es_client.index = AsyncMock()
        
        doc = ElasticsearchDocument("doc1", "更新内容", {"category": "updated"}, "更新标题")
        result = await service.update_document(doc, "test_index")
        
        assert result is True
        mock_es_client.index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_document_failure(self, service, mock_es_client):
        """测试更新文档失败"""
        service.client = mock_es_client
        mock_es_client.index.side_effect = Exception("更新失败")
        
        doc = ElasticsearchDocument("doc1", "内容", {}, "标题")
        result = await service.update_document(doc, "test_index")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_index_stats_success(self, service, mock_es_client):
        """测试成功获取索引统计"""
        service.client = mock_es_client
        
        mock_stats = {
            "indices": {
                "test_index": {
                    "total": {
                        "docs": {"count": 100, "deleted": 5},
                        "store": {"size_in_bytes": 1024000},
                        "segments": {"count": 3}
                    }
                }
            }
        }
        mock_es_client.indices.stats.return_value = mock_stats
        
        stats = await service.get_index_stats("test_index")
        
        assert stats["name"] == "test_index"
        assert stats["docs_count"] == 100
        assert stats["docs_deleted"] == 5
        assert stats["store_size"] == 1024000
        assert stats["segments_count"] == 3
    
    @pytest.mark.asyncio
    async def test_get_index_stats_failure(self, service, mock_es_client):
        """测试获取索引统计失败"""
        service.client = mock_es_client
        mock_es_client.indices.stats.side_effect = Exception("获取统计失败")
        
        stats = await service.get_index_stats("test_index")
        
        assert stats == {}
    
    @pytest.mark.asyncio
    async def test_list_indices_success(self, service, mock_es_client):
        """测试成功列出索引"""
        service.client = mock_es_client
        mock_es_client.indices.get_alias.return_value = {
            "index1": {},
            "index2": {},
            "index3": {}
        }
        
        indices = await service.list_indices()
        
        assert indices == ["index1", "index2", "index3"]
    
    @pytest.mark.asyncio
    async def test_list_indices_failure(self, service, mock_es_client):
        """测试列出索引失败"""
        service.client = mock_es_client
        mock_es_client.indices.get_alias.side_effect = Exception("列出索引失败")
        
        indices = await service.list_indices()
        
        assert indices == []
    
    @pytest.mark.asyncio
    async def test_delete_index_success(self, service, mock_es_client):
        """测试成功删除索引"""
        service.client = mock_es_client
        service.indices["test_index"] = {}
        mock_es_client.indices.delete = AsyncMock()
        
        result = await service.delete_index("test_index")
        
        assert result is True
        assert "test_index" not in service.indices
        mock_es_client.indices.delete.assert_called_once_with(index="test_index")
    
    @pytest.mark.asyncio
    async def test_delete_index_failure(self, service, mock_es_client):
        """测试删除索引失败"""
        service.client = mock_es_client
        mock_es_client.indices.delete.side_effect = Exception("删除索引失败")
        
        result = await service.delete_index("test_index")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_close(self, service, mock_es_client):
        """测试关闭连接"""
        service.client = mock_es_client
        
        await service.close()
        
        mock_es_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_without_client(self, service):
        """测试没有客户端时关闭连接"""
        service.client = None
        
        # 应该不会抛出异常
        await service.close()


class TestGlobalService:
    """全局服务实例测试"""
    
    def test_global_service_instance(self):
        """测试全局服务实例"""
        assert elasticsearch_service is not None
        assert isinstance(elasticsearch_service, ElasticsearchService)
        assert elasticsearch_service.client is None
        assert len(elasticsearch_service.indices) == 0
    
    def test_default_index_name(self):
        """测试默认索引名称"""
        with patch('src.core.config.settings') as mock_settings:
            mock_settings.ELASTICSEARCH_INDEX_PREFIX = "test"
            service = ElasticsearchService()
            assert service.default_index == "test_knowledge"