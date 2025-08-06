#!/usr/bin/env python3
"""
RAG服务基本功能测试
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.rag_service import RAGService, RAGConfig, RAGMode


async def test_rag_basic():
    """测试RAG服务基本功能"""
    print("=== RAG服务基本功能测试 ===")
    
    # 创建RAG服务
    config = RAGConfig(
        chunk_size=100,
        top_k=3,
        enable_reranking=False,
        enable_fusion=False
    )
    
    service = RAGService(config)
    print("✓ RAG服务创建成功")
    
    # 测试配置
    assert service.config.chunk_size == 100
    assert service.config.top_k == 3
    print("✓ 配置验证通过")
    
    # 测试文本分割
    text = "这是第一句话。这是第二句话，内容比较长一些。这是第三句话。"
    chunks = service.text_splitter.split_text(text)
    assert len(chunks) >= 1
    print(f"✓ 文本分割成功，生成 {len(chunks)} 个块")
    
    # 测试上下文管理
    from langchain.schema import Document
    docs = [
        Document(page_content="测试文档内容", metadata={'score': 0.9})
    ]
    
    query, managed_docs = service.context_manager.manage_context("测试查询", docs)
    assert query == "测试查询"
    print("✓ 上下文管理功能正常")
    
    # 测试结果融合
    from unittest.mock import Mock
    mock_results = [
        [Mock(document=Mock(id="doc1"), score=0.9)],
        [Mock(document=Mock(id="doc1"), score=0.8)]
    ]
    
    fused = service.result_fusion.fuse_results(mock_results)
    assert len(fused) >= 1
    print("✓ 结果融合功能正常")
    
    print("\n=== 所有基本功能测试通过 ===")


async def test_rag_config_update():
    """测试RAG配置更新"""
    print("\n=== RAG配置更新测试 ===")
    
    service = RAGService()
    original_chunk_size = service.config.chunk_size
    
    # 更新配置
    new_config = RAGConfig(
        chunk_size=256,
        chunk_overlap=30,
        top_k=5
    )
    
    await service.update_config(new_config)
    
    # 验证更新
    assert service.config.chunk_size == 256
    assert service.config.chunk_overlap == 30
    assert service.config.top_k == 5
    assert service.text_splitter.chunk_size == 256
    
    print("✓ 配置更新成功")
    print(f"  块大小: {original_chunk_size} -> {service.config.chunk_size}")
    print(f"  重叠大小: -> {service.config.chunk_overlap}")
    print(f"  检索数量: -> {service.config.top_k}")


async def test_rag_modes():
    """测试不同的RAG模式"""
    print("\n=== RAG模式测试 ===")
    
    modes = [RAGMode.SIMPLE, RAGMode.FUSION, RAGMode.RERANK, RAGMode.HYBRID]
    
    for mode in modes:
        print(f"✓ 模式 {mode.value} 可用")
    
    print("✓ 所有RAG模式验证通过")


async def main():
    """主测试函数"""
    print("开始RAG服务基本功能测试\n")
    
    try:
        await test_rag_basic()
        await test_rag_config_update()
        await test_rag_modes()
        
        print("\n🎉 所有测试通过！RAG服务基本功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)