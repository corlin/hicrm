"""
检索增强生成服务 (RAG Service)
基于LangChain和LlamaIndex实现的智能检索增强生成系统
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import numpy as np
from langchain.schema import Document
from langchain.prompts import PromptTemplate
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.retrievers import VectorStoreRetriever
    from langchain.chains import RetrievalQA
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    # 如果导入失败，使用占位符
    RecursiveCharacterTextSplitter = None
    VectorStoreRetriever = None
    RetrievalQA = None
    RunnablePassthrough = None
    StrOutputParser = None

try:
    from llama_index.core import VectorStoreIndex, ServiceContext, StorageContext
    from llama_index.core.node_parser import SimpleNodeParser
    from llama_index.core.schema import NodeWithScore, TextNode
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core.query_engine import RetrieverQueryEngine
    from llama_index.core.postprocessor import SimilarityPostprocessor
except ImportError:
    # 如果llama_index不可用，使用占位符
    VectorStoreIndex = None
    ServiceContext = None
    StorageContext = None
    SimpleNodeParser = None
    NodeWithScore = None
    TextNode = None
    VectorIndexRetriever = None
    RetrieverQueryEngine = None
    SimilarityPostprocessor = None

from src.core.config import settings
from src.services.vector_service import vector_service, VectorDocument, VectorSearchResult
from src.services.embedding_service import embedding_service
from src.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class RAGMode(str, Enum):
    """RAG模式枚举"""
    SIMPLE = "simple"  # 简单检索
    FUSION = "fusion"  # 融合检索
    RERANK = "rerank"  # 重排序检索
    HYBRID = "hybrid"  # 混合检索


@dataclass
class RAGConfig:
    """RAG配置"""
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 10
    similarity_threshold: float = 0.7
    rerank_top_k: int = 5
    context_window_size: int = 4000
    enable_reranking: bool = True
    enable_fusion: bool = True
    temperature: float = 0.1
    max_tokens: int = 1000


@dataclass
class RAGResult:
    """RAG结果"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    retrieval_time: float
    generation_time: float
    total_time: float
    mode: RAGMode
    metadata: Dict[str, Any]


@dataclass
class RetrievalResult:
    """检索结果"""
    documents: List[Document]
    scores: List[float]
    reranked_scores: Optional[List[float]] = None
    retrieval_time: float = 0.0
    metadata: Dict[str, Any] = None


class ChineseTextSplitter:
    """中文文本分割器"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 中文句子分割符
        self.sentence_separators = ['。', '！', '？', '；', '\n\n']
        # 中文段落分割符
        self.paragraph_separators = ['\n\n', '\n']
        
    def split_text(self, text: str) -> List[str]:
        """分割中文文本"""
        if not text:
            return []
            
        # 首先按段落分割
        paragraphs = self._split_by_separators(text, self.paragraph_separators)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果段落太长，按句子分割
            if len(paragraph) > self.chunk_size:
                sentences = self._split_by_separators(paragraph, self.sentence_separators)
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        # 处理重叠
                        if self.chunk_overlap > 0:
                            overlap_text = current_chunk[-self.chunk_overlap:]
                            current_chunk = overlap_text + sentence
                        else:
                            current_chunk = sentence
                    else:
                        current_chunk += sentence
            else:
                if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    current_chunk += paragraph
        
        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _split_by_separators(self, text: str, separators: List[str]) -> List[str]:
        """按分隔符分割文本"""
        import re
        
        # 构建正则表达式
        pattern = '|'.join(re.escape(sep) for sep in separators)
        parts = re.split(f'({pattern})', text)
        
        # 重新组合，保留分隔符
        result = []
        current = ""
        
        for part in parts:
            if part in separators:
                current += part
                if current.strip():
                    result.append(current)
                current = ""
            else:
                current += part
        
        if current.strip():
            result.append(current)
            
        return [r for r in result if r.strip()]


class ContextWindowManager:
    """中文上下文窗口管理器"""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        
    def manage_context(
        self, 
        query: str, 
        documents: List[Document], 
        system_prompt: str = ""
    ) -> Tuple[str, List[Document]]:
        """管理上下文窗口"""
        # 估算token数量（中文字符约等于1个token）
        query_tokens = len(query)
        system_tokens = len(system_prompt)
        available_tokens = self.max_tokens - query_tokens - system_tokens - 200  # 预留生成空间
        
        if available_tokens <= 0:
            logger.warning("上下文窗口不足，无法添加检索文档")
            return query, []
        
        # 按重要性排序文档
        sorted_docs = self._sort_documents_by_importance(documents)
        
        # 选择适合的文档
        selected_docs = []
        used_tokens = 0
        
        for doc in sorted_docs:
            doc_tokens = len(doc.page_content)
            if used_tokens + doc_tokens <= available_tokens:
                selected_docs.append(doc)
                used_tokens += doc_tokens
            else:
                # 尝试截断文档
                remaining_tokens = available_tokens - used_tokens
                if remaining_tokens > 100:  # 至少保留100个字符
                    truncated_content = doc.page_content[:remaining_tokens] + "..."
                    truncated_doc = Document(
                        page_content=truncated_content,
                        metadata=doc.metadata
                    )
                    selected_docs.append(truncated_doc)
                break
        
        return query, selected_docs
    
    def _sort_documents_by_importance(self, documents: List[Document]) -> List[Document]:
        """按重要性排序文档"""
        # 简单的重要性评分：基于元数据中的分数
        def get_importance_score(doc: Document) -> float:
            metadata = doc.metadata or {}
            return metadata.get('score', 0.0)
        
        return sorted(documents, key=get_importance_score, reverse=True)


class ResultFusion:
    """结果融合器"""
    
    def __init__(self):
        self.fusion_methods = {
            'rrf': self._reciprocal_rank_fusion,
            'weighted': self._weighted_fusion,
            'max': self._max_fusion
        }
    
    def fuse_results(
        self, 
        results_list: List[List[VectorSearchResult]], 
        method: str = 'rrf'
    ) -> List[VectorSearchResult]:
        """融合多个检索结果"""
        if not results_list or not results_list[0]:
            return []
        
        fusion_func = self.fusion_methods.get(method, self._reciprocal_rank_fusion)
        return fusion_func(results_list)
    
    def _reciprocal_rank_fusion(
        self, 
        results_list: List[List[VectorSearchResult]]
    ) -> List[VectorSearchResult]:
        """倒数排名融合 (Reciprocal Rank Fusion)"""
        doc_scores = {}
        k = 60  # RRF参数
        
        for results in results_list:
            for rank, result in enumerate(results):
                doc_id = result.document.id
                score = 1.0 / (k + rank + 1)
                
                if doc_id in doc_scores:
                    doc_scores[doc_id]['score'] += score
                else:
                    doc_scores[doc_id] = {
                        'score': score,
                        'result': result
                    }
        
        # 按融合分数排序
        sorted_items = sorted(
            doc_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        # 更新分数并返回结果
        fused_results = []
        for doc_id, item in sorted_items:
            result = item['result']
            result.score = item['score']
            fused_results.append(result)
        
        return fused_results
    
    def _weighted_fusion(
        self, 
        results_list: List[List[VectorSearchResult]]
    ) -> List[VectorSearchResult]:
        """加权融合"""
        doc_scores = {}
        weights = [1.0, 0.8, 0.6]  # 不同检索器的权重
        
        for i, results in enumerate(results_list):
            weight = weights[i] if i < len(weights) else 0.4
            
            for result in results:
                doc_id = result.document.id
                weighted_score = result.score * weight
                
                if doc_id in doc_scores:
                    doc_scores[doc_id]['score'] += weighted_score
                else:
                    doc_scores[doc_id] = {
                        'score': weighted_score,
                        'result': result
                    }
        
        # 排序并返回
        sorted_items = sorted(
            doc_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        fused_results = []
        for doc_id, item in sorted_items:
            result = item['result']
            result.score = item['score']
            fused_results.append(result)
        
        return fused_results
    
    def _max_fusion(
        self, 
        results_list: List[List[VectorSearchResult]]
    ) -> List[VectorSearchResult]:
        """最大值融合"""
        doc_scores = {}
        
        for results in results_list:
            for result in results:
                doc_id = result.document.id
                
                if doc_id in doc_scores:
                    if result.score > doc_scores[doc_id]['score']:
                        doc_scores[doc_id] = {
                            'score': result.score,
                            'result': result
                        }
                else:
                    doc_scores[doc_id] = {
                        'score': result.score,
                        'result': result
                    }
        
        # 排序并返回
        sorted_items = sorted(
            doc_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        return [item['result'] for doc_id, item in sorted_items]


class RAGService:
    """检索增强生成服务"""
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.text_splitter = ChineseTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        self.context_manager = ContextWindowManager(
            max_tokens=self.config.context_window_size
        )
        self.result_fusion = ResultFusion()
        
        # LangChain组件
        self.retriever: Optional[VectorStoreRetriever] = None
        self.qa_chain: Optional[RetrievalQA] = None
        
        # LlamaIndex组件
        self.llama_index: Optional[VectorStoreIndex] = None
        self.query_engine: Optional[RetrieverQueryEngine] = None
        
        # 中文优化的提示模板
        self.chinese_prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""你是一个专业的AI助手，请基于以下上下文信息回答用户的问题。

上下文信息：
{context}

用户问题：{question}

请注意：
1. 请仅基于提供的上下文信息回答问题
2. 如果上下文信息不足以回答问题，请明确说明
3. 回答要准确、简洁、有条理
4. 使用中文回答

回答："""
        )
    
    async def initialize(self) -> None:
        """初始化RAG服务"""
        try:
            logger.info("正在初始化RAG服务...")
            
            # 初始化依赖服务
            if not vector_service.client:
                await vector_service.initialize()
            
            if not embedding_service._model_loaded:
                await embedding_service.initialize()
            
            if not embedding_service._reranker_loaded:
                await embedding_service.initialize_reranker()
            
            # 初始化LlamaIndex（如果可用）
            if VectorStoreIndex is not None:
                await self._initialize_llama_index()
            
            logger.info("RAG服务初始化完成")
            
        except Exception as e:
            logger.error(f"RAG服务初始化失败: {e}")
            raise
    
    async def _initialize_llama_index(self) -> None:
        """初始化LlamaIndex组件"""
        try:
            # 创建服务上下文
            service_context = ServiceContext.from_defaults(
                embed_model=None,  # 使用自定义嵌入服务
                llm=None,  # 使用自定义LLM服务
                node_parser=SimpleNodeParser.from_defaults(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap
                )
            )
            
            # 这里可以进一步配置LlamaIndex
            logger.info("LlamaIndex组件初始化完成")
            
        except Exception as e:
            logger.warning(f"LlamaIndex初始化失败，将使用基础功能: {e}")
    
    async def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        collection_name: str = "rag_knowledge"
    ) -> bool:
        """添加文档到RAG系统"""
        try:
            # 处理文档
            processed_docs = []
            
            for doc_data in documents:
                content = doc_data.get('content', '')
                metadata = doc_data.get('metadata', {})
                
                # 分割文本
                chunks = self.text_splitter.split_text(content)
                
                # 为每个块创建文档
                for i, chunk in enumerate(chunks):
                    chunk_metadata = {
                        **metadata,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'original_doc_id': doc_data.get('id', ''),
                        'chunk_id': f"{doc_data.get('id', '')}_{i}"
                    }
                    
                    vector_doc = VectorDocument(
                        id=chunk_metadata['chunk_id'],
                        content=chunk,
                        metadata=chunk_metadata
                    )
                    processed_docs.append(vector_doc)
            
            # 添加到向量数据库
            success = await vector_service.add_documents(
                processed_docs, 
                collection_name
            )
            
            if success:
                logger.info(f"成功添加 {len(processed_docs)} 个文档块到RAG系统")
            
            return success
            
        except Exception as e:
            logger.error(f"添加文档到RAG系统失败: {e}")
            return False
    
    async def retrieve(
        self, 
        query: str, 
        mode: RAGMode = RAGMode.HYBRID,
        collection_name: str = "rag_knowledge"
    ) -> RetrievalResult:
        """检索相关文档"""
        start_time = datetime.now()
        
        try:
            if mode == RAGMode.SIMPLE:
                results = await self._simple_retrieve(query, collection_name)
            elif mode == RAGMode.FUSION:
                results = await self._fusion_retrieve(query, collection_name)
            elif mode == RAGMode.RERANK:
                results = await self._rerank_retrieve(query, collection_name)
            else:  # HYBRID
                results = await self._hybrid_retrieve(query, collection_name)
            
            # 转换为Document格式
            documents = []
            scores = []
            
            for result in results:
                doc = Document(
                    page_content=result.document.content,
                    metadata={
                        **result.document.metadata,
                        'score': result.score,
                        'distance': result.distance
                    }
                )
                documents.append(doc)
                scores.append(result.score)
            
            retrieval_time = (datetime.now() - start_time).total_seconds()
            
            return RetrievalResult(
                documents=documents,
                scores=scores,
                retrieval_time=retrieval_time,
                metadata={'mode': mode.value, 'total_results': len(documents)}
            )
            
        except Exception as e:
            logger.error(f"文档检索失败: {e}")
            return RetrievalResult(
                documents=[],
                scores=[],
                retrieval_time=(datetime.now() - start_time).total_seconds(),
                metadata={'error': str(e)}
            )
    
    async def _simple_retrieve(
        self, 
        query: str, 
        collection_name: str
    ) -> List[VectorSearchResult]:
        """简单向量检索"""
        return await vector_service.search(
            query=query,
            collection_name=collection_name,
            limit=self.config.top_k,
            score_threshold=self.config.similarity_threshold
        )
    
    async def _fusion_retrieve(
        self, 
        query: str, 
        collection_name: str
    ) -> List[VectorSearchResult]:
        """融合检索"""
        # 多种查询策略
        queries = [
            query,
            f"关于{query}的信息",
            f"{query}相关内容"
        ]
        
        all_results = []
        for q in queries:
            results = await vector_service.search(
                query=q,
                collection_name=collection_name,
                limit=self.config.top_k,
                score_threshold=self.config.similarity_threshold * 0.8
            )
            all_results.append(results)
        
        # 融合结果
        if all_results:
            return self.result_fusion.fuse_results(all_results, method='rrf')
        
        return []
    
    async def _rerank_retrieve(
        self, 
        query: str, 
        collection_name: str
    ) -> List[VectorSearchResult]:
        """重排序检索"""
        # 首先获取更多候选文档
        initial_results = await vector_service.search(
            query=query,
            collection_name=collection_name,
            limit=self.config.top_k * 2,
            score_threshold=self.config.similarity_threshold * 0.7
        )
        
        if not initial_results:
            return []
        
        # 准备重排序
        documents = [result.document.content for result in initial_results]
        
        # 使用BGE重排序模型
        reranked_indices = await embedding_service.rerank(
            query=query,
            documents=documents,
            top_k=self.config.rerank_top_k
        )
        
        # 重新排序结果
        reranked_results = []
        for idx, rerank_score in reranked_indices:
            if idx < len(initial_results):
                result = initial_results[idx]
                # 更新分数为重排序分数
                result.score = rerank_score
                reranked_results.append(result)
        
        return reranked_results
    
    async def _hybrid_retrieve(
        self, 
        query: str, 
        collection_name: str
    ) -> List[VectorSearchResult]:
        """混合检索（融合+重排序）"""
        # 先进行融合检索
        fusion_results = await self._fusion_retrieve(query, collection_name)
        
        if not fusion_results:
            return []
        
        # 如果启用重排序且结果足够多
        if self.config.enable_reranking and len(fusion_results) > self.config.rerank_top_k:
            documents = [result.document.content for result in fusion_results]
            
            # 重排序
            reranked_indices = await embedding_service.rerank(
                query=query,
                documents=documents,
                top_k=self.config.rerank_top_k
            )
            
            # 应用重排序结果
            reranked_results = []
            for idx, rerank_score in reranked_indices:
                if idx < len(fusion_results):
                    result = fusion_results[idx]
                    result.score = rerank_score
                    reranked_results.append(result)
            
            return reranked_results
        
        return fusion_results[:self.config.rerank_top_k]
    
    async def generate(
        self, 
        query: str, 
        documents: List[Document],
        mode: RAGMode = RAGMode.HYBRID
    ) -> str:
        """生成回答"""
        try:
            # 管理上下文窗口
            managed_query, managed_docs = self.context_manager.manage_context(
                query, documents
            )
            
            if not managed_docs:
                return "抱歉，没有找到相关信息来回答您的问题。"
            
            # 构建上下文
            context = "\n\n".join([
                f"文档{i+1}: {doc.page_content}" 
                for i, doc in enumerate(managed_docs)
            ])
            
            # 使用LLM生成回答
            prompt = self.chinese_prompt_template.format(
                context=context,
                question=managed_query
            )
            
            # 调用LLM服务
            response = await llm_service.generate_response(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            return response.get('content', '生成回答时出现错误。')
            
        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            return f"生成回答时出现错误: {str(e)}"
    
    async def query(
        self, 
        question: str, 
        mode: RAGMode = RAGMode.HYBRID,
        collection_name: str = "rag_knowledge"
    ) -> RAGResult:
        """完整的RAG查询流程"""
        total_start_time = datetime.now()
        
        try:
            # 1. 检索阶段
            retrieval_start = datetime.now()
            retrieval_result = await self.retrieve(
                query=question,
                mode=mode,
                collection_name=collection_name
            )
            retrieval_time = (datetime.now() - retrieval_start).total_seconds()
            
            # 2. 生成阶段
            generation_start = datetime.now()
            answer = await self.generate(
                query=question,
                documents=retrieval_result.documents,
                mode=mode
            )
            generation_time = (datetime.now() - generation_start).total_seconds()
            
            # 3. 计算置信度
            confidence = self._calculate_confidence(
                retrieval_result.scores,
                len(retrieval_result.documents)
            )
            
            # 4. 准备源信息
            sources = []
            for i, (doc, score) in enumerate(zip(
                retrieval_result.documents, 
                retrieval_result.scores
            )):
                source = {
                    'index': i + 1,
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                }
                sources.append(source)
            
            total_time = (datetime.now() - total_start_time).total_seconds()
            
            return RAGResult(
                answer=answer,
                sources=sources,
                confidence=confidence,
                retrieval_time=retrieval_time,
                generation_time=generation_time,
                total_time=total_time,
                mode=mode,
                metadata={
                    'total_documents_found': len(retrieval_result.documents),
                    'collection_name': collection_name,
                    'config': {
                        'top_k': self.config.top_k,
                        'similarity_threshold': self.config.similarity_threshold,
                        'rerank_enabled': self.config.enable_reranking
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"RAG查询失败: {e}")
            total_time = (datetime.now() - total_start_time).total_seconds()
            
            return RAGResult(
                answer=f"查询过程中出现错误: {str(e)}",
                sources=[],
                confidence=0.0,
                retrieval_time=0.0,
                generation_time=0.0,
                total_time=total_time,
                mode=mode,
                metadata={'error': str(e)}
            )
    
    def _calculate_confidence(self, scores: List[float], doc_count: int) -> float:
        """计算回答置信度"""
        if not scores:
            return 0.0
        
        # 基于检索分数和文档数量计算置信度
        avg_score = sum(scores) / len(scores)
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        
        # 归一化置信度
        confidence = avg_score * 0.7 + (1 - score_variance) * 0.2 + min(doc_count / 5, 1) * 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    async def update_config(self, new_config: RAGConfig) -> None:
        """更新RAG配置"""
        self.config = new_config
        
        # 更新文本分割器
        self.text_splitter = ChineseTextSplitter(
            chunk_size=new_config.chunk_size,
            chunk_overlap=new_config.chunk_overlap
        )
        
        # 更新上下文管理器
        self.context_manager = ContextWindowManager(
            max_tokens=new_config.context_window_size
        )
        
        logger.info("RAG配置已更新")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取RAG服务统计信息"""
        try:
            vector_stats = await vector_service.get_stats()
            embedding_info = await embedding_service.get_model_info()
            
            return {
                'config': {
                    'chunk_size': self.config.chunk_size,
                    'chunk_overlap': self.config.chunk_overlap,
                    'top_k': self.config.top_k,
                    'similarity_threshold': self.config.similarity_threshold,
                    'rerank_enabled': self.config.enable_reranking,
                    'fusion_enabled': self.config.enable_fusion
                },
                'vector_service': vector_stats,
                'embedding_service': embedding_info,
                'llama_index_available': VectorStoreIndex is not None
            }
            
        except Exception as e:
            logger.error(f"获取RAG统计信息失败: {e}")
            return {'error': str(e)}
    
    async def close(self) -> None:
        """关闭RAG服务"""
        try:
            # 这里可以添加清理逻辑
            logger.info("RAG服务已关闭")
        except Exception as e:
            logger.error(f"关闭RAG服务失败: {e}")


# 全局RAG服务实例
rag_service = RAGService()