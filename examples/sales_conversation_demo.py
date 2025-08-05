"""
销售对话演示程序

这个程序演示了一个完整的销售对话场景，展示对话状态管理系统
在实际业务中的应用，包括多Agent协作、客户信息收集、
需求分析、方案推荐等完整流程。
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from src.services.conversation_service import ConversationService
from src.schemas.conversation import (
    ConversationCreate, MessageCreate, MessageRole, 
    ConversationStateUpdate, ConversationStatus
)


class SalesConversationDemo:
    """销售对话演示类"""
    
    def __init__(self):
        self.mock_db = self._create_mock_db()
        self.conversation_service = ConversationService(self.mock_db)
        
        # 客户信息
        self.customer_info = {
            "name": "王总",
            "company": "创新科技有限公司",
            "industry": "软件开发",
            "company_size": "50-100人",
            "role": "CTO",
            "email": "wang@innovation-tech.com",
            "phone": "138****8888"
        }
        
        # 对话ID
        self.conversation_id = None
        
        # 消息计数器
        self.message_counter = 0
    
    def _create_mock_db(self):
        """创建模拟数据库"""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        return mock_db
    
    def _mock_message_refresh(self, obj):
        """模拟消息刷新"""
        self.message_counter += 1
        obj.id = f"msg-{self.message_counter:03d}"
        obj.created_at = datetime.utcnow()
    
    async def _add_message(self, role: MessageRole, content: str, agent_type: str = None, agent_id: str = None):
        """添加消息的辅助方法"""
        self.mock_db.refresh.side_effect = self._mock_message_refresh
        
        message = MessageCreate(
            role=role,
            content=content,
            agent_type=agent_type,
            agent_id=agent_id,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": 0.9 if agent_type else None
            }
        )
        
        await self.conversation_service.add_message(self.conversation_id, message)
        
        # 显示消息
        role_display = {
            MessageRole.USER: f"👤 {self.customer_info['name']}",
            MessageRole.ASSISTANT: f"🤖 {agent_type or 'Assistant'}",
            MessageRole.SYSTEM: "⚙️ System",
            MessageRole.AGENT: f"🎯 {agent_type or 'Agent'}"
        }
        
        print(f"\n{role_display.get(role, role)}: {content}")
        
        # 添加短暂延迟以模拟真实对话
        await asyncio.sleep(0.5)
    
    async def _update_state(self, **kwargs):
        """更新对话状态的辅助方法"""
        state_update = ConversationStateUpdate(**kwargs)
        await self.conversation_service.update_conversation_state(
            self.conversation_id, 
            state_update
        )
    
    async def _add_context(self, key: str, value: Any):
        """添加上下文变量的辅助方法"""
        await self.conversation_service.add_context_variable(
            self.conversation_id, 
            key, 
            value
        )
    
    async def _add_memory(self, key: str, value: Any, long_term: bool = False, importance: float = 0.5):
        """添加记忆的辅助方法"""
        if long_term:
            await self.conversation_service.promote_to_long_term_memory(
                self.conversation_id, 
                key, 
                value, 
                importance
            )
        else:
            await self.conversation_service.update_short_term_memory(
                self.conversation_id, 
                key, 
                value
            )
    
    async def initialize_conversation(self):
        """初始化对话"""
        print("🚀 初始化销售对话...")
        print("="*60)
        
        # 创建对话
        conversation_data = ConversationCreate(
            user_id=f"customer_{self.customer_info['email'].split('@')[0]}",
            title=f"销售咨询 - {self.customer_info['company']}",
            initial_context={
                "business_type": "sales",
                "priority": "high",
                "source": "inbound_inquiry",
                "customer_segment": "mid_market",
                "industry": self.customer_info["industry"]
            }
        )
        
        # 模拟对话创建
        def mock_refresh_conversation(obj):
            obj.id = "conv-sales-demo-001"
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        
        self.mock_db.refresh.side_effect = mock_refresh_conversation
        
        # 模拟状态跟踪器
        self.conversation_service.state_tracker.initialize_conversation_state = AsyncMock()
        self.conversation_service.state_tracker.update_conversation_state = AsyncMock(return_value=True)
        self.conversation_service.state_tracker.add_to_context = AsyncMock(return_value=True)
        self.conversation_service.state_tracker.update_short_term_memory = AsyncMock(return_value=True)
        self.conversation_service.state_tracker.promote_to_long_term_memory = AsyncMock(return_value=True)
        self.conversation_service.state_tracker.update_flow_state = AsyncMock(return_value=True)
        
        conversation = await self.conversation_service.create_conversation(conversation_data)
        self.conversation_id = "conv-sales-demo-001"
        
        print(f"✅ 对话创建成功")
        print(f"   对话ID: {self.conversation_id}")
        print(f"   客户: {self.customer_info['name']} ({self.customer_info['company']})")
        print(f"   行业: {self.customer_info['industry']}")
        
        # 初始化客户信息到长期记忆
        await self._add_memory("customer_profile", self.customer_info, long_term=True, importance=0.9)
        
    async def stage_1_greeting_and_rapport(self):
        """阶段1: 问候和建立关系"""
        print(f"\n{'='*60}")
        print("📞 阶段1: 问候和建立关系")
        print("="*60)
        
        # 更新对话状态
        await self._update_state(
            current_agent="sales_agent",
            current_task="greeting_and_rapport",
            flow_state="greeting",
            last_intent="initial_contact"
        )
        
        # 客户发起咨询
        await self._add_message(
            MessageRole.USER,
            "你好，我是创新科技的王总。我们公司最近在考虑升级CRM系统，听说你们的产品不错，想了解一下。"
        )
        
        # 记录客户意图
        await self._add_context("initial_intent", "crm_system_upgrade")
        await self._add_memory("customer_pain_point", "需要升级现有CRM系统")
        
        # 销售顾问回应
        await self._add_message(
            MessageRole.ASSISTANT,
            f"王总您好！很高兴认识您。我是您的专属销售顾问李明。了解到{self.customer_info['company']}在考虑CRM系统升级，这确实是一个重要的决策。能先了解一下您目前使用的是什么系统吗？遇到了哪些挑战？",
            agent_type="销售顾问",
            agent_id="sales_agent_001"
        )
        
        # 更新对话状态
        await self._update_state(
            flow_state="needs_discovery",
            last_intent="information_gathering"
        )
        
        await self._add_context("sales_rep", "李明")
        await self._add_context("rapport_established", True)
        
    async def stage_2_needs_assessment(self):
        """阶段2: 需求评估"""
        print(f"\n{'='*60}")
        print("🔍 阶段2: 需求评估")
        print("="*60)
        
        # 客户描述现状
        await self._add_message(
            MessageRole.USER,
            "我们现在用的是一个比较老的系统，主要问题是数据孤岛严重，销售、市场、客服的数据都不互通。而且报表功能很弱，每次要数据都要手工整理，效率很低。"
        )
        
        # 记录客户痛点
        pain_points = [
            "数据孤岛严重",
            "部门间数据不互通", 
            "报表功能弱",
            "手工整理数据",
            "效率低下"
        ]
        
        await self._add_memory("detailed_pain_points", pain_points, long_term=True, importance=0.8)
        await self._add_context("current_system_issues", pain_points)
        
        # 销售顾问深入了解
        await self._add_message(
            MessageRole.ASSISTANT,
            "我理解您的困扰，数据孤岛确实是很多企业面临的核心问题。能具体了解一下吗：1）目前有多少销售人员？2）每月大概处理多少客户和商机？3）对新系统的预算范围是多少？",
            agent_type="销售顾问",
            agent_id="sales_agent_001"
        )
        
        # 客户提供详细信息
        await self._add_message(
            MessageRole.USER,
            "我们销售团队有15个人，每月大概有300-400个新客户咨询，活跃商机在100个左右。预算的话，如果效果好，50-80万应该可以接受。"
        )
        
        # 记录关键业务数据
        business_data = {
            "sales_team_size": 15,
            "monthly_new_leads": "300-400",
            "active_opportunities": 100,
            "budget_range": "50-80万"
        }
        
        await self._add_memory("business_requirements", business_data, long_term=True, importance=0.9)
        await self._add_context("qualification_status", "qualified")
        
        # 更新对话状态
        await self._update_state(
            current_task="solution_matching",
            flow_state="solution_design",
            entities=business_data
        )
        
    async def stage_3_solution_presentation(self):
        """阶段3: 解决方案展示"""
        print(f"\n{'='*60}")
        print("💡 阶段3: 解决方案展示")
        print("="*60)
        
        # 销售顾问介绍解决方案
        await self._add_message(
            MessageRole.ASSISTANT,
            "根据您的需求，我推荐我们的企业版CRM解决方案。它可以完美解决您提到的问题：1）统一的客户数据平台，打通销售、市场、客服；2）强大的报表和分析功能；3）支持15人团队的协作需求。让我安排技术专家为您详细介绍。",
            agent_type="销售顾问",
            agent_id="sales_agent_001"
        )
        
        # 技术专家介入
        await self._update_state(
            current_agent="technical_agent",
            current_task="technical_presentation"
        )
        
        await self._add_message(
            MessageRole.ASSISTANT,
            "王总您好，我是技术专家张工。针对您的需求，我们的系统有几个核心优势：1）360度客户视图，整合所有触点数据；2）实时报表仪表板，支持自定义分析；3）工作流自动化，提升团队效率50%以上；4）移动端支持，随时随地办公。",
            agent_type="技术专家",
            agent_id="technical_agent_001"
        )
        
        # 记录解决方案要点
        solution_highlights = [
            "360度客户视图",
            "实时报表仪表板",
            "工作流自动化",
            "移动端支持",
            "效率提升50%+"
        ]
        
        await self._add_memory("presented_solution", solution_highlights)
        await self._add_context("technical_expert", "张工")
        
        # 客户表现出兴趣
        await self._add_message(
            MessageRole.USER,
            "听起来不错。我们特别关心数据安全和系统稳定性，你们在这方面怎么样？另外，实施周期大概需要多长时间？"
        )
        
        # 记录客户关注点
        customer_concerns = ["数据安全", "系统稳定性", "实施周期"]
        await self._add_memory("customer_concerns", customer_concerns, long_term=True, importance=0.7)
        
        # 技术专家回应关注点
        await self._add_message(
            MessageRole.ASSISTANT,
            "这是很好的问题。我们通过了ISO27001认证，数据采用银行级加密；系统可用性达到99.9%，有完善的容灾备份；实施周期一般是4-6周，包含数据迁移、培训和上线支持。我们已经服务了500+家企业，经验很丰富。",
            agent_type="技术专家",
            agent_id="technical_agent_001"
        )
        
        await self._add_context("customer_interest_level", "high")
        await self._add_context("concerns_addressed", True)
        
    async def stage_4_objection_handling(self):
        """阶段4: 异议处理"""
        print(f"\n{'='*60}")
        print("🤔 阶段4: 异议处理")
        print("="*60)
        
        # 客户提出价格关注
        await self._add_message(
            MessageRole.USER,
            "功能和服务听起来都不错，但我需要了解具体的价格。另外，我们现在的系统还能用，是否真的有必要现在就换？"
        )
        
        # 记录客户异议
        objections = ["价格关注", "更换必要性质疑"]
        await self._add_memory("customer_objections", objections)
        
        # 销售顾问处理异议
        await self._update_state(
            current_agent="sales_agent",
            current_task="objection_handling",
            flow_state="objection_handling"
        )
        
        await self._add_message(
            MessageRole.ASSISTANT,
            "我理解您的考虑。关于价格，我们的企业版年费是68万，平均到每个销售人员每月不到4000元，而效率提升带来的收益远超这个投入。关于更换时机，您提到的数据孤岛问题每天都在影响团队效率，早一天解决就早一天受益。",
            agent_type="销售顾问",
            agent_id="sales_agent_001"
        )
        
        # 提供ROI分析
        await self._add_message(
            MessageRole.ASSISTANT,
            "让我给您算一笔账：如果每个销售人员效率提升30%，按人均年产值200万计算，15人团队一年就能多创造900万价值。68万的投入，ROI超过13倍，这是非常划算的投资。",
            agent_type="销售顾问",
            agent_id="sales_agent_001"
        )
        
        # 记录ROI分析
        roi_analysis = {
            "annual_fee": "68万",
            "efficiency_improvement": "30%",
            "per_person_value": "200万",
            "team_additional_value": "900万",
            "roi_ratio": "13倍"
        }
        
        await self._add_memory("roi_analysis", roi_analysis)
        await self._add_context("objections_handled", True)
        
    async def stage_5_closing_and_next_steps(self):
        """阶段5: 成交和后续步骤"""
        print(f"\n{'='*60}")
        print("🎯 阶段5: 成交和后续步骤")
        print("="*60)
        
        # 客户表示认可
        await self._add_message(
            MessageRole.USER,
            "你们的分析很有道理，我基本认可这个方案。不过这是个重要决策，我需要和团队讨论一下。能否先安排一次产品演示，让我们的核心团队都看看？"
        )
        
        # 更新客户状态
        await self._update_state(
            current_task="closing",
            flow_state="proposal_preparation",
            last_intent="demo_request"
        )
        
        await self._add_context("buying_signal", "demo_request")
        await self._add_memory("decision_process", "需要团队讨论", importance=0.6)
        
        # 销售顾问安排后续步骤
        await self._add_message(
            MessageRole.ASSISTANT,
            "当然可以！我来安排一次专门的产品演示。建议邀请您的销售总监、IT负责人一起参加，这样能更全面地了解系统。我们可以根据您的业务场景定制演示内容。您看下周三下午2点怎么样？",
            agent_type="销售顾问",
            agent_id="sales_agent_001"
        )
        
        # 确认演示安排
        await self._add_message(
            MessageRole.USER,
            "下周三下午可以。我会安排销售总监刘经理和IT主管参加。请提前把演示大纲发给我，我好提前准备问题。"
        )
        
        # 记录后续行动
        next_actions = {
            "demo_date": "下周三下午2点",
            "attendees": ["王总(CTO)", "刘经理(销售总监)", "IT主管"],
            "preparation": "发送演示大纲",
            "follow_up": "准备定制化演示"
        }
        
        await self._add_memory("next_actions", next_actions, long_term=True, importance=0.8)
        
        # 销售顾问确认并总结
        await self._add_message(
            MessageRole.ASSISTANT,
            "完美！我会在今天下班前把演示大纲发到您邮箱。同时我会准备一份针对软件开发行业的定制化方案。期待下周三的演示，相信我们的产品能很好地解决您的需求。",
            agent_type="销售顾问",
            agent_id="sales_agent_001"
        )
        
        # 更新最终状态
        await self._update_state(
            flow_state="demo_scheduled",
            current_task="demo_preparation"
        )
        
        await self._add_context("deal_stage", "demo_scheduled")
        await self._add_context("conversion_probability", 0.75)
        
    async def generate_conversation_summary(self):
        """生成对话总结"""
        print(f"\n{'='*60}")
        print("📊 对话总结和分析")
        print("="*60)
        
        # 模拟获取对话摘要
        mock_summary = {
            "conversation_overview": {
                "duration": "25分钟",
                "total_messages": self.message_counter,
                "customer_engagement": "高",
                "outcome": "演示已安排"
            },
            "customer_profile": {
                "company": self.customer_info["company"],
                "industry": self.customer_info["industry"],
                "decision_maker": self.customer_info["name"],
                "company_size": self.customer_info["company_size"],
                "budget": "50-80万"
            },
            "business_requirements": {
                "pain_points": ["数据孤岛", "报表功能弱", "效率低下"],
                "team_size": 15,
                "monthly_leads": "300-400",
                "active_opportunities": 100
            },
            "sales_progress": {
                "qualification": "已完成",
                "needs_assessment": "已完成", 
                "solution_presentation": "已完成",
                "objection_handling": "已完成",
                "next_step": "产品演示",
                "conversion_probability": "75%"
            },
            "key_insights": [
                "客户对ROI分析很认可",
                "关注数据安全和系统稳定性",
                "决策需要团队讨论",
                "预算充足，需求明确"
            ]
        }
        
        print("✅ 对话概览:")
        overview = mock_summary["conversation_overview"]
        print(f"   对话时长: {overview['duration']}")
        print(f"   消息总数: {overview['total_messages']}")
        print(f"   客户参与度: {overview['customer_engagement']}")
        print(f"   对话结果: {overview['outcome']}")
        
        print(f"\n👤 客户档案:")
        profile = mock_summary["customer_profile"]
        for key, value in profile.items():
            print(f"   {key}: {value}")
        
        print(f"\n📋 业务需求:")
        requirements = mock_summary["business_requirements"]
        print(f"   痛点: {', '.join(requirements['pain_points'])}")
        print(f"   团队规模: {requirements['team_size']}人")
        print(f"   月度线索: {requirements['monthly_leads']}个")
        print(f"   活跃商机: {requirements['active_opportunities']}个")
        
        print(f"\n📈 销售进展:")
        progress = mock_summary["sales_progress"]
        for key, value in progress.items():
            print(f"   {key}: {value}")
        
        print(f"\n💡 关键洞察:")
        for insight in mock_summary["key_insights"]:
            print(f"   • {insight}")
        
        # 生成行动建议
        print(f"\n🎯 后续行动建议:")
        recommendations = [
            "准备定制化产品演示，重点展示数据整合和报表功能",
            "提前发送演示大纲，包含ROI计算器",
            "准备软件开发行业的成功案例",
            "邀请技术专家参与演示，回答技术问题",
            "准备详细的实施计划和时间表",
            "跟进演示后的决策时间表"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    async def run_demo(self):
        """运行完整的销售对话演示"""
        print("🎬 开始销售对话演示")
        print("="*80)
        print(f"场景: {self.customer_info['company']} CRM系统升级咨询")
        print(f"客户: {self.customer_info['name']} ({self.customer_info['role']})")
        print("="*80)
        
        try:
            # 执行各个阶段
            await self.initialize_conversation()
            await self.stage_1_greeting_and_rapport()
            await self.stage_2_needs_assessment()
            await self.stage_3_solution_presentation()
            await self.stage_4_objection_handling()
            await self.stage_5_closing_and_next_steps()
            await self.generate_conversation_summary()
            
            print(f"\n{'='*80}")
            print("🎉 销售对话演示完成！")
            print("✅ 成功展示了对话状态管理系统在销售场景中的应用")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ 演示过程中出现错误: {str(e)}")


async def main():
    """主函数"""
    demo = SalesConversationDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())