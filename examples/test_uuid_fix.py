#!/usr/bin/env python3
"""
UUID修复验证脚本

验证所有示例文件中的UUID格式修复是否正确
"""

import asyncio
import sys
import os
import uuid
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.vector_service import vector_service, VectorDocument
from src.services.embedding_service import embedding_service
from src.utils.unicode_utils import SafeOutput

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_uuid_fix():
    """测试UUID修复"""
    safe_output = SafeOutput()
    safe_output.safe_print(safe_output.format_status("info", "UUID格式修复验证", "🔧"))
    safe_output.safe_print("=" * 50)
    
    try:
        # 初始化服务
        safe_output.safe_print("1. 初始化服务...")
        await embedding_service.initialize()
        await vector_service.initialize()
        
        # 创建测试集合
        collection_name = "uuid_test_collection"
        safe_output.safe_print(f"2. 创建测试集合: {collection_name}")
        success = await vector_service.create_collection(collection_name, recreate=True)
        safe_output.safe_print(f"   创建结果: {'成功' if success else '失败'}")
        
        # 测试UUID格式的文档
        safe_output.safe_print("3. 测试UUID格式文档...")
        test_docs = []
        
        for i in range(3):
            doc_id = str(uuid.uuid4())
            doc = VectorDocument(
                id=doc_id,
                content=f"这是测试文档 {i+1}，用于验证UUID格式修复。",
                metadata={"test_id": i+1, "doc_name": f"test_doc_{i+1:03d}"}
            )
            test_docs.append(doc)
            safe_output.safe_print(f"   文档 {i+1} ID: {doc_id}")
        
        # 添加文档
        safe_output.safe_print("4. 添加文档到向量数据库...")
        success = await vector_service.add_documents(test_docs, collection_name)
        safe_output.safe_print(f"   添加结果: {'成功' if success else '失败'}")
        
        if success:
            # 测试搜索
            safe_output.safe_print("5. 测试向量搜索...")
            results = await vector_service.search(
                query="测试文档",
                collection_name=collection_name,
                limit=3
            )
            
            safe_output.safe_print(f"   搜索结果: {len(results)} 个文档")
            for i, result in enumerate(results, 1):
                safe_output.safe_print(f"   {i}. ID: {result.document.id}")
                safe_output.safe_print(f"      相似度: {result.score:.4f}")
                safe_output.safe_print(f"      内容: {result.document.content[:30]}...")
            
            # 测试文档删除
            safe_output.safe_print("6. 测试文档删除...")
            doc_ids = [doc.id for doc in test_docs]
            success = await vector_service.delete_documents(doc_ids, collection_name)
            safe_output.safe_print(f"   删除结果: {'成功' if success else '失败'}")
        
        # 清理测试集合
        safe_output.safe_print("7. 清理测试集合...")
        success = await vector_service.delete_collection(collection_name)
        safe_output.safe_print(f"   清理结果: {'成功' if success else '失败'}")
        
        safe_output.safe_print(f"\n{safe_output.format_status('success', 'UUID格式修复验证完成!')}")
        safe_output.safe_print("所有操作均使用UUID格式的文档ID，没有出现格式错误。")
        
    except Exception as e:
        safe_output.safe_print(f"\n{safe_output.format_status('error', f'验证过程中出现错误: {e}')}")
        logger.error(f"UUID修复验证失败: {e}")
        return False
    
    finally:
        # 关闭服务
        await vector_service.close()
        await embedding_service.close()
    
    return True


async def test_example_imports():
    """测试示例文件的导入和UUID使用"""
    safe_output = SafeOutput()
    safe_output.safe_print(f"\n{safe_output.format_status('info', '示例文件UUID使用检查', '🔍')}")
    safe_output.safe_print("=" * 50)
    
    try:
        # 测试向量数据库示例
        safe_output.safe_print("1. 检查向量数据库示例...")
        from examples.vector_database_examples import VectorDatabaseExamples
        vector_examples = VectorDatabaseExamples()
        
        # 检查文档ID格式
        for i, doc in enumerate(vector_examples.sample_documents[:2], 1):
            doc_id = doc["id"]
            safe_output.safe_print(f"   文档 {i} ID: {doc_id}")
            
            # 验证是否为有效UUID
            try:
                uuid.UUID(doc_id)
                safe_output.safe_print(f"   {safe_output.format_status('success', '有效的UUID格式')}")
            except ValueError:
                safe_output.safe_print(f"   {safe_output.format_status('error', '无效的UUID格式')}")
                return False
        
        # 测试混合搜索示例
        safe_output.safe_print("2. 检查混合搜索示例...")
        from examples.hybrid_search_examples import HybridSearchExamples
        hybrid_examples = HybridSearchExamples()
        
        for i, doc in enumerate(hybrid_examples.sample_documents[:2], 1):
            doc_id = doc["id"]
            safe_output.safe_print(f"   文档 {i} ID: {doc_id}")
            
            try:
                uuid.UUID(doc_id)
                safe_output.safe_print(f"   {safe_output.format_status('success', '有效的UUID格式')}")
            except ValueError:
                safe_output.safe_print(f"   {safe_output.format_status('error', '无效的UUID格式')}")
                return False
        
        # 测试中文搜索示例
        safe_output.safe_print("3. 检查中文搜索示例...")
        from examples.chinese_search_examples import ChineseSearchExamples
        chinese_examples = ChineseSearchExamples()
        
        for i, doc in enumerate(chinese_examples.chinese_documents[:2], 1):
            doc_id = doc["id"]
            safe_output.safe_print(f"   文档 {i} ID: {doc_id}")
            
            try:
                uuid.UUID(doc_id)
                safe_output.safe_print(f"   {safe_output.format_status('success', '有效的UUID格式')}")
            except ValueError:
                safe_output.safe_print(f"   {safe_output.format_status('error', '无效的UUID格式')}")
                return False
        
        safe_output.safe_print(f"\n{safe_output.format_status('success', '所有示例文件都正确使用UUID格式!')}")
        return True
        
    except Exception as e:
        safe_output.safe_print(f"\n{safe_output.format_status('error', f'示例文件检查失败: {e}')}")
        return False


async def main():
    """主函数"""
    safe_output = SafeOutput()
    safe_output.safe_print(safe_output.format_status("info", "开始UUID修复验证", "🚀"))
    safe_output.safe_print("=" * 60)
    
    # 测试UUID修复
    uuid_test_success = await test_uuid_fix()
    
    # 测试示例文件
    import_test_success = await test_example_imports()
    
    # 总结
    safe_output.safe_print(f"\n{safe_output.format_status('info', '验证结果总结', '📊')}")
    safe_output.safe_print("=" * 60)
    uuid_status = "success" if uuid_test_success else "error"
    uuid_text = "通过" if uuid_test_success else "失败"
    import_status = "success" if import_test_success else "error"
    import_text = "通过" if import_test_success else "失败"
    
    safe_output.safe_print(f"UUID功能测试: {safe_output.format_status(uuid_status, uuid_text)}")
    safe_output.safe_print(f"示例文件检查: {safe_output.format_status(import_status, import_text)}")
    
    if uuid_test_success and import_test_success:
        safe_output.safe_print(f"\n{safe_output.format_status('success', 'UUID格式修复验证全部通过!', '🎉')}")
        safe_output.safe_print("所有示例现在都使用正确的UUID格式，可以正常与Qdrant交互。")
        return True
    else:
        safe_output.safe_print(f"\n{safe_output.format_status('warning', '部分验证失败，请检查相关问题。')}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        safe_output = SafeOutput()
        safe_output.safe_print(f"\n\n{safe_output.format_status('info', '用户中断，验证退出', '👋')}")
        sys.exit(1)
    except Exception as e:
        safe_output = SafeOutput()
        safe_output.safe_print(f"\n{safe_output.format_status('error', f'验证程序异常: {e}')}")
        sys.exit(1)