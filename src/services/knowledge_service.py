"""
知识库管理服务
Knowledge Management Service
"""

import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from ..models.knowledge import (
    Knowledge, KnowledgeChunk, KnowledgeType, KnowledgeStatus,
    QualityMetrics, UsageStatistics, KnowledgeMetadata,
    KnowledgeSearchFilter, KnowledgeSearchResult, KnowledgeUpdateRequest,
    KnowledgeRelation
)
from .vector_service import VectorService
from .embedding_service import EmbeddingService


class DocumentParser:
    """文档解析器"""
    
    @staticmethod
    def parse_text(content: str, chunk_size: int = 512, overlap: int = 50) -> List[KnowledgeChunk]:
        """解析文本并分块"""
        chunks = []
        sentences = DocumentParser._split_sentences(content)
        
        current_chunk = ""
        current_position = 0
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                # 创建当前块
                chunk = KnowledgeChunk(
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    start_position=current_position - len(current_chunk),
                    end_position=current_position,
                    metadata={
                        "sentence_count": len(current_chunk.split('。')),
                        "word_count": len(current_chunk.replace(' ', ''))
                    }
                )
                chunks.append(chunk)
                
                # 处理重叠
                if overlap > 0:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + sentence
                else:
                    current_chunk = sentence
                    
                chunk_index += 1
            else:
                current_chunk += sentence
                
            current_position += len(sentence)
        
        # 处理最后一个块
        if current_chunk.strip():
            chunk = KnowledgeChunk(
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_position=current_position - len(current_chunk),
                end_position=current_position,
                metadata={
                    "sentence_count": len(current_chunk.split('。')),
                    "word_count": len(current_chunk.replace(' ', ''))
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """分句处理"""
        # 中文句子分割
        sentences = re.split(r'[。！？；\n]', text)
        return [s.strip() + '。' for s in sentences if s.strip()]
    
    @staticmethod
    def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（实际项目中可以使用更复杂的NLP方法）
        import re
        
        word_freq = defaultdict(int)
        
        # 停用词
        stop_words = {'是的', '这是', '那是', '可以', '应该', '需要', '进行', '实现', '具有', '包括', '通过', '使用', '提供', '支持', '管理', '系统', '功能', '服务', '信息', '数据', '的', '和', '是', '在', '有', '与', '为', '了', '等', '及', '或'}
        
        # 先提取所有可能的中文词汇（1-4字）
        all_words = []
        
        # 提取单字到4字的所有组合
        for i in range(len(content)):
            for j in range(i+1, min(i+5, len(content)+1)):
                word = content[i:j]
                if re.match(r'^[\u4e00-\u9fff]+$', word) and len(word) >= 2:
                    all_words.append(word)
        
        # 统计词频
        for word in all_words:
            if word not in stop_words:
                word_freq[word] += 1
        
        # 按频率排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]


class QualityAssessment:
    """知识质量评估器"""
    
    @staticmethod
    def assess_quality(knowledge: Knowledge) -> QualityMetrics:
        """评估知识质量"""
        accuracy_score = QualityAssessment._assess_accuracy(knowledge)
        completeness_score = QualityAssessment._assess_completeness(knowledge)
        relevance_score = QualityAssessment._assess_relevance(knowledge)
        freshness_score = QualityAssessment._assess_freshness(knowledge)
        usage_score = QualityAssessment._assess_usage(knowledge)
        
        # 计算综合评分
        weights = {
            'accuracy': 0.25,
            'completeness': 0.20,
            'relevance': 0.20,
            'freshness': 0.15,
            'usage': 0.20
        }
        
        overall_score = (
            accuracy_score * weights['accuracy'] +
            completeness_score * weights['completeness'] +
            relevance_score * weights['relevance'] +
            freshness_score * weights['freshness'] +
            usage_score * weights['usage']
        )
        
        return QualityMetrics(
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            relevance_score=relevance_score,
            freshness_score=freshness_score,
            usage_score=usage_score,
            overall_score=overall_score,
            last_evaluated=datetime.now()
        )
    
    @staticmethod
    def _assess_accuracy(knowledge: Knowledge) -> float:
        """评估准确性"""
        # 基于反馈和验证状态
        if knowledge.usage.feedback_count == 0:
            return 0.7  # 默认分数
        
        positive_ratio = knowledge.usage.positive_feedback / knowledge.usage.feedback_count
        return min(1.0, positive_ratio + 0.2)
    
    @staticmethod
    def _assess_completeness(knowledge: Knowledge) -> float:
        """评估完整性"""
        score = 0.0
        
        # 内容长度
        if len(knowledge.content) > 100:
            score += 0.3
        if len(knowledge.content) > 500:
            score += 0.2
            
        # 元数据完整性
        if knowledge.metadata.keywords:
            score += 0.2
        if knowledge.metadata.tags:
            score += 0.1
        if knowledge.metadata.domain:
            score += 0.1
            
        # 结构化程度
        if knowledge.chunks:
            score += 0.1
            
        return min(1.0, score)
    
    @staticmethod
    def _assess_relevance(knowledge: Knowledge) -> float:
        """评估相关性"""
        # 基于搜索命中率和引用次数
        if knowledge.usage.search_count == 0:
            return 0.5
            
        relevance = min(1.0, knowledge.usage.reference_count / max(1, knowledge.usage.search_count))
        return max(0.3, relevance)
    
    @staticmethod
    def _assess_freshness(knowledge: Knowledge) -> float:
        """评估时效性"""
        if not knowledge.updated_at:
            return 0.5
            
        days_old = (datetime.now() - knowledge.updated_at).days
        
        if days_old <= 30:
            return 1.0
        elif days_old <= 90:
            return 0.8
        elif days_old <= 180:
            return 0.6
        elif days_old <= 365:
            return 0.4
        else:
            return 0.2
    
    @staticmethod
    def _assess_usage(knowledge: Knowledge) -> float:
        """评估使用频率"""
        total_usage = (
            knowledge.usage.view_count +
            knowledge.usage.search_count * 2 +
            knowledge.usage.reference_count * 3
        )
        
        # 归一化处理
        return min(1.0, total_usage / 100.0)


class KnowledgeService:
    """知识库管理服务"""
    
    def __init__(self):
        self.vector_service = VectorService()
        self.embedding_service = EmbeddingService()
        self.knowledge_store: Dict[str, Knowledge] = {}
        self.parser = DocumentParser()
        self.quality_assessor = QualityAssessment()
    
    async def create_knowledge(
        self,
        title: str,
        content: str,
        knowledge_type: KnowledgeType,
        metadata: KnowledgeMetadata
    ) -> Knowledge:
        """创建知识条目"""
        # 解析和分块
        chunks = self.parser.parse_text(content)
        
        # 生成嵌入向量
        for chunk in chunks:
            try:
                # 初始化embedding服务
                if not hasattr(self.embedding_service, 'model') or self.embedding_service.model is None:
                    await self.embedding_service.initialize()
                
                # 获取嵌入向量
                embedding_result = await self.embedding_service.encode(chunk.content)
                if isinstance(embedding_result, list) and len(embedding_result) > 0:
                    chunk.embedding = embedding_result[0].tolist() if hasattr(embedding_result[0], 'tolist') else embedding_result[0]
                else:
                    chunk.embedding = embedding_result.tolist() if hasattr(embedding_result, 'tolist') else embedding_result
            except Exception as e:
                # 如果嵌入服务失败，使用默认的空向量
                chunk.embedding = None
        
        # 提取关键词
        keywords = self.parser.extract_keywords(content)
        metadata.keywords = keywords
        
        # 创建知识实体
        knowledge = Knowledge(
            title=title,
            content=content,
            type=knowledge_type,
            chunks=chunks,
            metadata=metadata,
            status=KnowledgeStatus.DRAFT
        )
        
        # 评估质量
        knowledge.quality = self.quality_assessor.assess_quality(knowledge)
        
        # 存储
        self.knowledge_store[knowledge.id] = knowledge
        
        # 存储到向量数据库
        await self._store_vectors(knowledge)
        
        return knowledge
    
    async def update_knowledge(
        self,
        knowledge_id: str,
        update_request: KnowledgeUpdateRequest
    ) -> Knowledge:
        """更新知识条目"""
        if knowledge_id not in self.knowledge_store:
            raise ValueError(f"Knowledge with id {knowledge_id} not found")
        
        knowledge = self.knowledge_store[knowledge_id]
        
        # 保存版本历史
        version_info = {
            "version": len(knowledge.version_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "changes": {}
        }
        
        # 更新字段
        if update_request.title:
            version_info["changes"]["title"] = {"old": knowledge.title, "new": update_request.title}
            knowledge.title = update_request.title
            
        if update_request.content:
            version_info["changes"]["content"] = {"old": len(knowledge.content), "new": len(update_request.content)}
            knowledge.content = update_request.content
            
            # 重新解析和分块
            chunks = self.parser.parse_text(update_request.content)
            for chunk in chunks:
                try:
                    # 初始化embedding服务
                    if not hasattr(self.embedding_service, 'model') or self.embedding_service.model is None:
                        await self.embedding_service.initialize()
                    
                    # 获取嵌入向量
                    embedding_result = await self.embedding_service.encode(chunk.content)
                    if isinstance(embedding_result, list) and len(embedding_result) > 0:
                        chunk.embedding = embedding_result[0].tolist() if hasattr(embedding_result[0], 'tolist') else embedding_result[0]
                    else:
                        chunk.embedding = embedding_result.tolist() if hasattr(embedding_result, 'tolist') else embedding_result
                except Exception as e:
                    # 如果嵌入服务失败，使用默认的空向量
                    chunk.embedding = None
            knowledge.chunks = chunks
            
            # 重新存储向量
            await self._store_vectors(knowledge)
        
        if update_request.metadata:
            knowledge.metadata = update_request.metadata
            
        if update_request.status:
            version_info["changes"]["status"] = {"old": knowledge.status, "new": update_request.status}
            knowledge.status = update_request.status
            
        if update_request.categories:
            knowledge.categories = update_request.categories
        
        # 更新时间戳
        knowledge.updated_at = datetime.now()
        knowledge.version_history.append(version_info)
        
        # 重新评估质量
        knowledge.quality = self.quality_assessor.assess_quality(knowledge)
        
        return knowledge
    
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """删除知识条目"""
        if knowledge_id not in self.knowledge_store:
            return False
        
        # 从向量数据库删除
        await self._delete_vectors(knowledge_id)
        
        # 从存储删除
        del self.knowledge_store[knowledge_id]
        
        return True
    
    def get_knowledge(self, knowledge_id: str) -> Optional[Knowledge]:
        """获取知识条目"""
        knowledge = self.knowledge_store.get(knowledge_id)
        if knowledge:
            # 更新访问统计
            knowledge.usage.view_count += 1
            knowledge.usage.last_accessed = datetime.now()
        return knowledge
    
    def list_knowledge(
        self,
        filter_params: Optional[KnowledgeSearchFilter] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Knowledge]:
        """列出知识条目"""
        knowledge_list = list(self.knowledge_store.values())
        
        # 应用过滤器
        if filter_params:
            knowledge_list = self._apply_filters(knowledge_list, filter_params)
        
        # 分页
        return knowledge_list[offset:offset + limit]
    
    async def search_knowledge(
        self,
        query: str,
        filter_params: Optional[KnowledgeSearchFilter] = None,
        limit: int = 10
    ) -> List[KnowledgeSearchResult]:
        """搜索知识"""
        # 生成查询向量
        try:
            # 初始化embedding服务
            if not hasattr(self.embedding_service, 'model') or self.embedding_service.model is None:
                await self.embedding_service.initialize()
            
            # 获取查询向量
            embedding_result = await self.embedding_service.encode(query)
            if isinstance(embedding_result, list) and len(embedding_result) > 0:
                query_embedding = embedding_result[0].tolist() if hasattr(embedding_result[0], 'tolist') else embedding_result[0]
            else:
                query_embedding = embedding_result.tolist() if hasattr(embedding_result, 'tolist') else embedding_result
        except Exception as e:
            # 如果嵌入服务失败，返回空结果
            return []
        
        # 向量搜索
        vector_results = await self.vector_service.search(
            query_embedding,
            collection_name="knowledge",
            limit=limit * 2  # 获取更多结果用于重排序
        )
        
        results = []
        for vector_result in vector_results:
            knowledge_id = vector_result.get("knowledge_id")
            chunk_id = vector_result.get("chunk_id")
            score = vector_result.get("score", 0.0)
            
            if knowledge_id in self.knowledge_store:
                knowledge = self.knowledge_store[knowledge_id]
                
                # 应用过滤器
                if filter_params and not self._match_filter(knowledge, filter_params):
                    continue
                
                # 找到匹配的块
                matched_chunk = None
                for chunk in knowledge.chunks:
                    if chunk.id == chunk_id:
                        matched_chunk = chunk
                        break
                
                # 生成摘要
                snippet = self._generate_snippet(knowledge.content, query)
                
                # 计算相关性分数
                relevance = self._calculate_relevance(knowledge, query)
                
                result = KnowledgeSearchResult(
                    knowledge=knowledge,
                    score=score,
                    relevance=relevance,
                    snippet=snippet,
                    matched_chunks=[matched_chunk] if matched_chunk else [],
                    highlight=self._generate_highlights(knowledge.content, query)
                )
                results.append(result)
                
                # 更新搜索统计
                knowledge.usage.search_count += 1
        
        # 按相关性排序
        results.sort(key=lambda x: x.relevance * x.score, reverse=True)
        
        return results[:limit]
    
    def update_usage_statistics(self, knowledge_id: str, action: str, feedback: Optional[bool] = None):
        """更新使用统计"""
        if knowledge_id not in self.knowledge_store:
            return
        
        knowledge = self.knowledge_store[knowledge_id]
        
        if action == "reference":
            knowledge.usage.reference_count += 1
        elif action == "feedback" and feedback is not None:
            knowledge.usage.feedback_count += 1
            if feedback:
                knowledge.usage.positive_feedback += 1
            else:
                knowledge.usage.negative_feedback += 1
    
    async def batch_quality_assessment(self) -> Dict[str, QualityMetrics]:
        """批量质量评估"""
        results = {}
        for knowledge_id, knowledge in self.knowledge_store.items():
            quality = self.quality_assessor.assess_quality(knowledge)
            knowledge.quality = quality
            results[knowledge_id] = quality
        return results
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        total_count = len(self.knowledge_store)
        type_counts = defaultdict(int)
        status_counts = defaultdict(int)
        quality_scores = []
        
        for knowledge in self.knowledge_store.values():
            type_counts[knowledge.type] += 1
            status_counts[knowledge.status] += 1
            if knowledge.quality:
                quality_scores.append(knowledge.quality.overall_score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "total_knowledge": total_count,
            "by_type": dict(type_counts),
            "by_status": dict(status_counts),
            "average_quality": avg_quality,
            "total_chunks": sum(len(k.chunks) for k in self.knowledge_store.values())
        }
    
    # 私有方法
    async def _store_vectors(self, knowledge: Knowledge):
        """存储向量到向量数据库"""
        try:
            # 初始化向量服务
            if not hasattr(self.vector_service, 'client') or self.vector_service.client is None:
                await self.vector_service.initialize()
            
            # 确保集合存在
            await self.vector_service.create_collection("knowledge")
            
            # 准备文档列表
            documents = []
            for chunk in knowledge.chunks:
                if chunk.embedding:
                    from src.services.vector_service import VectorDocument
                    
                    metadata = {
                        "knowledge_id": knowledge.id,
                        "chunk_id": chunk.id,
                        "title": knowledge.title,
                        "type": knowledge.type.value,
                        "chunk_index": chunk.chunk_index
                    }
                    
                    doc = VectorDocument(
                        id=chunk.id,
                        content=chunk.content,
                        vector=chunk.embedding,
                        metadata=metadata
                    )
                    documents.append(doc)
            
            # 批量添加文档
            if documents:
                await self.vector_service.add_documents(documents, "knowledge")
        except Exception as e:
            # 向量存储失败不应该影响知识创建
            pass
    
    async def _delete_vectors(self, knowledge_id: str):
        """从向量数据库删除向量"""
        # 这里需要根据实际的向量数据库实现
        pass
    
    def _apply_filters(self, knowledge_list: List[Knowledge], filters: KnowledgeSearchFilter) -> List[Knowledge]:
        """应用搜索过滤器"""
        filtered = []
        for knowledge in knowledge_list:
            if self._match_filter(knowledge, filters):
                filtered.append(knowledge)
        return filtered
    
    def _match_filter(self, knowledge: Knowledge, filters: KnowledgeSearchFilter) -> bool:
        """检查知识是否匹配过滤器"""
        if filters.types and knowledge.type not in filters.types:
            return False
        
        if filters.status and knowledge.status not in filters.status:
            return False
        
        if filters.domains and knowledge.metadata.domain not in filters.domains:
            return False
        
        if filters.tags:
            if not any(tag in knowledge.metadata.tags for tag in filters.tags):
                return False
        
        if filters.min_quality_score and knowledge.quality:
            if knowledge.quality.overall_score < filters.min_quality_score:
                return False
        
        if filters.author and knowledge.metadata.author != filters.author:
            return False
        
        return True
    
    def _generate_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        # 简单的摘要生成
        if len(content) <= max_length:
            return content
        
        # 尝试找到包含查询词的句子
        sentences = content.split('。')
        for sentence in sentences:
            if query in sentence and len(sentence) <= max_length:
                return sentence + '。'
        
        # 返回前N个字符
        return content[:max_length] + "..."
    
    def _calculate_relevance(self, knowledge: Knowledge, query: str) -> float:
        """计算相关性分数"""
        relevance = 0.0
        
        # 标题匹配
        if query in knowledge.title:
            relevance += 0.3
        
        # 内容匹配
        content_matches = knowledge.content.count(query)
        relevance += min(0.4, content_matches * 0.1)
        
        # 关键词匹配
        if query in knowledge.metadata.keywords:
            relevance += 0.2
        
        # 标签匹配
        if query in knowledge.metadata.tags:
            relevance += 0.1
        
        return min(1.0, relevance)
    
    def _generate_highlights(self, content: str, query: str) -> Dict[str, List[str]]:
        """生成高亮信息"""
        highlights = {"content": []}
        
        # 简单的高亮实现
        sentences = content.split('。')
        for sentence in sentences:
            if query in sentence:
                highlighted = sentence.replace(query, f"<mark>{query}</mark>")
                highlights["content"].append(highlighted)
        
        return highlights