"""
RAG服务API端点
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from src.services.rag_service import rag_service, RAGMode, RAGConfig
# from src.core.exceptions import ServiceError  # 暂时注释掉，如果需要可以后续添加

router = APIRouter()


class DocumentInput(BaseModel):
    """文档输入模型"""
    id: str = Field(..., description="文档ID")
    content: str = Field(..., description="文档内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")


class RAGQueryRequest(BaseModel):
    """RAG查询请求模型"""
    question: str = Field(..., description="用户问题")
    mode: RAGMode = Field(default=RAGMode.HYBRID, description="检索模式")
    collection_name: str = Field(default="rag_knowledge", description="知识库集合名称")


class RAGQueryResponse(BaseModel):
    """RAG查询响应模型"""
    answer: str = Field(..., description="生成的回答")
    sources: List[Dict[str, Any]] = Field(..., description="参考来源")
    confidence: float = Field(..., description="置信度")
    retrieval_time: float = Field(..., description="检索时间")
    generation_time: float = Field(..., description="生成时间")
    total_time: float = Field(..., description="总时间")
    mode: RAGMode = Field(..., description="使用的检索模式")
    metadata: Dict[str, Any] = Field(..., description="额外元数据")


class RAGConfigUpdate(BaseModel):
    """RAG配置更新模型"""
    chunk_size: Optional[int] = Field(None, ge=50, le=2000, description="文本块大小")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=500, description="文本块重叠大小")
    top_k: Optional[int] = Field(None, ge=1, le=50, description="检索文档数量")
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="相似度阈值")
    rerank_top_k: Optional[int] = Field(None, ge=1, le=20, description="重排序文档数量")
    context_window_size: Optional[int] = Field(None, ge=500, le=8000, description="上下文窗口大小")
    enable_reranking: Optional[bool] = Field(None, description="是否启用重排序")
    enable_fusion: Optional[bool] = Field(None, description="是否启用融合检索")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="生成温度")
    max_tokens: Optional[int] = Field(None, ge=100, le=4000, description="最大生成tokens")


@router.post("/documents", summary="添加文档到RAG系统")
async def add_documents(
    documents: List[DocumentInput],
    collection_name: str = "rag_knowledge",
    background_tasks: BackgroundTasks = None
):
    """
    添加文档到RAG知识库
    
    - **documents**: 文档列表
    - **collection_name**: 知识库集合名称
    """
    try:
        # 转换为服务所需格式
        doc_data = []
        for doc in documents:
            doc_data.append({
                'id': doc.id,
                'content': doc.content,
                'metadata': doc.metadata
            })
        
        # 添加文档
        success = await rag_service.add_documents(doc_data, collection_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="添加文档失败")
        
        return {
            "message": f"成功添加 {len(documents)} 个文档到集合 {collection_name}",
            "document_count": len(documents),
            "collection_name": collection_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加文档时出错: {str(e)}")


@router.post("/query", response_model=RAGQueryResponse, summary="RAG查询")
async def rag_query(request: RAGQueryRequest):
    """
    执行RAG查询
    
    - **question**: 用户问题
    - **mode**: 检索模式 (simple/fusion/rerank/hybrid)
    - **collection_name**: 知识库集合名称
    """
    try:
        # 执行RAG查询
        result = await rag_service.query(
            question=request.question,
            mode=request.mode,
            collection_name=request.collection_name
        )
        
        return RAGQueryResponse(
            answer=result.answer,
            sources=result.sources,
            confidence=result.confidence,
            retrieval_time=result.retrieval_time,
            generation_time=result.generation_time,
            total_time=result.total_time,
            mode=result.mode,
            metadata=result.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG查询失败: {str(e)}")


@router.get("/config", summary="获取RAG配置")
async def get_rag_config():
    """获取当前RAG配置"""
    try:
        config = rag_service.config
        return {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k": config.top_k,
            "similarity_threshold": config.similarity_threshold,
            "rerank_top_k": config.rerank_top_k,
            "context_window_size": config.context_window_size,
            "enable_reranking": config.enable_reranking,
            "enable_fusion": config.enable_fusion,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/config", summary="更新RAG配置")
async def update_rag_config(config_update: RAGConfigUpdate):
    """
    更新RAG配置
    
    只更新提供的字段，其他字段保持不变
    """
    try:
        current_config = rag_service.config
        
        # 创建新配置，只更新提供的字段
        new_config_dict = {
            "chunk_size": config_update.chunk_size or current_config.chunk_size,
            "chunk_overlap": config_update.chunk_overlap or current_config.chunk_overlap,
            "top_k": config_update.top_k or current_config.top_k,
            "similarity_threshold": config_update.similarity_threshold or current_config.similarity_threshold,
            "rerank_top_k": config_update.rerank_top_k or current_config.rerank_top_k,
            "context_window_size": config_update.context_window_size or current_config.context_window_size,
            "enable_reranking": config_update.enable_reranking if config_update.enable_reranking is not None else current_config.enable_reranking,
            "enable_fusion": config_update.enable_fusion if config_update.enable_fusion is not None else current_config.enable_fusion,
            "temperature": config_update.temperature or current_config.temperature,
            "max_tokens": config_update.max_tokens or current_config.max_tokens
        }
        
        new_config = RAGConfig(**new_config_dict)
        await rag_service.update_config(new_config)
        
        return {
            "message": "RAG配置更新成功",
            "config": new_config_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/stats", summary="获取RAG统计信息")
async def get_rag_stats():
    """获取RAG服务统计信息"""
    try:
        stats = await rag_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/initialize", summary="初始化RAG服务")
async def initialize_rag_service():
    """初始化RAG服务"""
    try:
        await rag_service.initialize()
        return {"message": "RAG服务初始化成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化RAG服务失败: {str(e)}")


@router.get("/health", summary="RAG服务健康检查")
async def rag_health_check():
    """RAG服务健康检查"""
    try:
        # 简单的健康检查
        config = rag_service.config
        
        return {
            "status": "healthy",
            "service": "RAG Service",
            "config_loaded": config is not None,
            "text_splitter_ready": rag_service.text_splitter is not None,
            "context_manager_ready": rag_service.context_manager is not None,
            "result_fusion_ready": rag_service.result_fusion is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "RAG Service",
            "error": str(e)
        }


# 示例查询端点
@router.post("/demo/query", summary="RAG演示查询")
async def demo_rag_query(question: str = "什么是RAG技术？"):
    """
    RAG演示查询，使用预设的示例数据
    """
    try:
        # 添加示例文档（如果需要）
        demo_docs = [
            {
                'id': 'demo_rag_1',
                'content': 'RAG（检索增强生成）是一种结合了信息检索和文本生成的AI技术。它首先从知识库中检索相关信息，然后基于这些信息生成准确的回答。',
                'metadata': {'title': 'RAG技术介绍', 'category': 'AI技术', 'source': 'demo'}
            },
            {
                'id': 'demo_rag_2', 
                'content': 'RAG系统通常包含三个主要组件：文档索引器、检索器和生成器。文档索引器负责将文档转换为向量表示，检索器根据查询找到相关文档，生成器基于检索到的信息生成回答。',
                'metadata': {'title': 'RAG系统架构', 'category': 'AI技术', 'source': 'demo'}
            }
        ]
        
        # 添加演示文档
        await rag_service.add_documents(demo_docs, "demo_collection")
        
        # 执行查询
        result = await rag_service.query(
            question=question,
            mode=RAGMode.SIMPLE,
            collection_name="demo_collection"
        )
        
        return {
            "question": question,
            "answer": result.answer,
            "sources": result.sources,
            "confidence": result.confidence,
            "performance": {
                "retrieval_time": result.retrieval_time,
                "generation_time": result.generation_time,
                "total_time": result.total_time
            },
            "metadata": result.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"演示查询失败: {str(e)}")