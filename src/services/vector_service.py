"""
向量数据库服务 - 基于Qdrant
"""

import asyncio
import logging
import sys
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
            
            # 验证连接配置
            await self._validate_connection_config()
            
            # 创建Qdrant客户端配置
            use_grpc = getattr(settings, 'QDRANT_USE_GRPC', True)
            
            if use_grpc:
                # gRPC连接配置
                if ':' in settings.QDRANT_URL:
                    host, port = settings.QDRANT_URL.split(':')
                    port = int(port)
                else:
                    host = settings.QDRANT_URL
                    port = 6334
                
                client_config = {
                    "host": host,
                    "port": port,
                    "prefer_grpc": True,
                    "timeout": 30,
                    "check_compatibility": False
                }
            else:
                # HTTP连接配置（保留兼容性）
                client_config = {
                    "url": settings.QDRANT_URL if settings.QDRANT_URL.startswith('http') else f"http://{settings.QDRANT_URL}",
                    "timeout": 30,
                    "prefer_grpc": False,
                    "https": settings.QDRANT_URL.startswith('https'),
                    "verify": False if not settings.QDRANT_URL.startswith('https') else True,
                    "check_compatibility": False
                }
            
            # 处理API key配置
            if settings.QDRANT_API_KEY and settings.QDRANT_API_KEY.strip():
                # 检查是否为开发环境的默认值
                if settings.QDRANT_API_KEY == "hicrm" and settings.QDRANT_URL.startswith('http://'):
                    logger.warning("检测到开发环境配置：使用HTTP协议和默认API key")
                    logger.warning("为避免安全警告，建议:")
                    logger.warning("1. 在.env中设置 QDRANT_API_KEY= (空值)")
                    logger.warning("2. 或使用HTTPS: QDRANT_URL=https://localhost:6333")
                    
                    # 在开发环境中，如果用户明确想要跳过API key，可以设置为空
                    if settings.DEBUG:
                        logger.info("开发模式：跳过API key以避免安全警告")
                        self.client = QdrantClient(**client_config)
                    else:
                        client_config["api_key"] = settings.QDRANT_API_KEY
                        self.client = QdrantClient(**client_config)
                else:
                    client_config["api_key"] = settings.QDRANT_API_KEY
                    self.client = QdrantClient(**client_config)
            else:
                logger.info("未配置API key，使用无认证连接")
                self.client = QdrantClient(**client_config)
            
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
    
    async def _validate_connection_config(self) -> None:
        """验证连接配置"""
        try:
            use_grpc = getattr(settings, 'QDRANT_USE_GRPC', True)
            
            logger.info(f"Qdrant连接配置验证:")
            logger.info(f"  - URL: {settings.QDRANT_URL}")
            logger.info(f"  - 连接方式: {'gRPC' if use_grpc else 'HTTP'}")
            logger.info(f"  - API Key: {'已配置' if settings.QDRANT_API_KEY else '未配置'}")
            
            if use_grpc:
                # gRPC连接验证
                if ':' in settings.QDRANT_URL:
                    host, port = settings.QDRANT_URL.split(':')
                    port = int(port)
                    logger.info(f"  - gRPC主机: {host}")
                    logger.info(f"  - gRPC端口: {port}")
                    
                    if port == 6334:
                        logger.info("  - 使用标准gRPC端口 (6334)")
                    elif port == 6333:
                        logger.warning("  - 使用HTTP端口 (6333) 进行gRPC连接，请确认配置")
                    else:
                        logger.warning(f"  - 使用非标准端口 ({port})，请确认配置正确")
                else:
                    logger.info(f"  - gRPC主机: {settings.QDRANT_URL}")
                    logger.info(f"  - gRPC端口: 6334 (默认)")
            else:
                # HTTP连接验证（保留兼容性）
                import urllib.parse
                if settings.QDRANT_URL.startswith('http'):
                    parsed_url = urllib.parse.urlparse(settings.QDRANT_URL)
                    logger.info(f"  - HTTP协议: {parsed_url.scheme}")
                    logger.info(f"  - HTTP主机: {parsed_url.hostname}")
                    logger.info(f"  - HTTP端口: {parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)}")
                else:
                    logger.info(f"  - HTTP主机: {settings.QDRANT_URL}")
                    logger.info(f"  - HTTP端口: 6333 (默认)")
            
        except Exception as e:
            logger.warning(f"连接配置验证失败: {e}")
    
    async def _check_port_connectivity(self, host: str, port: int) -> bool:
        """检查端口连通性"""
        import socket
        import asyncio
        
        try:
            # 创建socket连接测试
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: sock.connect_ex((host, port))
            )
            
            sock.close()
            return result == 0
            
        except Exception as e:
            logger.debug(f"端口连通性检查失败: {e}")
            return False
    
    async def _test_connection(self) -> None:
        """测试数据库连接"""
        import urllib.parse
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.get_collections)
            logger.info("Qdrant连接测试成功")
            
        except UnexpectedResponse as e:
            parsed_url = urllib.parse.urlparse(settings.QDRANT_URL)
            host = parsed_url.hostname or 'localhost'
            port = parsed_url.port or 6333
            
            if e.status_code == 502:
                logger.error("Qdrant服务未运行或不可访问 (502 Bad Gateway)")
                
                # 检查端口连通性
                logger.info("正在检查端口连通性...")
                
                # 检查HTTP端口 (6333)
                http_available = await self._check_port_connectivity(host, 6333)
                logger.info(f"端口 6333 (HTTP): {'可用' if http_available else '不可用'}")
                
                # 检查gRPC端口 (6334)
                grpc_available = await self._check_port_connectivity(host, 6334)
                logger.info(f"端口 6334 (gRPC): {'可用' if grpc_available else '不可用'}")
                
                logger.error("请检查:")
                logger.error("1. Qdrant服务是否已启动:")
                logger.error("   - docker-compose up -d qdrant")
                logger.error("   - docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")
                logger.error(f"2. 服务地址是否正确: {settings.QDRANT_URL}")
                
                if port == 6334:
                    logger.error("3. 当前配置使用gRPC端口(6334)，但客户端设置为HTTP模式")
                    logger.error("   建议修改URL为: http://localhost:6333")
                elif not http_available and grpc_available:
                    logger.error("3. HTTP端口(6333)不可用，但gRPC端口(6334)可用")
                    logger.error("   请检查Qdrant服务配置")
                
                logger.error("4. 防火墙是否阻止了连接")
                logger.error("5. 检查服务状态: curl http://localhost:6333/collections")
                
            elif e.status_code == 404:
                logger.error("Qdrant API端点未找到 (404 Not Found)")
                logger.error("可能的原因:")
                logger.error("1. URL路径不正确")
                logger.error("2. Qdrant版本不兼容")
                logger.error("3. 服务未完全启动")
                
            elif e.status_code == 401 or e.status_code == 403:
                logger.error(f"Qdrant认证失败 (HTTP {e.status_code})")
                logger.error("请检查:")
                logger.error("1. API Key是否正确")
                logger.error("2. Qdrant服务是否启用了认证")
                
            else:
                logger.error(f"Qdrant连接失败 (HTTP {e.status_code}): {e}")
                
            raise
            
        except Exception as e:
            logger.error(f"Qdrant连接测试失败: {e}")
            
            # 尝试基本的连通性检查
            try:
                parsed_url = urllib.parse.urlparse(settings.QDRANT_URL)
                host = parsed_url.hostname or 'localhost'
                
                logger.info("正在进行基本连通性检查...")
                http_available = await self._check_port_connectivity(host, 6333)
                grpc_available = await self._check_port_connectivity(host, 6334)
                
                logger.info(f"端口 6333 (HTTP): {'可用' if http_available else '不可用'}")
                logger.info(f"端口 6334 (gRPC): {'可用' if grpc_available else '不可用'}")
                
                if not http_available and not grpc_available:
                    logger.error("Qdrant服务似乎未运行，请启动服务")
                elif not http_available and grpc_available:
                    logger.error("HTTP端口不可用，请检查Qdrant配置")
                    
            except Exception as check_error:
                logger.debug(f"连通性检查失败: {check_error}")
                
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
            
            def create_collection_sync():
                return self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                    # 优化配置
                    optimizers_config=OptimizersConfigDiff(
                        default_segment_number=2,
                        max_segment_size=None,
                        memmap_threshold=None,
                        indexing_threshold=20000,
                        flush_interval_sec=5,
                        max_optimization_threads=None
                    ),
                    hnsw_config=HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10000,
                        max_indexing_threads=0,
                        on_disk=None,
                        payload_m=None
                    )
                )
            
            await loop.run_in_executor(None, create_collection_sync)
            
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
            

            # 检查是否获取到有效的嵌入向量
            if not embeddings or any(e is None or e.size == 0 for e in embeddings):
                logger.error("嵌入服务返回空或无效的向量，无法添加文档")
                return False
                
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
                def upsert_sync():
                    return self.client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                
                await loop.run_in_executor(None, upsert_sync)
                
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
            
            # 检查是否获取到有效的嵌入向量
            if query_embedding is None or not hasattr(query_embedding, 'size') or query_embedding.size == 0:
                logger.error("嵌入服务返回空或无效的向量，无法执行搜索")
                return []
                
            # 构建过滤器
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter(filters)
            
            # 执行搜索
            loop = asyncio.get_event_loop()
            def search_sync():
                return self.client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding.tolist(),
                    query_filter=filter_conditions,
                    limit=limit,
                    score_threshold=score_threshold
                )
            
            search_result = await loop.run_in_executor(None, search_sync)
            
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
                
                distance = point.score
                if self.collections.get(collection_name, {}).get("distance") == Distance.COSINE:
                    distance = 1.0 - point.score

                result = VectorSearchResult(
                    document=doc,
                    score=point.score,
                    distance=distance
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
            # 检查向量是否有效
            if vector is None or vector.size == 0:
                logger.error("提供的向量为空，无法执行搜索")
                return []
                
            # 构建过滤器
            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter(filters)
            
            # 执行搜索
            loop = asyncio.get_event_loop()
            def search_by_vector_sync():
                return self.client.search(
                    collection_name=collection_name,
                    query_vector=vector.tolist(),
                    query_filter=filter_conditions,
                    limit=limit,
                    score_threshold=score_threshold
                )
            
            search_result = await loop.run_in_executor(None, search_by_vector_sync)
            
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
                
                distance = point.score
                if self.collections.get(collection_name, {}).get("distance") == Distance.COSINE:
                    distance = 1.0 - point.score
                
                result = VectorSearchResult(
                    document=doc,
                    score=point.score,
                    distance=distance
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def _build_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """构建Qdrant过滤器"""
        conditions = []

        for key, value in filters.items():
            try:
                # Qdrant的MatchValue支持str, bool
                if isinstance(value, (str, bool)):
                    condition = FieldCondition(key=key, match=MatchValue(value=value))
                    conditions.append(condition)
                elif isinstance(value, (int, float)):
                    # 对于整数和浮点数，使用范围查询进行精确匹配
                    condition = FieldCondition(
                        key=key,
                        range=models.Range(
                            gte=value,
                            lte=value
                        )
                    )
                    conditions.append(condition)
                else:
                    logger.warning(f"不支持的过滤类型: {type(value)} for key {key}")

            except Exception as e:
                logger.warning(f"无法为值创建过滤条件: {key}={value}, 错误: {e}")
                continue
        
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
            def delete_sync():
                return self.client.delete(
                    collection_name=collection_name,
                    points_selector=document_ids
                )
            
            await loop.run_in_executor(None, delete_sync)
            
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
            
            # 检查是否获取到有效的嵌入向量
            if embedding is None or not hasattr(embedding, 'size') or embedding.size == 0:
                logger.error("嵌入服务返回空或无效的向量，无法更新文档")
                return False
                
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
            def update_sync():
                return self.client.upsert(
                    collection_name=collection_name,
                    points=[point]
                )
            
            await loop.run_in_executor(None, update_sync)
            
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
            def get_collection_sync():
                return self.client.get_collection(collection_name)
            
            info = await loop.run_in_executor(None, get_collection_sync)
            
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
            def delete_collection_sync():
                return self.client.delete_collection(collection_name)
            
            await loop.run_in_executor(None, delete_collection_sync)
            
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
