"""
Elasticsearch服务 - 用于BM25文本搜索
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import (
    ConnectionError, NotFoundError, RequestError, TransportError
)

from src.core.config import settings

logger = logging.getLogger(__name__)


class ElasticsearchDocument:
    """Elasticsearch文档类"""
    
    def __init__(
        self,
        id: str,
        content: str,
        metadata: Dict[str, Any],
        title: Optional[str] = None
    ):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.title = title or ""
        self.created_at = datetime.utcnow()


class ElasticsearchSearchResult:
    """Elasticsearch搜索结果类"""
    
    def __init__(
        self,
        document: ElasticsearchDocument,
        score: float,
        highlights: Optional[Dict[str, List[str]]] = None
    ):
        self.document = document
        self.score = score
        self.highlights = highlights or {}


class ElasticsearchService:
    """
    Elasticsearch服务类
    
    提供BM25文本搜索功能，用于混合检索
    """
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
        self.default_index = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_knowledge"
        self.indices: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """初始化Elasticsearch连接"""
        try:
            logger.info("正在初始化Elasticsearch连接...")
            
            # 创建客户端配置
            client_config = {
                "hosts": [settings.ELASTICSEARCH_URL],
                "timeout": 30,
                "max_retries": 3,
                "retry_on_timeout": True
            }
            
            # 添加认证信息
            if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
                client_config["basic_auth"] = (
                    settings.ELASTICSEARCH_USERNAME,
                    settings.ELASTICSEARCH_PASSWORD
                )
            
            # 创建客户端
            self.client = AsyncElasticsearch(**client_config)
            
            # 测试连接
            await self._test_connection()
            
            # 创建默认索引
            await self.create_index(self.default_index)
            
            logger.info("Elasticsearch初始化完成")
            
        except Exception as e:
            logger.error(f"初始化Elasticsearch失败: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """测试连接"""
        try:
            info = await self.client.info()
            logger.info(f"Elasticsearch连接成功，版本: {info['version']['number']}")
        except Exception as e:
            logger.error(f"Elasticsearch连接测试失败: {e}")
            raise
    
    async def create_index(
        self,
        index_name: str,
        recreate: bool = False
    ) -> bool:
        """
        创建索引
        
        Args:
            index_name: 索引名称
            recreate: 是否重新创建
            
        Returns:
            是否创建成功
        """
        try:
            # 检查索引是否存在
            exists = await self.client.indices.exists(index=index_name)
            
            if exists:
                if recreate:
                    logger.info(f"删除现有索引: {index_name}")
                    await self.client.indices.delete(index=index_name)
                else:
                    logger.info(f"索引已存在: {index_name}")
                    return True
            
            # 定义索引映射
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "ik_max_word",  # 中文分词器
                            "search_analyzer": "ik_smart"
                        },
                        "title": {
                            "type": "text",
                            "analyzer": "ik_max_word",
                            "search_analyzer": "ik_smart",
                            "boost": 2.0  # 标题权重更高
                        },
                        "created_at": {
                            "type": "date"
                        },
                        "metadata": {
                            "type": "object",
                            "dynamic": True
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "chinese_analyzer": {
                                "type": "custom",
                                "tokenizer": "ik_max_word",
                                "filter": ["lowercase", "stop"]
                            }
                        }
                    }
                }
            }
            
            # 如果没有IK分词器，使用标准分词器
            try:
                await self.client.indices.create(index=index_name, body=mapping)
            except RequestError as e:
                if "unknown_tokenizer" in str(e):
                    logger.warning("IK分词器不可用，使用标准分词器")
                    # 使用标准分词器的映射
                    mapping["mappings"]["properties"]["content"]["analyzer"] = "standard"
                    mapping["mappings"]["properties"]["content"]["search_analyzer"] = "standard"
                    mapping["mappings"]["properties"]["title"]["analyzer"] = "standard"
                    mapping["mappings"]["properties"]["title"]["search_analyzer"] = "standard"
                    del mapping["settings"]["analysis"]
                    
                    await self.client.indices.create(index=index_name, body=mapping)
                else:
                    raise
            
            self.indices[index_name] = {"created_at": datetime.utcnow()}
            logger.info(f"索引创建成功: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    async def add_documents(
        self,
        documents: List[ElasticsearchDocument],
        index_name: Optional[str] = None,
        batch_size: int = 100
    ) -> bool:
        """
        添加文档到索引
        
        Args:
            documents: 文档列表
            index_name: 索引名称
            batch_size: 批处理大小
            
        Returns:
            是否添加成功
        """
        if not documents:
            return True
        
        index_name = index_name or self.default_index
        
        try:
            # 确保索引存在
            if not await self.client.indices.exists(index=index_name):
                await self.create_index(index_name)
            
            # 批量处理
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                
                # 构建批量操作
                body = []
                for doc in batch_docs:
                    # 索引操作
                    body.append({
                        "index": {
                            "_index": index_name,
                            "_id": doc.id
                        }
                    })
                    
                    # 文档内容
                    doc_body = {
                        "content": doc.content,
                        "title": doc.title,
                        "created_at": doc.created_at.isoformat(),
                        "metadata": doc.metadata
                    }
                    body.append(doc_body)
                
                # 执行批量操作
                response = await self.client.bulk(body=body)
                
                # 检查错误
                if response.get("errors"):
                    errors = [
                        item for item in response["items"]
                        if "error" in item.get("index", {})
                    ]
                    if errors:
                        logger.warning(f"批量插入部分失败: {errors[:3]}")
                
                logger.debug(f"批量插入 {len(batch_docs)} 个文档到索引 {index_name}")
            
            logger.info(f"成功添加 {len(documents)} 个文档到索引 {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    async def search(
        self,
        query: str,
        index_name: Optional[str] = None,
        size: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        highlight: bool = True
    ) -> List[ElasticsearchSearchResult]:
        """
        BM25文本搜索
        
        Args:
            query: 查询文本
            index_name: 索引名称
            size: 返回结果数量
            min_score: 最小分数
            filters: 过滤条件
            highlight: 是否高亮显示
            
        Returns:
            搜索结果列表
        """
        index_name = index_name or self.default_index
        
        try:
            # 构建查询
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "boost": 1.0
                                    }
                                }
                            },
                            {
                                "match": {
                                    "title": {
                                        "query": query,
                                        "boost": 2.0
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": size,
                "min_score": min_score
            }
            
            # 添加过滤条件
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, (str, int, float, bool)):
                        filter_conditions.append({
                            "term": {f"metadata.{key}": value}
                        })
                    elif isinstance(value, list):
                        filter_conditions.append({
                            "terms": {f"metadata.{key}": value}
                        })
                
                if filter_conditions:
                    search_body["query"]["bool"]["filter"] = filter_conditions
            
            # 添加高亮
            if highlight:
                search_body["highlight"] = {
                    "fields": {
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        },
                        "title": {
                            "fragment_size": 100,
                            "number_of_fragments": 1
                        }
                    },
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            
            # 执行搜索
            response = await self.client.search(
                index=index_name,
                body=search_body
            )
            
            # 转换结果
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                
                doc = ElasticsearchDocument(
                    id=hit["_id"],
                    content=source.get("content", ""),
                    metadata=source.get("metadata", {}),
                    title=source.get("title", "")
                )
                
                highlights = hit.get("highlight", {})
                
                result = ElasticsearchSearchResult(
                    document=doc,
                    score=hit["_score"],
                    highlights=highlights
                )
                results.append(result)
            
            logger.debug(f"BM25搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"BM25搜索失败: {e}")
            return []
    
    async def multi_match_search(
        self,
        query: str,
        fields: List[str],
        index_name: Optional[str] = None,
        size: int = 10,
        fuzziness: str = "AUTO"
    ) -> List[ElasticsearchSearchResult]:
        """
        多字段匹配搜索
        
        Args:
            query: 查询文本
            fields: 搜索字段列表
            index_name: 索引名称
            size: 返回结果数量
            fuzziness: 模糊匹配程度
            
        Returns:
            搜索结果列表
        """
        index_name = index_name or self.default_index
        
        try:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": fields,
                        "type": "best_fields",
                        "fuzziness": fuzziness,
                        "operator": "or"
                    }
                },
                "size": size
            }
            
            response = await self.client.search(
                index=index_name,
                body=search_body
            )
            
            # 转换结果
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                
                doc = ElasticsearchDocument(
                    id=hit["_id"],
                    content=source.get("content", ""),
                    metadata=source.get("metadata", {}),
                    title=source.get("title", "")
                )
                
                result = ElasticsearchSearchResult(
                    document=doc,
                    score=hit["_score"]
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"多字段搜索失败: {e}")
            return []
    
    async def delete_documents(
        self,
        document_ids: List[str],
        index_name: Optional[str] = None
    ) -> bool:
        """
        删除文档
        
        Args:
            document_ids: 文档ID列表
            index_name: 索引名称
            
        Returns:
            是否删除成功
        """
        index_name = index_name or self.default_index
        
        try:
            # 构建批量删除操作
            body = []
            for doc_id in document_ids:
                body.append({
                    "delete": {
                        "_index": index_name,
                        "_id": doc_id
                    }
                })
            
            # 执行批量删除
            response = await self.client.bulk(body=body)
            
            # 检查错误
            if response.get("errors"):
                errors = [
                    item for item in response["items"]
                    if "error" in item.get("delete", {})
                ]
                if errors:
                    logger.warning(f"批量删除部分失败: {errors[:3]}")
            
            logger.info(f"成功删除 {len(document_ids)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def update_document(
        self,
        document: ElasticsearchDocument,
        index_name: Optional[str] = None
    ) -> bool:
        """
        更新文档
        
        Args:
            document: 文档对象
            index_name: 索引名称
            
        Returns:
            是否更新成功
        """
        index_name = index_name or self.default_index
        
        try:
            doc_body = {
                "content": document.content,
                "title": document.title,
                "created_at": document.created_at.isoformat(),
                "metadata": document.metadata
            }
            
            await self.client.index(
                index=index_name,
                id=document.id,
                body=doc_body
            )
            
            logger.debug(f"成功更新文档: {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    async def get_index_stats(
        self,
        index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取索引统计信息
        
        Args:
            index_name: 索引名称
            
        Returns:
            索引统计信息
        """
        index_name = index_name or self.default_index
        
        try:
            stats = await self.client.indices.stats(index=index_name)
            index_stats = stats["indices"][index_name]
            
            return {
                "name": index_name,
                "docs_count": index_stats["total"]["docs"]["count"],
                "docs_deleted": index_stats["total"]["docs"]["deleted"],
                "store_size": index_stats["total"]["store"]["size_in_bytes"],
                "segments_count": index_stats["total"]["segments"]["count"]
            }
            
        except Exception as e:
            logger.error(f"获取索引统计失败: {e}")
            return {}
    
    async def list_indices(self) -> List[str]:
        """列出所有索引"""
        try:
            indices = await self.client.indices.get_alias()
            return list(indices.keys())
        except Exception as e:
            logger.error(f"列出索引失败: {e}")
            return []
    
    async def delete_index(self, index_name: str) -> bool:
        """删除索引"""
        try:
            await self.client.indices.delete(index=index_name)
            
            if index_name in self.indices:
                del self.indices[index_name]
            
            logger.info(f"成功删除索引: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除索引失败: {e}")
            return False
    
    async def close(self) -> None:
        """关闭连接"""
        if self.client:
            try:
                await self.client.close()
                logger.info("Elasticsearch连接已关闭")
            except Exception as e:
                logger.error(f"关闭Elasticsearch连接失败: {e}")


# 全局Elasticsearch服务实例
elasticsearch_service = ElasticsearchService()