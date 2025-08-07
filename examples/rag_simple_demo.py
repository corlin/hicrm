#!/usr/bin/env python3
"""
RAG服务简化演示

这是一个简化的RAG服务演示程序，专门用于快速验证RAG功能，
避免外部依赖问题，适合功能测试和演示。
"""

import asyncio
import sys
import os
import time
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Unicode utilities for safe output
from src.utils.unicode_utils import SafeOutput

# Mock classes for demo purposes to avoid external dependencies
class RAGMode:
    SIMPLE = "simple"
    FUSION = "fusion"
    RERANK = "rerank"
    HYBRID = "hybrid"

class RAGConfig:
    def __init__(self, chunk_size=100, top_k=3, enable_reranking=False, enable_fusion=False):
        self.chunk_size = chunk_size
        self.top_k = top_k
        self.enable_reranking = enable_reranking
        self.enable_fusion = enable_fusion

class RAGService:
    def __init__(self, config):
        self.config = config

class ChineseTextSplitter:
    def __init__(self, chunk_size=100, chunk_overlap=0):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text):
        # Simple text splitting for demo
        sentences = text.split('。')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if sentence.strip():
                if len(current_chunk + sentence) < self.chunk_size:
                    current_chunk += sentence + "。"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]

class ContextWindowManager:
    def __init__(self, max_tokens=200):
        self.max_tokens = max_tokens

class ResultFusion:
    def __init__(self):
        self.fusion_methods = ["rrf", "weighted", "linear"]


class SimpleRAGDemo:
    """简化的RAG演示类"""
    
    def __init__(self):
        # Initialize safe output utility with proper encoding setup
        self.safe_output = SafeOutput(auto_setup=True)
        self.demo_data = self._prepare_demo_data()
        
    def _prepare_demo_data(self) -> Dict[str, Any]:
        """准备演示数据"""
        return {
            'documents': [
                {
                    'id': 'crm_001',
                    'content': 'CRM系统是客户关系管理系统，帮助企业管理客户信息，提高销售效率，改善客户服务质量。',
                    'metadata': {'title': 'CRM基础介绍', 'category': '基础知识'}
                },
                {
                    'id': 'ai_002', 
                    'content': '人工智能在CRM中的应用包括智能客服、销售预测、客户行为分析等，可以大幅提升业务效率。',
                    'metadata': {'title': 'AI在CRM中的应用', 'category': '技术应用'}
                },
                {
                    'id': 'sales_003',
                    'content': '销售流程标准化包括潜客开发、需求分析、方案设计、商务谈判、合同签署等关键步骤。',
                    'metadata': {'title': '销售流程管理', 'category': '业务流程'}
                }
            ],
            'questions': [
                '什么是CRM系统？',
                'AI如何改进CRM？',
                '销售流程有哪些步骤？'
            ]
        }
    
    async def run_demo(self):
        """运行完整演示"""
        self.safe_output.safe_print("[启动] RAG服务简化演示")
        self.safe_output.safe_print("=" * 50)
        
        try:
            # 1. 基础功能测试
            await self.test_basic_components()
            
            # 2. 文本处理测试
            await self.test_text_processing()
            
            # 3. 检索模式测试
            await self.test_retrieval_modes()
            
            # 4. 端到端演示
            await self.test_end_to_end()
            
            self.safe_output.safe_print("\n" + self.safe_output.format_status("success", "所有演示完成！"))
            
        except Exception as e:
            self.safe_output.safe_print(self.safe_output.format_status("error", f"演示失败: {e}"))
            raise
    
    async def test_basic_components(self):
        """测试基础组件"""
        self.safe_output.safe_print("\n[组件] 1. 基础组件测试")
        self.safe_output.safe_print("-" * 30)
        
        # 测试RAG配置
        config = RAGConfig(
            chunk_size=100,
            top_k=3,
            enable_reranking=False,
            enable_fusion=False
        )
        self.safe_output.safe_print(f"[成功] RAG配置创建: 块大小={config.chunk_size}, 检索数={config.top_k}")
        
        # 测试RAG服务
        service = RAGService(config)
        self.safe_output.safe_print(self.safe_output.format_status("success", "RAG服务创建: 配置加载成功"))
        
        # 测试文本分割器
        splitter = ChineseTextSplitter(chunk_size=50)
        test_text = "这是第一句。这是第二句。这是第三句。"
        chunks = splitter.split_text(test_text)
        self.safe_output.safe_print(self.safe_output.format_status("success", f"文本分割器: {len(chunks)}个块"))
        
        # 测试上下文管理器
        manager = ContextWindowManager(max_tokens=200)
        self.safe_output.safe_print(self.safe_output.format_status("success", f"上下文管理器: 最大{manager.max_tokens}tokens"))
        
        # 测试结果融合器
        fusion = ResultFusion()
        self.safe_output.safe_print(self.safe_output.format_status("success", f"结果融合器: 支持{len(fusion.fusion_methods)}种融合方法"))
    
    async def test_text_processing(self):
        """测试文本处理"""
        self.safe_output.safe_print("\n" + self.safe_output.format_section("2. 文本处理测试", 2))
        
        splitter = ChineseTextSplitter(chunk_size=80, chunk_overlap=10)
        
        for i, doc in enumerate(self.demo_data['documents']):
            content = doc['content']
            chunks = splitter.split_text(content)
            
            self.safe_output.safe_print(f"\n文档 {i+1}: {doc['metadata']['title']}")
            self.safe_output.safe_print(f"  原文长度: {len(content)} 字符")
            self.safe_output.safe_print(f"  分割结果: {len(chunks)} 个块")
            
            for j, chunk in enumerate(chunks):
                self.safe_output.safe_print(f"    块{j+1}: {chunk[:30]}...")
    
    async def test_retrieval_modes(self):
        """测试检索模式"""
        self.safe_output.safe_print("\n" + self.safe_output.format_section("3. 检索模式测试", 2))
        
        modes = [
            (RAGMode.SIMPLE, "简单检索"),
            (RAGMode.FUSION, "融合检索"),
            (RAGMode.RERANK, "重排序检索"),
            (RAGMode.HYBRID, "混合检索")
        ]
        
        query = "CRM系统的功能"
        
        for mode, mode_name in modes:
            # Use a target symbol for mode indication
            target_symbol = "🎯" if self.safe_output.unicode_supported else "[TARGET]"
            self.safe_output.safe_print(f"\n{target_symbol} {mode_name} ({mode}):")
            
            # 模拟检索过程
            start_time = time.time()
            
            # 这里模拟不同模式的特点
            if mode == RAGMode.SIMPLE:
                result_count = 3
                avg_score = 0.75
            elif mode == RAGMode.FUSION:
                result_count = 4
                avg_score = 0.80
            elif mode == RAGMode.RERANK:
                result_count = 3
                avg_score = 0.85
            else:  # HYBRID
                result_count = 5
                avg_score = 0.88
            
            process_time = time.time() - start_time
            
            self.safe_output.safe_print(f"  查询: '{query}'")
            self.safe_output.safe_print(f"  结果数: {result_count}")
            self.safe_output.safe_print(f"  平均分数: {avg_score:.2f}")
            self.safe_output.safe_print(f"  处理时间: {process_time*1000:.1f}ms")
            
            # 模拟结果
            for i in range(min(result_count, len(self.demo_data['documents']))):
                doc = self.demo_data['documents'][i]
                score = avg_score - i * 0.05
                self.safe_output.safe_print(f"    {i+1}. {doc['metadata']['title']} (分数: {score:.2f})")
    
    async def test_end_to_end(self):
        """测试端到端流程"""
        # Use robot symbol for end-to-end testing
        robot_symbol = "🤖" if self.safe_output.unicode_supported else "[BOT]"
        self.safe_output.safe_print(f"\n{robot_symbol} 4. 端到端问答演示")
        self.safe_output.safe_print("-" * 30)
        
        # 模拟RAG问答流程
        for i, question in enumerate(self.demo_data['questions']):
            self.safe_output.safe_print(f"\n问题 {i+1}: {question}")
            self.safe_output.safe_print("-" * 25)
            
            # 模拟检索阶段
            search_symbol = "🔍" if self.safe_output.unicode_supported else "[SEARCH]"
            self.safe_output.safe_print(f"{search_symbol} 检索阶段:")
            retrieval_time = 0.12 + i * 0.02
            
            # 根据问题匹配相关文档
            relevant_docs = []
            for doc in self.demo_data['documents']:
                # 简单的关键词匹配
                if self._is_relevant(question, doc['content']):
                    relevant_docs.append(doc)
            
            self.safe_output.safe_print(f"  检索时间: {retrieval_time*1000:.0f}ms")
            self.safe_output.safe_print(f"  找到文档: {len(relevant_docs)}个")
            
            for j, doc in enumerate(relevant_docs[:2]):
                self.safe_output.safe_print(f"    {j+1}. {doc['metadata']['title']}")
            
            # 模拟生成阶段
            thinking_symbol = "💭" if self.safe_output.unicode_supported else "[THINKING]"
            self.safe_output.safe_print(f"\n{thinking_symbol} 生成阶段:")
            generation_time = 0.25 + i * 0.03
            
            # 生成模拟回答
            answers = {
                '什么是CRM系统？': 'CRM系统是客户关系管理系统，主要用于管理客户信息，提高销售效率和客户服务质量。',
                'AI如何改进CRM？': 'AI可以通过智能客服、销售预测、客户行为分析等方式改进CRM系统，大幅提升业务效率。',
                '销售流程有哪些步骤？': '标准销售流程包括潜客开发、需求分析、方案设计、商务谈判、合同签署等关键步骤。'
            }
            
            answer = answers.get(question, '基于检索到的信息，我可以为您提供相关回答。')
            
            self.safe_output.safe_print(f"  生成时间: {generation_time*1000:.0f}ms")
            self.safe_output.safe_print(f"  总耗时: {(retrieval_time + generation_time)*1000:.0f}ms")
            
            lightbulb_symbol = "💡" if self.safe_output.unicode_supported else "[IDEA]"
            self.safe_output.safe_print(f"\n{lightbulb_symbol} 回答:")
            self.safe_output.safe_print(f"  {answer}")
            
            # 计算置信度
            confidence = 0.85 + (len(relevant_docs) * 0.05)
            confidence = min(confidence, 0.95)
            
            chart_symbol = "📊" if self.safe_output.unicode_supported else "[STATS]"
            self.safe_output.safe_print(f"\n{chart_symbol} 质量指标:")
            self.safe_output.safe_print(f"  置信度: {confidence:.2f}")
            self.safe_output.safe_print(f"  相关文档: {len(relevant_docs)}个")
            
            if confidence > 0.8:
                quality = "高质量"
            elif confidence > 0.6:
                quality = "中等质量"
            else:
                quality = "需要改进"
            
            self.safe_output.safe_print(f"  回答质量: {quality}")
    
    def _is_relevant(self, question: str, content: str) -> bool:
        """简单的相关性判断"""
        question_lower = question.lower()
        content_lower = content.lower()
        
        # 关键词匹配
        keywords_map = {
            'crm': ['crm', '客户关系', '客户管理'],
            'ai': ['ai', '人工智能', '智能'],
            '销售': ['销售', '流程', '步骤']
        }
        
        for key, keywords in keywords_map.items():
            if any(kw in question_lower for kw in keywords):
                if any(kw in content_lower for kw in keywords):
                    return True
        
        return False
    
    async def run_performance_test(self):
        """运行性能测试"""
        lightning_symbol = "⚡" if self.safe_output.unicode_supported else "[FAST]"
        self.safe_output.safe_print(f"\n{lightning_symbol} 性能测试")
        self.safe_output.safe_print("-" * 30)
        
        # 测试不同配置的性能
        configs = [
            RAGConfig(chunk_size=100, top_k=3, enable_reranking=False),
            RAGConfig(chunk_size=200, top_k=5, enable_reranking=True),
            RAGConfig(chunk_size=300, top_k=10, enable_reranking=True, enable_fusion=True)
        ]
        
        config_names = ["轻量级", "标准", "高精度"]
        
        for config, name in zip(configs, config_names):
            chart_symbol = "📊" if self.safe_output.unicode_supported else "[STATS]"
            self.safe_output.safe_print(f"\n{chart_symbol} {name}配置:")
            
            # 模拟性能指标
            base_time = 0.1
            if config.enable_fusion:
                base_time += 0.05
            if config.enable_reranking:
                base_time += 0.08
            base_time += config.top_k * 0.01
            
            accuracy = 0.75
            if config.enable_reranking:
                accuracy += 0.1
            if config.enable_fusion:
                accuracy += 0.05
            
            self.safe_output.safe_print(f"  响应时间: {base_time*1000:.0f}ms")
            self.safe_output.safe_print(f"  准确率: {accuracy:.2f}")
            self.safe_output.safe_print(f"  内存使用: ~{config.chunk_size * 0.01:.1f}MB")
    
    async def run_interactive_demo(self):
        """运行交互式演示"""
        target_symbol = "🎯" if self.safe_output.unicode_supported else "[TARGET]"
        self.safe_output.safe_print(f"\n{target_symbol} 交互式问答演示")
        self.safe_output.safe_print("-" * 30)
        self.safe_output.safe_print("输入问题进行测试，输入 'quit' 退出")
        
        while True:
            try:
                question_symbol = "❓" if self.safe_output.unicode_supported else "[?]"
                question = input(f"\n{question_symbol} 请输入问题: ").strip()
                
                if question.lower() in ['quit', 'exit', '退出']:
                    wave_symbol = "👋" if self.safe_output.unicode_supported else "[BYE]"
                    self.safe_output.safe_print(f"{wave_symbol} 演示结束！")
                    break
                
                if not question:
                    continue
                
                search_symbol = "🔍" if self.safe_output.unicode_supported else "[SEARCH]"
                self.safe_output.safe_print(f"\n{search_symbol} 正在处理问题: '{question}'")
                
                # 模拟处理过程
                await asyncio.sleep(0.2)  # 模拟检索时间
                
                # 简单的回答生成
                if 'crm' in question.lower() or '客户' in question:
                    answer = "CRM系统是企业管理客户关系的重要工具，可以帮助提高销售效率和客户满意度。"
                elif 'ai' in question.lower() or '人工智能' in question:
                    answer = "人工智能技术可以通过自动化、预测分析等方式显著改进CRM系统的功能和效率。"
                elif '销售' in question:
                    answer = "销售流程的标准化对于提高成交率和管理效率非常重要，包括多个关键环节。"
                else:
                    answer = f"关于'{question}'的问题，我会基于知识库为您提供相关信息。"
                
                lightbulb_symbol = "💡" if self.safe_output.unicode_supported else "[IDEA]"
                self.safe_output.safe_print(f"{lightbulb_symbol} 回答: {answer}")
                
                clock_symbol = "⏱️" if self.safe_output.unicode_supported else "[TIME]"
                self.safe_output.safe_print(f"{clock_symbol} 处理时间: 200ms")
                
                chart_symbol = "📊" if self.safe_output.unicode_supported else "[STATS]"
                self.safe_output.safe_print(f"{chart_symbol} 置信度: 0.82")
                
            except KeyboardInterrupt:
                wave_symbol = "👋" if self.safe_output.unicode_supported else "[BYE]"
                self.safe_output.safe_print(f"\n{wave_symbol} 演示结束！")
                break
            except Exception as e:
                self.safe_output.safe_print(self.safe_output.format_status("error", f"处理错误: {e}"))


async def main():
    """主函数"""
    # Initialize safe output for main function
    safe_output = SafeOutput(auto_setup=True)
    demo = SimpleRAGDemo()
    
    safe_output.safe_print("欢迎使用RAG服务简化演示！")
    safe_output.safe_print("本演示展示RAG系统的核心功能，无需外部依赖。")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'performance':
            await demo.run_performance_test()
        elif mode == 'interactive':
            await demo.run_interactive_demo()
        elif mode == 'basic':
            await demo.test_basic_components()
        else:
            safe_output.safe_print(f"未知模式: {mode}")
            safe_output.safe_print("可用模式: basic, performance, interactive")
    else:
        # 运行完整演示
        await demo.run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Initialize safe output for exception handling
        safe_output = SafeOutput(auto_setup=True)
        wave_symbol = "👋" if safe_output.unicode_supported else "[BYE]"
        safe_output.safe_print(f"\n{wave_symbol} 演示被用户中断")
    except Exception as e:
        # Initialize safe output for exception handling
        safe_output = SafeOutput(auto_setup=True)
        safe_output.safe_print(safe_output.format_status("error", f"演示失败: {e}"))
        sys.exit(1)