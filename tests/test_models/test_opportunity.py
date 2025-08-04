"""
销售机会模型测试
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.opportunity import (
    Opportunity, OpportunityStage, OpportunityActivity, 
    OpportunityStageHistory, OpportunityStatus, OpportunityPriority, StageType
)
from src.models.customer import Customer, CompanySize, CustomerStatus


class TestOpportunityStage:
    """销售机会阶段模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_opportunity_stage(self, db_session: AsyncSession):
        """测试创建销售机会阶段"""
        stage = OpportunityStage(
            name="需求分析",
            description="分析客户需求阶段",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,
            probability=0.3,
            requirements=["需求调研", "方案初步设计"],
            entry_criteria=["客户确认需求"],
            exit_criteria=["需求文档完成"],
            duration_days=7
        )
        
        db_session.add(stage)
        await db_session.commit()
        await db_session.refresh(stage)
        
        assert stage.id is not None
        assert stage.name == "需求分析"
        assert stage.stage_type == StageType.NEEDS_ANALYSIS
        assert stage.order == 1
        assert stage.probability == 0.3
        assert stage.is_active is True
        assert stage.created_at is not None
        assert stage.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_stage_relationships(self, db_session: AsyncSession):
        """测试阶段关系"""
        # 创建客户
        customer = Customer(
            name="张三",
            company="测试公司",
            industry="制造业",
            size=CompanySize.MEDIUM,
            status=CustomerStatus.PROSPECT
        )
        db_session.add(customer)
        
        # 创建阶段
        stage = OpportunityStage(
            name="商务谈判",
            stage_type=StageType.NEGOTIATION,
            order=1,
            probability=0.7
        )
        db_session.add(stage)
        await db_session.flush()
        
        # 创建机会
        opportunity = Opportunity(
            name="ERP系统项目",
            customer_id=customer.id,
            stage_id=stage.id,
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.commit()
        
        # 验证关系
        await db_session.refresh(stage)
        assert len(stage.opportunities) == 1
        assert stage.opportunities[0].name == "ERP系统项目"


class TestOpportunity:
    """销售机会模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_opportunity(self, db_session: AsyncSession):
        """测试创建销售机会"""
        # 创建客户
        customer = Customer(
            name="李四",
            company="科技公司",
            industry="软件",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
        )
        db_session.add(customer)
        
        # 创建阶段
        stage = OpportunityStage(
            name="方案提议",
            stage_type=StageType.PROPOSAL,
            order=1,
            probability=0.5
        )
        db_session.add(stage)
        await db_session.flush()
        
        # 创建机会
        opportunity = Opportunity(
            name="CRM系统升级项目",
            description="客户关系管理系统升级改造",
            customer_id=customer.id,
            stage_id=stage.id,
            value=500000.0,
            probability=0.6,
            expected_close_date=datetime.utcnow() + timedelta(days=30),
            status=OpportunityStatus.OPEN,
            priority=OpportunityPriority.HIGH,
            products=[
                {
                    "id": "prod-001",
                    "name": "CRM标准版",
                    "quantity": 1,
                    "unit_price": 300000.0
                },
                {
                    "id": "prod-002", 
                    "name": "定制开发服务",
                    "quantity": 1,
                    "unit_price": 200000.0
                }
            ],
            competitors=[
                {
                    "name": "竞争对手A",
                    "strengths": ["价格优势", "本地化服务"],
                    "weaknesses": ["功能单一"]
                }
            ],
            stakeholders=[
                {
                    "name": "王总",
                    "title": "CTO",
                    "role": "技术决策者",
                    "influence_level": "high"
                }
            ],
            risks=[
                {
                    "type": "技术风险",
                    "description": "系统集成复杂度高",
                    "probability": 0.3,
                    "impact": "medium"
                }
            ],
            assigned_to="sales001",
            team_members=["sales001", "tech001"],
            tags=["重点项目", "Q1目标"],
            category="软件销售"
        )
        
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        assert opportunity.id is not None
        assert opportunity.name == "CRM系统升级项目"
        assert opportunity.value == 500000.0
        assert opportunity.probability == 0.6
        assert opportunity.status == OpportunityStatus.OPEN
        assert opportunity.priority == OpportunityPriority.HIGH
        assert len(opportunity.products) == 2
        assert len(opportunity.competitors) == 1
        assert len(opportunity.stakeholders) == 1
        assert len(opportunity.risks) == 1
        assert len(opportunity.team_members) == 2
        assert len(opportunity.tags) == 2
        assert opportunity.created_at is not None
        assert opportunity.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_opportunity_relationships(self, db_session: AsyncSession):
        """测试机会关系"""
        # 创建客户
        customer = Customer(
            name="王五",
            company="贸易公司",
            industry="贸易",
            size=CompanySize.SMALL,
            status=CustomerStatus.CUSTOMER
        )
        db_session.add(customer)
        
        # 创建阶段
        stage = OpportunityStage(
            name="成交阶段",
            stage_type=StageType.CLOSING,
            order=1,
            probability=0.9
        )
        db_session.add(stage)
        await db_session.flush()
        
        # 创建机会
        opportunity = Opportunity(
            name="财务软件项目",
            customer_id=customer.id,
            stage_id=stage.id,
            value=80000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建活动
        activity = OpportunityActivity(
            opportunity_id=opportunity.id,
            activity_type="会议",
            title="项目启动会议",
            description="讨论项目实施计划",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            participants=["客户方", "我方团队"],
            organizer="sales001"
        )
        db_session.add(activity)
        
        # 创建阶段历史
        stage_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            to_stage_id=stage.id,
            reason="初始创建",
            changed_by="system"
        )
        db_session.add(stage_history)
        
        await db_session.commit()
        
        # 验证关系
        await db_session.refresh(opportunity)
        await db_session.refresh(customer)
        
        assert opportunity.customer == customer
        assert opportunity.stage == stage
        assert len(opportunity.activities) == 1
        assert len(opportunity.stage_history) == 1
        assert len(customer.opportunities) == 1
        
        assert opportunity.activities[0].title == "项目启动会议"
        assert opportunity.stage_history[0].reason == "初始创建"


class TestOpportunityActivity:
    """销售机会活动模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_activity(self, db_session: AsyncSession):
        """测试创建活动"""
        # 创建必要的依赖数据
        customer = Customer(
            name="赵六",
            company="服务公司",
            industry="服务业",
            size=CompanySize.MEDIUM,
            status=CustomerStatus.PROSPECT
        )
        db_session.add(customer)
        
        stage = OpportunityStage(
            name="跟进阶段",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.2
        )
        db_session.add(stage)
        await db_session.flush()
        
        opportunity = Opportunity(
            name="咨询服务项目",
            customer_id=customer.id,
            stage_id=stage.id,
            value=50000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建活动
        activity = OpportunityActivity(
            opportunity_id=opportunity.id,
            activity_type="电话沟通",
            title="需求确认电话",
            description="与客户确认具体需求和预算",
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            duration_minutes=60,
            participants=["客户负责人", "销售代表"],
            organizer="sales002",
            outcome="需求明确",
            next_actions=[
                {
                    "action": "准备方案",
                    "assignee": "sales002",
                    "due_date": datetime.utcnow() + timedelta(days=3),
                    "priority": "high"
                }
            ],
            status="completed"
        )
        
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        assert activity.id is not None
        assert activity.opportunity_id == opportunity.id
        assert activity.activity_type == "电话沟通"
        assert activity.title == "需求确认电话"
        assert activity.duration_minutes == 60
        assert len(activity.participants) == 2
        assert activity.organizer == "sales002"
        assert activity.outcome == "需求明确"
        assert len(activity.next_actions) == 1
        assert activity.status == "completed"
        assert activity.created_at is not None
        assert activity.updated_at is not None


class TestOpportunityStageHistory:
    """销售机会阶段历史模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_stage_history(self, db_session: AsyncSession):
        """测试创建阶段历史"""
        # 创建必要的依赖数据
        customer = Customer(
            name="孙七",
            company="制造企业",
            industry="制造业",
            size=CompanySize.ENTERPRISE,
            status=CustomerStatus.QUALIFIED
        )
        db_session.add(customer)
        
        # 创建两个阶段
        stage1 = OpportunityStage(
            name="初步接触",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.1
        )
        stage2 = OpportunityStage(
            name="需求分析",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=2,
            probability=0.3
        )
        db_session.add_all([stage1, stage2])
        await db_session.flush()
        
        opportunity = Opportunity(
            name="生产管理系统",
            customer_id=customer.id,
            stage_id=stage2.id,
            value=1000000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建阶段历史记录
        stage_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            from_stage_id=stage1.id,
            to_stage_id=stage2.id,
            reason="客户需求明确",
            notes="客户已确认预算和时间计划",
            changed_by="sales003",
            duration_days=5
        )
        
        db_session.add(stage_history)
        await db_session.commit()
        await db_session.refresh(stage_history)
        
        assert stage_history.id is not None
        assert stage_history.opportunity_id == opportunity.id
        assert stage_history.from_stage_id == stage1.id
        assert stage_history.to_stage_id == stage2.id
        assert stage_history.reason == "客户需求明确"
        assert stage_history.notes == "客户已确认预算和时间计划"
        assert stage_history.changed_by == "sales003"
        assert stage_history.duration_days == 5
        assert stage_history.changed_at is not None
    
    @pytest.mark.asyncio
    async def test_stage_history_relationships(self, db_session: AsyncSession):
        """测试阶段历史关系"""
        # 创建必要的依赖数据
        customer = Customer(
            name="周八",
            company="科技企业",
            industry="科技",
            size=CompanySize.LARGE,
            status=CustomerStatus.CUSTOMER
        )
        db_session.add(customer)
        
        # 创建阶段
        from_stage = OpportunityStage(
            name="方案提议",
            stage_type=StageType.PROPOSAL,
            order=1,
            probability=0.5
        )
        to_stage = OpportunityStage(
            name="商务谈判",
            stage_type=StageType.NEGOTIATION,
            order=2,
            probability=0.7
        )
        db_session.add_all([from_stage, to_stage])
        await db_session.flush()
        
        opportunity = Opportunity(
            name="数字化转型项目",
            customer_id=customer.id,
            stage_id=to_stage.id,
            value=2000000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建阶段历史
        stage_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            from_stage_id=from_stage.id,
            to_stage_id=to_stage.id,
            reason="方案获得认可",
            changed_by="sales004",
            duration_days=10
        )
        db_session.add(stage_history)
        await db_session.commit()
        
        # 验证关系
        await db_session.refresh(stage_history)
        
        assert stage_history.opportunity is not None
        assert stage_history.from_stage is not None
        assert stage_history.to_stage is not None
        assert stage_history.opportunity.name == "数字化转型项目"
        assert stage_history.from_stage.name == "方案提议"
        assert stage_history.to_stage.name == "商务谈判"


class TestOpportunityEnums:
    """销售机会枚举测试"""
    
    def test_opportunity_status_enum(self):
        """测试机会状态枚举"""
        assert OpportunityStatus.OPEN == "open"
        assert OpportunityStatus.WON == "won"
        assert OpportunityStatus.LOST == "lost"
        assert OpportunityStatus.CANCELLED == "cancelled"
        
        # 测试所有状态值
        all_statuses = [status.value for status in OpportunityStatus]
        assert "open" in all_statuses
        assert "won" in all_statuses
        assert "lost" in all_statuses
        assert "cancelled" in all_statuses
    
    def test_opportunity_priority_enum(self):
        """测试机会优先级枚举"""
        assert OpportunityPriority.LOW == "low"
        assert OpportunityPriority.MEDIUM == "medium"
        assert OpportunityPriority.HIGH == "high"
        assert OpportunityPriority.CRITICAL == "critical"
        
        # 测试所有优先级值
        all_priorities = [priority.value for priority in OpportunityPriority]
        assert "low" in all_priorities
        assert "medium" in all_priorities
        assert "high" in all_priorities
        assert "critical" in all_priorities
    
    def test_stage_type_enum(self):
        """测试阶段类型枚举"""
        assert StageType.QUALIFICATION == "qualification"
        assert StageType.NEEDS_ANALYSIS == "needs_analysis"
        assert StageType.PROPOSAL == "proposal"
        assert StageType.NEGOTIATION == "negotiation"
        assert StageType.CLOSING == "closing"
        assert StageType.DELIVERY == "delivery"
        
        # 测试所有阶段类型值
        all_types = [stage_type.value for stage_type in StageType]
        assert "qualification" in all_types
        assert "needs_analysis" in all_types
        assert "proposal" in all_types
        assert "negotiation" in all_types
        assert "closing" in all_types
        assert "delivery" in all_types