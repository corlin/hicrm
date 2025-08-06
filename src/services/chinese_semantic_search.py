"""
中文语义搜索服务 - 专门针对中文文本的语义搜索优化
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass

from src.services.hybrid_search_service import hybrid_search_service, HybridSearchResult, SearchMode
from src.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


@dataclass
class ChineseSearchResult:
    """中文搜索结果"""
    id: str
    content: str
    title: str
    metadata: Dict[str, Any]
    semantic_score: float
    keyword_score: float
    combined_score: float
    highlights: Optional[Dict[str, List[str]]] = None
    chinese_features: Optional[Dict[str, Any]] = None


class ChineseSemanticSearchService:
    """
    中文语义搜索服务
    
    专门针对中文文本进行优化的语义搜索服务，包括：
    - 中文分词和语义理解
    - 中文同义词扩展
    - 中文语言特征提取
    - 中文相似度计算优化
    """
    
    def __init__(self):
        self.chinese_stopwords = self._load_chinese_stopwords()
        self.chinese_synonyms = self._load_chinese_synonyms()
        
    def _load_chinese_stopwords(self) -> set:
        """加载中文停用词"""
        # 常见中文停用词
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '就是', '还是', '把', '比', '或者', '虽然', '因为',
            '所以', '但是', '如果', '这样', '那样', '怎么', '什么', '哪里', '为什么',
            '怎样', '多少', '第一', '可以', '已经', '现在', '需要', '应该', '能够',
            '通过', '进行', '实现', '提供', '包括', '具有', '作为', '由于', '关于'
        }
        return stopwords
    
    def _load_chinese_synonyms(self) -> Dict[str, List[str]]:
        """加载中文同义词词典"""
        # 简化的同义词词典，实际应用中可以使用更完整的词典
        synonyms = {
            '人工智能': ['AI', '机器智能', '智能系统', '人工智慧'],
            '机器学习': ['ML', '机器学习算法', '自动学习', '机器训练'],
            '深度学习': ['DL', '深层学习', '神经网络学习', '深层神经网络'],
            '自然语言处理': ['NLP', '语言处理', '文本处理', '语言理解'],
            '计算机视觉': ['CV', '机器视觉', '图像识别', '视觉识别'],
            '数据挖掘': ['数据分析', '数据探索', '信息挖掘', '知识发现'],
            '大数据': ['海量数据', '巨量数据', '大规模数据', '数据海洋'],
            '云计算': ['云服务', '云平台', '分布式计算', '云端计算'],
            '区块链': ['分布式账本', '链式数据库', '去中心化账本'],
            '物联网': ['IoT', '万物互联', '智能互联', '设备互联']
        }
        return synonyms
    
    def _preprocess_chinese_text(self, text: str) -> str:
        """预处理中文文本"""
        # 移除多余空格和特殊字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除英文标点符号，保留中文标点
        text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？；：""''（）【】《》]', ' ', text)
        
        # 标准化中文标点
        text = text.replace('，', ',').replace('。', '.').replace('！', '!')
        text = text.replace('？', '?').replace('；', ';').replace('：', ':')
        
        return text.strip()
    
    def _extract_chinese_keywords(self, text: str) -> List[str]:
        """提取中文关键词"""
        # 简单的中文关键词提取（实际应用中可以使用jieba等分词工具）
        text = self._preprocess_chinese_text(text)
        
        # 基于长度和字符特征的简单分词
        keywords = []
        
        # 提取2-4字的中文词汇
        for length in [4, 3, 2]:
            for i in range(len(text) - length + 1):
                word = text[i:i+length]
                if self._is_valid_chinese_word(word):
                    keywords.append(word)
        
        # 去重并过滤停用词
        keywords = list(set(keywords))
        keywords = [kw for kw in keywords if kw not in self.chinese_stopwords]
        
        return keywords[:20]  # 返回前20个关键词
    
    def _is_valid_chinese_word(self, word: str) -> bool:
        """判断是否为有效的中文词汇"""
        # 检查是否主要由中文字符组成
        chinese_chars = sum(1 for char in word if '\u4e00' <= char <= '\u9fff')
        return chinese_chars >= len(word) * 0.7 and len(word) >= 2
    
    def _expand_query_with_synonyms(self, query: str) -> List[str]:
        """使用同义词扩展查询"""
        expanded_queries = [query]
        
        for term, synonyms in self.chinese_synonyms.items():
            if term in query:
                for synonym in synonyms:
                    expanded_query = query.replace(term, synonym)
                    if expanded_query != query:
                        expanded_queries.append(expanded_query)
        
        return expanded_queries
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        use_synonym_expansion: bool = True,
        collection_name: Optional[str] = None,
        index_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ChineseSearchResult]:
        """
        中文语义搜索
        
        Args:
            query: 中文查询文本
            limit: 返回结果数量
            semantic_weight: 语义搜索权重
            keyword_weight: 关键词搜索权重
            use_synonym_expansion: 是否使用同义词扩展
            collection_name: 向量数据库集合名称
            index_name: Elasticsearch索引名称
            filters: 过滤条件
            
        Returns:
            中文搜索结果列表
        """
        try:
            # 预处理查询
            processed_query = self._preprocess_chinese_text(query)
            
            # 同义词扩展
            queries = [processed_query]
            if use_synonym_expansion:
                queries.extend(self._expand_query_with_synonyms(processed_query))
            
            # 执行多查询搜索
            all_results = []
            for q in queries[:3]:  # 限制查询数量避免过多请求
                results = await hybrid_search_service.search(
                    query=q,
                    mode=SearchMode.HYBRID,
                    limit=limit * 2,  # 获取更多结果用于后续处理
                    collection_name=collection_name,
                    index_name=index_name,
                    filters=filters,
                    rerank=True,
                    vector_weight=semantic_weight,
                    bm25_weight=keyword_weight
                )
                all_results.extend(results)
            
            # 去重并合并结果
            unique_results = self._deduplicate_results(all_results)
            
            # 转换为中文搜索结果
            chinese_results = []
            for result in unique_results:
                chinese_features = await self._extract_chinese_features(
                    result.content, processed_query
                )
                
                chinese_result = ChineseSearchResult(
                    id=result.id,
                    content=result.content,
                    title=result.title,
                    metadata=result.metadata,
                    semantic_score=result.vector_score,
                    keyword_score=result.bm25_score,
                    combined_score=result.hybrid_score,
                    highlights=result.highlights,
                    chinese_features=chinese_features
                )
                chinese_results.append(chinese_result)
            
            # 基于中文特征重新排序
            chinese_results = self._rerank_by_chinese_features(
                chinese_results, processed_query
            )
            
            return chinese_results[:limit]
            
        except Exception as e:
            logger.error(f"中文语义搜索失败: {e}")
            return []
    
    def _deduplicate_results(self, results: List[HybridSearchResult]) -> List[HybridSearchResult]:
        """去重搜索结果"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)
        
        return unique_results
    
    async def _extract_chinese_features(
        self, 
        content: str, 
        query: str
    ) -> Dict[str, Any]:
        """提取中文语言特征"""
        try:
            # 提取关键词
            content_keywords = self._extract_chinese_keywords(content)
            query_keywords = self._extract_chinese_keywords(query)
            
            # 计算关键词重叠度
            keyword_overlap = len(set(content_keywords) & set(query_keywords))
            keyword_overlap_ratio = keyword_overlap / max(len(query_keywords), 1)
            
            # 计算文本长度特征
            content_length = len(content)
            chinese_char_ratio = sum(
                1 for char in content if '\u4e00' <= char <= '\u9fff'
            ) / max(content_length, 1)
            
            # 计算语义相似度
            semantic_similarity = await self._compute_chinese_similarity(content, query)
            
            return {
                'content_keywords': content_keywords,
                'keyword_overlap': keyword_overlap,
                'keyword_overlap_ratio': keyword_overlap_ratio,
                'content_length': content_length,
                'chinese_char_ratio': chinese_char_ratio,
                'semantic_similarity': semantic_similarity
            }
            
        except Exception as e:
            logger.warning(f"提取中文特征失败: {e}")
            return {}
    
    async def _compute_chinese_similarity(self, text1: str, text2: str) -> float:
        """计算中文文本相似度"""
        try:
            similarity = await embedding_service.compute_similarity(text1, text2)
            return similarity
        except Exception as e:
            logger.warning(f"计算中文相似度失败: {e}")
            return 0.0
    
    def _rerank_by_chinese_features(
        self, 
        results: List[ChineseSearchResult], 
        query: str
    ) -> List[ChineseSearchResult]:
        """基于中文特征重新排序"""
        try:
            for result in results:
                if result.chinese_features:
                    # 综合评分：结合原始分数和中文特征
                    feature_score = (
                        result.chinese_features.get('keyword_overlap_ratio', 0) * 0.3 +
                        result.chinese_features.get('semantic_similarity', 0) * 0.4 +
                        min(result.chinese_features.get('chinese_char_ratio', 0), 1.0) * 0.2 +
                        min(result.combined_score, 1.0) * 0.1
                    )
                    
                    # 更新综合分数
                    result.combined_score = (result.combined_score + feature_score) / 2
            
            # 按综合分数排序
            results.sort(key=lambda x: x.combined_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.warning(f"基于中文特征重排序失败: {e}")
            return results
    
    async def find_similar_documents(
        self,
        document_content: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        collection_name: Optional[str] = None
    ) -> List[ChineseSearchResult]:
        """
        查找相似的中文文档
        
        Args:
            document_content: 文档内容
            limit: 返回结果数量
            similarity_threshold: 相似度阈值
            collection_name: 向量数据库集合名称
            
        Returns:
            相似文档列表
        """
        try:
            # 提取关键词作为查询
            keywords = self._extract_chinese_keywords(document_content)
            if not keywords:
                return []
            
            # 使用前几个关键词构建查询
            query = ' '.join(keywords[:5])
            
            # 执行语义搜索
            results = await hybrid_search_service.semantic_search(
                query=query,
                limit=limit * 2,
                similarity_threshold=similarity_threshold,
                collection_name=collection_name
            )
            
            # 转换为中文搜索结果
            chinese_results = []
            for result in results:
                chinese_features = await self._extract_chinese_features(
                    result.content, document_content
                )
                
                chinese_result = ChineseSearchResult(
                    id=result.id,
                    content=result.content,
                    title=result.title,
                    metadata=result.metadata,
                    semantic_score=result.vector_score,
                    keyword_score=0.0,
                    combined_score=result.hybrid_score,
                    chinese_features=chinese_features
                )
                chinese_results.append(chinese_result)
            
            return chinese_results[:limit]
            
        except Exception as e:
            logger.error(f"查找相似中文文档失败: {e}")
            return []
    
    async def get_search_suggestions(
        self,
        partial_query: str,
        limit: int = 5
    ) -> List[str]:
        """
        获取中文搜索建议
        
        Args:
            partial_query: 部分查询文本
            limit: 建议数量
            
        Returns:
            搜索建议列表
        """
        try:
            suggestions = []
            
            # 基于同义词的建议
            for term, synonyms in self.chinese_synonyms.items():
                if partial_query in term:
                    suggestions.append(term)
                    suggestions.extend(synonyms[:2])
                elif any(partial_query in synonym for synonym in synonyms):
                    suggestions.append(term)
            
            # 去重并限制数量
            suggestions = list(set(suggestions))[:limit]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"获取中文搜索建议失败: {e}")
            return []
    
    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        分析中文查询意图
        
        Args:
            query: 查询文本
            
        Returns:
            意图分析结果
        """
        try:
            processed_query = self._preprocess_chinese_text(query)
            keywords = self._extract_chinese_keywords(processed_query)
            
            # 简单的意图分类
            intent_keywords = {
                'search': ['搜索', '查找', '寻找', '找到', '检索'],
                'compare': ['比较', '对比', '区别', '差异', '不同'],
                'explain': ['解释', '说明', '介绍', '什么是', '如何'],
                'recommend': ['推荐', '建议', '最好', '优秀', '推荐'],
                'analyze': ['分析', '评估', '研究', '调查', '探讨']
            }
            
            intent_scores = {}
            for intent, intent_words in intent_keywords.items():
                score = sum(1 for word in intent_words if word in processed_query)
                if score > 0:
                    intent_scores[intent] = score
            
            # 确定主要意图
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0] if intent_scores else 'search'
            
            return {
                'primary_intent': primary_intent,
                'intent_scores': intent_scores,
                'keywords': keywords,
                'processed_query': processed_query,
                'query_length': len(processed_query),
                'chinese_char_count': sum(1 for char in processed_query if '\u4e00' <= char <= '\u9fff')
            }
            
        except Exception as e:
            logger.error(f"分析中文查询意图失败: {e}")
            return {'primary_intent': 'search', 'keywords': []}


# 全局中文语义搜索服务实例
chinese_search_service = ChineseSemanticSearchService()