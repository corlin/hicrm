#!/usr/bin/env python3
"""
向量数据库服务使用示例

本文件展示如何使用向量数据库服务进行文档存储、搜索和管理。
包括基本操作、批量处理、过滤搜索等功能演示。
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Any
import numpy as np
import uuid

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.vector_service import vector_service, VectorDocument
from src.services.embedding_service import embedding_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorDatabaseExamples:
    """向量数据库使用示例类"""
    
    def __init__(self):
        self.collection_name = "example_collection"
        # 生成UUID格式的文档ID (Qdrant要求UUID格式)
        self.sample_documents = [
            {
                "id": str(uuid.uuid4()),
                "content": "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                "metadata": {"category": "AI", "author": "张三", "language": "zh", "doc_name": "doc_001"}
            },
            {
                "id": str(uuid.uuid4()), 
                "content": "机器学习是人工智能的一个子领域，专注于开发能够从数据中学习的算法。",
                "metadata": {"category": "ML", "author": "李四", "language": "zh", "doc_name": "doc_002"}
            },
            {
                "id": str(uuid.uuid4()),
                "content": "深度学习使用多层神经网络来模拟人脑的工作方式，在图像识别和自然语言处理方面取得了突破性进展。",
                "metadata": {"category": "DL", "author": "王五", "language": "zh", "doc_name": "doc_003"}
            },
            {
                "id": str(uuid.uuid4()),
                "content": "Natural language processing (NLP) is a subfield of AI that focuses on the interaction between computers and human language.",
                "metadata": {"category": "NLP", "author": "John", "language": "en", "doc_name": "doc_004"}
            },
            {
                "id": str(uuid.uuid4()),
                "content": "Computer vision enables machines to interpret and understand visual information from the world.",
                "metadata": {"category": "CV", "author": "Alice", "language": "en", "doc_name": "doc_005"}
            }
        ]
    
    async def example_01_basic_setup(self):
        """示例1: 基本设置和初始化"""
        print("\n" + "="*60)
        print("示例1: 基本设置和初始化")
        print("="*60)
        
        try:
            # 初始化服务
            logger.info("初始化嵌入服务...")
            await embedding_service.initialize()
            
            logger.info("初始化向量数据库服务...")
            await vector_service.initialize()
            
            # 获取模型信息
            model_info = await embedding_service.get_model_info()
            print(f"嵌入模型信息: {model_info}")
            
            # 创建测试集合
            success = await vector_service.create_collection(
                self.collection_name, 
                recreate=True
            )
            print(f"创建集合 '{self.collection_name}': {'成功' if success else '失败'}")
            
            # 获取集合信息
            collection_info = await vector_service.get_collection_info(self.collection_name)
            print(f"集合信息: {collection_info}")
            
        except Exception as e:
            logger.error(f"基本设置失败: {e}")
            raise
    
    async def example_02_add_documents(self):
        """示例2: 添加文档到向量数据库"""
        print("\n" + "="*60)
        print("示例2: 添加文档到向量数据库")
        print("="*60)
        
        try:
            # 创建向量文档对象
            vector_docs = []
            for doc_data in self.sample_documents:
                vector_doc = VectorDocument(
                    id=doc_data["id"],
                    content=doc_data["content"],
                    metadata=doc_data["metadata"]
                )
                vector_docs.append(vector_doc)
            
            # 批量添加文档
            logger.info(f"添加 {len(vector_docs)} 个文档到集合...")
            success = await vector_service.add_documents(
                vector_docs, 
                self.collection_name
            )
            print(f"批量添加文档: {'成功' if success else '失败'}")
            
            # 获取更新后的集合信息
            collection_info = await vector_service.get_collection_info(self.collection_name)
            print(f"集合中的文档数量: {collection_info.get('points_count', 0)}")
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise
    
    async def example_03_basic_search(self):
        """示例3: 基本向量搜索"""
        print("\n" + "="*60)
        print("示例3: 基本向量搜索")
        print("="*60)
        
        try:
            # 搜索查询
            queries = [
                "什么是人工智能？",
                "机器学习算法",
                "neural networks",
                "计算机视觉技术"
            ]
            
            for query in queries:
                print(f"\n查询: '{query}'")
                results = await vector_service.search(
                    query=query,
                    collection_name=self.collection_name,
                    limit=3
                )
                
                print(f"找到 {len(results)} 个相关结果:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. 文档ID: {result.document.id}")
                    print(f"     相似度: {result.score:.4f}")
                    print(f"     内容: {result.document.content[:50]}...")
                    print(f"     元数据: {result.document.metadata}")
                    print()
                
        except Exception as e:
            logger.error(f"基本搜索失败: {e}")
            raise
    
    async def example_04_filtered_search(self):
        """示例4: 带过滤条件的搜索"""
        print("\n" + "="*60)
        print("示例4: 带过滤条件的搜索")
        print("="*60)
        
        try:
            query = "artificial intelligence"
            
            # 不同的过滤条件
            filters_list = [
                {"language": "zh"},  # 只搜索中文文档
                {"language": "en"},  # 只搜索英文文档
                {"category": "AI"},  # 只搜索AI类别
                {"author": "张三"}   # 只搜索特定作者
            ]
            
            for filters in filters_list:
                print(f"\n过滤条件: {filters}")
                results = await vector_service.search(
                    query=query,
                    collection_name=self.collection_name,
                    limit=5,
                    filters=filters
                )
                
                print(f"找到 {len(results)} 个匹配结果:")
                for result in results:
                    print(f"  - {result.document.id}: {result.document.content[:40]}...")
                    print(f"    元数据: {result.document.metadata}")
                
        except Exception as e:
            logger.error(f"过滤搜索失败: {e}")
            raise
    
    async def example_05_vector_search(self):
        """示例5: 直接使用向量搜索"""
        print("\n" + "="*60)
        print("示例5: 直接使用向量搜索")
        print("="*60)
        
        try:
            # 生成查询向量
            query_text = "深度学习神经网络"
            print(f"查询文本: '{query_text}'")
            
            query_vector = await embedding_service.encode(query_text)
            print(f"查询向量维度: {len(query_vector)}")
            print(f"向量前5个值: {query_vector[:5]}")
            
            # 使用向量搜索
            results = await vector_service.search_by_vector(
                vector=query_vector,
                collection_name=self.collection_name,
                limit=3
            )
            
            print(f"\n向量搜索结果 ({len(results)} 个):")
            for i, result in enumerate(results, 1):
                print(f"  {i}. 文档ID: {result.document.id}")
                print(f"     相似度: {result.score:.4f}")
                print(f"     内容: {result.document.content}")
                print()
                
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def example_06_similarity_calculation(self):
        """示例6: 相似度计算"""
        print("\n" + "="*60)
        print("示例6: 相似度计算")
        print("="*60)
        
        try:
            # 测试文本对
            text_pairs = [
                ("人工智能", "机器智能"),
                ("深度学习", "神经网络"),
                ("计算机视觉", "图像识别"),
                ("自然语言处理", "文本分析"),
                ("人工智能", "苹果水果")  # 不相关的对比
            ]
            
            print("文本相似度计算:")
            for text1, text2 in text_pairs:
                similarity = await embedding_service.compute_similarity(text1, text2)
                print(f"  '{text1}' vs '{text2}': {similarity:.4f}")
            
            # 一对多相似度计算
            query = "机器学习算法"
            documents = [doc["content"] for doc in self.sample_documents]
            
            print(f"\n查询 '{query}' 与所有文档的相似度:")
            similarities = await embedding_service.compute_similarities(query, documents)
            
            for i, (doc, sim) in enumerate(zip(self.sample_documents, similarities)):
                print(f"  文档{i+1} ({doc['id']}): {sim:.4f}")
                print(f"    内容: {doc['content'][:50]}...")
                
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            raise
    
    async def example_07_document_management(self):
        """示例7: 文档管理操作"""
        print("\n" + "="*60)
        print("示例7: 文档管理操作")
        print("="*60)
        
        try:
            # 添加新文档 (使用UUID格式ID)
            new_doc_id = str(uuid.uuid4())
            new_doc = VectorDocument(
                id=new_doc_id,
                content="量子计算是一种利用量子力学现象进行计算的新型计算方式。",
                metadata={"category": "QC", "author": "赵六", "language": "zh", "doc_name": "doc_new"}
            )
            
            print("添加新文档...")
            success = await vector_service.add_documents([new_doc], self.collection_name)
            print(f"添加结果: {'成功' if success else '失败'}")
            
            # 搜索新文档
            results = await vector_service.search("量子计算", self.collection_name, limit=2)
            print(f"搜索 '量子计算' 找到 {len(results)} 个结果")
            
            # 更新文档 (使用相同的UUID)
            updated_doc = VectorDocument(
                id=new_doc_id,
                content="量子计算是一种革命性的计算技术，利用量子比特的叠加和纠缠特性实现超越经典计算机的计算能力。",
                metadata={"category": "QC", "author": "赵六", "language": "zh", "updated": True, "doc_name": "doc_new"}
            )
            
            print("\n更新文档...")
            success = await vector_service.update_document(updated_doc, self.collection_name)
            print(f"更新结果: {'成功' if success else '失败'}")
            
            # 再次搜索验证更新
            results = await vector_service.search("量子比特", self.collection_name, limit=2)
            if results:
                print(f"更新后搜索结果: {results[0].document.content}")
            
            # 删除文档 (使用UUID)
            print("\n删除文档...")
            success = await vector_service.delete_documents([new_doc_id], self.collection_name)
            print(f"删除结果: {'成功' if success else '失败'}")
            
        except Exception as e:
            logger.error(f"文档管理失败: {e}")
            raise
    
    async def example_08_collection_management(self):
        """示例8: 集合管理"""
        print("\n" + "="*60)
        print("示例8: 集合管理")
        print("="*60)
        
        try:
            # 列出所有集合
            collections = await vector_service.list_collections()
            print(f"当前集合列表: {collections}")
            
            # 获取统计信息
            stats = await vector_service.get_stats()
            print(f"\n数据库统计信息:")
            print(f"  总集合数: {stats.get('total_collections', 0)}")
            
            for name, info in stats.get('collections', {}).items():
                print(f"  集合 '{name}':")
                print(f"    文档数量: {info.get('points_count', 0)}")
                print(f"    向量数量: {info.get('vectors_count', 0)}")
                print(f"    状态: {info.get('status', 'unknown')}")
            
            # 创建临时集合进行测试
            temp_collection = "temp_test_collection"
            print(f"\n创建临时集合: {temp_collection}")
            success = await vector_service.create_collection(temp_collection)
            print(f"创建结果: {'成功' if success else '失败'}")
            
            # 删除临时集合
            print(f"删除临时集合: {temp_collection}")
            success = await vector_service.delete_collection(temp_collection)
            print(f"删除结果: {'成功' if success else '失败'}")
            
        except Exception as e:
            logger.error(f"集合管理失败: {e}")
            raise
    
    async def example_09_performance_test(self):
        """示例9: 性能测试"""
        print("\n" + "="*60)
        print("示例9: 性能测试")
        print("="*60)
        
        try:
            import time
            
            # 批量编码性能测试
            test_texts = [
                f"这是测试文本 {i}，用于性能测试。包含一些中文内容和数字 {i*10}。"
                for i in range(50)
            ]
            
            print(f"批量编码 {len(test_texts)} 个文本...")
            start_time = time.time()
            embeddings = await embedding_service.encode(test_texts)
            encode_time = time.time() - start_time
            
            print(f"编码耗时: {encode_time:.2f} 秒")
            print(f"平均每个文本: {encode_time/len(test_texts)*1000:.2f} 毫秒")
            print(f"嵌入向量维度: {len(embeddings[0])}")
            
            # 批量搜索性能测试
            search_queries = [
                "测试文本",
                "性能测试",
                "中文内容",
                "数字信息"
            ]
            
            print(f"\n执行 {len(search_queries)} 个搜索查询...")
            start_time = time.time()
            
            for query in search_queries:
                results = await vector_service.search(
                    query, 
                    self.collection_name, 
                    limit=5
                )
            
            search_time = time.time() - start_time
            print(f"搜索总耗时: {search_time:.2f} 秒")
            print(f"平均每个查询: {search_time/len(search_queries)*1000:.2f} 毫秒")
            
        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            raise
    
    async def example_10_cleanup(self):
        """示例10: 清理资源"""
        print("\n" + "="*60)
        print("示例10: 清理资源")
        print("="*60)
        
        try:
            # 删除测试集合
            print(f"删除测试集合: {self.collection_name}")
            success = await vector_service.delete_collection(self.collection_name)
            print(f"删除结果: {'成功' if success else '失败'}")
            
            # 清理缓存
            print("清理嵌入服务缓存...")
            embedding_service.clear_cache()
            
            # 关闭连接
            print("关闭服务连接...")
            await vector_service.close()
            await embedding_service.close()
            
            print("资源清理完成!")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
            raise


async def run_all_examples():
    """运行所有示例"""
    examples = VectorDatabaseExamples()
    
    try:
        await examples.example_01_basic_setup()
        await examples.example_02_add_documents()
        await examples.example_03_basic_search()
        await examples.example_04_filtered_search()
        await examples.example_05_vector_search()
        await examples.example_06_similarity_calculation()
        await examples.example_07_document_management()
        await examples.example_08_collection_management()
        await examples.example_09_performance_test()
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise
    finally:
        await examples.example_10_cleanup()


async def run_specific_example(example_num: int):
    """运行特定示例"""
    examples = VectorDatabaseExamples()
    
    # 基本设置总是需要的
    await examples.example_01_basic_setup()
    if example_num > 1:
        await examples.example_02_add_documents()
    
    try:
        if example_num == 3:
            await examples.example_03_basic_search()
        elif example_num == 4:
            await examples.example_04_filtered_search()
        elif example_num == 5:
            await examples.example_05_vector_search()
        elif example_num == 6:
            await examples.example_06_similarity_calculation()
        elif example_num == 7:
            await examples.example_07_document_management()
        elif example_num == 8:
            await examples.example_08_collection_management()
        elif example_num == 9:
            await examples.example_09_performance_test()
        else:
            print(f"示例 {example_num} 不存在")
            return
            
    finally:
        await examples.example_10_cleanup()


if __name__ == "__main__":
    print("向量数据库服务使用示例")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            print(f"运行示例 {example_num}")
            asyncio.run(run_specific_example(example_num))
        except ValueError:
            print("请提供有效的示例编号 (1-9)")
    else:
        print("运行所有示例...")
        asyncio.run(run_all_examples())