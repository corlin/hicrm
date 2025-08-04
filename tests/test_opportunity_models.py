"""
销售机会模型单元测试
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.models.opportunity import (
    Opportunity, OpportunityStage, OpportunityActivity, 
    OpportunityStageHistory, OpportunityStatus, OpportunityPriority, StageType
)
from src.models.customer import Customer, CompanySize, CustomerStatus


@pytest.fixture
async def async_engine():
    """创建异步测试数据库引擎"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """创建异步数据库会话"""
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


class TestOpportunityModels:
    """销售机会模型测试"""
    
    @pytest.mark.asyncio
    async def test_opportunity_stage_creation(self, db_session: AsyncSession):
        """测试销售机会阶段创建"""
        stage = OpportunityStage(
            name="需求分析",
            description="分析客户需求阶段",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,
            probability=0.3,
            requirements=["需求调研", "方案设计"],
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
        assert len(stage.requirements) == 2
        assert stage.is_active is True
        assert stage.created_at is not None
    
    @pytest.mark.asyncio
    async def test_opportunity_creation(self, db_session: AsyncSession):
        """测试销售机会创建"""
        # 创建依赖数据
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="制造业",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
        )
        
        stage = OpportunityStage(
            name="需求分析",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,
            probability=0.3
        )
        
        db_session.add_all([customer, stage])
        await db_session.flush()
        
        # 创建销售机会
        opportunity = Opportunity(
            name="CRM系统项目",
            description="为客户实施CRM系统",
            customer_id=customer.id,
            stage_id=stage.id,
            value=500000.0,
            probability=0.6,
            expected_close_date=datetime.now() + timedelta(days=30),
            status=OpportunityStatus.OPEN,
            priority=OpportunityPriority.HIGH,
            products=[{
                "id": "prod-1",
                "name": "CRM标准版",
                "quantity": 1,
                "unit_price": 500000.0
            }],
            stakeholders=[{
                "name": "李总",
                "title": "CTO",
                "role": "技术决策者",
                "influence_level": "high"
            }],
            assigned_to="张三",
            tags=["CRM", "企业级"]
        )
        
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        assert opportunity.id is not None
        assert opportunity.name == "CRM系统项目"
        assert opportunity.customer_id == customer.id
        assert opportunity.stage_id == stage.id
        assert opportunity.value == 500000.0
        assert opportunity.status == OpportunityStatus.OPEN
        assert opportunity.priority == OpportunityPriority.HIGH
        assert len(opportunity.products) == 1
        assert len(opportunity.stakeholders) == 1
        assert len(opportunity.tags) == 2
        assert opportunity.created_at is not None
    
    @pytest.mark.asyncio
    async def test_opportunity_activity_creation(self, db_session: AsyncSession):
        """测试销售机会活动创建"""
        # 创建依赖数据
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="制造业",
            size=CompanySize.MEDIUM,
            status=CustomerStatus.PROSPECT
        )
        
        stage = OpportunityStage(
            name="商务谈判",
            stage_type=StageType.NEGOTIATION,
            order=1,
            probability=0.7
        )
        
        db_session.add_all([customer, stage])
        await db_session.flush()
        
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage.id,
            value=200000.0,
            status=OpportunityStatus.OPEN
        )
        
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建活动
        activity = OpportunityActivity(
            opportunity_id=opportunity.id,
            activity_type="meeting",
            title="需求调研会议",
            description="与客户讨论具体需求",
            scheduled_at=datetime.now() + timedelta(days=1),
            duration_minutes=120,
            participants=["张三", "李四", "客户代表"],
            organizer="张三",
            status="planned"
        )
        
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        assert activity.id is not None
        assert activity.opportunity_id == opportunity.id
        assert activity.activity_type == "meeting"
        assert activity.title == "需求调研会议"
        assert activity.duration_minutes == 120
        assert len(activity.participants) == 3
        assert activity.organizer == "张三"
        assert activity.status == "planned"
        assert activity.created_at is not None
    
    @pytest.mark.asyncio
    async def test_opportunity_stage_history_creation(self, db_session: AsyncSession):
        """测试销售机会阶段历史创建"""
        # 创建依赖数据
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="服务业",
            size=CompanySize.SMALL,
            status=CustomerStatus.CUSTOMER
        )
        
        stage1 = OpportunityStage(
            name="需求分析",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,
            probability=0.3
        )
        
        stage2 = OpportunityStage(
            name="方案提议",
            stage_type=StageType.PROPOSAL,
            order=2,
            probability=0.6
        )
        
        db_session.add_all([customer, stage1, stage2])
        await db_session.flush()
        
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage1.id,
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建阶段历史记录
        stage_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            from_stage_id=stage1.id,
            to_stage_id=stage2.id,
            reason="客户确认需求",
            notes="客户对方案很满意",
            changed_by="张三",
            duration_days=5
        )
        
        db_session.add(stage_history)
        await db_session.commit()
        await db_session.refresh(stage_history)
        
        assert stage_history.id is not None
        assert stage_history.opportunity_id == opportunity.id
        assert stage_history.from_stage_id == stage1.id
        assert stage_history.to_stage_id == stage2.id
        assert stage_history.reason == "客户确认需求"
        assert stage_history.notes == "客户对方案很满意"
        assert stage_history.changed_by == "张三"
        assert stage_history.duration_days == 5
        assert stage_history.changed_at is not None
    
    @pytest.mark.asyncio
    async def test_opportunity_relationships(self, db_session: AsyncSession):
        """测试销售机会关系"""
        # 创建依赖数据
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="制造业",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
        )
        
        stage = OpportunityStage(
            name="需求分析",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,
            probability=0.3
        )
        
        db_session.add_all([customer, stage])
        await db_session.flush()
        
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage.id,
            value=300000.0,
            status=OpportunityStatus.OPEN
        )
        
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建活动
        activity = OpportunityActivity(
            opportunity_id=opportunity.id,
            activity_type="call",
            title="电话沟通",
            status="completed"
        )
        
        # 创建阶段历史
        stage_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            to_stage_id=stage.id,
            reason="初始创建",
            changed_by="system"
        )
        
        db_session.add_all([activity, stage_history])
        await db_session.commit()
        
        # 刷新数据以加载关系
        await db_session.refresh(opportunity)
        await db_session.refresh(customer)
        await db_session.refresh(stage)
        
        # 验证关系
        assert opportunity.customer_id == customer.id
        assert opportunity.stage_id == stage.id
        
        # 注意：由于我们使用的是简单的内存数据库，
        # 复杂的关系加载可能需要显式查询
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # 重新查询以加载关系
        result = await db_session.execute(
            select(Opportunity)
            .options(
                selectinload(Opportunity.activities),
                selectinload(Opportunity.stage_history)
            )
            .where(Opportunity.id == opportunity.id)
        )
        opportunity_with_relations = result.scalar_one()
        
        assert len(opportunity_with_relations.activities) == 1
        assert len(opportunity_with_relations.stage_history) == 1
        assert opportunity_with_relations.activities[0].title == "电话沟通"
        assert opportunity_with_relations.stage_history[0].reason == "初始创建"