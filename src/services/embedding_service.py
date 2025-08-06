"""
嵌入服务 - 基于BGE-M3多语言嵌入模型
"""

import asyncio
import logging
import sys
from typing import List, Dict, Any, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import warnings

# Suppress all FutureWarnings from transformers and other libraries to prevent test failures
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="`encoder_attention_mask` is deprecated")

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    嵌入服务类
    
    使用BGE-M3多语言嵌入模型，支持中英文文本的向量化
    """
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.reranker_model: Optional[SentenceTransformer] = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._model_loaded = False
        self._reranker_loaded = False
        self.cache: Dict[str, np.ndarray] = {}
        self.max_cache_size = 1000
        
    async def initialize(self) -> None:
        """初始化嵌入模型"""
        try:
            logger.info("正在初始化BGE-M3嵌入模型...")
            
            # 在线程池中加载模型以避免阻塞
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                self._load_embedding_model
            )
            self._model_loaded = True
            
            logger.info(f"BGE-M3嵌入模型初始化完成，设备: {settings.BGE_DEVICE}")
            
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {e}")
            raise
    
    async def initialize_reranker(self) -> None:
        """初始化重排序模型"""
        try:
            logger.info("正在初始化BGE重排序模型...")
            
            loop = asyncio.get_event_loop()
            self.reranker_model = await loop.run_in_executor(
                self.executor,
                self._load_reranker_model
            )
            self._reranker_loaded = True
            
            logger.info("BGE重排序模型初始化完成")
            
        except Exception as e:
            logger.error(f"初始化重排序模型失败: {e}")
            raise
    
    def _load_embedding_model(self) -> SentenceTransformer:
        """加载嵌入模型"""
        try:
            # Suppress specific deprecation warnings from transformers
            warnings.filterwarnings("ignore", message="`encoder_attention_mask` is deprecated", category=FutureWarning)
            model = SentenceTransformer(
                settings.BGE_MODEL_NAME,
                device=settings.BGE_DEVICE
            )
            
            # 设置模型为评估模式
            model.eval()
            
            return model
            
        except Exception as e:
            logger.error(f"加载BGE-M3模型失败: {e}")
            raise
    
    def _load_reranker_model(self) -> SentenceTransformer:
        """加载重排序模型"""
        try:
            # Suppress specific deprecation warnings from transformers
            warnings.filterwarnings("ignore", message="`encoder_attention_mask` is deprecated", category=FutureWarning)
            model = SentenceTransformer(
                settings.BGE_RERANKER_MODEL,
                device=settings.BGE_DEVICE
            )
            
            model.eval()
            return model
            
        except Exception as e:
            logger.error(f"加载BGE重排序模型失败: {e}")
            raise
    
    def _get_cache_key(self, text: str, normalize: bool = True) -> str:
        """生成缓存键"""
        cache_data = {
            "text": text,
            "normalize": normalize,
            "model": settings.BGE_MODEL_NAME
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def _manage_cache(self) -> None:
        """管理缓存大小"""
        if len(self.cache) > self.max_cache_size:
            # 删除最旧的一半缓存项
            items_to_remove = len(self.cache) - self.max_cache_size // 2
            keys_to_remove = list(self.cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self.cache[key]
    
    async def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        编码文本为向量
        
        Args:
            texts: 单个文本或文本列表
            normalize: 是否归一化向量
            batch_size: 批处理大小
            
        Returns:
            向量或向量列表
        """
        if not self._model_loaded:
            await self.initialize()
        
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        # 检查缓存
        cached_results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text, normalize)
            if cache_key in self.cache:
                cached_results.append((i, self.cache[cache_key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 处理未缓存的文本
        if uncached_texts:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self._encode_batch,
                uncached_texts,
                normalize,
                batch_size
            )
            
            # 更新缓存
            for text, embedding in zip(uncached_texts, embeddings):
                cache_key = self._get_cache_key(text, normalize)
                self.cache[cache_key] = embedding
            
            self._manage_cache()
        else:
            embeddings = []
        
        # 合并结果
        results = [None] * len(texts)
        
        # 填入缓存结果
        for idx, embedding in cached_results:
            results[idx] = embedding
        
        # 填入新计算结果
        for i, idx in enumerate(uncached_indices):
            results[idx] = embeddings[i]
        
        if is_single:
            return results[0]
        
        return results
    
    def _encode_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[np.ndarray]:
        """批量编码文本"""
        if not self.model:
            logger.error("Embedding model is not available for encoding.")
            raise RuntimeError("Embedding model not initialized")

        # 预处理文本
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        try:
            # 批量编码
            embeddings = self.model.encode(
                processed_texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # 确保结果是列表
            if isinstance(embeddings, np.ndarray) and len(embeddings.shape) == 2:
                embeddings = [embeddings[i] for i in range(embeddings.shape[0])]

            # 确保每个向量的数据类型为 float32
            embeddings = [emb.astype(np.float32) for emb in embeddings]
            
            return embeddings
                
        except RuntimeError as e:
            logger.error(f"批量编码运行时错误: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 清理文本
        text = text.strip()
        
        # 限制文本长度（BGE-M3最大支持8192 tokens）
        if len(text) > 6000:  # 保守估计
            text = text[:6000] + "..."
        
        return text
    
    async def compute_similarity(
        self,
        text1: str,
        text2: str,
        normalize: bool = True
    ) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            normalize: 是否归一化向量
            
        Returns:
            相似度分数 (0-1)
        """
        embeddings = await self.encode([text1, text2], normalize=normalize)
        
        # 计算余弦相似度
        similarity = np.dot(embeddings[0], embeddings[1])
        
        # 如果没有归一化，手动计算余弦相似度
        if not normalize:
            norm1 = np.linalg.norm(embeddings[0])
            norm2 = np.linalg.norm(embeddings[1])
            similarity = similarity / (norm1 * norm2)
        
        # 确保结果在[0, 1]范围内
        similarity = max(0.0, min(1.0, (similarity + 1) / 2))
        
        return float(similarity)
    
    async def compute_similarities(
        self,
        query: str,
        texts: List[str],
        normalize: bool = True
    ) -> List[float]:
        """
        计算查询文本与多个文本的相似度
        
        Args:
            query: 查询文本
            texts: 文本列表
            normalize: 是否归一化向量
            
        Returns:
            相似度分数列表
        """
        all_texts = [query] + texts
        embeddings = await self.encode(all_texts, normalize=normalize)
        
        query_embedding = embeddings[0]
        text_embeddings = embeddings[1:]
        
        similarities = []
        for text_embedding in text_embeddings:
            similarity = np.dot(query_embedding, text_embedding)
            
            if not normalize:
                norm_query = np.linalg.norm(query_embedding)
                norm_text = np.linalg.norm(text_embedding)
                similarity = similarity / (norm_query * norm_text)
            
            # 转换到[0, 1]范围
            similarity = max(0.0, min(1.0, (similarity + 1) / 2))
            similarities.append(float(similarity))
        
        return similarities
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[tuple]:
        """
        使用重排序模型对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个结果
            
        Returns:
            (文档索引, 重排序分数) 的列表，按分数降序排列
        """
        if not self._reranker_loaded:
            await self.initialize_reranker()
        
        if not documents:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                self.executor,
                self._rerank_batch,
                query,
                documents
            )
            
            # 创建(索引, 分数)对并排序
            indexed_scores = [(i, score) for i, score in enumerate(scores)]
            indexed_scores.sort(key=lambda x: x[1], reverse=True)
            
            if top_k:
                indexed_scores = indexed_scores[:top_k]
            
            return indexed_scores
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            # 如果重排序失败，返回原始顺序
            return [(i, 0.5) for i in range(len(documents))]
    
    def _rerank_batch(self, query: str, documents: List[str]) -> List[float]:
        """批量重排序"""
        try:
            # 构建查询-文档对
            pairs = [[query, doc] for doc in documents]
            
            # 计算重排序分数
            scores = self.reranker_model.predict(pairs)
            
            # 确保分数为浮点数列表
            if isinstance(scores, np.ndarray):
                scores = scores.tolist()
            
            return [float(score) for score in scores]
            
        except Exception as e:
            logger.error(f"批量重排序失败: {e}")
            # 返回默认分数
            return [0.5] * len(documents)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            "embedding_model": settings.BGE_MODEL_NAME,
            "reranker_model": settings.BGE_RERANKER_MODEL,
            "device": settings.BGE_DEVICE,
            "embedding_model_loaded": self._model_loaded,
            "reranker_model_loaded": self._reranker_loaded,
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size
        }
        
        if self._model_loaded and self.model:
            try:
                # 获取嵌入维度
                sample_embedding = await self.encode("test", normalize=False)
                info["embedding_dimension"] = len(sample_embedding)
            except Exception as e:
                logger.warning(f"无法获取嵌入维度: {e}")
                info["embedding_dimension"] = "unknown"
        
        return info
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("嵌入缓存已清空")
    
    async def close(self) -> None:
        """关闭服务"""
        self.clear_cache()
        self.executor.shutdown(wait=True)
        logger.info("嵌入服务已关闭")


# 全局嵌入服务实例
embedding_service = EmbeddingService()
