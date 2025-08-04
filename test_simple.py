#!/usr/bin/env python3
"""
简单的opportunity模型测试
"""

import sys
import os
sys.path.append('.')

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from src.core.database import Base
from src.models.opportunity import (
    Opportunity, OpportunityStage, OpportunityActivity, 
    OpportunityStageHistory, OpportunityStatus, OpportunityPriority, StageType
)
from src.models.customer import Customer, CompanySize, CustomerStatus


async def test_opportunity_models():
    """测试opportunity模型"""
    print("开始测试opportunity模型...")
    
    # 创建内存数据库
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 测试1: 创建阶段
        print("测试1: 创建销售机会阶段...")
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
        
        session.add(stage)
        await session.commit()
        await session.refresh(stage)
        
        assert stage.id is not None
        assert stage.name == "需求分析"
        assert stage.stage_type == StageType.NEEDS_ANALYSIS
        print("✓ 阶段创建测试通过")
        
        # 测试2: 创建客户
        print("测试2: 创建客户...")
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="制造业",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
        )
        
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        
        assert customer.id is not None
        assert customer.name == "测试客户"
        print("✓ 客户创建测试通过")
        
        # 测试3: 创建销售机会
        print("测试3: 创建销售机会...")
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
        
        session.add(opportunity)
        await session.commit()
        await session.refresh(opportunity)
        
        assert opportunity.id is not None
        assert opportunity.name == "CRM系统项目"
        assert opportunity.value == 500000.0
        print("✓ 销售机会创建测试通过")
        
        # 测试4: 创建活动
        print("测试4: 创建销售机会活动...")
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
        
        session.add(activity)
        await session.commit()
        await session.refresh(activity)
        
        assert activity.id is not None
        assert activity.title == "需求调研会议"
        print("✓ 活动创建测试通过")
        
        # 测试5: 创建阶段历史
        print("测试5: 创建阶段历史...")
        stage_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            to_stage_id=stage.id,
            reason="初始创建",
            changed_by="system"
        )
        
        session.add(stage_history)
        await session.commit()
        await session.refresh(stage_history)
        
        assert stage_history.id is not None
        assert stage_history.reason == "初始创建"
        print("✓ 阶段历史创建测试通过")
    
    await engine.dispose()
    print("所有测试通过! ✓")


if __name__ == "__main__":
    asyncio.run(test_opportunity_models())