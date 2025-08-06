#!/usr/bin/env python3
"""
测试gRPC连接和ID修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.vector_service import vector_service, VectorDocument


async def test_grpc_connection():
    """测试gRPC连接和基本操作"""
    print("🧪 测试gRPC连接和ID修复")
    print("=" * 40)
    
    try:
        # 1. 测试连接
        print("1. 测试连接...")
        await vector_service.initialize()
        print("   ✅ 连接成功")
        
        # 2. 创建测试集合
        test_collection = "grpc_test"
        print(f"2. 创建测试集合: {test_collection}")
        success = await vector_service.create_collection(test_collection, recreate=True)
        if success:
            print("   ✅ 集合创建成功")
        else:
            print("   ❌ 集合创建失败")
            return False
        
        # 3. 测试文档添加（使用整数ID）
        print("3. 测试文档添加...")
        test_docs = [
            VectorDocument(
                id=1,
                content="测试文档1",
                metadata={"type": "test", "index": 1}
            ),
            VectorDocument(
                id=2,
                content="测试文档2",
                metadata={"type": "test", "index": 2}
            )
        ]
        
        success = await vector_service.add_documents(test_docs, test_collection)
        if success:
            print("   ✅ 文档添加成功")
        else:
            print("   ❌ 文档添加失败")
            return False
        
        # 4. 测试搜索
        print("4. 测试搜索...")
        results = await vector_service.search("测试", test_collection, limit=2)
        if results:
            print(f"   ✅ 搜索成功，返回 {len(results)} 个结果")
            for i, result in enumerate(results, 1):
                print(f"      结果 {i}: ID={result.document.id}, 内容='{result.document.content}'")
        else:
            print("   ⚠️  搜索未返回结果")
        
        # 5. 清理
        print("5. 清理测试集合...")
        await vector_service.delete_collection(test_collection)
        print("   ✅ 清理完成")
        
        print("\n🎉 所有测试通过！gRPC连接和ID修复成功")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            await vector_service.close()
        except:
            pass


async def main():
    """主函数"""
    success = await test_grpc_connection()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))