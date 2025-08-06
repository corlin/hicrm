#!/usr/bin/env python3
"""
中文语义搜索服务使用示例

本文件展示如何使用中文语义搜索服务，包括中文文本处理、
同义词扩展、查询意图分析、相似文档查找等功能。
"""

import asyncio
import sys
import os
import logging
import time
from typing import List, Dict, Any
import uuid

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.chinese_semantic_search import chinese_search_service
from src.services.hybrid_search_service import hybrid_search_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChineseSearchExamples:
    """中文语义搜索服务使用示例类"""
    
    def __init__(self):
        self.collection_name = "chinese_search_demo"
        self.index_name = "chinese_search_demo"
        
        # 中文示例文档 (使用UUID格式ID)
        self.chinese_documents = [
            {
                "id": str(uuid.uuid4()),
                "title": "人工智能技术发展现状",
                "content": "人工智能作为新一代信息技术的重要组成部分，正在深刻改变着人类的生产生活方式。当前，人工智能技术在计算机视觉、自然语言处理、机器学习等领域取得了重大突破，为各行各业的数字化转型提供了强有力的技术支撑。",
                "metadata": {
                    "category": "技术发展",
                    "author": "张教授",
                    "tags": ["人工智能", "技术发展", "数字化转型"],
                    "publish_date": "2024-01-15",
                    "doc_name": "zh_001"
                }
            },
            {
                "id": str(uuid.uuid4()), 
                "title": "机器学习算法在金融风控中的应用",
                "content": "随着金融科技的快速发展，机器学习算法在风险控制领域发挥着越来越重要的作用。通过分析海量的交易数据和用户行为数据，机器学习模型能够有效识别潜在的欺诈行为，提高风控系统的准确性和效率。",
                "metadata": {
                    "category": "金融科技",
                    "author": "李分析师",
                    "tags": ["机器学习", "金融风控", "数据分析"],
                    "publish_date": "2024-02-01",
                    "doc_name": "zh_002"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "深度学习在医疗诊断中的突破",
                "content": "深度学习技术在医疗影像诊断领域取得了令人瞩目的成果。卷积神经网络能够准确识别X光片、CT扫描和MRI图像中的异常情况，辅助医生进行疾病诊断。这项技术不仅提高了诊断的准确性，还大大缩短了诊断时间。",
                "metadata": {
                    "category": "医疗健康",
                    "author": "王医生",
                    "tags": ["深度学习", "医疗诊断", "医疗影像"],
                    "publish_date": "2024-02-15",
                    "doc_name": "zh_003"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "自然语言处理技术的最新进展",
                "content": "近年来，自然语言处理技术发展迅速，特别是大型语言模型的出现，使得机器对人类语言的理解能力有了质的飞跃。这些技术在智能客服、机器翻译、文本摘要等应用场景中展现出巨大的潜力。",
                "metadata": {
                    "category": "自然语言处理",
                    "author": "赵研究员",
                    "tags": ["自然语言处理", "大语言模型", "智能客服"],
                    "publish_date": "2024-03-01",
                    "doc_name": "zh_004"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "计算机视觉在智能制造中的应用",
                "content": "计算机视觉技术正在推动制造业的智能化升级。通过机器视觉系统，工厂能够实现产品质量的自动检测、生产流程的智能监控，以及设备故障的预测性维护。这些应用显著提高了生产效率和产品质量。",
                "metadata": {
                    "category": "智能制造",
                    "author": "陈工程师",
                    "tags": ["计算机视觉", "智能制造", "质量检测"],
                    "publish_date": "2024-03-15",
                    "doc_name": "zh_005"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "大数据技术在城市治理中的创新应用",
                "content": "大数据技术为智慧城市建设提供了强有力的支撑。通过整合交通、环境、公安、医疗等各领域的数据，城市管理者能够更好地了解城市运行状况，制定更加科学合理的治理策略，提升城市治理的现代化水平。",
                "metadata": {
                    "category": "智慧城市",
                    "author": "孙主任",
                    "tags": ["大数据", "智慧城市", "城市治理"],
                    "publish_date": "2024-04-01",
                    "doc_name": "zh_006"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "区块链技术在供应链管理中的价值",
                "content": "区块链技术以其去中心化、不可篡改的特性，为供应链管理带来了新的解决方案。通过区块链技术，企业能够实现供应链的全程追溯，提高供应链的透明度和可信度，有效防范供应链风险。",
                "metadata": {
                    "category": "区块链应用",
                    "author": "周总监",
                    "tags": ["区块链", "供应链管理", "可追溯性"],
                    "publish_date": "2024-04-15",
                    "doc_name": "zh_007"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "物联网技术推动农业现代化发展",
                "content": "物联网技术在农业领域的应用日益广泛，智能传感器能够实时监测土壤湿度、温度、光照等环境参数，帮助农民实现精准农业。这种技术不仅提高了农作物的产量和质量，还减少了资源浪费，促进了农业的可持续发展。",
                "metadata": {
                    "category": "智慧农业",
                    "author": "吴专家",
                    "tags": ["物联网", "智慧农业", "精准农业"],
                    "publish_date": "2024-05-01",
                    "doc_name": "zh_008"
                }
            }
        ]
    
    async def example_01_service_initialization(self):
        """示例1: 中文搜索服务初始化"""
        print("\n" + "="*60)
        print("示例1: 中文语义搜索服务初始化")
        print("="*60)
        
        try:
            # 初始化混合搜索服务 (中文搜索服务依赖于此)
            logger.info("初始化混合搜索服务...")
            await hybrid_search_service.initialize()
            
            print("中文语义搜索服务初始化完成!")
            print("服务特性:")
            print("  - 中文文本预处理和分词")
            print("  - 中文停用词过滤")
            print("  - 同义词扩展支持")
            print("  - 中文语义相似度计算")
            print("  - 查询意图分析")
            print("  - 搜索建议生成")
            
            # 显示中文停用词示例
            stopwords_sample = list(chinese_search_service.chinese_stopwords)[:10]
            print(f"\n中文停用词示例: {stopwords_sample}")
            
            # 显示同义词示例
            synonyms_sample = dict(list(chinese_search_service.chinese_synonyms.items())[:3])
            print(f"同义词词典示例: {synonyms_sample}")
            
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            raise
    
    async def example_02_add_chinese_documents(self):
        """示例2: 添加中文文档"""
        print("\n" + "="*60)
        print("示例2: 添加中文文档到搜索系统")
        print("="*60)
        
        try:
            print(f"准备添加 {len(self.chinese_documents)} 个中文文档...")
            
            # 显示部分文档信息
            for i, doc in enumerate(self.chinese_documents[:3], 1):
                print(f"\n文档 {i}:")
                print(f"  ID: {doc['id']}")
                print(f"  标题: {doc['title']}")
                print(f"  内容: {doc['content'][:60]}...")
                print(f"  类别: {doc['metadata']['category']}")
                print(f"  标签: {doc['metadata']['tags']}")
            
            print(f"\n... 还有 {len(self.chinese_documents) - 3} 个文档")
            
            # 添加文档到混合搜索系统
            success = await hybrid_search_service.add_documents(
                self.chinese_documents,
                collection_name=self.collection_name,
                index_name=self.index_name
            )
            
            print(f"\n中文文档添加结果: {'成功' if success else '失败'}")
            
        except Exception as e:
            logger.error(f"添加中文文档失败: {e}")
            raise
    
    async def example_03_chinese_text_processing(self):
        """示例3: 中文文本处理功能"""
        print("\n" + "="*60)
        print("示例3: 中文文本处理功能")
        print("="*60)
        
        try:
            # 测试文本预处理
            test_texts = [
                "  这是一个包含多余空格的文本！！！  ",
                "人工智能、机器学习和深度学习是相关的技术领域。",
                "自然语言处理（NLP）技术发展迅速，应用广泛。",
                "大数据分析在各个行业都有重要应用价值。"
            ]
            
            print("中文文本预处理:")
            print("-" * 50)
            for text in test_texts:
                processed = chinese_search_service._preprocess_chinese_text(text)
                print(f"原文: {text}")
                print(f"处理后: {processed}")
                print()
            
            # 测试关键词提取
            print("中文关键词提取:")
            print("-" * 50)
            for text in test_texts:
                keywords = chinese_search_service._extract_chinese_keywords(text)
                print(f"文本: {text[:30]}...")
                print(f"关键词: {keywords}")
                print()
            
            # 测试同义词扩展
            print("同义词扩展:")
            print("-" * 50)
            test_queries = ["人工智能应用", "机器学习算法", "自然语言处理技术"]
            
            for query in test_queries:
                expanded = chinese_search_service._expand_query_with_synonyms(query)
                print(f"原查询: {query}")
                print(f"扩展查询: {expanded}")
                print()
                
        except Exception as e:
            logger.error(f"中文文本处理失败: {e}")
            raise
    
    async def example_04_chinese_semantic_search(self):
        """示例4: 中文语义搜索"""
        print("\n" + "="*60)
        print("示例4: 中文语义搜索")
        print("="*60)
        
        try:
            # 中文查询测试
            chinese_queries = [
                "人工智能在医疗领域的应用",
                "机器学习风险控制",
                "深度学习图像识别",
                "大数据城市管理",
                "区块链供应链追溯"
            ]
            
            for query in chinese_queries:
                print(f"\n中文查询: '{query}'")
                print("-" * 50)
                
                results = await chinese_search_service.search(
                    query=query,
                    limit=3,
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                print(f"找到 {len(results)} 个相关结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n  {i}. 文档: {result.title}")
                    print(f"     语义分数: {result.semantic_score:.4f}")
                    print(f"     关键词分数: {result.keyword_score:.4f}")
                    print(f"     综合分数: {result.combined_score:.4f}")
                    print(f"     内容: {result.content[:80]}...")
                    
                    # 显示中文特征
                    if result.chinese_features:
                        features = result.chinese_features
                        print(f"     中文特征:")
                        print(f"       关键词重叠: {features.get('keyword_overlap', 0)}")
                        print(f"       中文字符比例: {features.get('chinese_char_ratio', 0):.2f}")
                        print(f"       语义相似度: {features.get('semantic_similarity', 0):.4f}")
                
        except Exception as e:
            logger.error(f"中文语义搜索失败: {e}")
            raise
    
    async def example_05_synonym_expansion_search(self):
        """示例5: 同义词扩展搜索"""
        print("\n" + "="*60)
        print("示例5: 同义词扩展搜索对比")
        print("="*60)
        
        try:
            # 包含同义词的查询
            test_queries = [
                "人工智能技术发展",  # 可扩展为AI、机器智能等
                "机器学习应用",      # 可扩展为ML、自动学习等
                "自然语言处理",      # 可扩展为NLP、语言处理等
            ]
            
            for query in test_queries:
                print(f"\n查询: '{query}'")
                print("=" * 60)
                
                # 不使用同义词扩展
                print("不使用同义词扩展:")
                results_no_expansion = await chinese_search_service.search(
                    query=query,
                    limit=3,
                    use_synonym_expansion=False,
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                for i, result in enumerate(results_no_expansion, 1):
                    print(f"  {i}. {result.title} (分数: {result.combined_score:.4f})")
                
                # 使用同义词扩展
                print("\n使用同义词扩展:")
                results_with_expansion = await chinese_search_service.search(
                    query=query,
                    limit=3,
                    use_synonym_expansion=True,
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                for i, result in enumerate(results_with_expansion, 1):
                    print(f"  {i}. {result.title} (分数: {result.combined_score:.4f})")
                
                # 对比分析
                print(f"\n结果对比:")
                print(f"  无扩展结果数: {len(results_no_expansion)}")
                print(f"  有扩展结果数: {len(results_with_expansion)}")
                
                if results_no_expansion and results_with_expansion:
                    score_diff = results_with_expansion[0].combined_score - results_no_expansion[0].combined_score
                    print(f"  最高分差异: {score_diff:+.4f}")
                
        except Exception as e:
            logger.error(f"同义词扩展搜索失败: {e}")
            raise
    
    async def example_06_custom_weights_search(self):
        """示例6: 自定义权重搜索"""
        print("\n" + "="*60)
        print("示例6: 自定义权重搜索")
        print("="*60)
        
        try:
            query = "深度学习医疗诊断应用"
            
            # 不同权重配置
            weight_configs = [
                {"semantic": 0.8, "keyword": 0.2, "desc": "偏重语义理解"},
                {"semantic": 0.5, "keyword": 0.5, "desc": "平衡搜索"},
                {"semantic": 0.2, "keyword": 0.8, "desc": "偏重关键词匹配"}
            ]
            
            print(f"查询: '{query}'")
            
            for config in weight_configs:
                print(f"\n{config['desc']} (语义:{config['semantic']}, 关键词:{config['keyword']}):")
                print("-" * 60)
                
                results = await chinese_search_service.search(
                    query=query,
                    limit=3,
                    semantic_weight=config["semantic"],
                    keyword_weight=config["keyword"],
                    collection_name=self.collection_name,
                    index_name=self.index_name
                )
                
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.title}")
                    print(f"     语义: {result.semantic_score:.3f}, "
                          f"关键词: {result.keyword_score:.3f}, "
                          f"综合: {result.combined_score:.3f}")
                    
                    # 分析匹配原因
                    if "深度学习" in result.content and "医疗" in result.content:
                        print(f"     匹配: 包含'深度学习'和'医疗'关键词")
                    elif "深度学习" in result.content:
                        print(f"     匹配: 包含'深度学习'关键词")
                    elif "医疗" in result.content:
                        print(f"     匹配: 包含'医疗'关键词")
                    else:
                        print(f"     匹配: 语义相关")
                
        except Exception as e:
            logger.error(f"自定义权重搜索失败: {e}")
            raise
    
    async def example_07_query_intent_analysis(self):
        """示例7: 查询意图分析"""
        print("\n" + "="*60)
        print("示例7: 中文查询意图分析")
        print("="*60)
        
        try:
            # 不同意图的查询
            test_queries = [
                "搜索人工智能相关资料",           # 搜索意图
                "比较机器学习和深度学习的区别",     # 比较意图
                "解释什么是自然语言处理",         # 解释意图
                "推荐最好的大数据分析工具",       # 推荐意图
                "分析区块链技术的发展趋势",       # 分析意图
                "人工智能技术应用"               # 无明确意图
            ]
            
            print("查询意图分析结果:")
            print("-" * 70)
            print(f"{'查询':<25} {'主要意图':<10} {'关键词数':<8} {'中文字符数'}")
            print("-" * 70)
            
            for query in test_queries:
                intent_analysis = await chinese_search_service.analyze_query_intent(query)
                
                primary_intent = intent_analysis.get('primary_intent', 'unknown')
                keywords_count = len(intent_analysis.get('keywords', []))
                chinese_char_count = intent_analysis.get('chinese_char_count', 0)
                
                print(f"{query:<25} {primary_intent:<10} {keywords_count:<8} {chinese_char_count}")
                
                # 显示详细分析
                if intent_analysis.get('intent_scores'):
                    scores = intent_analysis['intent_scores']
                    print(f"  意图分数: {scores}")
                
                keywords = intent_analysis.get('keywords', [])[:5]  # 显示前5个关键词
                if keywords:
                    print(f"  关键词: {keywords}")
                print()
                
        except Exception as e:
            logger.error(f"查询意图分析失败: {e}")
            raise
    
    async def example_08_similar_documents(self):
        """示例8: 相似文档查找"""
        print("\n" + "="*60)
        print("示例8: 相似文档查找")
        print("="*60)
        
        try:
            # 选择一个参考文档
            reference_doc = self.chinese_documents[2]  # 深度学习医疗诊断文档
            
            print(f"参考文档: {reference_doc['title']}")
            print(f"内容: {reference_doc['content'][:100]}...")
            
            # 查找相似文档
            similar_docs = await chinese_search_service.find_similar_documents(
                document_content=reference_doc['content'],
                limit=4,
                similarity_threshold=0.3,
                collection_name=self.collection_name
            )
            
            print(f"\n找到 {len(similar_docs)} 个相似文档:")
            print("-" * 60)
            
            for i, result in enumerate(similar_docs, 1):
                print(f"{i}. 文档: {result.title}")
                print(f"   相似度: {result.semantic_score:.4f}")
                print(f"   内容: {result.content[:80]}...")
                
                # 分析相似性
                if result.chinese_features:
                    features = result.chinese_features
                    overlap_ratio = features.get('keyword_overlap_ratio', 0)
                    semantic_sim = features.get('semantic_similarity', 0)
                    
                    print(f"   关键词重叠率: {overlap_ratio:.3f}")
                    print(f"   语义相似度: {semantic_sim:.3f}")
                    
                    # 相似性分析
                    if overlap_ratio > 0.3:
                        print(f"   相似原因: 关键词重叠度高")
                    elif semantic_sim > 0.7:
                        print(f"   相似原因: 语义高度相关")
                    else:
                        print(f"   相似原因: 主题相关")
                print()
            
            # 测试不同相似度阈值
            print("不同相似度阈值的结果数量:")
            print("-" * 40)
            thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
            
            for threshold in thresholds:
                similar_docs_thresh = await chinese_search_service.find_similar_documents(
                    document_content=reference_doc['content'],
                    limit=10,
                    similarity_threshold=threshold,
                    collection_name=self.collection_name
                )
                print(f"阈值 {threshold}: {len(similar_docs_thresh)} 个文档")
                
        except Exception as e:
            logger.error(f"相似文档查找失败: {e}")
            raise
    
    async def example_09_search_suggestions(self):
        """示例9: 搜索建议生成"""
        print("\n" + "="*60)
        print("示例9: 中文搜索建议生成")
        print("="*60)
        
        try:
            # 部分查询词
            partial_queries = [
                "人工",      # 应该建议"人工智能"
                "机器",      # 应该建议"机器学习"
                "自然语言",   # 应该建议"自然语言处理"
                "深度",      # 应该建议"深度学习"
                "大数",      # 应该建议"大数据"
                "区块",      # 应该建议"区块链"
                "计算机视",   # 应该建议"计算机视觉"
                "智能制"     # 应该建议"智能制造"
            ]
            
            print("搜索建议生成:")
            print("-" * 50)
            print(f"{'部分查询':<15} {'建议'}")
            print("-" * 50)
            
            for partial_query in partial_queries:
                suggestions = await chinese_search_service.get_search_suggestions(
                    partial_query=partial_query,
                    limit=3
                )
                
                suggestions_str = ", ".join(suggestions) if suggestions else "无建议"
                print(f"{partial_query:<15} {suggestions_str}")
            
            # 测试更复杂的建议场景
            print(f"\n复杂建议场景:")
            print("-" * 50)
            
            complex_partials = [
                "AI",        # 英文缩写
                "ML",        # 英文缩写
                "NLP",       # 英文缩写
                "智能",       # 通用词汇
                "学习"        # 通用词汇
            ]
            
            for partial in complex_partials:
                suggestions = await chinese_search_service.get_search_suggestions(
                    partial_query=partial,
                    limit=5
                )
                
                print(f"'{partial}' -> {suggestions}")
                
        except Exception as e:
            logger.error(f"搜索建议生成失败: {e}")
            raise
    
    async def example_10_performance_analysis(self):
        """示例10: 中文搜索性能分析"""
        print("\n" + "="*60)
        print("示例10: 中文搜索性能分析")
        print("="*60)
        
        try:
            # 性能测试查询
            test_queries = [
                "人工智能医疗应用",
                "机器学习金融风控",
                "深度学习图像识别",
                "自然语言处理技术",
                "大数据城市治理"
            ]
            
            print("中文搜索性能测试:")
            print("-" * 60)
            
            # 测试不同配置的性能
            configs = [
                {"expansion": False, "weights": (0.6, 0.4), "desc": "基础搜索"},
                {"expansion": True, "weights": (0.6, 0.4), "desc": "同义词扩展"},
                {"expansion": True, "weights": (0.8, 0.2), "desc": "偏重语义"},
                {"expansion": True, "weights": (0.2, 0.8), "desc": "偏重关键词"}
            ]
            
            for config in configs:
                print(f"\n{config['desc']}:")
                print("-" * 40)
                
                total_time = 0
                total_results = 0
                
                for query in test_queries:
                    start_time = time.time()
                    
                    results = await chinese_search_service.search(
                        query=query,
                        limit=5,
                        use_synonym_expansion=config["expansion"],
                        semantic_weight=config["weights"][0],
                        keyword_weight=config["weights"][1],
                        collection_name=self.collection_name,
                        index_name=self.index_name
                    )
                    
                    search_time = time.time() - start_time
                    total_time += search_time
                    total_results += len(results)
                
                avg_time = (total_time / len(test_queries)) * 1000
                avg_results = total_results / len(test_queries)
                
                print(f"  平均搜索时间: {avg_time:.2f} 毫秒")
                print(f"  平均结果数量: {avg_results:.1f}")
                print(f"  总搜索时间: {total_time:.3f} 秒")
            
            # 质量分析
            print(f"\n搜索质量分析 (查询: '人工智能医疗诊断'):")
            print("-" * 60)
            
            quality_query = "人工智能医疗诊断"
            results = await chinese_search_service.search(
                query=quality_query,
                limit=5,
                use_synonym_expansion=True,
                collection_name=self.collection_name,
                index_name=self.index_name
            )
            
            print(f"查询: '{quality_query}'")
            print(f"结果数量: {len(results)}")
            
            if results:
                print(f"最高分数: {results[0].combined_score:.4f}")
                print(f"最低分数: {results[-1].combined_score:.4f}")
                print(f"平均分数: {sum(r.combined_score for r in results) / len(results):.4f}")
                
                # 分析结果相关性
                relevant_count = 0
                for result in results:
                    if ("人工智能" in result.content or "AI" in result.content) and \
                       ("医疗" in result.content or "诊断" in result.content):
                        relevant_count += 1
                
                relevance_ratio = relevant_count / len(results)
                print(f"相关性比例: {relevance_ratio:.2%}")
                
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
            raise
    
    async def example_11_cleanup(self):
        """示例11: 清理资源"""
        print("\n" + "="*60)
        print("示例11: 清理资源")
        print("="*60)
        
        try:
            # 删除测试文档
            document_ids = [doc["id"] for doc in self.chinese_documents]
            print(f"删除 {len(document_ids)} 个中文测试文档...")
            
            success = await hybrid_search_service.delete_documents(
                document_ids,
                collection_name=self.collection_name,
                index_name=self.index_name
            )
            print(f"删除结果: {'成功' if success else '失败'}")
            
            # 关闭服务
            print("关闭混合搜索服务...")
            await hybrid_search_service.close()
            
            print("中文搜索示例资源清理完成!")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
            raise


async def run_all_examples():
    """运行所有示例"""
    examples = ChineseSearchExamples()
    
    try:
        await examples.example_01_service_initialization()
        await examples.example_02_add_chinese_documents()
        await examples.example_03_chinese_text_processing()
        await examples.example_04_chinese_semantic_search()
        await examples.example_05_synonym_expansion_search()
        await examples.example_06_custom_weights_search()
        await examples.example_07_query_intent_analysis()
        await examples.example_08_similar_documents()
        await examples.example_09_search_suggestions()
        await examples.example_10_performance_analysis()
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise
    finally:
        await examples.example_11_cleanup()


async def run_specific_example(example_num: int):
    """运行特定示例"""
    examples = ChineseSearchExamples()
    
    # 基本设置总是需要的
    await examples.example_01_service_initialization()
    if example_num > 2:
        await examples.example_02_add_chinese_documents()
    
    try:
        if example_num == 2:
            await examples.example_02_add_chinese_documents()
        elif example_num == 3:
            await examples.example_03_chinese_text_processing()
        elif example_num == 4:
            await examples.example_04_chinese_semantic_search()
        elif example_num == 5:
            await examples.example_05_synonym_expansion_search()
        elif example_num == 6:
            await examples.example_06_custom_weights_search()
        elif example_num == 7:
            await examples.example_07_query_intent_analysis()
        elif example_num == 8:
            await examples.example_08_similar_documents()
        elif example_num == 9:
            await examples.example_09_search_suggestions()
        elif example_num == 10:
            await examples.example_10_performance_analysis()
        else:
            print(f"示例 {example_num} 不存在")
            return
            
    finally:
        await examples.example_11_cleanup()


if __name__ == "__main__":
    print("中文语义搜索服务使用示例")
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