"""
向量数据库服务 - 基于Qdrant
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import uuid
from datetime import datetime
import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance, VectorParams, CreateCollection, PointStruct,
    Filter, FieldCondition, MatchValue, SearchRequest,
    UpdateCollection, OptimizersConfigDiff, HnswConfigDiff
)
from qdrant_client.http.exceptions import UnexpectedResponse

from src.core.config import settings
from src.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class VectorDocument:
    """向量文档类"""
    
    def __init__(
        self,
        id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[np.ndarray] = None
    ):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.embedding = embedding
        self.created_at = datetime.utcnow()


class VectorSearchResult:
    """向量搜索结果类"""
    
    def __init__(
        self,
        document: VectorDocument,
        score: float,
        distance: float
    ):
        self.document = document
        self.score = score
        self.distance = distance


class VectorService:
    """
    向量数据库服务类
    
    基于Qdrant实现向量存储和检索功能
    """
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collections: Dict[str, Dict[str, Any]] = {}
        self.default_collection = "hicrm_knowledge"
        self.embedding_dimension = 1024  # BGE-M3默认维度
        
    async def initialize(self) -> None:
        """初始化向量数据库连接"""
        try:
            logger.info("正在初始化Qdrant向量数据库连接...")
            
            # 创建Qdrant客户端
            if settings.QDRANT_API_KEY:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=30
                )
            else:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    timeout=30
                )
            
            # 测试连接
            await self._test_connection()
            
            # 获取嵌入维度
            await self._get_embedding_dimension()
            
            # 创建默认集合
            await self.create_collection(self.default_collection)
            
            logger.info("Qdrant向量数据库初始化完成")
            
        except Exception as e:
            logger.error(f"初始化Qdrant失败: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """测试数据库连接"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.get_collections)
            logger.info("Qdrant连接测试成功")
        except Exception as e:
            logger.error(f"Qdrant连接测试失败: {e}")
            raise
    
    async def _get_embedding_dimension(self) -> None:
        """获取嵌入向量维度"""
        try:
            # 使用嵌入服务获取维度
            sample_embedding = await embedding_service.encode("test")
            self.embedding_dimension = len(sample_embedding)
            logger.info(f"嵌入向量维度: {self.embedding_dimension}")
        except Exception as e:
            logger.warning(f"无法获取嵌入维度，使用默认值: {e}")
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: Optional[int] = None,
        distance: Distance = Distance.COSINE,
        recreate: bool = False
    ) -> bool:
        """
        创建向量集合
        
        Args:
            collection_name: 集合名称
            vector_size: 向量维度
            distance: 距离度量方式
            recreate: 是否重新创建
            
        Returns:
            是否创建成功
        """
        try:
            if vector_size is None:
                vector_size = self.embedding_dimension
            
            loop = asyncio.get_event_loop()
            
            # 检查集合是否存在
            collections = await loop.run_in_executor(None, self.client.get_collections)
            collection_exists = any(
                col.name == collection_name for col in collections.collections
            )
            
            if collection_exists:
                if recreate:
                    logger.info(f"删除现有集合: {collection_name}")
                    await loop.run_in_executor(
                        None, self.client.delete_collection, collection_name
                    )
                else:
                    logger.info(f"集合已存在: {collection_name}")
                    self.collections[collection_name] = {
                        "vector_size": vector_size,
                        "distance": distance
                    }
                    return True
            
            # 创建集合
            logger.info(f"创建向量集合: {collection_name}, 维度: {vector_size}")
            
            await loop.run_in_executor(
                None,
                self.client.create_collection,
                collection_name,
                VectorParams(size=vector_size, distance=distance),
                # 优化配置
                OptimizersConfigDiff(
                    default_segment_number=2,
                    max_segment_size=None,
                    memmap_threshold=None,
                    indexing_threshold=20000,
                    flush_interval_sec=5,
                    max_optimization_threads=None
                ),
                HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                    full_scan_threshold=10000,
                    max_indexing_threads=0,
                    on_disk=None,
                    payload_m=None
                )
            )
            
            self.collections[collection_name] = {
                "vector_size": vector_size,
                "distance": distance
            }
            
            logger.info(f"集合创建成功: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False
    
    async def add_documents(
        self,
        documents: List[VectorDocument],
        collection_name: Optional[str] = None,
        batch_size: int = 100
    ) -> bool:
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表
            collection_name: 集合名称
            batch_size: 批处理大小
            
        Returns:
            是否添加成功
        """
        if not documents:
            return True
        
        collection_name = collection_name or self.default_collection
        
        try:
            # 确保集合存在
            if collection_name not in self.collections:
                await self.create_collection(collection_name)
            
            # 生成嵌入向量
            texts = [doc.content for doc in documents]
            embeddings = await embedding_service.encode(texts)
            
            # 批量处理
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                
                points = []
                for doc, embedding in zip(batch_docs, batch_embeddings):
                    # 准备元数据
                    payload = {
                        "content": doc.content,
                        "created_at": doc.created_at.isoformat(),
                        **doc.metadata
                    }
                    
                    point = PointStruct(
                        id=doc.id,
                        vector=embedding.tolist(),
                        payload=payload
                    )
                    points.append(point)
                
                # 插入点
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.client.upsert,
                    collection_name,
                    points
                )
                
                logger.debug(f"批量插入 {len(points)} 个文档到集合 {collection_name}")
            
            logger.info(f"成功添加 {len(documents)} 个文档到集合 {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    async def search(
        self,
        query: str,
        collection_name: Optional[str] = None,
        limit: int = 10,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        向量搜索
        
        Args:
            query: 查询文本
            collection_name: 集合名称
            limit: 返回结果数量
            score_threshold: 分数阈值
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        collection_name = collection_name or self.default_collection
        
        try:
            # 生成查询向量
            query_embedding = await embedding_service.encode(query)
            
            # 构建过滤器
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter(filters)
            
            # 执行搜索
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                self.client.search,
                collection_name,
                query_embedding.tolist(),
                filter_conditions,
                limit,
                score_threshold
            )
            
            # 转换结果
            results = []
            for point in search_result:
                doc = VectorDocument(
                    id=str(point.id),
                    content=point.payload.get("content", ""),
                    metadata={
                        k: v for k, v in point.payload.items()
                        if k not in ["content", "created_at"]
                    }
                )
                
                result = VectorSearchResult(
                    document=doc,
                    score=point.score,
                    distance=1.0 - point.score  # 转换为距离
                )
                results.append(result)
            
            logger.debug(f"向量搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def search_by_vector(
        self,
        vector: np.ndarray,
        collection_name: Optional[str] = None,
        limit: int = 10,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        通过向量搜索
        
        Args:
            vector: 查询向量
            collection_name: 集合名称
            limit: 返回结果数量
            score_threshold: 分数阈值
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        collection_name = collection_name or self.default_collection
        
        try:
            # 构建过滤器
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter(filters)
            
            # 执行搜索
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                self.client.search,
                collection_name,
                vector.tolist(),
                filter_conditions,
                limit,
                score_threshold
            )
            
            # 转换结果
            results = []
            for point in search_result:
                doc = VectorDocument(
                    id=str(point.id),
                    content=point.payload.get("content", ""),
                    metadata={
                        k: v for k, v in point.payload.items()
                        if k not in ["content", "created_at"]
                    }
                )
                
                result = VectorSearchResult(
                    document=doc,
                    score=point.score,
                    distance=1.0 - point.score
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """构建Qdrant过滤器"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, (str, int, float, bool)):
                condition = FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
                conditions.append(condition)
        
        return Filter(must=conditions) if conditions else None
    
    async def delete_documents(
        self,
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> bool:
        """
        删除文档
        
        Args:
            document_ids: 文档ID列表
            collection_name: 集合名称
            
        Returns:
            是否删除成功
        """
        collection_name = collection_name or self.default_collection
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.delete,
                collection_name,
                document_ids
            )
            
            logger.info(f"成功删除 {len(document_ids)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def update_document(
        self,
        document: VectorDocument,
        collection_name: Optional[str] = None
    ) -> bool:
        """
        更新文档
        
        Args:
            document: 文档对象
            collection_name: 集合名称
            
        Returns:
            是否更新成功
        """
        collection_name = collection_name or self.default_collection
        
        try:
            # 生成嵌入向量
            embedding = await embedding_service.encode(document.content)
            
            # 准备元数据
            payload = {
                "content": document.content,
                "created_at": document.created_at.isoformat(),
                **document.metadata
            }
            
            point = PointStruct(
                id=document.id,
                vector=embedding.tolist(),
                payload=payload
            )
            
            # 更新点
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.upsert,
                collection_name,
                [point]
            )
            
            logger.debug(f"成功更新文档: {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    async def get_collection_info(
        self,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取集合信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            集合信息
        """
        collection_name = collection_name or self.default_collection
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self.client.get_collection,
                collection_name
            )
            
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance.value
                },
                "status": info.status.value
            }
            
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {}
    
    async def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            loop = asyncio.get_event_loop()
            collections = await loop.run_in_executor(None, self.client.get_collections)
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.delete_collection,
                collection_name
            )
            
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            logger.info(f"成功删除集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取向量数据库统计信息"""
        try:
            collections = await self.list_collections()
            stats = {
                "total_collections": len(collections),
                "collections": {}
            }
            
            for collection_name in collections:
                info = await self.get_collection_info(collection_name)
                stats["collections"][collection_name] = info
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    async def close(self) -> None:
        """关闭连接"""
        if self.client:
            try:
                # Qdrant客户端会自动处理连接关闭
                self.client = None
                logger.info("Qdrant连接已关闭")
            except Exception as e:
                logger.error(f"关闭Qdrant连接失败: {e}")


# 全局向量服务实例
vector_service = VectorService()