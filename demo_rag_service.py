#!/usr/bin/env python3
"""
RAG服务演示脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.rag_service import (
    RAGService, RAGConfig, RAGMode,
    ChineseTextSplitter, ContextWindowManager, ResultFusion
)


async def demo_chinese_text_splitter():
    """演示中文文本分割器"""
    print("=== 中文文本分割器演示 ===")
    
    splitter = ChineseTextSplitter(chunk_size=100, chunk_overlap=20)
    
    text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它致力于创建能够执行通常需要人类智能的任务的系统。
    这些任务包括学习、推理、问题解决、感知和语言理解。机器学习是人工智能的一个重要子领域，它使计算机能够从数据中学习而无需明确编程。
    深度学习又是机器学习的一个分支，它使用神经网络来模拟人脑的工作方式。近年来，深度学习在图像识别、自然语言处理和语音识别等领域取得了突破性进展。
    """
    
    chunks = splitter.split_text(text.strip())
    
    print(f"原文长度: {len(text.strip())}")
    print(f"分割后块数: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\n块 {i+1} (长度: {len(chunk)}):")
        print(f"内容: {chunk[:50]}...")


async def demo_context_window_manager():
    """演示上下文窗口管理器"""
    print("\n=== 上下文窗口管理器演示 ===")
    
    from langchain.schema import Document
    
    manager = ContextWindowManager(max_tokens=200)
    
    documents = [
        Document(page_content="这是第一个文档，包含重要信息", metadata={'score': 0.9}),
        Document(page_content="这是第二个文档，也很重要", metadata={'score': 0.8}),
        Document(page_content="这是第三个文档，相对不那么重要", metadata={'score': 0.6}),
    ]
    
    query = "测试查询"
    
    managed_query, managed_docs = manager.manage_context(query, documents)
    
    print(f"原始文档数量: {len(documents)}")
    print(f"管理后文档数量: {len(managed_docs)}")
    print(f"查询: {managed_query}")
    
    for i, doc in enumerate(managed_docs):
        print(f"文档 {i+1}: {doc.page_content}")


async def demo_result_fusion():
    """演示结果融合器"""
    print("\n=== 结果融合器演示 ===")
    
    from unittest.mock import Mock
    
    fusion = ResultFusion()
    
    # 创建模拟搜索结果
    results_1 = [
        Mock(document=Mock(id="doc1"), score=0.9),
        Mock(document=Mock(id="doc2"), score=0.8),
        Mock(document=Mock(id="doc3"), score=0.7)
    ]
    
    results_2 = [
        Mock(document=Mock(id="doc2"), score=0.85),
        Mock(document=Mock(id="doc1"), score=0.75),
        Mock(document=Mock(id="doc4"), score=0.6)
    ]
    
    # 测试不同融合方法
    methods = ['rrf', 'weighted', 'max']
    
    for method in methods:
        fused = fusion.fuse_results([results_1, results_2], method=method)
        print(f"\n{method.upper()} 融合结果:")
        for i, result in enumerate(fused[:3]):  # 只显示前3个
            print(f"  {i+1}. 文档ID: {result.document.id}, 分数: {result.score:.3f}")


async def demo_rag_config():
    """演示RAG配置"""
    print("\n=== RAG配置演示 ===")
    
    config = RAGConfig(
        chunk_size=256,
        chunk_overlap=30,
        top_k=5,
        similarity_threshold=0.75,
        rerank_top_k=3,
        context_window_size=2000,
        enable_reranking=True,
        enable_fusion=True,
        temperature=0.1,
        max_tokens=500
    )
    
    print(f"块大小: {config.chunk_size}")
    print(f"重叠大小: {config.chunk_overlap}")
    print(f"检索数量: {config.top_k}")
    print(f"相似度阈值: {config.similarity_threshold}")
    print(f"重排序数量: {config.rerank_top_k}")
    print(f"上下文窗口: {config.context_window_size}")
    print(f"启用重排序: {config.enable_reranking}")
    print(f"启用融合: {config.enable_fusion}")


async def demo_rag_service_basic():
    """演示RAG服务基本功能"""
    print("\n=== RAG服务基本功能演示 ===")
    
    config = RAGConfig(
        chunk_size=100,
        top_k=3,
        enable_reranking=False,  # 简化演示
        enable_fusion=False
    )
    
    service = RAGService(config)
    
    print("RAG服务创建成功")
    print(f"文本分割器块大小: {service.text_splitter.chunk_size}")
    print(f"上下文管理器最大tokens: {service.context_manager.max_tokens}")
    print(f"配置信息: {service.config}")
    
    # 测试文档处理
    documents = [
        {
            'id': 'demo_doc_1',
            'content': 'RAG（检索增强生成）是一种结合了信息检索和文本生成的AI技术。它首先从知识库中检索相关信息，然后基于这些信息生成回答。',
            'metadata': {'title': 'RAG技术介绍', 'category': 'AI'}
        }
    ]
    
    print(f"\n准备处理 {len(documents)} 个文档")
    
    # 这里只演示文档处理逻辑，不实际调用向量服务
    for doc_data in documents:
        content = doc_data.get('content', '')
        chunks = service.text_splitter.split_text(content)
        print(f"文档 '{doc_data['metadata']['title']}' 分割为 {len(chunks)} 个块")
        
        for i, chunk in enumerate(chunks):
            print(f"  块 {i+1}: {chunk[:30]}...")


async def main():
    """主函数"""
    print("RAG服务演示开始\n")
    
    try:
        await demo_chinese_text_splitter()
        await demo_context_window_manager()
        await demo_result_fusion()
        await demo_rag_config()
        await demo_rag_service_basic()
        
        print("\n=== 演示完成 ===")
        print("RAG服务的主要组件都已成功演示！")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())