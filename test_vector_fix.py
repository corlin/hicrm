"""
测试向量服务修复
"""

import asyncio
import numpy as np
from src.services.vector_service import VectorService, VectorDocument
from src.services.embedding_service import EmbeddingService

async def test_embedding_service_fix():
    """测试嵌入服务修复"""
    print("测试嵌入服务修复...")
    
    # 创建嵌入服务实例
    embedding_service = EmbeddingService()
    
    # 测试批量编码方法
    texts = ["测试文本1", "测试文本2", "测试文本3"]
    
    # 模拟抛出弃用警告异常
    try:
        # 直接调用内部方法进行测试
        embeddings = embedding_service._encode_batch(texts)
        
        # 检查返回的嵌入向量
        if embeddings and len(embeddings) == len(texts):
            print(f"成功: 返回了 {len(embeddings)} 个嵌入向量")
            print(f"第一个向量维度: {len(embeddings[0])}")
            return True
        else:
            print(f"失败: 返回了空的嵌入向量列表")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

async def test_vector_service_filter():
    """测试向量服务过滤器修复"""
    print("\n测试向量服务过滤器修复...")
    
    # 创建向量服务实例
    vector_service = VectorService()
    
    # 测试构建过滤器
    filters = {
        "category": "tech",
        "author": "张三",
        "score": 0.8,
        "published": True
    }
    
    try:
        # 调用过滤器构建方法
        filter_obj = vector_service._build_filter(filters)
        
        if filter_obj and len(filter_obj.must) == 4:
            print(f"成功: 过滤器包含 {len(filter_obj.must)} 个条件")
            return True
        else:
            print("失败: 过滤器构建不正确")
            return False
    except Exception as e:
        print(f"异常: {e}")
        return False

async def main():
    """主函数"""
    print("开始测试向量服务修复...\n")
    
    embedding_result = await test_embedding_service_fix()
    filter_result = await test_vector_service_filter()
    
    print("\n测试结果汇总:")
    print(f"嵌入服务修复: {'成功' if embedding_result else '失败'}")
    print(f"过滤器修复: {'成功' if filter_result else '失败'}")
    
    if embedding_result and filter_result:
        print("\n所有修复都成功!")
    else:
        print("\n部分修复失败，请检查代码!")

if __name__ == "__main__":
    asyncio.run(main())
