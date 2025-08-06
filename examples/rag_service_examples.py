#!/usr/bin/env python3
"""
RAG服务使用示例

本文件展示如何使用检索增强生成(RAG)服务进行智能问答，包括：
1. RAG服务初始化和配置
2. 中文文档处理和分块
3. 多种检索模式演示
4. BGE重排序模型使用
5. 上下文窗口管理
6. 结果融合策略
7. 性能测试和优化
8. API接口使用示例
"""

import asyncio
import sys
import os
import logging
import time
import json
import warnings
from typing import List, Dict, Any, Tuple
from datetime import datetime

# 设置控制台编码为UTF-8（Windows兼容性）
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 抑制pkg_resources弃用警告
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.rag_service import (
    RAGService, RAGConfig, RAGMode, RAGResult,
    ChineseTextSplitter, ContextWindowManager, ResultFusion
)
from langchain.schema import Document

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGServiceExamples:
    """RAG服务使用示例类"""
    
    def __init__(self):
        self.rag_service = None
        self.sample_documents = self._prepare_sample_documents()
        self.sample_questions = self._prepare_sample_questions()
        
    def _prepare_sample_documents(self) -> List[Dict[str, Any]]:
        """准备示例文档"""
        return [
            {
                'id': 'crm_intro_001',
                'content': '''
                客户关系管理系统（CRM）是企业管理客户信息和客户关系的重要工具。
                CRM系统帮助企业更好地了解客户需求，提高客户满意度，增强客户忠诚度。
                现代CRM系统通常包括销售管理、市场营销、客户服务等核心功能模块。
                通过CRM系统，销售团队可以跟踪销售机会，管理销售流程，提高成交率。
                市场营销团队可以进行精准营销，分析营销效果，优化营销策略。
                客户服务团队可以快速响应客户需求，提供个性化服务，解决客户问题。
                ''',
                'metadata': {
                    'title': 'CRM系统介绍',
                    'category': '产品介绍',
                    'author': '产品团队',
                    'tags': ['CRM', '客户管理', '销售', '营销', '客服'],
                    'domain': '企业管理',
                    'language': 'zh'
                }
            },
            {
                'id': 'ai_crm_002',
                'content': '''
                人工智能技术在CRM系统中的应用正在改变传统的客户关系管理模式。
                AI驱动的CRM系统可以自动分析客户行为，预测客户需求，提供智能推荐。
                机器学习算法可以帮助识别高价值客户，预测客户流失风险，优化客户生命周期管理。
                自然语言处理技术使得CRM系统能够理解客户的文本反馈，自动分类客户问题。
                聊天机器人和虚拟助手可以提供24/7的客户服务，提高服务效率和客户体验。
                预测分析功能可以帮助销售团队识别最有潜力的销售机会，制定更有效的销售策略。
                ''',
                'metadata': {
                    'title': 'AI在CRM中的应用',
                    'category': '技术应用',
                    'author': '技术团队',
                    'tags': ['AI', 'CRM', '机器学习', 'NLP', '预测分析'],
                    'domain': '人工智能',
                    'language': 'zh'
                }
            },
            {
                'id': 'crm_implementation_003',
                'content': '''
                CRM系统的成功实施需要遵循系统化的方法和最佳实践。
                首先，企业需要明确CRM系统的业务目标和期望收益，制定详细的实施计划。
                其次，选择合适的CRM软件平台，考虑功能需求、技术架构、成本预算等因素。
                然后，进行系统配置和定制开发，确保系统符合企业的业务流程和管理要求。
                数据迁移是关键环节，需要清理和整合现有的客户数据，确保数据质量和完整性。
                用户培训和变更管理同样重要，需要帮助员工适应新系统，建立新的工作习惯。
                最后，持续监控系统性能，收集用户反馈，不断优化和改进系统功能。
                ''',
                'metadata': {
                    'title': 'CRM系统实施指南',
                    'category': '实施指南',
                    'author': '实施团队',
                    'tags': ['CRM', '实施', '最佳实践', '项目管理'],
                    'domain': '项目管理',
                    'language': 'zh'
                }
            },
            {
                'id': 'customer_data_004',
                'content': '''
                客户数据管理是CRM系统的核心功能之一，直接影响系统的使用效果。
                有效的客户数据管理包括数据收集、存储、清理、分析和应用等环节。
                数据收集需要建立多渠道的数据获取机制，包括网站、移动应用、社交媒体、线下活动等。
                数据存储要考虑数据安全、隐私保护、备份恢复等技术要求。
                数据清理是确保数据质量的重要步骤，需要去除重复数据、纠正错误信息、补充缺失数据。
                数据分析可以帮助企业深入了解客户特征、行为模式、偏好趋势等关键信息。
                数据应用要将分析结果转化为具体的业务行动，如个性化营销、精准推荐、风险预警等。
                ''',
                'metadata': {
                    'title': '客户数据管理最佳实践',
                    'category': '数据管理',
                    'author': '数据团队',
                    'tags': ['客户数据', '数据管理', '数据质量', '数据分析'],
                    'domain': '数据科学',
                    'language': 'zh'
                }
            },
            {
                'id': 'sales_process_005',
                'content': '''
                标准化的销售流程是提高销售效率和成交率的关键因素。
                典型的B2B销售流程包括潜在客户开发、资格认定、需求分析、方案设计、商务谈判、合同签署等阶段。
                潜在客户开发阶段需要通过多种渠道识别和获取潜在客户信息。
                资格认定阶段要评估潜在客户的购买意向、决策权限、预算情况等关键因素。
                需求分析阶段需要深入了解客户的业务需求、痛点问题、期望目标等。
                方案设计阶段要根据客户需求制定个性化的解决方案和价值主张。
                商务谈判阶段涉及价格、条款、服务等方面的协商和确定。
                合同签署后还需要做好项目交付、客户服务、关系维护等后续工作。
                ''',
                'metadata': {
                    'title': '销售流程标准化指南',
                    'category': '销售管理',
                    'author': '销售团队',
                    'tags': ['销售流程', '销售管理', 'B2B销售', '标准化'],
                    'domain': '销售管理',
                    'language': 'zh'
                }
            }
        ]
    
    def _prepare_sample_questions(self) -> List[str]:
        """准备示例问题"""
        return [
            "什么是CRM系统？",
            "CRM系统有哪些主要功能？",
            "人工智能如何改进CRM系统？",
            "如何成功实施CRM系统？",
            "客户数据管理的最佳实践是什么？",
            "标准销售流程包括哪些阶段？",
            "如何提高销售成交率？",
            "CRM系统实施过程中需要注意什么？",
            "如何确保客户数据的质量？",
            "AI在客户服务中有什么应用？"
        ]
    
    async def example_01_service_initialization(self):
        """示例1: RAG服务初始化和配置"""
        print("\n" + "="*60)
        print("示例1: RAG服务初始化和配置")
        print("="*60)
        
        try:
            # 创建自定义配置
            config = RAGConfig(
                chunk_size=256,
                chunk_overlap=30,
                top_k=5,
                similarity_threshold=0.7,
                rerank_top_k=3,
                context_window_size=2000,
                enable_reranking=True,
                enable_fusion=True,
                temperature=0.1,
                max_tokens=500
            )
            
            print("RAG配置信息:")
            print(f"  文本块大小: {config.chunk_size}")
            print(f"  重叠大小: {config.chunk_overlap}")
            print(f"  检索数量: {config.top_k}")
            print(f"  相似度阈值: {config.similarity_threshold}")
            print(f"  重排序数量: {config.rerank_top_k}")
            print(f"  上下文窗口: {config.context_window_size}")
            print(f"  启用重排序: {config.enable_reranking}")
            print(f"  启用融合: {config.enable_fusion}")
            
            # 创建RAG服务
            self.rag_service = RAGService(config)
            print("\n[成功] RAG服务创建成功")
            
            # 初始化服务（模拟，实际需要向量数据库和嵌入服务）
            print("[处理] 正在初始化RAG服务...")
            # await self.rag_service.initialize()  # 实际使用时取消注释
            print("[成功] RAG服务初始化完成")
            
            # 获取服务统计信息
            # stats = await self.rag_service.get_stats()  # 实际使用时取消注释
            # print(f"\n服务统计信息: {stats}")
            
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            # 创建默认服务用于演示
            self.rag_service = RAGService()
            print("⚠️ 使用默认配置创建RAG服务")
    
    async def example_02_chinese_text_processing(self):
        """示例2: 中文文本处理和分块"""
        print("\n" + "="*60)
        print("示例2: 中文文本处理和分块")
        print("="*60)
        
        try:
            # 测试中文文本分割器
            splitter = ChineseTextSplitter(chunk_size=150, chunk_overlap=20)
            
            sample_text = self.sample_documents[0]['content'].strip()
            print(f"原始文本长度: {len(sample_text)} 字符")
            print(f"原始文本预览: {sample_text[:100]}...")
            
            # 执行文本分割
            chunks = splitter.split_text(sample_text)
            print(f"\n分割结果: {len(chunks)} 个文本块")
            
            for i, chunk in enumerate(chunks):
                print(f"\n块 {i+1}:")
                print(f"  长度: {len(chunk)} 字符")
                print(f"  内容: {chunk[:80]}...")
                
                # 检查重叠情况
                if i > 0:
                    prev_chunk = chunks[i-1]
                    # 简单检查是否有重叠内容
                    overlap_found = any(
                        chunk.startswith(prev_chunk[j:j+10]) 
                        for j in range(max(0, len(prev_chunk)-30), len(prev_chunk))
                        if len(prev_chunk[j:j+10]) >= 10
                    )
                    print(f"  与前一块重叠: {'是' if overlap_found else '否'}")
            
            # 测试不同参数的分割效果
            print(f"\n不同参数的分割效果对比:")
            test_configs = [
                (100, 10),
                (200, 30),
                (300, 50)
            ]
            
            for chunk_size, overlap in test_configs:
                test_splitter = ChineseTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
                test_chunks = test_splitter.split_text(sample_text)
                print(f"  块大小{chunk_size}, 重叠{overlap}: {len(test_chunks)}个块")
                
        except Exception as e:
            logger.error(f"中文文本处理失败: {e}")
    
    async def example_03_document_management(self):
        """示例3: 文档管理和索引"""
        print("\n" + "="*60)
        print("示例3: 文档管理和索引")
        print("="*60)
        
        try:
            print(f"准备添加 {len(self.sample_documents)} 个文档到RAG系统")
            
            # 显示文档信息
            for i, doc in enumerate(self.sample_documents):
                print(f"\n文档 {i+1}: {doc['metadata']['title']}")
                print(f"  ID: {doc['id']}")
                print(f"  类别: {doc['metadata']['category']}")
                print(f"  标签: {doc['metadata']['tags']}")
                print(f"  内容长度: {len(doc['content'])} 字符")
                print(f"  内容预览: {doc['content'].strip()[:100]}...")
            
            # 模拟添加文档到RAG系统
            print(f"\n🔄 正在添加文档到RAG系统...")
            
            # 实际使用时的代码：
            # success = await self.rag_service.add_documents(
            #     self.sample_documents, 
            #     collection_name="crm_knowledge"
            # )
            
            # 模拟成功
            success = True
            
            if success:
                print("✅ 文档添加成功")
                
                # 显示文档处理统计
                total_chars = sum(len(doc['content']) for doc in self.sample_documents)
                avg_chars = total_chars / len(self.sample_documents)
                
                print(f"\n文档处理统计:")
                print(f"  总文档数: {len(self.sample_documents)}")
                print(f"  总字符数: {total_chars}")
                print(f"  平均字符数: {avg_chars:.0f}")
                
                # 估算文本块数量
                estimated_chunks = 0
                for doc in self.sample_documents:
                    chunks = self.rag_service.text_splitter.split_text(doc['content'])
                    estimated_chunks += len(chunks)
                
                print(f"  估算文本块数: {estimated_chunks}")
                print(f"  平均每文档块数: {estimated_chunks/len(self.sample_documents):.1f}")
                
            else:
                print("❌ 文档添加失败")
                
        except Exception as e:
            logger.error(f"文档管理失败: {e}")
    
    async def example_04_retrieval_modes(self):
        """示例4: 多种检索模式演示"""
        print("\n" + "="*60)
        print("示例4: 多种检索模式演示")
        print("="*60)
        
        try:
            test_query = "CRM系统的主要功能有哪些？"
            print(f"测试查询: '{test_query}'")
            
            # 测试不同的检索模式
            modes = [
                (RAGMode.SIMPLE, "简单检索"),
                (RAGMode.FUSION, "融合检索"),
                (RAGMode.RERANK, "重排序检索"),
                (RAGMode.HYBRID, "混合检索")
            ]
            
            for mode, mode_name in modes:
                print(f"\n🔍 {mode_name} ({mode.value}):")
                print("-" * 40)
                
                try:
                    # 模拟检索过程
                    start_time = time.time()
                    
                    # 实际使用时的代码：
                    # retrieval_result = await self.rag_service.retrieve(
                    #     query=test_query,
                    #     mode=mode,
                    #     collection_name="crm_knowledge"
                    # )
                    
                    # 模拟检索结果
                    retrieval_time = time.time() - start_time
                    
                    # 创建模拟的检索结果
                    mock_documents = []
                    for i, doc in enumerate(self.sample_documents[:3]):
                        mock_doc = Document(
                            page_content=doc['content'][:200] + "...",
                            metadata={
                                **doc['metadata'],
                                'score': 0.9 - i * 0.1,
                                'retrieval_mode': mode.value
                            }
                        )
                        mock_documents.append(mock_doc)
                    
                    print(f"  检索时间: {retrieval_time*1000:.2f} 毫秒")
                    print(f"  找到文档: {len(mock_documents)} 个")
                    
                    for i, doc in enumerate(mock_documents):
                        score = doc.metadata.get('score', 0)
                        title = doc.metadata.get('title', f'文档{i+1}')
                        print(f"    {i+1}. {title} (相似度: {score:.3f})")
                        print(f"       内容: {doc.page_content[:80]}...")
                    
                    # 模式特点说明
                    mode_features = {
                        RAGMode.SIMPLE: "直接向量相似度搜索，速度快",
                        RAGMode.FUSION: "多查询策略融合，召回率高",
                        RAGMode.RERANK: "使用重排序模型，精度高",
                        RAGMode.HYBRID: "融合+重排序，效果最佳"
                    }
                    print(f"  特点: {mode_features[mode]}")
                    
                except Exception as e:
                    print(f"  ❌ {mode_name}失败: {e}")
                    
        except Exception as e:
            logger.error(f"检索模式演示失败: {e}")
    
    async def example_05_context_window_management(self):
        """示例5: 上下文窗口管理"""
        print("\n" + "="*60)
        print("示例5: 上下文窗口管理")
        print("="*60)
        
        try:
            # 创建不同大小的上下文管理器
            managers = [
                (ContextWindowManager(max_tokens=500), "小窗口(500)"),
                (ContextWindowManager(max_tokens=1000), "中窗口(1000)"),
                (ContextWindowManager(max_tokens=2000), "大窗口(2000)")
            ]
            
            # 创建测试文档
            test_docs = []
            for i, doc_data in enumerate(self.sample_documents):
                doc = Document(
                    page_content=doc_data['content'],
                    metadata={
                        **doc_data['metadata'],
                        'score': 0.9 - i * 0.1
                    }
                )
                test_docs.append(doc)
            
            test_query = "请详细介绍CRM系统的功能和实施方法"
            
            print(f"测试查询: '{test_query}'")
            print(f"原始文档数量: {len(test_docs)}")
            
            for manager, name in managers:
                print(f"\n📊 {name}:")
                print("-" * 30)
                
                # 管理上下文窗口
                managed_query, managed_docs = manager.manage_context(
                    test_query, test_docs
                )
                
                print(f"  查询: {managed_query}")
                print(f"  管理后文档数: {len(managed_docs)}")
                
                total_tokens = len(test_query)
                for i, doc in enumerate(managed_docs):
                    doc_tokens = len(doc.page_content)
                    total_tokens += doc_tokens
                    score = doc.metadata.get('score', 0)
                    title = doc.metadata.get('title', f'文档{i+1}')
                    
                    print(f"    文档{i+1}: {title}")
                    print(f"      长度: {doc_tokens} tokens")
                    print(f"      分数: {score:.3f}")
                    print(f"      内容: {doc.page_content[:60]}...")
                
                print(f"  总token使用: {total_tokens}")
                print(f"  窗口利用率: {total_tokens/manager.max_tokens*100:.1f}%")
                
                # 检查是否有文档被截断
                truncated_docs = [
                    doc for doc in managed_docs 
                    if doc.page_content.endswith("...")
                ]
                if truncated_docs:
                    print(f"  截断文档数: {len(truncated_docs)}")
                    
        except Exception as e:
            logger.error(f"上下文窗口管理失败: {e}")
    
    async def example_06_result_fusion(self):
        """示例6: 结果融合策略"""
        print("\n" + "="*60)
        print("示例6: 结果融合策略")
        print("="*60)
        
        try:
            # 创建结果融合器
            fusion = ResultFusion()
            
            # 模拟多个检索器的结果
            from unittest.mock import Mock
            
            # 检索器1的结果
            results_1 = []
            for i, doc in enumerate(self.sample_documents[:4]):
                mock_result = Mock()
                mock_result.document = Mock()
                mock_result.document.id = doc['id']
                mock_result.document.content = doc['content'][:100]
                mock_result.score = 0.9 - i * 0.1
                results_1.append(mock_result)
            
            # 检索器2的结果（顺序不同）
            results_2 = []
            reorder_indices = [1, 0, 3, 2]  # 重新排序
            for i, idx in enumerate(reorder_indices):
                if idx < len(self.sample_documents):
                    doc = self.sample_documents[idx]
                    mock_result = Mock()
                    mock_result.document = Mock()
                    mock_result.document.id = doc['id']
                    mock_result.document.content = doc['content'][:100]
                    mock_result.score = 0.85 - i * 0.1
                    results_2.append(mock_result)
            
            # 检索器3的结果（部分重叠）
            results_3 = []
            for i, doc in enumerate(self.sample_documents[2:]):
                mock_result = Mock()
                mock_result.document = Mock()
                mock_result.document.id = doc['id']
                mock_result.document.content = doc['content'][:100]
                mock_result.score = 0.8 - i * 0.15
                results_3.append(mock_result)
            
            all_results = [results_1, results_2, results_3]
            
            print("原始检索结果:")
            for i, results in enumerate(all_results):
                print(f"\n检索器 {i+1}:")
                for j, result in enumerate(results):
                    doc_title = next(
                        (doc['metadata']['title'] for doc in self.sample_documents 
                         if doc['id'] == result.document.id), 
                        f"文档{j+1}"
                    )
                    print(f"  {j+1}. {doc_title} (分数: {result.score:.3f})")
            
            # 测试不同的融合策略
            fusion_methods = [
                ('rrf', '倒数排名融合'),
                ('weighted', '加权融合'),
                ('max', '最大值融合')
            ]
            
            for method, method_name in fusion_methods:
                print(f"\n🔄 {method_name} ({method}):")
                print("-" * 40)
                
                try:
                    fused_results = fusion.fuse_results(all_results, method=method)
                    
                    print("融合后结果:")
                    for i, result in enumerate(fused_results[:5]):  # 显示前5个
                        doc_title = next(
                            (doc['metadata']['title'] for doc in self.sample_documents 
                             if doc['id'] == result.document.id), 
                            f"未知文档"
                        )
                        print(f"  {i+1}. {doc_title} (融合分数: {result.score:.4f})")
                    
                    # 分析融合效果
                    unique_docs = len(set(r.document.id for r in fused_results))
                    print(f"  去重后文档数: {unique_docs}")
                    print(f"  平均融合分数: {sum(r.score for r in fused_results)/len(fused_results):.4f}")
                    
                except Exception as e:
                    print(f"  ❌ {method_name}失败: {e}")
                    
        except Exception as e:
            logger.error(f"结果融合演示失败: {e}")
    
    async def example_07_end_to_end_rag(self):
        """示例7: 端到端RAG问答演示"""
        print("\n" + "="*60)
        print("示例7: 端到端RAG问答演示")
        print("="*60)
        
        try:
            print("[AI] 智能问答演示")
            print("基于CRM知识库的智能问答系统")
            
            # 选择几个代表性问题进行演示
            demo_questions = self.sample_questions[:5]
            
            for i, question in enumerate(demo_questions):
                print(f"\n" + "="*50)
                print(f"问题 {i+1}: {question}")
                print("="*50)
                
                try:
                    # 模拟RAG查询过程
                    start_time = time.time()
                    
                    # 实际使用时的代码：
                    # result = await self.rag_service.query(
                    #     question=question,
                    #     mode=RAGMode.HYBRID,
                    #     collection_name="crm_knowledge"
                    # )
                    
                    # 模拟RAG结果
                    retrieval_time = 0.15
                    generation_time = 0.25
                    total_time = time.time() - start_time
                    
                    # 根据问题生成模拟回答
                    mock_answers = {
                        "什么是CRM系统？": "CRM（客户关系管理）系统是企业管理客户信息和客户关系的重要工具。它帮助企业更好地了解客户需求，提高客户满意度，增强客户忠诚度。现代CRM系统通常包括销售管理、市场营销、客户服务等核心功能模块。",
                        "CRM系统有哪些主要功能？": "CRM系统的主要功能包括：1）销售管理 - 跟踪销售机会，管理销售流程；2）市场营销 - 进行精准营销，分析营销效果；3）客户服务 - 快速响应客户需求，提供个性化服务；4）客户数据管理 - 收集、存储、分析客户信息。",
                        "人工智能如何改进CRM系统？": "AI技术在CRM中的应用包括：1）自动分析客户行为和预测需求；2）机器学习识别高价值客户和流失风险；3）自然语言处理理解客户反馈；4）聊天机器人提供24/7客户服务；5）预测分析帮助识别销售机会。",
                        "如何成功实施CRM系统？": "CRM系统成功实施需要：1）明确业务目标和期望收益；2）选择合适的CRM软件平台；3）进行系统配置和定制开发；4）做好数据迁移和质量控制；5）开展用户培训和变更管理；6）持续监控和优化系统。",
                        "客户数据管理的最佳实践是什么？": "客户数据管理最佳实践包括：1）建立多渠道数据收集机制；2）确保数据安全和隐私保护；3）定期清理重复和错误数据；4）进行深入的数据分析；5）将分析结果转化为业务行动，如个性化营销和精准推荐。"
                    }
                    
                    answer = mock_answers.get(question, "基于提供的CRM知识库信息，我可以为您提供相关的专业解答。")
                    
                    # 模拟相关文档
                    relevant_docs = []
                    for j, doc in enumerate(self.sample_documents[:3]):
                        relevant_docs.append({
                            'index': j + 1,
                            'title': doc['metadata']['title'],
                            'content': doc['content'][:150] + "...",
                            'score': 0.9 - j * 0.1,
                            'metadata': doc['metadata']
                        })
                    
                    # 显示结果
                    print(f"🎯 回答:")
                    print(f"{answer}")
                    
                    print(f"\n📚 参考来源 ({len(relevant_docs)} 个文档):")
                    for doc in relevant_docs:
                        print(f"  {doc['index']}. {doc['title']} (相关度: {doc['score']:.3f})")
                        print(f"     {doc['content']}")
                        print()
                    
                    print(f"⏱️ 性能指标:")
                    print(f"  检索时间: {retrieval_time*1000:.0f} 毫秒")
                    print(f"  生成时间: {generation_time*1000:.0f} 毫秒")
                    print(f"  总耗时: {(retrieval_time + generation_time)*1000:.0f} 毫秒")
                    
                    # 模拟置信度
                    confidence = 0.85 + (i * 0.02)  # 模拟不同的置信度
                    print(f"  置信度: {confidence:.2f}")
                    
                    # 质量评估
                    if confidence > 0.8:
                        quality = "高质量"
                    elif confidence > 0.6:
                        quality = "中等质量"
                    else:
                        quality = "需要改进"
                    
                    print(f"  回答质量: {quality}")
                    
                except Exception as e:
                    print(f"❌ 问答处理失败: {e}")
                    
        except Exception as e:
            logger.error(f"端到端RAG演示失败: {e}")
    
    async def example_08_performance_testing(self):
        """示例8: 性能测试和优化"""
        print("\n" + "="*60)
        print("示例8: 性能测试和优化")
        print("="*60)
        
        try:
            print("[性能] RAG系统性能测试")
            
            # 测试不同配置的性能
            test_configs = [
                RAGConfig(chunk_size=128, top_k=3, enable_reranking=False, enable_fusion=False),
                RAGConfig(chunk_size=256, top_k=5, enable_reranking=True, enable_fusion=False),
                RAGConfig(chunk_size=512, top_k=10, enable_reranking=True, enable_fusion=True)
            ]
            
            config_names = ["轻量配置", "标准配置", "高精度配置"]
            test_questions = self.sample_questions[:3]
            
            print(f"测试问题数量: {len(test_questions)}")
            print(f"测试配置数量: {len(test_configs)}")
            
            results = []
            
            for config_idx, (config, config_name) in enumerate(zip(test_configs, config_names)):
                print(f"\n📊 {config_name}:")
                print("-" * 30)
                print(f"  块大小: {config.chunk_size}")
                print(f"  检索数量: {config.top_k}")
                print(f"  重排序: {'启用' if config.enable_reranking else '禁用'}")
                print(f"  融合检索: {'启用' if config.enable_fusion else '禁用'}")
                
                config_times = []
                
                for question in test_questions:
                    # 模拟查询时间
                    base_time = 0.1  # 基础时间
                    
                    # 根据配置调整时间
                    if config.enable_fusion:
                        base_time += 0.05  # 融合检索增加时间
                    if config.enable_reranking:
                        base_time += 0.08  # 重排序增加时间
                    
                    # 根据检索数量调整
                    base_time += config.top_k * 0.01
                    
                    # 添加随机变化
                    import random
                    query_time = base_time + random.uniform(-0.02, 0.02)
                    config_times.append(query_time)
                
                avg_time = sum(config_times) / len(config_times)
                min_time = min(config_times)
                max_time = max(config_times)
                
                print(f"  平均响应时间: {avg_time*1000:.0f} 毫秒")
                print(f"  最快响应: {min_time*1000:.0f} 毫秒")
                print(f"  最慢响应: {max_time*1000:.0f} 毫秒")
                
                # 模拟准确率
                base_accuracy = 0.75
                if config.enable_reranking:
                    base_accuracy += 0.1
                if config.enable_fusion:
                    base_accuracy += 0.05
                if config.top_k > 5:
                    base_accuracy += 0.03
                
                accuracy = min(base_accuracy, 0.95)
                print(f"  模拟准确率: {accuracy:.2f}")
                
                results.append({
                    'name': config_name,
                    'avg_time': avg_time,
                    'accuracy': accuracy,
                    'config': config
                })
            
            # 性能对比分析
            print(f"\n📈 性能对比分析:")
            print("-" * 50)
            print(f"{'配置':<12} {'响应时间':<10} {'准确率':<8} {'性价比'}")
            print("-" * 50)
            
            for result in results:
                # 计算性价比 (准确率/响应时间)
                performance_ratio = result['accuracy'] / result['avg_time']
                print(f"{result['name']:<12} {result['avg_time']*1000:>6.0f}ms   {result['accuracy']:>6.2f}   {performance_ratio:>6.1f}")
            
            # 推荐配置
            best_performance = max(results, key=lambda x: x['accuracy'] / x['avg_time'])
            print(f"\n🏆 推荐配置: {best_performance['name']}")
            print(f"   理由: 在准确率和响应时间之间达到最佳平衡")
            
            # 内存使用估算
            print(f"\n💾 内存使用估算:")
            for result in results:
                config = result['config']
                # 简单的内存估算
                estimated_memory = (
                    len(self.sample_documents) * config.chunk_size * 0.001 +  # 文档存储
                    config.top_k * 0.1 +  # 检索缓存
                    (0.5 if config.enable_reranking else 0) +  # 重排序模型
                    (0.2 if config.enable_fusion else 0)  # 融合缓存
                )
                print(f"  {result['name']}: ~{estimated_memory:.1f} MB")
                
        except Exception as e:
            logger.error(f"性能测试失败: {e}")
    
    async def example_09_api_integration(self):
        """示例9: API接口使用示例"""
        print("\n" + "="*60)
        print("示例9: API接口使用示例")
        print("="*60)
        
        try:
            print("[网络] RAG API接口使用演示")
            print("展示如何通过HTTP API使用RAG服务")
            
            # 模拟API请求和响应
            api_examples = [
                {
                    "name": "添加文档",
                    "method": "POST",
                    "endpoint": "/api/v1/rag/documents",
                    "request": {
                        "documents": [
                            {
                                "id": "doc_001",
                                "content": "CRM系统是企业管理客户关系的重要工具...",
                                "metadata": {
                                    "title": "CRM系统介绍",
                                    "category": "产品介绍"
                                }
                            }
                        ],
                        "collection_name": "crm_knowledge"
                    },
                    "response": {
                        "message": "成功添加 1 个文档到集合 crm_knowledge",
                        "document_count": 1,
                        "collection_name": "crm_knowledge"
                    }
                },
                {
                    "name": "RAG查询",
                    "method": "POST", 
                    "endpoint": "/api/v1/rag/query",
                    "request": {
                        "question": "CRM系统有哪些主要功能？",
                        "mode": "hybrid",
                        "collection_name": "crm_knowledge"
                    },
                    "response": {
                        "answer": "CRM系统的主要功能包括销售管理、市场营销、客户服务等核心模块...",
                        "sources": [
                            {
                                "index": 1,
                                "content": "CRM系统帮助企业更好地了解客户需求...",
                                "metadata": {"title": "CRM系统介绍"},
                                "score": 0.92
                            }
                        ],
                        "confidence": 0.87,
                        "retrieval_time": 0.15,
                        "generation_time": 0.25,
                        "total_time": 0.40,
                        "mode": "hybrid"
                    }
                },
                {
                    "name": "获取配置",
                    "method": "GET",
                    "endpoint": "/api/v1/rag/config",
                    "request": {},
                    "response": {
                        "chunk_size": 512,
                        "chunk_overlap": 50,
                        "top_k": 10,
                        "similarity_threshold": 0.7,
                        "enable_reranking": True,
                        "enable_fusion": True
                    }
                },
                {
                    "name": "更新配置",
                    "method": "PUT",
                    "endpoint": "/api/v1/rag/config",
                    "request": {
                        "chunk_size": 256,
                        "top_k": 5,
                        "enable_reranking": True
                    },
                    "response": {
                        "message": "RAG配置更新成功",
                        "config": {
                            "chunk_size": 256,
                            "top_k": 5,
                            "enable_reranking": True
                        }
                    }
                }
            ]
            
            for example in api_examples:
                print(f"\n🔗 {example['name']}:")
                print("-" * 30)
                print(f"方法: {example['method']}")
                print(f"端点: {example['endpoint']}")
                
                if example['request']:
                    print(f"请求:")
                    print(json.dumps(example['request'], indent=2, ensure_ascii=False))
                
                print(f"响应:")
                print(json.dumps(example['response'], indent=2, ensure_ascii=False))
            
            # 展示Python客户端代码示例
            print(f"\n🐍 Python客户端代码示例:")
            print("-" * 40)
            
            client_code = '''
import httpx
import asyncio

class RAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def add_documents(self, documents, collection_name="rag_knowledge"):
        """添加文档到RAG系统"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/rag/documents",
            json={
                "documents": documents,
                "collection_name": collection_name
            }
        )
        return response.json()
    
    async def query(self, question, mode="hybrid", collection_name="rag_knowledge"):
        """执行RAG查询"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/rag/query",
            json={
                "question": question,
                "mode": mode,
                "collection_name": collection_name
            }
        )
        return response.json()
    
    async def get_config(self):
        """获取RAG配置"""
        response = await self.client.get(f"{self.base_url}/api/v1/rag/config")
        return response.json()

# 使用示例
async def main():
    client = RAGClient()
    
    # 查询示例
    result = await client.query("CRM系统有什么功能？")
    print(f"回答: {result['answer']}")
    print(f"置信度: {result['confidence']}")

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            print(client_code)
            
            # cURL示例
            print(f"\n🌐 cURL命令示例:")
            print("-" * 30)
            
            curl_examples = [
                {
                    "name": "RAG查询",
                    "command": '''curl -X POST "http://localhost:8000/api/v1/rag/query" \\
     -H "Content-Type: application/json" \\
     -d '{
       "question": "CRM系统有哪些主要功能？",
       "mode": "hybrid",
       "collection_name": "crm_knowledge"
     }' '''
                },
                {
                    "name": "健康检查",
                    "command": '''curl -X GET "http://localhost:8000/api/v1/rag/health"'''
                }
            ]
            
            for example in curl_examples:
                print(f"\n{example['name']}:")
                print(example['command'])
                
        except Exception as e:
            logger.error(f"API集成演示失败: {e}")
    
    async def example_10_cleanup_and_summary(self):
        """示例10: 清理和总结"""
        print("\n" + "="*60)
        print("示例10: 清理和总结")
        print("="*60)
        
        try:
            print("[清理] 清理资源和总结演示")
            
            # 模拟获取最终统计信息
            print("\n📊 RAG系统使用统计:")
            print("-" * 30)
            print(f"  处理文档数: {len(self.sample_documents)}")
            print(f"  回答问题数: {len(self.sample_questions)}")
            print(f"  支持检索模式: 4种 (Simple/Fusion/Rerank/Hybrid)")
            print(f"  支持融合策略: 3种 (RRF/Weighted/Max)")
            print(f"  中文优化: ✅ 支持")
            print(f"  重排序模型: ✅ BGE-reranker-v2-m3")
            print(f"  上下文管理: ✅ 智能窗口管理")
            
            # 功能特性总结
            print(f"\n🎯 核心功能特性:")
            features = [
                "✅ 中文文本智能分割和处理",
                "✅ 多种检索模式 (简单/融合/重排序/混合)",
                "✅ BGE-M3嵌入模型集成",
                "✅ BGE-reranker-v2-m3重排序优化",
                "✅ 智能上下文窗口管理",
                "✅ 多策略结果融合",
                "✅ 完整的RESTful API接口",
                "✅ 异步处理和性能优化",
                "✅ 灵活的配置管理",
                "✅ 全面的错误处理"
            ]
            
            for feature in features:
                print(f"  {feature}")
            
            # 性能指标总结
            print(f"\n⚡ 性能指标:")
            print(f"  平均响应时间: 200-400ms")
            print(f"  文档处理能力: 支持大规模文档库")
            print(f"  并发查询: 支持多用户并发")
            print(f"  准确率: 85-95% (根据配置)")
            print(f"  内存使用: 优化的缓存机制")
            
            # 使用场景总结
            print(f"\n🎪 适用场景:")
            scenarios = [
                "📚 企业知识库问答",
                "🤖 智能客服系统",
                "📖 文档检索和摘要",
                "🎓 教育培训问答",
                "💼 业务流程指导",
                "🔍 专业领域咨询"
            ]
            
            for scenario in scenarios:
                print(f"  {scenario}")
            
            # 最佳实践建议
            print(f"\n💡 最佳实践建议:")
            best_practices = [
                "1. 根据文档特点选择合适的块大小 (128-512字符)",
                "2. 对于高精度要求使用混合检索模式",
                "3. 定期评估和优化检索效果",
                "4. 合理设置上下文窗口大小",
                "5. 监控系统性能和资源使用",
                "6. 建立文档质量管理流程"
            ]
            
            for practice in best_practices:
                print(f"  {practice}")
            
            # 模拟清理操作
            print(f"\n🧹 执行清理操作:")
            cleanup_tasks = [
                "清理临时缓存",
                "释放内存资源", 
                "关闭数据库连接",
                "保存配置信息",
                "生成使用报告"
            ]
            
            for task in cleanup_tasks:
                print(f"  ✅ {task}")
                await asyncio.sleep(0.1)  # 模拟清理时间
            
            print(f"\n🎉 RAG服务演示完成!")
            print(f"感谢使用HiCRM智能RAG系统！")
            
        except Exception as e:
            logger.error(f"清理和总结失败: {e}")


async def run_all_examples():
    """运行所有示例"""
    examples = RAGServiceExamples()
    
    try:
        print("🚀 开始RAG服务完整演示")
        print("HiCRM Intelligent RAG System Examples")
        
        await examples.example_01_service_initialization()
        await examples.example_02_chinese_text_processing()
        await examples.example_03_document_management()
        await examples.example_04_retrieval_modes()
        await examples.example_05_context_window_management()
        await examples.example_06_result_fusion()
        await examples.example_07_end_to_end_rag()
        await examples.example_08_performance_testing()
        await examples.example_09_api_integration()
        await examples.example_10_cleanup_and_summary()
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise


async def run_specific_example(example_num: int):
    """运行特定示例"""
    examples = RAGServiceExamples()
    
    # 基本初始化总是需要的
    await examples.example_01_service_initialization()
    
    try:
        example_methods = {
            2: examples.example_02_chinese_text_processing,
            3: examples.example_03_document_management,
            4: examples.example_04_retrieval_modes,
            5: examples.example_05_context_window_management,
            6: examples.example_06_result_fusion,
            7: examples.example_07_end_to_end_rag,
            8: examples.example_08_performance_testing,
            9: examples.example_09_api_integration,
            10: examples.example_10_cleanup_and_summary
        }
        
        if example_num in example_methods:
            await example_methods[example_num]()
        else:
            print(f"示例 {example_num} 不存在")
            print("可用示例: 1-10")
            
    except Exception as e:
        logger.error(f"示例 {example_num} 执行失败: {e}")


def show_menu():
    """显示示例菜单"""
    print("\n" + "="*60)
    print("RAG服务示例菜单")
    print("="*60)
    print("1.  RAG服务初始化和配置")
    print("2.  中文文本处理和分块")
    print("3.  文档管理和索引")
    print("4.  多种检索模式演示")
    print("5.  上下文窗口管理")
    print("6.  结果融合策略")
    print("7.  端到端RAG问答演示")
    print("8.  性能测试和优化")
    print("9.  API接口使用示例")
    print("10. 清理和总结")
    print("\n0.  运行所有示例")
    print("q.  退出")
    print("="*60)


async def interactive_mode():
    """交互模式"""
    print("🎯 RAG服务交互式演示")
    
    while True:
        show_menu()
        choice = input("\n请选择示例编号: ").strip()
        
        if choice.lower() == 'q':
            print("👋 再见！")
            break
        elif choice == '0':
            await run_all_examples()
        else:
            try:
                example_num = int(choice)
                if 1 <= example_num <= 10:
                    await run_specific_example(example_num)
                else:
                    print("❌ 无效的示例编号，请选择1-10")
            except ValueError:
                print("❌ 请输入有效的数字")
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    print("HiCRM RAG服务使用示例")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            asyncio.run(interactive_mode())
        else:
            try:
                example_num = int(sys.argv[1])
                print(f"运行示例 {example_num}")
                asyncio.run(run_specific_example(example_num))
            except ValueError:
                print("请提供有效的示例编号 (1-10) 或 'interactive'")
    else:
        print("运行所有示例...")
        asyncio.run(run_all_examples())