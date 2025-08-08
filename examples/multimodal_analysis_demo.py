#!/usr/bin/env python3
"""
多模态数据分析能力完整示例程序

这个示例展示了如何使用对话式CRM系统的多模态数据分析功能，
包括语音识别、行为分析、高价值客户识别和数据融合等核心能力。

运行方式:
    python examples/multimodal_analysis_demo.py

功能演示:
1. 语音识别和文本转换
2. 客户行为数据分析
3. 高价值客户自动识别
4. 多模态数据融合分析
5. 端到端分析管道
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入多模态分析相关模块
from src.services.speech_recognition_service import SpeechRecognitionService
from src.services.behavior_analysis_service import BehaviorAnalysisService
from src.services.high_value_customer_service import HighValueCustomerService
from src.services.multimodal_fusion_service import MultimodalFusionService

from src.models.multimodal import (
    DataModalityType, VoiceAnalysisResult, BehaviorData, 
    MultimodalAnalysisRequest, HighValueCustomerProfile
)

class MultimodalAnalysisDemo:
    """多模态数据分析演示类"""
    
    def __init__(self):
        """初始化演示环境"""
        print("🚀 初始化多模态数据分析演示环境...")
        
        # 初始化各个服务
        self.speech_service = SpeechRecognitionService()
        self.behavior_service = BehaviorAnalysisService()
        self.high_value_service = HighValueCustomerService()
        self.fusion_service = MultimodalFusionService()
        
        print("✅ 所有服务初始化完成\n")
    
    def print_section(self, title: str):
        """打印章节标题"""
        print(f"\n{'='*60}")
        print(f"📊 {title}")
        print(f"{'='*60}")
    
    def print_subsection(self, title: str):
        """打印子章节标题"""
        print(f"\n🔹 {title}")
        print("-" * 40)
    
    async def demo_speech_recognition(self):
        """演示语音识别和文本转换功能"""
        self.print_section("1. 语音识别和文本转换演示")
        
        # 模拟不同类型的音频数据
        audio_samples = [
            {
                'name': '产品咨询',
                'data': b'product_inquiry_audio_data' * 50,
                'format': 'wav',
                'description': '客户询问产品功能的语音'
            },
            {
                'name': '价格询问',
                'data': b'price_inquiry_audio_data' * 80,
                'format': 'mp3', 
                'description': '客户询问价格和预算的语音'
            },
            {
                'name': '技术支持',
                'data': b'technical_support_audio_data' * 120,
                'format': 'flac',
                'description': '客户寻求技术支持的语音'
            }
        ]
        
        results = []
        for sample in audio_samples:
            self.print_subsection(f"处理 {sample['name']} 语音")
            
            try:
                # 执行语音识别
                result = await self.speech_service.transcribe_audio(
                    sample['data'], 
                    format=sample['format']
                )
                
                results.append(result)
                
                # 显示分析结果
                print(f"📝 转录文本: {result.transcript}")
                print(f"🎯 置信度: {result.confidence:.2f}")
                print(f"😊 情感分析: {result.sentiment} ({result.emotion})")
                print(f"🗣️  语速: {result.speaking_rate:.1f} 词/分钟")
                print(f"🔑 关键词: {', '.join(result.keywords)}")
                print(f"💡 意图识别: {result.intent or '未识别'}")
                
            except Exception as e:
                print(f"❌ 处理失败: {str(e)}")
        
        # 演示批量处理
        self.print_subsection("批量语音识别演示")
        batch_results = await self.speech_service.batch_transcribe(audio_samples)
        print(f"✅ 批量处理完成，共处理 {len(batch_results)} 个音频文件")
        
        return results
    
    async def demo_behavior_analysis(self):
        """演示客户行为数据分析功能"""
        self.print_section("2. 客户行为数据分析演示")
        
        # 创建模拟的客户行为数据
        customer_id = "demo_customer_001"
        behavior_data = self._create_sample_behavior_data(customer_id)
        
        self.print_subsection("客户行为数据概览")
        print(f"👤 客户ID: {customer_id}")
        print(f"📊 会话数量: {len(behavior_data)}")
        print(f"📅 数据时间范围: {min(d.timestamp for d in behavior_data).strftime('%Y-%m-%d')} 到 {max(d.timestamp for d in behavior_data).strftime('%Y-%m-%d')}")
        
        # 执行行为分析
        self.print_subsection("执行多维度行为分析")
        analysis_result = await self.behavior_service.analyze_customer_behavior(
            customer_id, behavior_data
        )
        
        # 显示分析结果
        self.print_subsection("参与度指标")
        engagement = analysis_result['engagement_metrics']
        print(f"📈 平均参与度评分: {engagement.get('average_engagement_score', 0):.2f}")
        print(f"👀 总页面浏览量: {engagement.get('total_page_views', 0)}")
        print(f"🖱️  总点击次数: {engagement.get('total_clicks', 0)}")
        print(f"⏱️  平均会话时长: {engagement.get('average_session_duration', 0):.1f} 秒")
        print(f"📉 跳出率: {engagement.get('bounce_rate', 0):.1%}")
        
        self.print_subsection("行为模式分析")
        profile = analysis_result['behavior_profile']
        print(f"🏆 客户类型: {profile.get('customer_type', 'unknown')}")
        print(f"⭐ 综合评分: {profile.get('overall_score', 0):.2f}")
        print(f"📊 参与水平: {profile.get('engagement_level', 'unknown')}")
        print(f"🎯 兴趣点: {', '.join(profile.get('interests', []))}")
        
        self.print_subsection("转化分析")
        conversion = analysis_result['conversion_metrics']
        print(f"💰 转化率: {conversion.get('conversion_rate', 0):.1%}")
        print(f"🎯 转化事件数: {conversion.get('total_conversion_events', 0)}")
        print(f"⚡ 转化速度: {conversion.get('conversion_velocity', 0):.1f} 小时")
        
        self.print_subsection("智能推荐")
        recommendations = analysis_result.get('recommendations', [])
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"{i}. {rec}")
        
        return analysis_result
    
    async def demo_high_value_customer_identification(self):
        """演示高价值客户自动识别功能"""
        self.print_section("3. 高价值客户自动识别演示")
        
        # 准备测试数据
        customer_data = self._create_sample_customer_data()
        behavior_data = self._create_sample_behavior_data_for_hv()
        voice_data = self._create_sample_voice_data()
        
        self.print_subsection("输入数据概览")
        print(f"👥 客户数量: {len(customer_data)}")
        print(f"📊 行为数据点: {len(behavior_data)}")
        print(f"🎤 语音数据点: {len(voice_data)}")
        
        # 执行高价值客户识别
        self.print_subsection("执行高价值客户识别算法")
        high_value_profiles = await self.high_value_service.identify_high_value_customers(
            customer_data, behavior_data, voice_data
        )
        
        # 显示识别结果
        self.print_subsection("高价值客户识别结果")
        print(f"🎯 识别出 {len(high_value_profiles)} 个高价值客户")
        
        for i, profile in enumerate(high_value_profiles[:3], 1):
            print(f"\n🏆 高价值客户 #{i}")
            print(f"   客户ID: {profile.customer_id}")
            print(f"   综合评分: {profile.overall_score:.2f}")
            print(f"   预测价值: {profile.predicted_value:.2f}")
            print(f"   价值指标数: {len(profile.value_indicators)}")
            print(f"   风险因素: {len(profile.risk_factors)} 个")
            print(f"   机会点: {len(profile.opportunities)} 个")
            print(f"   推荐行动: {len(profile.recommended_actions)} 项")
            
            # 显示前3个推荐行动
            if profile.recommended_actions:
                print("   🎯 主要推荐行动:")
                for j, action in enumerate(profile.recommended_actions[:3], 1):
                    print(f"      {j}. {action}")
        
        return high_value_profiles
    
    async def demo_multimodal_fusion(self):
        """演示多模态数据融合和分析管道"""
        self.print_section("4. 多模态数据融合分析演示")
        
        # 创建多模态分析请求
        customer_id = "fusion_demo_customer"
        
        analysis_requests = [
            {
                'type': 'high_value_identification',
                'description': '高价值客户识别分析'
            },
            {
                'type': 'behavior_pattern_analysis', 
                'description': '行为模式分析'
            },
            {
                'type': 'sentiment_analysis',
                'description': '情感分析'
            },
            {
                'type': 'engagement_analysis',
                'description': '参与度分析'
            }
        ]
        
        results = []
        
        for req_info in analysis_requests:
            self.print_subsection(f"执行 {req_info['description']}")
            
            # 创建分析请求
            request = MultimodalAnalysisRequest(
                customer_id=customer_id,
                analysis_type=req_info['type'],
                modalities=[
                    DataModalityType.TEXT,
                    DataModalityType.VOICE, 
                    DataModalityType.BEHAVIOR,
                    DataModalityType.INTERACTION
                ],
                time_range={
                    'start': datetime.now() - timedelta(days=30),
                    'end': datetime.now()
                },
                parameters={'detailed_analysis': True}
            )
            
            # 执行分析
            result = await self.fusion_service.process_multimodal_analysis(request)
            results.append(result)
            
            # 显示结果
            print(f"✅ 分析完成")
            print(f"   🎯 置信度: {result.confidence:.2f}")
            print(f"   ⏱️  处理时间: {result.processing_time:.3f} 秒")
            print(f"   💡 推荐建议: {len(result.recommendations)} 条")
            
            # 显示具体分析结果
            if result.results:
                print("   📊 分析结果:")
                for key, value in list(result.results.items())[:3]:
                    if isinstance(value, (int, float)):
                        print(f"      {key}: {value:.2f}")
                    elif isinstance(value, str):
                        print(f"      {key}: {value}")
                    elif isinstance(value, list) and len(value) <= 3:
                        print(f"      {key}: {', '.join(map(str, value))}")
        
        return results
    
    async def demo_end_to_end_pipeline(self):
        """演示端到端分析管道"""
        self.print_section("5. 端到端多模态分析管道演示")
        
        # 模拟真实业务场景
        customers = [
            "enterprise_client_001",
            "startup_client_002", 
            "medium_business_003"
        ]
        
        self.print_subsection("批量客户分析")
        print(f"🎯 分析目标: {len(customers)} 个客户")
        print(f"📊 分析类型: 高价值客户识别")
        
        # 执行批量分析
        start_time = datetime.now()
        batch_results = await self.fusion_service.batch_process_customers(
            customers, "high_value_identification"
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # 显示批量处理结果
        self.print_subsection("批量处理结果")
        print(f"✅ 处理完成")
        print(f"⏱️  总处理时间: {processing_time:.2f} 秒")
        print(f"📊 成功处理: {len(batch_results)}/{len(customers)} 个客户")
        print(f"⚡ 平均处理速度: {processing_time/len(customers):.2f} 秒/客户")
        
        # 分析结果统计
        if batch_results:
            confidences = [result.confidence for result in batch_results.values()]
            avg_confidence = sum(confidences) / len(confidences)
            
            print(f"🎯 平均置信度: {avg_confidence:.2f}")
            
            # 按置信度排序显示结果
            sorted_results = sorted(
                batch_results.items(), 
                key=lambda x: x[1].confidence, 
                reverse=True
            )
            
            print("\n🏆 客户价值排名:")
            for i, (customer_id, result) in enumerate(sorted_results, 1):
                value_score = result.results.get('value_score', 0)
                value_level = result.results.get('value_level', 'unknown')
                print(f"   {i}. {customer_id}: {value_score:.2f} ({value_level})")
        
        return batch_results
    
    async def demo_performance_analysis(self):
        """演示性能分析"""
        self.print_section("6. 性能分析演示")
        
        # 测试并发处理能力
        self.print_subsection("并发处理性能测试")
        
        concurrent_customers = [f"perf_test_customer_{i}" for i in range(10)]
        
        start_time = datetime.now()
        
        # 创建并发任务
        tasks = []
        for customer_id in concurrent_customers:
            request = MultimodalAnalysisRequest(
                customer_id=customer_id,
                analysis_type="high_value_identification",
                modalities=[DataModalityType.BEHAVIOR, DataModalityType.TEXT],
                time_range={
                    'start': datetime.now() - timedelta(days=7),
                    'end': datetime.now()
                }
            )
            tasks.append(self.fusion_service.process_multimodal_analysis(request))
        
        # 执行并发分析
        concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        concurrent_time = (end_time - start_time).total_seconds()
        successful_results = [r for r in concurrent_results if not isinstance(r, Exception)]
        
        print(f"✅ 并发处理完成")
        print(f"⏱️  总时间: {concurrent_time:.2f} 秒")
        print(f"📊 成功率: {len(successful_results)}/{len(concurrent_customers)} ({len(successful_results)/len(concurrent_customers)*100:.1f}%)")
        print(f"⚡ 并发吞吐量: {len(successful_results)/concurrent_time:.1f} 请求/秒")
        
        return successful_results
    
    def _create_sample_behavior_data(self, customer_id: str) -> List[BehaviorData]:
        """创建示例行为数据"""
        behavior_data = []
        
        # 模拟一周的用户行为
        for day in range(7):
            timestamp = datetime.now() - timedelta(days=day)
            
            behavior_data.append(BehaviorData(
                customer_id=customer_id,
                session_id=f"session_{customer_id}_{day}",
                page_views=[
                    {"url": "/products", "timestamp": timestamp, "duration": 120 + day * 10},
                    {"url": "/pricing", "timestamp": timestamp, "duration": 180 + day * 15},
                    {"url": "/features", "timestamp": timestamp, "duration": 90 + day * 5},
                    {"url": "/demo", "timestamp": timestamp, "duration": 300 + day * 20}
                ],
                click_events=[
                    {"element": "demo_button", "timestamp": timestamp},
                    {"element": "pricing_link", "timestamp": timestamp},
                    {"element": "contact_form", "timestamp": timestamp}
                ],
                time_spent={
                    "/products": 120.0 + day * 10,
                    "/pricing": 180.0 + day * 15,
                    "/features": 90.0 + day * 5,
                    "/demo": 300.0 + day * 20
                },
                interaction_patterns={
                    "scroll_depth": 0.8 + day * 0.02,
                    "click_through_rate": 0.7 + day * 0.03,
                    "form_completion": day % 2 == 0
                },
                engagement_score=0.75 + day * 0.03,
                conversion_indicators=["demo_request", "contact_form"] if day < 3 else ["page_view"],
                timestamp=timestamp
            ))
        
        return behavior_data
    
    def _create_sample_customer_data(self) -> List[Dict[str, Any]]:
        """创建示例客户数据"""
        return [
            {
                'id': 'customer_001',
                'name': 'TechCorp Solutions',
                'size': 'large',
                'industry': 'technology',
                'status': 'qualified',
                'location': {'city': '北京'},
                'founded_year': 2015
            },
            {
                'id': 'customer_002', 
                'name': 'StartupX Inc',
                'size': 'small',
                'industry': 'fintech',
                'status': 'prospect',
                'location': {'city': '上海'},
                'founded_year': 2020
            },
            {
                'id': 'customer_003',
                'name': 'Manufacturing Plus',
                'size': 'medium',
                'industry': 'manufacturing',
                'status': 'customer',
                'location': {'city': '深圳'},
                'founded_year': 2010
            }
        ]
    
    def _create_sample_behavior_data_for_hv(self) -> List[BehaviorData]:
        """为高价值客户识别创建示例行为数据"""
        behavior_data = []
        
        customers = ['customer_001', 'customer_002', 'customer_003']
        
        for customer_id in customers:
            for session in range(3):
                behavior_data.append(BehaviorData(
                    customer_id=customer_id,
                    session_id=f"session_{customer_id}_{session}",
                    page_views=[
                        {"url": "/products", "duration": 150},
                        {"url": "/pricing", "duration": 200},
                        {"url": "/enterprise", "duration": 180}
                    ],
                    click_events=[
                        {"element": "enterprise_demo"},
                        {"element": "contact_sales"}
                    ],
                    time_spent={"/products": 150.0, "/pricing": 200.0, "/enterprise": 180.0},
                    interaction_patterns={"scroll_depth": 0.9, "engagement_rate": 0.85},
                    engagement_score=0.8 + session * 0.05,
                    conversion_indicators=["enterprise_demo", "contact_sales"],
                    timestamp=datetime.now() - timedelta(days=session)
                ))
        
        return behavior_data
    
    def _create_sample_voice_data(self) -> List[VoiceAnalysisResult]:
        """创建示例语音数据"""
        return [
            VoiceAnalysisResult(
                transcript="我们对企业级CRM解决方案很感兴趣，希望了解更多细节",
                confidence=0.95,
                sentiment="positive",
                emotion="interested",
                speaking_rate=125.0,
                pause_frequency=0.12,
                voice_quality={"clarity": 0.9, "volume": 0.8, "pitch_stability": 0.85},
                keywords=["企业级", "CRM", "解决方案", "感兴趣"],
                intent="product_inquiry"
            ),
            VoiceAnalysisResult(
                transcript="我们公司有500名员工，需要一个能够扩展的系统",
                confidence=0.92,
                sentiment="neutral",
                emotion="business_focused",
                speaking_rate=118.0,
                pause_frequency=0.15,
                voice_quality={"clarity": 0.88, "volume": 0.75, "pitch_stability": 0.82},
                keywords=["公司", "员工", "扩展", "系统"],
                intent="requirement_specification"
            ),
            VoiceAnalysisResult(
                transcript="价格方面我们的预算大概在100万左右",
                confidence=0.89,
                sentiment="neutral",
                emotion="cautious",
                speaking_rate=110.0,
                pause_frequency=0.18,
                voice_quality={"clarity": 0.85, "volume": 0.78, "pitch_stability": 0.80},
                keywords=["价格", "预算", "100万"],
                intent="price_inquiry"
            )
        ]
    
    async def run_complete_demo(self):
        """运行完整演示"""
        print("🎯 多模态数据分析能力完整演示")
        print("=" * 60)
        print("本演示将展示对话式CRM系统的多模态数据分析核心功能")
        print("包括语音识别、行为分析、高价值客户识别和数据融合等")
        print()
        
        try:
            # 1. 语音识别演示
            await self.demo_speech_recognition()
            
            # 2. 行为分析演示  
            await self.demo_behavior_analysis()
            
            # 3. 高价值客户识别演示
            await self.demo_high_value_customer_identification()
            
            # 4. 多模态融合演示
            await self.demo_multimodal_fusion()
            
            # 5. 端到端管道演示
            await self.demo_end_to_end_pipeline()
            
            # 6. 性能分析演示
            await self.demo_performance_analysis()
            
            # 总结
            self.print_section("演示总结")
            print("🎉 多模态数据分析能力演示完成！")
            print()
            print("✅ 已成功演示的功能:")
            print("   1. 语音识别和文本转换")
            print("   2. 客户行为数据多维度分析")
            print("   3. 高价值客户自动识别算法")
            print("   4. 多模态数据融合和分析管道")
            print("   5. 端到端分析流程")
            print("   6. 并发处理性能")
            print()
            print("🚀 系统已准备好用于生产环境！")
            
        except Exception as e:
            print(f"❌ 演示过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数"""
    demo = MultimodalAnalysisDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())