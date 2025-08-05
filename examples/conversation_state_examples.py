"""
对话状态管理系统示例程序

这个示例程序演示了如何使用对话状态管理系统的各种功能，
包括对话创建、消息管理、状态跟踪、记忆管理等。
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

# 导入对话相关的模块
from src.services.conversation_service import ConversationService
from src.services.conversation_state_tracker import ConversationStateTracker
from src.schemas.conversation import (
    ConversationCreate, MessageCreate, MessageRole, 
    ConversationStateUpdate, ConversationStatus
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationStateExamples:
    """对话状态管理示例类"""
    
    def __init__(self):
        # 创建模拟的数据库会话
        self.mock_db = self._create_mock_db()
        self.conversation_service = ConversationService(self.mock_db)
        self.state_tracker = ConversationStateTracker(self.mock_db)
        
        # 模拟数据
        self.sample_conversation_id = "conv-12345"
        self.sample_user_id = "user-67890"
    
    def _create_mock_db(self):
        """创建模拟数据库会话"""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        return mock_db
    
    async def example_1_basic_conversation_flow(self):
        """示例1: 基本对话流程"""
        print("\n" + "="*60)
        print("示例1: 基本对话流程")
        print("="*60)
        
        try:
            # 1. 创建对话
            print("\n1. 创建新对话...")
            conversation_data = ConversationCreate(
                user_id=self.sample_user_id,
                title="客户咨询 - 产品演示",
                initial_context={
                    "business_type": "sales",
                    "priority": "high",
                    "source": "website_form",
                    "customer_segment": "enterprise"
                }
            )
            
            # 模拟对话创建
            def mock_refresh_conversation(obj):
                obj.id = self.sample_conversation_id
                obj.created_at = datetime.utcnow()
                obj.updated_at = datetime.utcnow()
            
            self.mock_db.refresh.side_effect = mock_refresh_conversation
            
            # 模拟状态跟踪器初始化
            self.conversation_service.state_tracker.initialize_conversation_state = AsyncMock()
            
            conversation = await self.conversation_service.create_conversation(conversation_data)
            print(f"✅ 对话创建成功: {self.sample_conversation_id}")
            print(f"   用户ID: {conversation_data.user_id}")
            print(f"   标题: {conversation_data.title}")
            print(f"   初始上下文: {conversation_data.initial_context}")
            
            # 2. 添加用户消息
            print("\n2. 添加用户消息...")
            user_message = MessageCreate(
                role=MessageRole.USER,
                content="你好，我想了解一下你们的CRM系统功能",
                metadata={
                    "source": "web_chat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_agent": "Mozilla/5.0..."
                }
            )
            
            def mock_refresh_message(obj):
                obj.id = "msg-001"
                obj.created_at = datetime.utcnow()
            
            self.mock_db.refresh.side_effect = mock_refresh_message
            
            message = await self.conversation_service.add_message(
                self.sample_conversation_id, 
                user_message
            )
            print(f"✅ 用户消息添加成功")
            print(f"   消息内容: {user_message.content}")
            print(f"   消息角色: {user_message.role}")
            
            # 3. 更新对话状态
            print("\n3. 更新对话状态...")
            state_update = ConversationStateUpdate(
                current_task="product_inquiry",
                current_agent="sales_agent",
                flow_state="greeting",
                last_intent="product_information_request",
                entities={
                    "product_type": "CRM系统",
                    "inquiry_stage": "initial"
                }
            )
            
            # 模拟状态更新
            self.conversation_service.state_tracker.update_conversation_state = AsyncMock(return_value=True)
            
            success = await self.conversation_service.update_conversation_state(
                self.sample_conversation_id, 
                state_update
            )
            print(f"✅ 对话状态更新成功: {success}")
            print(f"   当前任务: {state_update.current_task}")
            print(f"   当前Agent: {state_update.current_agent}")
            print(f"   流程状态: {state_update.flow_state}")
            
            print("\n✅ 基本对话流程示例完成")
            
        except Exception as e:
            print(f"❌ 基本对话流程示例失败: {str(e)}")
    
    async def example_2_memory_management(self):
        """示例2: 记忆管理"""
        print("\n" + "="*60)
        print("示例2: 记忆管理")
        print("="*60)
        
        try:
            # 模拟状态跟踪器方法
            self.conversation_service.state_tracker.update_short_term_memory = AsyncMock(return_value=True)
            self.conversation_service.state_tracker.get_short_term_memory = AsyncMock()
            self.conversation_service.state_tracker.promote_to_long_term_memory = AsyncMock(return_value=True)
            self.conversation_service.state_tracker.get_long_term_memory = AsyncMock()
            
            # 1. 短期记忆管理
            print("\n1. 短期记忆管理...")
            
            # 添加短期记忆
            await self.conversation_service.update_short_term_memory(
                self.sample_conversation_id,
                "customer_name",
                "张总"
            )
            print("✅ 短期记忆添加: customer_name = 张总")
            
            await self.conversation_service.update_short_term_memory(
                self.sample_conversation_id,
                "company_size",
                "100-500人"
            )
            print("✅ 短期记忆添加: company_size = 100-500人")
            
            await self.conversation_service.update_short_term_memory(
                self.sample_conversation_id,
                "current_pain_point",
                "客户数据分散，缺乏统一管理"
            )
            print("✅ 短期记忆添加: current_pain_point = 客户数据分散，缺乏统一管理")
            
            # 获取短期记忆
            self.conversation_service.state_tracker.get_short_term_memory.return_value = "张总"
            customer_name = await self.conversation_service.get_short_term_memory(
                self.sample_conversation_id,
                "customer_name"
            )
            print(f"✅ 短期记忆获取: customer_name = {customer_name}")
            
            # 2. 长期记忆管理
            print("\n2. 长期记忆管理...")
            
            # 提升重要信息到长期记忆
            customer_profile = {
                "name": "张总",
                "company": "ABC制造有限公司",
                "industry": "制造业",
                "company_size": "100-500人",
                "decision_maker": True,
                "budget_range": "50-100万",
                "timeline": "3个月内"
            }
            
            await self.conversation_service.promote_to_long_term_memory(
                self.sample_conversation_id,
                "customer_profile",
                customer_profile,
                importance_score=0.9
            )
            print("✅ 长期记忆添加: customer_profile (重要性: 0.9)")
            print(f"   客户档案: {customer_profile}")
            
            # 添加偏好信息
            preferences = {
                "communication_style": "formal",
                "preferred_meeting_time": "下午",
                "decision_factors": ["功能完整性", "价格", "服务支持"],
                "concerns": ["数据安全", "系统稳定性"]
            }
            
            await self.conversation_service.promote_to_long_term_memory(
                self.sample_conversation_id,
                "customer_preferences",
                preferences,
                importance_score=0.8
            )
            print("✅ 长期记忆添加: customer_preferences (重要性: 0.8)")
            print(f"   客户偏好: {preferences}")
            
            # 获取长期记忆
            self.conversation_service.state_tracker.get_long_term_memory.return_value = customer_profile
            stored_profile = await self.conversation_service.get_long_term_memory(
                self.sample_conversation_id,
                "customer_profile"
            )
            print(f"✅ 长期记忆获取: customer_profile = {stored_profile}")
            
            print("\n✅ 记忆管理示例完成")
            
        except Exception as e:
            print(f"❌ 记忆管理示例失败: {str(e)}")
    
    async def example_3_context_management(self):
        """示例3: 上下文管理"""
        print("\n" + "="*60)
        print("示例3: 上下文管理")
        print("="*60)
        
        try:
            # 模拟状态跟踪器方法
            self.conversation_service.state_tracker.add_to_context = AsyncMock(return_value=True)
            self.conversation_service.state_tracker.get_context_variable = AsyncMock()
            
            # 1. 添加上下文变量
            print("\n1. 添加上下文变量...")
            
            context_variables = {
                "current_topic": "产品功能介绍",
                "demo_stage": "核心功能展示",
                "customer_interest_level": "high",
                "next_action": "安排技术演示",
                "follow_up_date": "2024-01-15",
                "assigned_sales_rep": "李经理"
            }
            
            for key, value in context_variables.items():
                await self.conversation_service.add_context_variable(
                    self.sample_conversation_id,
                    key,
                    value
                )
                print(f"✅ 上下文变量添加: {key} = {value}")
            
            # 2. 获取上下文变量
            print("\n2. 获取上下文变量...")
            
            self.conversation_service.state_tracker.get_context_variable.return_value = "产品功能介绍"
            current_topic = await self.conversation_service.get_context_variable(
                self.sample_conversation_id,
                "current_topic"
            )
            print(f"✅ 上下文变量获取: current_topic = {current_topic}")
            
            # 3. 更新业务流程状态
            print("\n3. 更新业务流程状态...")
            
            # 模拟流程状态更新
            self.conversation_service.state_tracker.update_flow_state = AsyncMock(return_value=True)
            
            flow_states = [
                "greeting",
                "needs_assessment", 
                "solution_presentation",
                "objection_handling",
                "proposal_preparation"
            ]
            
            for state in flow_states:
                success = await self.conversation_service.update_flow_state(
                    self.sample_conversation_id,
                    state
                )
                print(f"✅ 流程状态更新: {state} (成功: {success})")
            
            print("\n✅ 上下文管理示例完成")
            
        except Exception as e:
            print(f"❌ 上下文管理示例失败: {str(e)}")
    
    async def example_4_multi_agent_conversation(self):
        """示例4: 多Agent对话场景"""
        print("\n" + "="*60)
        print("示例4: 多Agent对话场景")
        print("="*60)
        
        try:
            # 模拟多个Agent参与的对话
            agents = [
                {"type": "sales_agent", "id": "agent_001", "name": "销售助手"},
                {"type": "technical_agent", "id": "agent_002", "name": "技术专家"},
                {"type": "pricing_agent", "id": "agent_003", "name": "报价专员"}
            ]
            
            print("\n1. 多Agent对话流程...")
            
            # 销售Agent开始对话
            print("\n--- 销售Agent介入 ---")
            await self.conversation_service.update_conversation_state(
                self.sample_conversation_id,
                ConversationStateUpdate(
                    current_agent="sales_agent",
                    current_task="initial_consultation",
                    flow_state="needs_assessment"
                )
            )
            
            sales_message = MessageCreate(
                role=MessageRole.ASSISTANT,
                content="您好！我是您的销售顾问。了解到您对我们的CRM系统感兴趣，能详细说说您目前的业务挑战吗？",
                agent_type="sales_agent",
                agent_id="agent_001",
                metadata={"confidence": 0.95, "agent_name": "销售助手"}
            )
            
            def mock_refresh_sales_msg(obj):
                obj.id = "msg-sales-001"
                obj.created_at = datetime.utcnow()
            
            self.mock_db.refresh.side_effect = mock_refresh_sales_msg
            
            await self.conversation_service.add_message(self.sample_conversation_id, sales_message)
            print(f"✅ 销售Agent消息: {sales_message.content}")
            
            # 用户回复后，技术Agent介入
            print("\n--- 技术Agent介入 ---")
            await self.conversation_service.update_conversation_state(
                self.sample_conversation_id,
                ConversationStateUpdate(
                    current_agent="technical_agent",
                    current_task="technical_consultation",
                    flow_state="solution_design"
                )
            )
            
            technical_message = MessageCreate(
                role=MessageRole.ASSISTANT,
                content="我是技术专家，针对您提到的数据集成需求，我们的系统支持200+种第三方应用集成，包括您使用的ERP系统。",
                agent_type="technical_agent", 
                agent_id="agent_002",
                metadata={"confidence": 0.92, "agent_name": "技术专家"}
            )
            
            def mock_refresh_tech_msg(obj):
                obj.id = "msg-tech-001"
                obj.created_at = datetime.utcnow()
            
            self.mock_db.refresh.side_effect = mock_refresh_tech_msg
            
            await self.conversation_service.add_message(self.sample_conversation_id, technical_message)
            print(f"✅ 技术Agent消息: {technical_message.content}")
            
            # 报价Agent介入
            print("\n--- 报价Agent介入 ---")
            await self.conversation_service.update_conversation_state(
                self.sample_conversation_id,
                ConversationStateUpdate(
                    current_agent="pricing_agent",
                    current_task="pricing_consultation",
                    flow_state="proposal_preparation"
                )
            )
            
            pricing_message = MessageCreate(
                role=MessageRole.ASSISTANT,
                content="根据您的需求，我为您准备了定制化的报价方案。100用户的企业版年费为68万，包含所有核心功能和技术支持。",
                agent_type="pricing_agent",
                agent_id="agent_003", 
                metadata={"confidence": 0.88, "agent_name": "报价专员"}
            )
            
            def mock_refresh_pricing_msg(obj):
                obj.id = "msg-pricing-001"
                obj.created_at = datetime.utcnow()
            
            self.mock_db.refresh.side_effect = mock_refresh_pricing_msg
            
            await self.conversation_service.add_message(self.sample_conversation_id, pricing_message)
            print(f"✅ 报价Agent消息: {pricing_message.content}")
            
            # 2. Agent协作状态管理
            print("\n2. Agent协作状态管理...")
            
            # 记录Agent协作信息
            await self.conversation_service.add_context_variable(
                self.sample_conversation_id,
                "active_agents",
                [agent["type"] for agent in agents]
            )
            
            await self.conversation_service.add_context_variable(
                self.sample_conversation_id,
                "agent_handoff_history",
                ["sales_agent", "technical_agent", "pricing_agent"]
            )
            
            print("✅ Agent协作状态已记录")
            print(f"   活跃Agents: {[agent['type'] for agent in agents]}")
            print(f"   切换历史: sales_agent → technical_agent → pricing_agent")
            
            print("\n✅ 多Agent对话场景示例完成")
            
        except Exception as e:
            print(f"❌ 多Agent对话场景示例失败: {str(e)}")
    
    async def example_5_user_preference_learning(self):
        """示例5: 用户偏好学习"""
        print("\n" + "="*60)
        print("示例5: 用户偏好学习")
        print("="*60)
        
        try:
            # 模拟用户偏好学习
            self.conversation_service.state_tracker.learn_user_preferences = AsyncMock(return_value=True)
            
            print("\n1. 学习用户交互偏好...")
            
            # 学习通信风格偏好
            interaction_data_1 = {
                "response_length": "detailed",
                "communication_style": "formal",
                "preferred_agent": "technical_agent",
                "response_time_preference": "immediate"
            }
            
            await self.conversation_service.learn_user_preferences(
                self.sample_conversation_id,
                interaction_data_1
            )
            print("✅ 学习通信风格偏好:")
            print(f"   回复长度偏好: {interaction_data_1['response_length']}")
            print(f"   通信风格: {interaction_data_1['communication_style']}")
            print(f"   偏好Agent: {interaction_data_1['preferred_agent']}")
            
            # 学习任务模式
            interaction_data_2 = {
                "task_pattern": "technical_deep_dive",
                "decision_making_style": "analytical",
                "information_processing": "sequential"
            }
            
            await self.conversation_service.learn_user_preferences(
                self.sample_conversation_id,
                interaction_data_2
            )
            print("✅ 学习任务模式:")
            print(f"   任务模式: {interaction_data_2['task_pattern']}")
            print(f"   决策风格: {interaction_data_2['decision_making_style']}")
            print(f"   信息处理: {interaction_data_2['information_processing']}")
            
            # 学习业务偏好
            interaction_data_3 = {
                "business_focus": ["ROI", "implementation_timeline", "support_quality"],
                "risk_tolerance": "low",
                "innovation_adoption": "early_majority"
            }
            
            await self.conversation_service.learn_user_preferences(
                self.sample_conversation_id,
                interaction_data_3
            )
            print("✅ 学习业务偏好:")
            print(f"   关注重点: {interaction_data_3['business_focus']}")
            print(f"   风险承受度: {interaction_data_3['risk_tolerance']}")
            print(f"   创新采用: {interaction_data_3['innovation_adoption']}")
            
            print("\n2. 应用学习到的偏好...")
            
            # 基于学习到的偏好调整对话策略
            learned_preferences = {
                "response_style": "detailed_technical",
                "preferred_agents": ["technical_agent", "sales_agent"],
                "communication_tone": "formal_professional",
                "content_focus": ["technical_specifications", "ROI_analysis", "implementation_plan"]
            }
            
            await self.conversation_service.promote_to_long_term_memory(
                self.sample_conversation_id,
                "learned_user_preferences",
                learned_preferences,
                importance_score=0.95
            )
            
            print("✅ 偏好应用策略:")
            print(f"   回复风格: {learned_preferences['response_style']}")
            print(f"   偏好Agents: {learned_preferences['preferred_agents']}")
            print(f"   沟通语调: {learned_preferences['communication_tone']}")
            print(f"   内容重点: {learned_preferences['content_focus']}")
            
            print("\n✅ 用户偏好学习示例完成")
            
        except Exception as e:
            print(f"❌ 用户偏好学习示例失败: {str(e)}")
    
    async def example_6_conversation_summary(self):
        """示例6: 对话摘要和分析"""
        print("\n" + "="*60)
        print("示例6: 对话摘要和分析")
        print("="*60)
        
        try:
            # 模拟对话摘要获取
            mock_summary = {
                "recent_messages": [
                    {
                        "role": "user",
                        "content": "你好，我想了解一下你们的CRM系统功能",
                        "agent_type": None,
                        "created_at": "2024-01-10T10:00:00"
                    },
                    {
                        "role": "assistant", 
                        "content": "您好！我是您的销售顾问。了解到您对我们的CRM系统感兴趣...",
                        "agent_type": "sales_agent",
                        "created_at": "2024-01-10T10:01:00"
                    },
                    {
                        "role": "assistant",
                        "content": "我是技术专家，针对您提到的数据集成需求...",
                        "agent_type": "technical_agent", 
                        "created_at": "2024-01-10T10:05:00"
                    }
                ],
                "current_state": {
                    "flow_state": "proposal_preparation",
                    "current_agent": "pricing_agent",
                    "current_task": "pricing_consultation",
                    "last_intent": "pricing_inquiry"
                },
                "context_keys": [
                    "current_topic", "demo_stage", "customer_interest_level",
                    "next_action", "follow_up_date", "assigned_sales_rep"
                ],
                "memory_summary": {
                    "short_term_items": 3,
                    "long_term_items": 2
                }
            }
            
            self.conversation_service.state_tracker.get_conversation_history_summary = AsyncMock(
                return_value=mock_summary
            )
            
            print("\n1. 获取对话摘要...")
            summary = await self.conversation_service.get_conversation_summary(
                self.sample_conversation_id
            )
            
            print("✅ 对话摘要获取成功:")
            print(f"\n📝 最近消息 ({len(summary['recent_messages'])}条):")
            for i, msg in enumerate(summary['recent_messages'], 1):
                agent_info = f" ({msg['agent_type']})" if msg['agent_type'] else ""
                print(f"   {i}. [{msg['role']}{agent_info}] {msg['content'][:50]}...")
            
            print(f"\n🎯 当前状态:")
            print(f"   流程状态: {summary['current_state']['flow_state']}")
            print(f"   当前Agent: {summary['current_state']['current_agent']}")
            print(f"   当前任务: {summary['current_state']['current_task']}")
            print(f"   最后意图: {summary['current_state']['last_intent']}")
            
            print(f"\n🔧 上下文变量 ({len(summary['context_keys'])}个):")
            for key in summary['context_keys']:
                print(f"   - {key}")
            
            print(f"\n🧠 记忆统计:")
            print(f"   短期记忆: {summary['memory_summary']['short_term_items']} 项")
            print(f"   长期记忆: {summary['memory_summary']['long_term_items']} 项")
            
            # 2. 生成对话分析报告
            print("\n2. 生成对话分析报告...")
            
            analysis_report = {
                "conversation_metrics": {
                    "total_messages": 6,
                    "user_messages": 2,
                    "agent_messages": 4,
                    "average_response_time": "2.3秒",
                    "conversation_duration": "15分钟"
                },
                "agent_performance": {
                    "sales_agent": {"messages": 2, "confidence_avg": 0.95},
                    "technical_agent": {"messages": 1, "confidence_avg": 0.92},
                    "pricing_agent": {"messages": 1, "confidence_avg": 0.88}
                },
                "user_engagement": {
                    "engagement_level": "high",
                    "question_count": 3,
                    "follow_up_rate": 0.8,
                    "satisfaction_indicators": ["positive_language", "detailed_questions"]
                },
                "business_outcomes": {
                    "lead_quality": "high",
                    "conversion_probability": 0.75,
                    "next_steps": ["技术演示", "方案定制", "合同谈判"],
                    "estimated_deal_value": "68万"
                }
            }
            
            print("✅ 对话分析报告:")
            print(f"\n📊 对话指标:")
            metrics = analysis_report["conversation_metrics"]
            print(f"   总消息数: {metrics['total_messages']}")
            print(f"   用户消息: {metrics['user_messages']}")
            print(f"   Agent消息: {metrics['agent_messages']}")
            print(f"   平均响应时间: {metrics['average_response_time']}")
            print(f"   对话时长: {metrics['conversation_duration']}")
            
            print(f"\n🤖 Agent表现:")
            for agent, perf in analysis_report["agent_performance"].items():
                print(f"   {agent}: {perf['messages']}条消息, 平均置信度: {perf['confidence_avg']}")
            
            print(f"\n👤 用户参与度:")
            engagement = analysis_report["user_engagement"]
            print(f"   参与水平: {engagement['engagement_level']}")
            print(f"   提问次数: {engagement['question_count']}")
            print(f"   跟进率: {engagement['follow_up_rate']}")
            print(f"   满意度指标: {', '.join(engagement['satisfaction_indicators'])}")
            
            print(f"\n💼 业务结果:")
            outcomes = analysis_report["business_outcomes"]
            print(f"   线索质量: {outcomes['lead_quality']}")
            print(f"   转化概率: {outcomes['conversion_probability']}")
            print(f"   下一步行动: {', '.join(outcomes['next_steps'])}")
            print(f"   预估成交金额: {outcomes['estimated_deal_value']}")
            
            print("\n✅ 对话摘要和分析示例完成")
            
        except Exception as e:
            print(f"❌ 对话摘要和分析示例失败: {str(e)}")
    
    async def run_all_examples(self):
        """运行所有示例"""
        print("🚀 开始运行对话状态管理系统示例程序")
        print("="*80)
        
        examples = [
            self.example_1_basic_conversation_flow,
            self.example_2_memory_management,
            self.example_3_context_management,
            self.example_4_multi_agent_conversation,
            self.example_5_user_preference_learning,
            self.example_6_conversation_summary
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                await example()
                print(f"\n✅ 示例 {i} 执行成功")
            except Exception as e:
                print(f"\n❌ 示例 {i} 执行失败: {str(e)}")
        
        print("\n" + "="*80)
        print("🎉 所有示例程序执行完成！")
        print("="*80)


async def main():
    """主函数"""
    examples = ConversationStateExamples()
    await examples.run_all_examples()


if __name__ == "__main__":
    asyncio.run(main())