#!/usr/bin/env python3
"""
客户行为分析专项示例

展示客户行为分析服务的各种功能，包括：
- 多维度行为分析
- 客户行为画像生成
- 异常行为检测
- 转化分析

运行方式:
    python examples/behavior_analysis_example.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.behavior_analysis_service import BehaviorAnalysisService
from src.models.multimodal import BehaviorData

class BehaviorAnalysisExample:
    """行为分析示例类"""
    
    def __init__(self):
        self.behavior_service = BehaviorAnalysisService()
    
    def create_realistic_behavior_data(self, customer_id: str, days: int = 14) -> list[BehaviorData]:
        """创建真实的客户行为数据"""
        behavior_data = []
        
        # 模拟不同类型的客户行为模式
        customer_types = {
            'high_engagement': {
                'base_engagement': 0.8,
                'page_views_range': (8, 15),
                'clicks_range': (5, 12),
                'session_duration_range': (300, 900),
                'conversion_probability': 0.7
            },
            'medium_engagement': {
                'base_engagement': 0.6,
                'page_views_range': (4, 8),
                'clicks_range': (2, 6),
                'session_duration_range': (120, 400),
                'conversion_probability': 0.4
            },
            'low_engagement': {
                'base_engagement': 0.3,
                'page_views_range': (1, 3),
                'clicks_range': (0, 2),
                'session_duration_range': (30, 120),
                'conversion_probability': 0.1
            }
        }
        
        # 随机选择客户类型
        customer_type = random.choice(list(customer_types.keys()))
        type_config = customer_types[customer_type]
        
        print(f"🎯 生成 {customer_type} 类型客户的行为数据")
        
        # 生成指定天数的行为数据
        for day in range(days):
            # 某些天可能没有访问
            if random.random() < 0.2:  # 20%的天数没有访问
                continue
            
            timestamp = datetime.now() - timedelta(days=day)
            
            # 生成页面浏览数据
            num_page_views = random.randint(*type_config['page_views_range'])
            page_views = []
            
            pages = ['/products', '/pricing', '/features', '/demo', '/case-studies', 
                    '/contact', '/about', '/blog', '/support', '/enterprise']
            
            visited_pages = random.sample(pages, min(num_page_views, len(pages)))
            
            for i, page in enumerate(visited_pages):
                duration = random.randint(30, 300)
                page_views.append({
                    "url": page,
                    "timestamp": timestamp + timedelta(minutes=i*2),
                    "duration": duration
                })
            
            # 生成点击事件
            num_clicks = random.randint(*type_config['clicks_range'])
            click_events = []
            
            click_elements = ['demo_button', 'pricing_link', 'contact_form', 
                            'download_link', 'video_play', 'feature_tab', 
                            'case_study_link', 'signup_button']
            
            for i in range(num_clicks):
                element = random.choice(click_elements)
                click_events.append({
                    "element": element,
                    "timestamp": timestamp + timedelta(minutes=i*3)
                })
            
            # 计算页面停留时间
            time_spent = {}
            for page_view in page_views:
                page = page_view['url']
                time_spent[page] = time_spent.get(page, 0) + page_view['duration']
            
            # 生成交互模式数据
            interaction_patterns = {
                "scroll_depth": random.uniform(0.3, 1.0),
                "click_through_rate": random.uniform(0.1, 0.9),
                "form_completion": random.random() < 0.3,
                "bounce_rate": random.uniform(0.1, 0.8),
                "return_visitor": day < days * 0.7  # 前70%的时间是回访用户
            }
            
            # 计算参与度评分
            base_score = type_config['base_engagement']
            score_variation = random.uniform(-0.1, 0.1)
            engagement_score = max(0.0, min(1.0, base_score + score_variation))
            
            # 生成转化指标
            conversion_indicators = []
            if random.random() < type_config['conversion_probability']:
                possible_conversions = ['demo_request', 'contact_form', 'newsletter_signup',
                                     'whitepaper_download', 'trial_signup', 'pricing_inquiry']
                num_conversions = random.randint(1, 3)
                conversion_indicators = random.sample(possible_conversions, num_conversions)
            
            behavior_data.append(BehaviorData(
                customer_id=customer_id,
                session_id=f"session_{customer_id}_{day}_{random.randint(1000, 9999)}",
                page_views=page_views,
                click_events=click_events,
                time_spent=time_spent,
                interaction_patterns=interaction_patterns,
                engagement_score=engagement_score,
                conversion_indicators=conversion_indicators,
                timestamp=timestamp
            ))
        
        return behavior_data
    
    async def basic_behavior_analysis(self):
        """基础行为分析示例"""
        print("📊 基础客户行为分析示例")
        print("-" * 40)
        
        # 创建示例数据
        customer_id = "behavior_demo_001"
        behavior_data = self.create_realistic_behavior_data(customer_id, days=21)
        
        print(f"👤 客户ID: {customer_id}")
        print(f"📅 数据时间跨度: 21天")
        print(f"📊 会话数量: {len(behavior_data)}")
        
        # 执行行为分析
        print("\n🔄 执行多维度行为分析...")
        result = await self.behavior_service.analyze_customer_behavior(
            customer_id, behavior_data
        )
        
        # 显示参与度指标
        print("\n📈 参与度指标:")
        engagement = result['engagement_metrics']
        print(f"   平均参与度评分: {engagement.get('average_engagement_score', 0):.2f}")
        print(f"   总页面浏览量: {engagement.get('total_page_views', 0)}")
        print(f"   总点击次数: {engagement.get('total_clicks', 0)}")
        print(f"   平均会话时长: {engagement.get('average_session_duration', 0):.1f} 秒")
        print(f"   跳出率: {engagement.get('bounce_rate', 0):.1%}")
        print(f"   会话数量: {engagement.get('sessions_count', 0)}")
        
        # 显示访问模式
        print("\n🕒 访问模式分析:")
        patterns = result['access_patterns']
        print(f"   高峰访问时间: {patterns.get('peak_access_hour', 0)}:00")
        print(f"   高峰访问日: 周{patterns.get('peak_access_day', 0) + 1}")
        print(f"   访问过的独特页面数: {patterns.get('unique_pages_visited', 0)}")
        
        if patterns.get('top_pages'):
            print("   最受欢迎页面:")
            for page, count in patterns['top_pages'][:3]:
                print(f"     {page}: {count} 次访问")
        
        # 显示转化分析
        print("\n💰 转化分析:")
        conversion = result['conversion_metrics']
        print(f"   转化率: {conversion.get('conversion_rate', 0):.1%}")
        print(f"   转化事件总数: {conversion.get('total_conversion_events', 0)}")
        print(f"   独特转化事件数: {conversion.get('unique_conversion_events', 0)}")
        print(f"   转化速度: {conversion.get('conversion_velocity', 0):.1f} 小时")
        
        # 显示行为画像
        print("\n👤 客户行为画像:")
        profile = result['behavior_profile']
        print(f"   客户类型: {profile.get('customer_type', 'unknown')}")
        print(f"   综合评分: {profile.get('overall_score', 0):.2f}")
        print(f"   参与水平: {profile.get('engagement_level', 'unknown')}")
        print(f"   数字化成熟度: {profile.get('digital_maturity', 'unknown')}")
        
        if profile.get('interests'):
            print(f"   兴趣点: {', '.join(profile['interests'])}")
        
        # 显示异常检测
        if result.get('anomalies'):
            print("\n⚠️  异常行为检测:")
            for anomaly in result['anomalies'][:3]:
                print(f"   • {anomaly.get('type', 'unknown')}: {anomaly.get('session_id', 'N/A')}")
        
        # 显示推荐建议
        print("\n💡 智能推荐建议:")
        for i, recommendation in enumerate(result.get('recommendations', [])[:5], 1):
            print(f"   {i}. {recommendation}")
        
        return result
    
    async def time_window_analysis(self):
        """时间窗口分析示例"""
        print("\n⏰ 时间窗口分析示例")
        print("-" * 40)
        
        customer_id = "time_window_demo"
        behavior_data = self.create_realistic_behavior_data(customer_id, days=30)
        
        # 分析不同时间窗口
        time_windows = [
            (timedelta(days=7), "最近一周"),
            (timedelta(days=14), "最近两周"),
            (timedelta(days=30), "最近一月")
        ]
        
        print(f"📊 对比分析不同时间窗口的客户行为")
        print(f"👤 客户ID: {customer_id}")
        print(f"📅 总数据跨度: 30天")
        
        results = {}
        
        for time_window, description in time_windows:
            print(f"\n🔍 分析 {description} 的数据...")
            
            result = await self.behavior_service.analyze_customer_behavior(
                customer_id, behavior_data, time_window
            )
            
            results[description] = result
            
            # 显示关键指标
            engagement = result['engagement_metrics']
            profile = result['behavior_profile']
            
            print(f"   数据点数量: {result['data_points_count']}")
            print(f"   平均参与度: {engagement.get('average_engagement_score', 0):.2f}")
            print(f"   客户类型: {profile.get('customer_type', 'unknown')}")
            print(f"   综合评分: {profile.get('overall_score', 0):.2f}")
        
        # 对比分析
        print("\n📈 时间窗口对比分析:")
        print("时间窗口        | 数据点 | 参与度 | 评分  | 类型")
        print("-" * 50)
        
        for description, result in results.items():
            data_count = result['data_points_count']
            engagement_score = result['engagement_metrics'].get('average_engagement_score', 0)
            overall_score = result['behavior_profile'].get('overall_score', 0)
            customer_type = result['behavior_profile'].get('customer_type', 'unknown')
            
            print(f"{description:12} | {data_count:6} | {engagement_score:6.2f} | {overall_score:5.2f} | {customer_type}")
        
        return results
    
    async def multiple_customers_comparison(self):
        """多客户对比分析示例"""
        print("\n👥 多客户对比分析示例")
        print("-" * 40)
        
        # 创建多个客户的数据
        customers = [
            "enterprise_client_001",
            "startup_client_002", 
            "medium_business_003",
            "individual_client_004"
        ]
        
        print(f"🎯 对比分析 {len(customers)} 个客户的行为模式")
        
        customer_results = {}
        
        for customer_id in customers:
            print(f"\n🔄 分析客户: {customer_id}")
            
            # 为每个客户生成不同的行为数据
            behavior_data = self.create_realistic_behavior_data(customer_id, days=14)
            
            result = await self.behavior_service.analyze_customer_behavior(
                customer_id, behavior_data
            )
            
            customer_results[customer_id] = result
            
            # 显示简要信息
            profile = result['behavior_profile']
            engagement = result['engagement_metrics']
            
            print(f"   客户类型: {profile.get('customer_type', 'unknown')}")
            print(f"   综合评分: {profile.get('overall_score', 0):.2f}")
            print(f"   参与度: {engagement.get('average_engagement_score', 0):.2f}")
        
        # 生成对比报告
        print("\n📊 客户对比分析报告:")
        print("客户ID                | 类型        | 综合评分 | 参与度 | 转化率")
        print("-" * 65)
        
        # 按综合评分排序
        sorted_customers = sorted(
            customer_results.items(),
            key=lambda x: x[1]['behavior_profile'].get('overall_score', 0),
            reverse=True
        )
        
        for customer_id, result in sorted_customers:
            profile = result['behavior_profile']
            engagement = result['engagement_metrics']
            conversion = result['conversion_metrics']
            
            customer_type = profile.get('customer_type', 'unknown')
            overall_score = profile.get('overall_score', 0)
            engagement_score = engagement.get('average_engagement_score', 0)
            conversion_rate = conversion.get('conversion_rate', 0)
            
            print(f"{customer_id:20} | {customer_type:11} | {overall_score:8.2f} | {engagement_score:6.2f} | {conversion_rate:6.1%}")
        
        # 识别最佳客户
        best_customer = sorted_customers[0]
        print(f"\n🏆 最佳客户: {best_customer[0]}")
        print(f"   推荐行动: {', '.join(best_customer[1].get('recommendations', [])[:3])}")
        
        return customer_results
    
    async def anomaly_detection_demo(self):
        """异常检测演示"""
        print("\n🚨 异常行为检测演示")
        print("-" * 40)
        
        customer_id = "anomaly_demo_customer"
        
        # 创建包含异常行为的数据
        normal_data = self.create_realistic_behavior_data(customer_id, days=10)
        
        # 添加一些异常行为
        anomaly_timestamp = datetime.now() - timedelta(days=2)
        
        # 异常1: 异常高的页面浏览量
        anomaly_behavior_1 = BehaviorData(
            customer_id=customer_id,
            session_id=f"anomaly_session_1",
            page_views=[{"url": f"/page_{i}", "duration": 10} for i in range(100)],  # 异常多的页面
            click_events=[{"element": "button"} for _ in range(200)],  # 异常多的点击
            time_spent={f"/page_{i}": 10.0 for i in range(100)},
            interaction_patterns={"scroll_depth": 0.1, "click_through_rate": 0.9},
            engagement_score=0.1,  # 异常低的参与度
            conversion_indicators=[],
            timestamp=anomaly_timestamp
        )
        
        # 异常2: 异常长的会话时间
        anomaly_behavior_2 = BehaviorData(
            customer_id=customer_id,
            session_id=f"anomaly_session_2",
            page_views=[{"url": "/products", "duration": 7200}],  # 2小时停留
            click_events=[],
            time_spent={"/products": 7200.0},
            interaction_patterns={"scroll_depth": 0.0, "click_through_rate": 0.0},
            engagement_score=0.95,  # 异常高的参与度但无交互
            conversion_indicators=[],
            timestamp=anomaly_timestamp + timedelta(hours=1)
        )
        
        # 合并正常和异常数据
        all_behavior_data = normal_data + [anomaly_behavior_1, anomaly_behavior_2]
        
        print(f"📊 分析包含异常行为的数据集")
        print(f"   正常行为数据: {len(normal_data)} 条")
        print(f"   异常行为数据: 2 条")
        print(f"   总数据量: {len(all_behavior_data)} 条")
        
        # 执行分析
        result = await self.behavior_service.analyze_customer_behavior(
            customer_id, all_behavior_data
        )
        
        # 显示异常检测结果
        anomalies = result.get('anomalies', [])
        
        print(f"\n🔍 检测到 {len(anomalies)} 个异常行为:")
        
        for i, anomaly in enumerate(anomalies, 1):
            print(f"\n   异常 #{i}:")
            print(f"     类型: {anomaly.get('type', 'unknown')}")
            print(f"     会话ID: {anomaly.get('session_id', 'N/A')}")
            print(f"     严重程度: {anomaly.get('severity', 'unknown')}")
            print(f"     异常值: {anomaly.get('value', 'N/A')}")
            
            if 'expected_range' in anomaly:
                expected = anomaly['expected_range']
                print(f"     预期范围: {expected[0]:.2f} - {expected[1]:.2f}")
        
        # 显示异常对整体分析的影响
        print(f"\n📈 异常行为对分析结果的影响:")
        profile = result['behavior_profile']
        print(f"   客户类型: {profile.get('customer_type', 'unknown')}")
        print(f"   综合评分: {profile.get('overall_score', 0):.2f}")
        print(f"   是否需要人工审核: {'是' if len(anomalies) > 2 else '否'}")
        
        return result
    
    async def run_all_examples(self):
        """运行所有示例"""
        print("📊 客户行为分析功能演示")
        print("=" * 50)
        
        try:
            await self.basic_behavior_analysis()
            await self.time_window_analysis()
            await self.multiple_customers_comparison()
            await self.anomaly_detection_demo()
            
            print("\n🎉 客户行为分析演示完成！")
            print("\n✅ 演示的功能:")
            print("   • 多维度客户行为分析")
            print("   • 时间窗口对比分析")
            print("   • 多客户行为对比")
            print("   • 异常行为检测")
            print("   • 智能推荐生成")
            print("   • 客户价值评估")
            
        except Exception as e:
            print(f"❌ 演示过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数"""
    example = BehaviorAnalysisExample()
    await example.run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())