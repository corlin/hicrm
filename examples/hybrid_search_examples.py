#!/usr/bin/env python3
"""
混合搜索服务使用示例

本文件展示如何使用混合搜索服务，结合向量搜索和BM25搜索，
实现更准确和全面的搜索功能。包括不同搜索模式、权重调整、
重排序等功能演示。
"""

import asyncio
import sys
import os
import logging
import time
from typing import List, Dict, Any
import json
import uuid

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.hybrid_search_service import hybrid_search_service, SearchMode
from src.services.vector_service import vector_service
from src.services.elasticsearch_service import elasticsearch_service
from src.services.embedding_service import embedding_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HybridSearchExamples:
    """混合搜索服务使用示例类"""
    
    def __init__(self):
        self.collection_name = "hybrid_search_demo"
        self.index_name = "hybrid_search_demo"
        
        # 示例文档数据 (使用UUID格式ID)
        self.sample_documents = [
            {
                "id": str(uuid.uuid4()),
                "title": "人工智能基础概念",
                "content": "人工智能(AI)是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。AI包括机器学习、深度学习、自然语言处理等多个子领域。",
                "metadata": {
                    "category": "AI基础",
                    "author": "张三",
                    "tags": ["人工智能", "基础概念", "计算机科学"],
                    "publish_date": "2024-01-15",
                    "language": "zh",
                    "doc_name": "doc_001"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "机器学习算法详解",
                "content": "机器学习是人工智能的核心技术之一，通过算法让计算机从数据中学习模式。常见的机器学习算法包括线性回归、决策树、随机森林、支持向量机等。",
                "metadata": {
                    "category": "机器学习",
                    "author": "李四",
                    "tags": ["机器学习", "算法", "数据分析"],
                    "publish_date": "2024-02-01",
                    "language": "zh",
                    "doc_name": "doc_002"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "深度学习与神经网络",
                "content": "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的工作方式。卷积神经网络(CNN)在图像识别方面表现出色，循环神经网络(RNN)适合处理序列数据。",
                "metadata": {
                    "category": "深度学习",
                    "author": "王五",
                    "tags": ["深度学习", "神经网络", "CNN", "RNN"],
                    "publish_date": "2024-02-15",
                    "language": "zh",
                    "doc_name": "doc_003"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Natural Language Processing Fundamentals",
                "content": "Natural Language Processing (NLP) is a subfield of AI that focuses on the interaction between computers and human language. Key NLP tasks include text classification, sentiment analysis, named entity recognition, and machine translation.",
                "metadata": {
                    "category": "NLP",
                    "author": "John Smith",
                    "tags": ["NLP", "text processing", "language models"],
                    "publish_date": "2024-03-01",
                    "language": "en",
                    "doc_name": "doc_004"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Computer Vision Applications",
                "content": "Computer vision enables machines to interpret and understand visual information from the world. Applications include image classification, object detection, facial recognition, and autonomous driving systems.",
                "metadata": {
                    "category": "Computer Vision",
                    "author": "Alice Johnson",
                    "tags": ["computer vision", "image processing", "object detection"],
                    "publish_date": "2024-03-15",
                    "language": "en",
                    "doc_name": "doc_005"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "大数据与人工智能",
                "content": "大数据为人工智能提供了丰富的训练数据。通过分析海量数据，AI系统能够发现隐藏的模式和趋势。大数据技术包括Hadoop、Spark、NoSQL数据库等。",
                "metadata": {
                    "category": "大数据",
                    "author": "赵六",
                    "tags": ["大数据", "数据分析", "Hadoop", "Spark"],
                    "publish_date": "2024-04-01",
                    "language": "zh",
                    "doc_name": "doc_006"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "AI Ethics and Responsible AI",
                "content": "As AI systems become more powerful and widespread, ethical considerations become increasingly important. Key issues include bias in AI systems, privacy protection, transparency, and the societal impact of automation.",
                "metadata": {
                    "category": "AI Ethics",
                    "author": "Dr. Sarah Wilson",
                    "tags": ["AI ethics", "responsible AI", "bias", "privacy"],
                    "publish_date": "2024-04-15",
                    "language": "en",
                    "doc_name": "doc_007"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "量子计算与AI的未来",
                "content": "量子计算有望为人工智能带来革命性的变化。量子算法可能在某些AI任务上提供指数级的加速，特别是在优化问题和机器学习模型训练方面。",
                "metadata": {
                    "category": "量子计算",
                    "author": "陈七",
                    "tags": ["量子计算", "量子算法", "未来技术"],
                    "publish_date": "2024-05-01",
                    "language": "zh",
                    "doc_name": "doc_008"
                }
            }
        ]
    
    async def example_01_service_initialization(self):
        """示例1: 服务初始化"""
        print("\n" + "="*60)
        print("示例1: 混合搜索服务初始化")
        print("="*60)
        
        try:
            logger.info("初始化混合搜索服务...")
            await hybrid_search_service.initialize()
            
            print("混合搜索服务初始化完成!")
            print("包含的组件:")
            print("  - BGE-M3嵌入服务 (语义搜索)")
            print("  - Qdrant向量数据库 (向量存储)")
            print("  - Elasticsearch (BM25文本搜索)")
            
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            raise
    
    async def example_02_add_documents(self):
        """示例2: 添加文档到混合搜索系统"""
        print("\n" + "="*60)
        print("示例2: 添加文档到混合搜索系统")
        print("="*60)
        
        try:
            print(f"准备添加 {len(self.sample_documents)} 个文档...")
            
            # 显示文档信息
            for i, doc in enumerate(self.sample_documents[:3], 1):
                print(f"\n文档 {i}:")
                print(f"  ID: {doc['id']}")
                print(f"  标题: {doc['title']}")
                print(f"  内容: {doc['content'][:50]}...")
                print(f"  类别: {doc['metadata']['category']}")
            
            print(f"\n... 还有 {len(self.sample_documents) - 3} 个文档")
            
            # 添加文档到混合搜索系统
            success = await hybrid_search_service.add_documents(
                self.sample_documents,
                collection_name=self.collection_name,
                index_name=self.index_name
            )
            
            print(f"\n文档添加结果: {'成功' if success else '失败'}")
            
            if success:
                print("文档已同时添加到:")
                print("  - Qdrant向量数据库 (用于语义搜索)")
                print("  - Elasticsearch索引 (用于关键词搜索)")
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise
    
    async def example_03_vector_only_search(self):
        """示例3: 仅向量搜索模式"""
        print("\n" + "="*60)
        print("示例3: 仅向量搜索模式 (语义搜索)")
        print("="*60)
        
        try:
            queries = [
                "人工智能的基本概念",
                "machine learning algorithms",
                "深度学习网络结构",
                "计算机视觉应用"
            ]
            
            for query in queries:
                print(f"\n查询: '{query}'")
                print("-" * 50)
                
                results = await hybrid_search_service.search(
                    query=query,
                    mode=SearchMode.VECTOR_ONLY,
                    limit=3,
                    collection_name=self.collection_name
                )
                
                print(f"找到 {len(results)} 个语义相关结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n  {i}. 文档: {result.title}")
                    print(f"     语义相似度: {result.vector_score:.4f}")
                    print(f"     内容: {result.content[:80]}...")
                    print(f"     类别: {result.metadata.get('category', 'N/A')}")
                
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def example_04_bm25_only_search(self):
        """示例4: 仅BM25搜索模式"""
        print("\n" + "="*60)
        print("示例4: 仅BM25搜索模式 (关键词搜索)")
        print("="*60)
        
        try:
            queries = [
                "机器学习算法",
                "neural network CNN",
                "数据分析",
                "computer vision"
            ]
            
            for query in queries:
                print(f"\n查询: '{query}'")
                print("-" * 50)
                
                results = await hybrid_search_service.search(
                    query=query,
                    mode=SearchMode.BM25_ONLY,
                    limit=3,
                    index_name=self.index_name
                )
                
                print(f"找到 {len(results)} 个关键词匹配结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n  {i}. 文档: {result.title}")
                    print(f"     BM25分数: {result.bm25_score:.4f}")
                    print(f"     内容: {result.content[:80]}...")
                    
                    # 显示高亮信息
                    if result.highlights:
                        print(f"     关键词高亮: {result.highlights}")
                
        except Exception as e:
            logger.error(f"BM25搜索失败: {e}")
            raise
    
    async def example_05_hybrid_search(self):
        """示例5: 混合搜索模式"""
        print("\n" + "="*60)
        print("示例5: 混合搜索模式 (语义 + 关键词)")
        print("="*60)
        
        try:
            queries = [
                "人工智能算法应用",
                "deep learning neural networks",
                "机器学习数据分析",
                "AI ethics and bias"
            ]
            
            for query in queries:
                print(f"\n查询: '{query}'")
                print("-" * 50)
                
                results = await hybrid_search_service.search(
                    query=query,
                    mode=SearchMode.HYBRID,
                    limit=4,
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                print(f"找到 {len(results)} 个混合搜索结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n  {i}. 文档: {result.title}")
                    print(f"     语义分数: {result.vector_score:.4f}")
                    print(f"     关键词分数: {result.bm25_score:.4f}")
                    print(f"     混合分数: {result.hybrid_score:.4f}")
                    print(f"     内容: {result.content[:80]}...")
                    
                    if result.rerank_score:
                        print(f"     重排序分数: {result.rerank_score:.4f}")
                
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            raise
    
    async def example_06_custom_weights(self):
        """示例6: 自定义搜索权重"""
        print("\n" + "="*60)
        print("示例6: 自定义搜索权重")
        print("="*60)
        
        try:
            query = "机器学习深度学习算法"
            
            # 不同的权重配置
            weight_configs = [
                {"vector_weight": 0.8, "bm25_weight": 0.2, "desc": "偏重语义搜索"},
                {"vector_weight": 0.5, "bm25_weight": 0.5, "desc": "平衡搜索"},
                {"vector_weight": 0.2, "bm25_weight": 0.8, "desc": "偏重关键词搜索"}
            ]
            
            print(f"查询: '{query}'")
            
            for config in weight_configs:
                print(f"\n{config['desc']} (语义:{config['vector_weight']}, 关键词:{config['bm25_weight']}):")
                print("-" * 60)
                
                results = await hybrid_search_service.search(
                    query=query,
                    mode=SearchMode.HYBRID,
                    limit=3,
                    vector_weight=config["vector_weight"],
                    bm25_weight=config["bm25_weight"],
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.title}")
                    print(f"     混合分数: {result.hybrid_score:.4f} "
                          f"(语义:{result.vector_score:.3f}, 关键词:{result.bm25_score:.3f})")
                
        except Exception as e:
            logger.error(f"自定义权重搜索失败: {e}")
            raise
    
    async def example_07_filtered_search(self):
        """示例7: 带过滤条件的搜索"""
        print("\n" + "="*60)
        print("示例7: 带过滤条件的搜索")
        print("="*60)
        
        try:
            query = "artificial intelligence"
            
            # 不同的过滤条件
            filter_configs = [
                {"language": "zh", "desc": "仅中文文档"},
                {"language": "en", "desc": "仅英文文档"},
                {"category": "机器学习", "desc": "仅机器学习类别"},
                {"author": "张三", "desc": "仅特定作者"}
            ]
            
            print(f"查询: '{query}'")
            
            for filter_config in filter_configs:
                filters = {k: v for k, v in filter_config.items() if k != "desc"}
                print(f"\n{filter_config['desc']} - 过滤条件: {filters}")
                print("-" * 50)
                
                results = await hybrid_search_service.search(
                    query=query,
                    mode=SearchMode.HYBRID,
                    limit=5,
                    filters=filters,
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                print(f"找到 {len(results)} 个匹配结果:")
                for result in results:
                    print(f"  - {result.title}")
                    print(f"    语言: {result.metadata.get('language', 'N/A')}, "
                          f"类别: {result.metadata.get('category', 'N/A')}, "
                          f"作者: {result.metadata.get('author', 'N/A')}")
                
        except Exception as e:
            logger.error(f"过滤搜索失败: {e}")
            raise
    
    async def example_08_semantic_search(self):
        """示例8: 语义搜索功能"""
        print("\n" + "="*60)
        print("示例8: 语义搜索功能")
        print("="*60)
        
        try:
            queries = [
                "智能系统的道德问题",  # 应该匹配AI Ethics文档
                "视觉识别技术",        # 应该匹配Computer Vision文档
                "未来计算技术",        # 应该匹配量子计算文档
                "大规模数据处理"       # 应该匹配大数据文档
            ]
            
            for query in queries:
                print(f"\n语义查询: '{query}'")
                print("-" * 50)
                
                results = await hybrid_search_service.semantic_search(
                    query=query,
                    limit=3,
                    similarity_threshold=0.3,  # 降低阈值以获得更多结果
                    collection_name=self.collection_name
                )
                
                print(f"找到 {len(results)} 个语义相关结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n  {i}. 文档: {result.title}")
                    print(f"     语义相似度: {result.vector_score:.4f}")
                    print(f"     内容: {result.content[:100]}...")
                    
                    # 分析为什么匹配
                    if "道德" in query or "ethics" in result.content.lower():
                        print(f"     匹配原因: 道德伦理相关")
                    elif "视觉" in query or "vision" in result.content.lower():
                        print(f"     匹配原因: 视觉技术相关")
                    elif "未来" in query or "量子" in result.content:
                        print(f"     匹配原因: 未来技术相关")
                    elif "数据" in query or "data" in result.content.lower():
                        print(f"     匹配原因: 数据处理相关")
                
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            raise
    
    async def example_09_performance_comparison(self):
        """示例9: 不同搜索模式性能对比"""
        print("\n" + "="*60)
        print("示例9: 不同搜索模式性能对比")
        print("="*60)
        
        try:
            test_queries = [
                "人工智能机器学习",
                "deep learning neural network",
                "数据分析算法",
                "computer vision applications"
            ]
            
            modes = [
                (SearchMode.VECTOR_ONLY, "仅向量搜索"),
                (SearchMode.BM25_ONLY, "仅BM25搜索"),
                (SearchMode.HYBRID, "混合搜索")
            ]
            
            print("性能对比测试:")
            print("-" * 70)
            print(f"{'搜索模式':<15} {'查询数':<8} {'总耗时(秒)':<12} {'平均耗时(毫秒)':<15} {'结果数'}")
            print("-" * 70)
            
            for mode, mode_name in modes:
                start_time = time.time()
                total_results = 0
                
                for query in test_queries:
                    results = await hybrid_search_service.search(
                        query=query,
                        mode=mode,
                        limit=5,
                        collection_name=self.collection_name,
                        index_name=self.index_name
                    )
                    total_results += len(results)
                
                total_time = time.time() - start_time
                avg_time = (total_time / len(test_queries)) * 1000
                
                print(f"{mode_name:<15} {len(test_queries):<8} {total_time:<12.3f} {avg_time:<15.2f} {total_results}")
            
            # 质量对比
            print(f"\n搜索质量对比 (查询: '机器学习算法'):")
            print("-" * 60)
            
            for mode, mode_name in modes:
                results = await hybrid_search_service.search(
                    query="机器学习算法",
                    mode=mode,
                    limit=3,
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                print(f"\n{mode_name}:")
                for i, result in enumerate(results, 1):
                    score = result.vector_score if mode == SearchMode.VECTOR_ONLY else \
                           result.bm25_score if mode == SearchMode.BM25_ONLY else \
                           result.hybrid_score
                    print(f"  {i}. {result.title} (分数: {score:.4f})")
                
        except Exception as e:
            logger.error(f"性能对比失败: {e}")
            raise
    
    async def example_10_search_statistics(self):
        """示例10: 搜索统计信息"""
        print("\n" + "="*60)
        print("示例10: 搜索统计信息")
        print("="*60)
        
        try:
            # 获取混合搜索系统统计信息
            stats = await hybrid_search_service.get_stats()
            
            print("混合搜索系统统计信息:")
            print("=" * 50)
            
            # 向量数据库统计
            if "vector_database" in stats:
                vector_stats = stats["vector_database"]
                print(f"\n向量数据库 (Qdrant):")
                print(f"  总集合数: {vector_stats.get('total_collections', 0)}")
                
                for collection_name, collection_info in vector_stats.get('collections', {}).items():
                    print(f"  集合 '{collection_name}':")
                    print(f"    文档数量: {collection_info.get('points_count', 0)}")
                    print(f"    向量数量: {collection_info.get('vectors_count', 0)}")
                    print(f"    向量维度: {collection_info.get('config', {}).get('vector_size', 'N/A')}")
                    print(f"    距离度量: {collection_info.get('config', {}).get('distance', 'N/A')}")
            
            # Elasticsearch统计
            if "elasticsearch" in stats:
                es_stats = stats["elasticsearch"]
                print(f"\nElasticsearch:")
                if isinstance(es_stats, dict):
                    print(f"  索引名称: {es_stats.get('name', 'N/A')}")
                    print(f"  文档数量: {es_stats.get('docs_count', 'N/A')}")
                    print(f"  存储大小: {es_stats.get('store_size', 'N/A')}")
            
            # 搜索权重配置
            if "search_weights" in stats:
                weights = stats["search_weights"]
                print(f"\n搜索权重配置:")
                print(f"  向量搜索权重: {weights.get('vector_weight', 'N/A')}")
                print(f"  BM25搜索权重: {weights.get('bm25_weight', 'N/A')}")
            
            # 测试权重调整
            print(f"\n测试权重调整:")
            original_weights = (
                stats.get('search_weights', {}).get('vector_weight', 0.6),
                stats.get('search_weights', {}).get('bm25_weight', 0.4)
            )
            
            print(f"原始权重: 向量={original_weights[0]:.2f}, BM25={original_weights[1]:.2f}")
            
            # 调整权重
            hybrid_search_service.set_search_weights(0.7, 0.3)
            print(f"调整后权重: 向量=0.70, BM25=0.30")
            
            # 恢复原始权重
            hybrid_search_service.set_search_weights(original_weights[0], original_weights[1])
            print(f"恢复权重: 向量={original_weights[0]:.2f}, BM25={original_weights[1]:.2f}")
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise
    
    async def example_11_cleanup(self):
        """示例11: 清理资源"""
        print("\n" + "="*60)
        print("示例11: 清理资源")
        print("="*60)
        
        try:
            # 删除测试文档
            document_ids = [doc["id"] for doc in self.sample_documents]
            print(f"删除 {len(document_ids)} 个测试文档...")
            
            success = await hybrid_search_service.delete_documents(
                document_ids,
                collection_name=self.collection_name,
                index_name=self.index_name
            )
            print(f"删除结果: {'成功' if success else '失败'}")
            
            # 关闭服务
            print("关闭混合搜索服务...")
            await hybrid_search_service.close()
            
            print("资源清理完成!")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
            raise


async def run_all_examples():
    """运行所有示例"""
    examples = HybridSearchExamples()
    
    try:
        await examples.example_01_service_initialization()
        await examples.example_02_add_documents()
        await examples.example_03_vector_only_search()
        await examples.example_04_bm25_only_search()
        await examples.example_05_hybrid_search()
        await examples.example_06_custom_weights()
        await examples.example_07_filtered_search()
        await examples.example_08_semantic_search()
        await examples.example_09_performance_comparison()
        await examples.example_10_search_statistics()
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise
    finally:
        await examples.example_11_cleanup()


async def run_specific_example(example_num: int):
    """运行特定示例"""
    examples = HybridSearchExamples()
    
    # 基本设置总是需要的
    await examples.example_01_service_initialization()
    if example_num > 2:
        await examples.example_02_add_documents()
    
    try:
        if example_num == 2:
            await examples.example_02_add_documents()
        elif example_num == 3:
            await examples.example_03_vector_only_search()
        elif example_num == 4:
            await examples.example_04_bm25_only_search()
        elif example_num == 5:
            await examples.example_05_hybrid_search()
        elif example_num == 6:
            await examples.example_06_custom_weights()
        elif example_num == 7:
            await examples.example_07_filtered_search()
        elif example_num == 8:
            await examples.example_08_semantic_search()
        elif example_num == 9:
            await examples.example_09_performance_comparison()
        elif example_num == 10:
            await examples.example_10_search_statistics()
        else:
            print(f"示例 {example_num} 不存在")
            return
            
    finally:
        await examples.example_11_cleanup()


if __name__ == "__main__":
    print("混合搜索服务使用示例")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            print(f"运行示例 {example_num}")
            asyncio.run(run_specific_example(example_num))
        except ValueError:
            print("请提供有效的示例编号 (1-10)")
    else:
        print("运行所有示例...")
        asyncio.run(run_all_examples())