"""
混合检索服务 - 结合向量搜索和BM25文本搜索
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from src.services.vector_service import vector_service, VectorDocument, VectorSearchResult
from src.services.elasticsearch_service import (
    elasticsearch_service, ElasticsearchDocument, ElasticsearchSearchResult
)
from src.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """搜索模式"""
    VECTOR_ONLY = "vector_only"
    BM25_ONLY = "bm25_only"
    HYBRID = "hybrid"
    RERANK = "rerank"


@dataclass
class HybridSearchResult:
    """混合搜索结果"""
    id: str
    content: str
    title: str
    metadata: Dict[str, Any]
    vector_score: float
    bm25_score: float
    hybrid_score: float
    rerank_score: Optional[float] = None
    highlights: Optional[Dict[str, List[str]]] = None


class HybridSearchService:
    """
    混合检索服务类
    
    结合向量搜索(语义相似度)和BM25搜索(关键词匹配)，
    提供更准确和全面的搜索结果
    """
    
    def __init__(self):
        self.vector_weight = 0.6  # 向量搜索权重
        self.bm25_weight = 0.4   # BM25搜索权重
        self.min_vector_score = 0.1
        self.min_bm25_score = 0.1
        
    async def initialize(self) -> None:
        """初始化混合搜索服务"""
        try:
            logger.info("正在初始化混合检索服务...")
            
            # 初始化各个服务
            await embedding_service.initialize()
            await vector_service.initialize()
            await elasticsearch_service.initialize()
            
            logger.info("混合检索服务初始化完成")
            
        except Exception as e:
            logger.error(f"初始化混合检索服务失败: {e}")
            raise
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: Optional[str] = None,
        index_name: Optional[str] = None
    ) -> bool:
        """
        添加文档到混合搜索系统
        
        Args:
            documents: 文档列表，每个文档包含id, content, metadata等字段
            collection_name: 向量数据库集合名称
            index_name: Elasticsearch索引名称
            
        Returns:
            是否添加成功
        """
        try:
            if not documents:
                return True
            
            # 转换为向量文档格式
            vector_docs = []
            es_docs = []
            
            for doc in documents:
                doc_id = doc.get("id")
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                title = doc.get("title", "")
                
                if not doc_id or not content:
                    logger.warning(f"跳过无效文档: {doc}")
                    continue
                
                # 向量文档
                vector_doc = VectorDocument(
                    id=doc_id,
                    content=content,
                    metadata={**metadata, "title": title}
                )
                vector_docs.append(vector_doc)
                
                # Elasticsearch文档
                es_doc = ElasticsearchDocument(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    title=title
                )
                es_docs.append(es_doc)
            
            # 并行添加到两个系统
            vector_task = vector_service.add_documents(vector_docs, collection_name)
            es_task = elasticsearch_service.add_documents(es_docs, index_name)
            
            vector_success, es_success = await asyncio.gather(
                vector_task, es_task, return_exceptions=True
            )
            
            # 检查结果
            if isinstance(vector_success, Exception):
                logger.error(f"向量数据库添加失败: {vector_success}")
                vector_success = False
            
            if isinstance(es_success, Exception):
                logger.error(f"Elasticsearch添加失败: {es_success}")
                es_success = False
            
            success = vector_success and es_success
            
            if success:
                logger.info(f"成功添加 {len(documents)} 个文档到混合搜索系统")
            else:
                logger.warning("部分文档添加失败")
            
            return success
            
        except Exception as e:
            logger.error(f"添加文档到混合搜索系统失败: {e}")
            return False
    
    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        limit: int = 10,
        vector_limit: int = 20,
        bm25_limit: int = 20,
        collection_name: Optional[str] = None,
        index_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        vector_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None
    ) -> List[HybridSearchResult]:
        """
        混合搜索
        
        Args:
            query: 查询文本
            mode: 搜索模式
            limit: 最终返回结果数量
            vector_limit: 向量搜索结果数量
            bm25_limit: BM25搜索结果数量
            collection_name: 向量数据库集合名称
            index_name: Elasticsearch索引名称
            filters: 过滤条件
            rerank: 是否使用重排序
            vector_weight: 向量搜索权重
            bm25_weight: BM25搜索权重
            
        Returns:
            混合搜索结果列表
        """
        try:
            # 使用自定义权重或默认权重
            v_weight = vector_weight or self.vector_weight
            b_weight = bm25_weight or self.bm25_weight
            
            # 归一化权重
            total_weight = v_weight + b_weight
            if total_weight > 0:
                v_weight = v_weight / total_weight
                b_weight = b_weight / total_weight
            
            # 根据模式执行搜索
            if mode == SearchMode.VECTOR_ONLY:
                return await self._vector_only_search(
                    query, limit, collection_name, filters
                )
            elif mode == SearchMode.BM25_ONLY:
                return await self._bm25_only_search(
                    query, limit, index_name, filters
                )
            else:
                return await self._hybrid_search(
                    query, limit, vector_limit, bm25_limit,
                    collection_name, index_name, filters,
                    v_weight, b_weight, rerank
                )
                
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []
    
    async def _vector_only_search(
        self,
        query: str,
        limit: int,
        collection_name: Optional[str],
        filters: Optional[Dict[str, Any]]
    ) -> List[HybridSearchResult]:
        """仅向量搜索"""
        try:
            vector_results = await vector_service.search(
                query=query,
                collection_name=collection_name,
                limit=limit,
                filters=filters
            )
            
            results = []
            for result in vector_results:
                hybrid_result = HybridSearchResult(
                    id=result.document.id,
                    content=result.document.content,
                    title=result.document.metadata.get("title", ""),
                    metadata=result.document.metadata,
                    vector_score=result.score,
                    bm25_score=0.0,
                    hybrid_score=result.score
                )
                results.append(hybrid_result)
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def _bm25_only_search(
        self,
        query: str,
        limit: int,
        index_name: Optional[str],
        filters: Optional[Dict[str, Any]]
    ) -> List[HybridSearchResult]:
        """仅BM25搜索"""
        try:
            bm25_results = await elasticsearch_service.search(
                query=query,
                index_name=index_name,
                size=limit,
                filters=filters
            )
            
            results = []
            for result in bm25_results:
                hybrid_result = HybridSearchResult(
                    id=result.document.id,
                    content=result.document.content,
                    title=result.document.title,
                    metadata=result.document.metadata,
                    vector_score=0.0,
                    bm25_score=result.score,
                    hybrid_score=result.score,
                    highlights=result.highlights
                )
                results.append(hybrid_result)
            
            return results
            
        except Exception as e:
            logger.error(f"BM25搜索失败: {e}")
            return []
    
    async def _hybrid_search(
        self,
        query: str,
        limit: int,
        vector_limit: int,
        bm25_limit: int,
        collection_name: Optional[str],
        index_name: Optional[str],
        filters: Optional[Dict[str, Any]],
        vector_weight: float,
        bm25_weight: float,
        rerank: bool
    ) -> List[HybridSearchResult]:
        """混合搜索实现"""
        try:
            # 并行执行向量搜索和BM25搜索
            vector_task = vector_service.search(
                query=query,
                collection_name=collection_name,
                limit=vector_limit,
                filters=filters
            )
            
            bm25_task = elasticsearch_service.search(
                query=query,
                index_name=index_name,
                size=bm25_limit,
                filters=filters
            )
            
            vector_results, bm25_results = await asyncio.gather(
                vector_task, bm25_task, return_exceptions=True
            )
            
            # 处理异常
            if isinstance(vector_results, Exception):
                logger.error(f"向量搜索失败: {vector_results}")
                vector_results = []
            
            if isinstance(bm25_results, Exception):
                logger.error(f"BM25搜索失败: {bm25_results}")
                bm25_results = []
            
            # 合并结果
            merged_results = self._merge_results(
                vector_results, bm25_results, vector_weight, bm25_weight
            )
            
            # 重排序
            if rerank and merged_results:
                merged_results = await self._rerank_results(query, merged_results)
            
            # 返回前N个结果
            return merged_results[:limit]
            
        except Exception as e:
            logger.error(f"混合搜索实现失败: {e}")
            return []
    
    def _merge_results(
        self,
        vector_results: List[VectorSearchResult],
        bm25_results: List[ElasticsearchSearchResult],
        vector_weight: float,
        bm25_weight: float
    ) -> List[HybridSearchResult]:
        """合并搜索结果"""
        try:
            # 创建结果字典
            results_dict = {}
            
            # 归一化向量搜索分数
            if vector_results:
                max_vector_score = max(r.score for r in vector_results)
                min_vector_score = min(r.score for r in vector_results)
                vector_range = max_vector_score - min_vector_score
                
                for result in vector_results:
                    if vector_range > 0:
                        normalized_score = (result.score - min_vector_score) / vector_range
                    else:
                        normalized_score = 1.0
                    
                    results_dict[result.document.id] = {
                        "id": result.document.id,
                        "content": result.document.content,
                        "title": result.document.metadata.get("title", ""),
                        "metadata": result.document.metadata,
                        "vector_score": normalized_score,
                        "bm25_score": 0.0,
                        "highlights": {}
                    }
            
            # 归一化BM25搜索分数
            if bm25_results:
                max_bm25_score = max(r.score for r in bm25_results)
                min_bm25_score = min(r.score for r in bm25_results)
                bm25_range = max_bm25_score - min_bm25_score
                
                for result in bm25_results:
                    if bm25_range > 0:
                        normalized_score = (result.score - min_bm25_score) / bm25_range
                    else:
                        normalized_score = 1.0
                    
                    doc_id = result.document.id
                    if doc_id in results_dict:
                        # 更新现有结果
                        results_dict[doc_id]["bm25_score"] = normalized_score
                        results_dict[doc_id]["highlights"] = result.highlights
                    else:
                        # 创建新结果
                        results_dict[doc_id] = {
                            "id": doc_id,
                            "content": result.document.content,
                            "title": result.document.title,
                            "metadata": result.document.metadata,
                            "vector_score": 0.0,
                            "bm25_score": normalized_score,
                            "highlights": result.highlights
                        }
            
            # 计算混合分数并创建结果对象
            hybrid_results = []
            for doc_data in results_dict.values():
                # 计算混合分数
                hybrid_score = (
                    doc_data["vector_score"] * vector_weight +
                    doc_data["bm25_score"] * bm25_weight
                )
                
                # 过滤低分结果
                if (doc_data["vector_score"] >= self.min_vector_score or 
                    doc_data["bm25_score"] >= self.min_bm25_score):
                    
                    result = HybridSearchResult(
                        id=doc_data["id"],
                        content=doc_data["content"],
                        title=doc_data["title"],
                        metadata=doc_data["metadata"],
                        vector_score=doc_data["vector_score"],
                        bm25_score=doc_data["bm25_score"],
                        hybrid_score=hybrid_score,
                        highlights=doc_data["highlights"]
                    )
                    hybrid_results.append(result)
            
            # 按混合分数排序
            hybrid_results.sort(key=lambda x: x.hybrid_score, reverse=True)
            
            return hybrid_results
            
        except Exception as e:
            logger.error(f"合并搜索结果失败: {e}")
            return []
    
    async def _rerank_results(
        self,
        query: str,
        results: List[HybridSearchResult]
    ) -> List[HybridSearchResult]:
        """重排序结果"""
        try:
            if not results:
                return results
            
            # 提取文档内容
            documents = [result.content for result in results]
            
            # 使用重排序模型
            rerank_scores = await embedding_service.rerank(query, documents)
            
            # 更新重排序分数
            for i, (idx, score) in enumerate(rerank_scores):
                if idx < len(results):
                    results[idx].rerank_score = score
            
            # 按重排序分数排序
            results.sort(key=lambda x: x.rerank_score or 0, reverse=True)
            
            logger.debug(f"重排序完成，处理 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            # 如果重排序失败，返回原始结果
            return results
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        collection_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[HybridSearchResult]:
        """
        语义搜索 - 基于语义相似度的搜索
        
        Args:
            query: 查询文本
            limit: 返回结果数量
            similarity_threshold: 相似度阈值
            collection_name: 向量数据库集合名称
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            # 计算查询向量
            query_embedding = await embedding_service.encode(query)
            
            # 向量搜索
            vector_results = await vector_service.search_by_vector(
                vector=query_embedding,
                collection_name=collection_name,
                limit=limit * 2,  # 获取更多结果用于过滤
                filters=filters
            )
            
            # 过滤低相似度结果
            filtered_results = []
            for result in vector_results:
                if result.score >= similarity_threshold:
                    hybrid_result = HybridSearchResult(
                        id=result.document.id,
                        content=result.document.content,
                        title=result.document.metadata.get("title", ""),
                        metadata=result.document.metadata,
                        vector_score=result.score,
                        bm25_score=0.0,
                        hybrid_score=result.score
                    )
                    filtered_results.append(hybrid_result)
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    async def delete_documents(
        self,
        document_ids: List[str],
        collection_name: Optional[str] = None,
        index_name: Optional[str] = None
    ) -> bool:
        """
        从混合搜索系统删除文档
        
        Args:
            document_ids: 文档ID列表
            collection_name: 向量数据库集合名称
            index_name: Elasticsearch索引名称
            
        Returns:
            是否删除成功
        """
        try:
            # 并行删除
            vector_task = vector_service.delete_documents(document_ids, collection_name)
            es_task = elasticsearch_service.delete_documents(document_ids, index_name)
            
            vector_success, es_success = await asyncio.gather(
                vector_task, es_task, return_exceptions=True
            )
            
            # 检查结果
            if isinstance(vector_success, Exception):
                logger.error(f"向量数据库删除失败: {vector_success}")
                vector_success = False
            
            if isinstance(es_success, Exception):
                logger.error(f"Elasticsearch删除失败: {es_success}")
                es_success = False
            
            success = vector_success and es_success
            
            if success:
                logger.info(f"成功从混合搜索系统删除 {len(document_ids)} 个文档")
            
            return success
            
        except Exception as e:
            logger.error(f"从混合搜索系统删除文档失败: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取混合搜索系统统计信息"""
        try:
            # 并行获取统计信息
            vector_stats_task = vector_service.get_stats()
            es_stats_task = elasticsearch_service.get_index_stats()
            
            vector_stats, es_stats = await asyncio.gather(
                vector_stats_task, es_stats_task, return_exceptions=True
            )
            
            # 处理异常
            if isinstance(vector_stats, Exception):
                logger.error(f"获取向量数据库统计失败: {vector_stats}")
                vector_stats = {}
            
            if isinstance(es_stats, Exception):
                logger.error(f"获取Elasticsearch统计失败: {es_stats}")
                es_stats = {}
            
            return {
                "vector_database": vector_stats,
                "elasticsearch": es_stats,
                "search_weights": {
                    "vector_weight": self.vector_weight,
                    "bm25_weight": self.bm25_weight
                }
            }
            
        except Exception as e:
            logger.error(f"获取混合搜索统计信息失败: {e}")
            return {}
    
    def set_search_weights(self, vector_weight: float, bm25_weight: float) -> None:
        """设置搜索权重"""
        total = vector_weight + bm25_weight
        if total > 0:
            self.vector_weight = vector_weight / total
            self.bm25_weight = bm25_weight / total
            logger.info(f"搜索权重已更新: 向量={self.vector_weight:.2f}, BM25={self.bm25_weight:.2f}")
    
    async def close(self) -> None:
        """关闭混合搜索服务"""
        try:
            await asyncio.gather(
                vector_service.close(),
                elasticsearch_service.close(),
                embedding_service.close(),
                return_exceptions=True
            )
            logger.info("混合搜索服务已关闭")
        except Exception as e:
            logger.error(f"关闭混合搜索服务失败: {e}")


# 全局混合搜索服务实例
hybrid_search_service = HybridSearchService()