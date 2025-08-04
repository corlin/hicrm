"""
销售机会服务测试
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.services.opportunity_service import (
    OpportunityService, OpportunityStageService, OpportunityActivityService
)
from src.models.opportunity import (
    Opportunity, OpportunityStage, OpportunityActivity, 
    OpportunityStageHistory, OpportunityStatus, OpportunityPriority, StageType
)
from src.models.customer import Customer, CompanySize, CustomerStatus
from src.schemas.opportunity import (
    OpportunityCreate, OpportunityUpdate, OpportunityStageCreate, 
    OpportunityStageUpdate, ActivityCreate, ActivityUpdate,
    StageTransitionRequest, ProductInfo, CompetitorInfo, StakeholderInfo, RiskInfo, NextAction
)
from src.core.exceptions import NotFoundError, ValidationError, BusinessLogicError


class TestOpportunityStageService:
    """销售机会阶段服务测试"""
    
    @pytest.mark.asyncio
    async def test_create_stage_success(self, db_session: AsyncSession):
        """测试成功创建销售机会阶段"""
        stage_service = OpportunityStageService(db_session)
        
        stage_data = OpportunityStageCreate(
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
        
        result = await stage_service.create_stage(stage_data)
        
        assert result.id is not None
        assert result.name == "需求分析"
        assert result.stage_type == StageType.NEEDS_ANALYSIS
        assert result.order == 1
        assert result.probability == 0.3
        assert len(result.requirements) == 2
        assert len(result.entry_criteria) == 1
        assert len(result.exit_criteria) == 1
        assert result.duration_days == 7
        assert result.is_active is True
        assert result.created_at is not None
        assert result.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_create_stage_duplicate_order(self, db_session: AsyncSession):
        """测试创建重复顺序的阶段"""
        stage_service = OpportunityStageService(db_session)
        
        # 先创建一个阶段
        stage1 = OpportunityStage(
            name="阶段1",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.2
        )
        db_session.add(stage1)
        await db_session.commit()
        
        # 尝试创建相同顺序的阶段
        stage_data = OpportunityStageCreate(
            name="阶段2",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,  # 重复的顺序
            probability=0.3
        )
        
        with pytest.raises(ValidationError) as exc_info:
            await stage_service.create_stage(stage_data)
        
        assert "阶段顺序 1 已存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_stage_success(self, db_session: AsyncSession):
        """测试成功获取销售机会阶段"""
        stage_service = OpportunityStageService(db_session)
        
        # 创建阶段
        stage = OpportunityStage(
            name="商务谈判",
            stage_type=StageType.NEGOTIATION,
            order=1,
            probability=0.7
        )
        db_session.add(stage)
        await db_session.commit()
        await db_session.refresh(stage)
        
        result = await stage_service.get_stage(str(stage.id))
        
        assert result.id == str(stage.id)
        assert result.name == "商务谈判"
        assert result.stage_type == StageType.NEGOTIATION
        assert result.probability == 0.7
    
    @pytest.mark.asyncio
    async def test_get_stage_not_found(self, db_session: AsyncSession):
        """测试获取不存在的阶段"""
        stage_service = OpportunityStageService(db_session)
        
        with pytest.raises(NotFoundError) as exc_info:
            await stage_service.get_stage("non-existent-id")
        
        assert "销售机会阶段不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_stages_active_only(self, db_session: AsyncSession):
        """测试获取活跃阶段列表"""
        stage_service = OpportunityStageService(db_session)
        
        # 创建活跃和非活跃阶段
        active_stage = OpportunityStage(
            name="活跃阶段",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.2,
            is_active=True
        )
        inactive_stage = OpportunityStage(
            name="非活跃阶段",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=2,
            probability=0.3,
            is_active=False
        )
        db_session.add_all([active_stage, inactive_stage])
        await db_session.commit()
        
        # 只获取活跃阶段
        result = await stage_service.get_stages(active_only=True)
        
        assert len(result) == 1
        assert result[0].name == "活跃阶段"
        assert result[0].is_active is True
        
        # 获取所有阶段
        all_result = await stage_service.get_stages(active_only=False)
        assert len(all_result) == 2
    
    @pytest.mark.asyncio
    async def test_update_stage_success(self, db_session: AsyncSession):
        """测试成功更新销售机会阶段"""
        stage_service = OpportunityStageService(db_session)
        
        # 创建阶段
        stage = OpportunityStage(
            name="原始阶段",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.2
        )
        db_session.add(stage)
        await db_session.commit()
        await db_session.refresh(stage)
        
        # 更新阶段
        update_data = OpportunityStageUpdate(
            name="更新后的阶段",
            probability=0.5,
            requirements=["新要求1", "新要求2"]
        )
        
        result = await stage_service.update_stage(str(stage.id), update_data)
        
        assert result.name == "更新后的阶段"
        assert result.probability == 0.5
        assert len(result.requirements) == 2
        assert result.stage_type == StageType.QUALIFICATION  # 未更新的字段保持不变
        assert result.order == 1
    
    @pytest.mark.asyncio
    async def test_update_stage_order_conflict(self, db_session: AsyncSession):
        """测试更新阶段顺序冲突"""
        stage_service = OpportunityStageService(db_session)
        
        # 创建两个阶段
        stage1 = OpportunityStage(
            name="阶段1",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.2
        )
        stage2 = OpportunityStage(
            name="阶段2",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=2,
            probability=0.3
        )
        db_session.add_all([stage1, stage2])
        await db_session.commit()
        await db_session.refresh(stage2)
        
        # 尝试将stage2的顺序更新为1（与stage1冲突）
        update_data = OpportunityStageUpdate(order=1)
        
        with pytest.raises(ValidationError) as exc_info:
            await stage_service.update_stage(str(stage2.id), update_data)
        
        assert "阶段顺序 1 已存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_stage_success(self, db_session: AsyncSession):
        """测试成功删除销售机会阶段"""
        stage_service = OpportunityStageService(db_session)
        
        # 创建阶段
        stage = OpportunityStage(
            name="待删除阶段",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.2
        )
        db_session.add(stage)
        await db_session.commit()
        await db_session.refresh(stage)
        
        result = await stage_service.delete_stage(str(stage.id))
        
        assert result is True
        
        # 验证阶段已被删除
        with pytest.raises(NotFoundError):
            await stage_service.get_stage(str(stage.id))
    
    @pytest.mark.asyncio
    async def test_delete_stage_with_opportunities(self, db_session: AsyncSession):
        """测试删除有机会使用的阶段"""
        stage_service = OpportunityStageService(db_session)
        
        # 创建客户和阶段
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="测试行业",
            size=CompanySize.MEDIUM,
            status=CustomerStatus.PROSPECT
        )
        stage = OpportunityStage(
            name="使用中的阶段",
            stage_type=StageType.QUALIFICATION,
            order=1,
            probability=0.2
        )
        db_session.add_all([customer, stage])
        await db_session.flush()
        
        # 创建使用该阶段的机会
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage.id,
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(stage)
        
        # 尝试删除阶段
        with pytest.raises(BusinessLogicError) as exc_info:
            await stage_service.delete_stage(str(stage.id))
        
        assert "无法删除正在使用的阶段" in str(exc_info.value)


class TestOpportunityService:
    """销售机会服务测试"""
    
    @pytest.mark.asyncio
    async def test_create_opportunity_success(self, db_session: AsyncSession):
        """测试成功创建销售机会"""
        opportunity_service = OpportunityService(db_session)
        
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
        
        # 创建机会数据
        opportunity_data = OpportunityCreate(
            name="CRM系统项目",
            description="为客户实施CRM系统",
            customer_id=str(customer.id),
            stage_id=str(stage.id),
            value=500000.0,
            probability=0.6,
            expected_close_date=datetime.now() + timedelta(days=30),
            priority=OpportunityPriority.HIGH,
            assigned_to="张三",
            tags=["CRM", "企业级"],
            products=[
                ProductInfo(
                    id="prod-1",
                    name="CRM标准版",
                    quantity=1,
                    unit_price=500000.0,
                    total_price=500000.0
                )
            ],
            stakeholders=[
                StakeholderInfo(
                    name="李总",
                    title="CTO",
                    role="技术决策者",
                    influence_level="high",
                    decision_power="high"
                )
            ]
        )
        
        result = await opportunity_service.create_opportunity(opportunity_data)
        
        assert result.id is not None
        assert result.name == "CRM系统项目"
        assert result.customer_id == str(customer.id)
        assert result.stage_id == str(stage.id)
        assert result.value == 500000.0
        assert result.probability == 0.6
        assert result.priority == OpportunityPriority.HIGH
        assert result.assigned_to == "张三"
        assert len(result.tags) == 2
        assert len(result.products) == 1
        assert len(result.stakeholders) == 1
        assert result.status == OpportunityStatus.OPEN
        assert result.created_at is not None
        assert result.updated_at is not None
        
        # 验证阶段历史记录被创建
        assert len(result.stage_history) == 1
        assert result.stage_history[0].to_stage_id == str(stage.id)
        assert result.stage_history[0].reason == "初始创建"
    
    @pytest.mark.asyncio
    async def test_create_opportunity_invalid_customer(self, db_session: AsyncSession):
        """测试创建机会时客户不存在"""
        opportunity_service = OpportunityService(db_session)
        
        # 创建阶段
        stage = OpportunityStage(
            name="需求分析",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,
            probability=0.3
        )
        db_session.add(stage)
        await db_session.flush()
        
        opportunity_data = OpportunityCreate(
            name="测试机会",
            customer_id="non-existent-customer",
            stage_id=str(stage.id),
            value=100000.0
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            await opportunity_service.create_opportunity(opportunity_data)
        
        assert "客户不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_opportunity_invalid_stage(self, db_session: AsyncSession):
        """测试创建机会时阶段不存在"""
        opportunity_service = OpportunityService(db_session)
        
        # 创建客户
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="测试行业",
            size=CompanySize.MEDIUM,
            status=CustomerStatus.PROSPECT
        )
        db_session.add(customer)
        await db_session.flush()
        
        opportunity_data = OpportunityCreate(
            name="测试机会",
            customer_id=str(customer.id),
            stage_id="non-existent-stage",
            value=100000.0
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            await opportunity_service.create_opportunity(opportunity_data)
        
        assert "销售机会阶段不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_opportunity_success(self, db_session: AsyncSession):
        """测试成功获取销售机会"""
        opportunity_service = OpportunityService(db_session)
        
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
        
        # 创建机会
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage.id,
            value=200000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        result = await opportunity_service.get_opportunity(str(opportunity.id))
        
        assert result.id == str(opportunity.id)
        assert result.name == "测试机会"
        assert result.value == 200000.0
        assert result.stage.name == "需求分析"
    
    @pytest.mark.asyncio
    async def test_get_opportunity_not_found(self, db_session: AsyncSession):
        """测试获取不存在的机会"""
        opportunity_service = OpportunityService(db_session)
        
        with pytest.raises(NotFoundError) as exc_info:
            await opportunity_service.get_opportunity("non-existent-id")
        
        assert "销售机会不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_opportunities_with_filters(self, db_session: AsyncSession):
        """测试带过滤条件的机会列表查询"""
        opportunity_service = OpportunityService(db_session)
        
        # 创建依赖数据
        customer1 = Customer(
            name="客户1",
            company="公司1",
            industry="制造业",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
        )
        customer2 = Customer(
            name="客户2",
            company="公司2",
            industry="服务业",
            size=CompanySize.MEDIUM,
            status=CustomerStatus.PROSPECT
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
        db_session.add_all([customer1, customer2, stage1, stage2])
        await db_session.flush()
        
        # 创建多个机会
        opportunities = [
            Opportunity(
                name="机会1",
                customer_id=customer1.id,
                stage_id=stage1.id,
                value=100000.0,
                status=OpportunityStatus.OPEN,
                assigned_to="张三"
            ),
            Opportunity(
                name="机会2",
                customer_id=customer1.id,
                stage_id=stage2.id,
                value=200000.0,
                status=OpportunityStatus.OPEN,
                assigned_to="李四"
            ),
            Opportunity(
                name="机会3",
                customer_id=customer2.id,
                stage_id=stage1.id,
                value=150000.0,
                status=OpportunityStatus.WON,
                assigned_to="张三"
            )
        ]
        db_session.add_all(opportunities)
        await db_session.commit()
        
        # 测试按客户过滤
        result = await opportunity_service.get_opportunities(customer_id=str(customer1.id))
        assert result["total"] == 2
        assert len(result["opportunities"]) == 2
        
        # 测试按阶段过滤
        result = await opportunity_service.get_opportunities(stage_id=str(stage1.id))
        assert result["total"] == 2
        
        # 测试按状态过滤
        result = await opportunity_service.get_opportunities(status=OpportunityStatus.WON)
        assert result["total"] == 1
        assert result["opportunities"][0].name == "机会3"
        
        # 测试按负责人过滤
        result = await opportunity_service.get_opportunities(assigned_to="张三")
        assert result["total"] == 2
        
        # 测试分页
        result = await opportunity_service.get_opportunities(page=1, size=1)
        assert result["total"] == 3
        assert len(result["opportunities"]) == 1
        assert result["pages"] == 3
    
    @pytest.mark.asyncio
    async def test_update_opportunity_success(self, db_session: AsyncSession):
        """测试成功更新销售机会"""
        opportunity_service = OpportunityService(db_session)
        
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
        
        # 创建机会
        opportunity = Opportunity(
            name="原始机会",
            customer_id=customer.id,
            stage_id=stage.id,
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        # 更新机会
        update_data = OpportunityUpdate(
            name="更新后的机会",
            value=200000.0,
            probability=0.8,
            tags=["更新", "测试"]
        )
        
        result = await opportunity_service.update_opportunity(str(opportunity.id), update_data)
        
        assert result.name == "更新后的机会"
        assert result.value == 200000.0
        assert result.probability == 0.8
        assert len(result.tags) == 2
        assert result.customer_id == str(customer.id)  # 未更新的字段保持不变
    
    @pytest.mark.asyncio
    async def test_update_opportunity_stage_transition(self, db_session: AsyncSession):
        """测试更新机会时的阶段转换"""
        opportunity_service = OpportunityService(db_session)
        
        # 创建依赖数据
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="制造业",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
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
        
        # 创建机会
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage1.id,
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        
        # 创建初始阶段历史
        initial_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            to_stage_id=stage1.id,
            reason="初始创建",
            changed_by="system"
        )
        db_session.add(initial_history)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        # 更新机会阶段
        update_data = OpportunityUpdate(
            stage_id=str(stage2.id),
            assigned_to="张三"
        )
        
        result = await opportunity_service.update_opportunity(str(opportunity.id), update_data)
        
        assert result.stage_id == str(stage2.id)
        assert result.stage.name == "方案提议"
        assert len(result.stage_history) == 2  # 初始 + 转换
        
        # 验证新的阶段历史记录
        latest_history = result.stage_history[-1]
        assert latest_history.from_stage_id == str(stage1.id)
        assert latest_history.to_stage_id == str(stage2.id)
        assert latest_history.reason == "手动更新"
    
    @pytest.mark.asyncio
    async def test_transition_stage_success(self, db_session: AsyncSession):
        """测试成功的阶段转换"""
        opportunity_service = OpportunityService(db_session)
        
        # 创建依赖数据
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="制造业",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
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
        
        # 创建机会
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage1.id,
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        # 执行阶段转换
        transition_request = StageTransitionRequest(
            opportunity_id=str(opportunity.id),
            to_stage_id=str(stage2.id),
            reason="客户确认需求",
            notes="客户对方案很满意",
            validate_criteria=False
        )
        
        result = await opportunity_service.transition_stage(transition_request)
        
        assert result.success is True
        assert "成功转换到阶段: 方案提议" in result.message
        assert result.opportunity is not None
        assert result.opportunity.stage_id == str(stage2.id)
        assert result.opportunity.probability == 0.6  # 使用新阶段的概率
        assert len(result.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_transition_stage_invalid_opportunity(self, db_session: AsyncSession):
        """测试转换不存在机会的阶段"""
        opportunity_service = OpportunityService(db_session)
        
        transition_request = StageTransitionRequest(
            opportunity_id="non-existent-id",
            to_stage_id="stage-id",
            validate_criteria=False
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            await opportunity_service.transition_stage(transition_request)
        
        assert "销售机会不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_transition_stage_invalid_target_stage(self, db_session: AsyncSession):
        """测试转换到不存在的阶段"""
        opportunity_service = OpportunityService(db_session)
        
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
        
        # 创建机会
        opportunity = Opportunity(
            name="测试机会",
            customer_id=customer.id,
            stage_id=stage.id,
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        transition_request = StageTransitionRequest(
            opportunity_id=str(opportunity.id),
            to_stage_id="non-existent-stage",
            validate_criteria=False
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            await opportunity_service.transition_stage(transition_request)
        
        assert "目标阶段不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, db_session: AsyncSession):
        """测试获取销售机会统计"""
        opportunity_service = OpportunityService(db_session)
        
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
        
        # 创建多个机会
        opportunities = [
            Opportunity(
                name="机会1",
                customer_id=customer.id,
                stage_id=stage.id,
                value=100000.0,
                probability=0.5,
                status=OpportunityStatus.OPEN,
                assigned_to="张三"
            ),
            Opportunity(
                name="机会2",
                customer_id=customer.id,
                stage_id=stage.id,
                value=200000.0,
                probability=0.8,
                status=OpportunityStatus.WON,
                assigned_to="李四",
                actual_close_date=datetime.now()
            ),
            Opportunity(
                name="机会3",
                customer_id=customer.id,
                stage_id=stage.id,
                value=150000.0,
                probability=0.3,
                status=OpportunityStatus.LOST,
                assigned_to="张三"
            )
        ]
        db_session.add_all(opportunities)
        await db_session.commit()
        
        result = await opportunity_service.get_statistics()
        
        assert result.total_opportunities == 3
        assert result.total_value == 450000.0
        assert result.weighted_value == 290000.0  # 100000*0.5 + 200000*0.8 + 150000*0.3
        assert result.by_status["open"] == 1
        assert result.by_status["won"] == 1
        assert result.by_status["lost"] == 1
        assert result.by_assigned["张三"] == 2
        assert result.by_assigned["李四"] == 1
        assert result.average_value == 150000.0
        assert result.win_rate == 1/3  # 1 won out of 3 total
    
    @pytest.mark.asyncio
    async def test_get_funnel_analysis(self, db_session: AsyncSession):
        """测试获取销售漏斗分析"""
        opportunity_service = OpportunityService(db_session)
        
        # 创建依赖数据
        customer = Customer(
            name="测试客户",
            company="测试公司",
            industry="制造业",
            size=CompanySize.LARGE,
            status=CustomerStatus.QUALIFIED
        )
        stage1 = OpportunityStage(
            name="需求分析",
            stage_type=StageType.NEEDS_ANALYSIS,
            order=1,
            probability=0.3,
            is_active=True
        )
        stage2 = OpportunityStage(
            name="方案提议",
            stage_type=StageType.PROPOSAL,
            order=2,
            probability=0.6,
            is_active=True
        )
        db_session.add_all([customer, stage1, stage2])
        await db_session.flush()
        
        # 创建机会
        opportunities = [
            Opportunity(
                name="机会1",
                customer_id=customer.id,
                stage_id=stage1.id,
                value=100000.0,
                probability=0.3,
                status=OpportunityStatus.OPEN
            ),
            Opportunity(
                name="机会2",
                customer_id=customer.id,
                stage_id=stage1.id,
                value=200000.0,
                probability=0.3,
                status=OpportunityStatus.OPEN
            ),
            Opportunity(
                name="机会3",
                customer_id=customer.id,
                stage_id=stage2.id,
                value=150000.0,
                probability=0.6,
                status=OpportunityStatus.OPEN
            )
        ]
        db_session.add_all(opportunities)
        await db_session.commit()
        
        result = await opportunity_service.get_funnel_analysis()
        
        assert len(result.funnel_stages) == 2
        assert result.total_pipeline_value == 450000.0
        assert result.weighted_pipeline_value == 180000.0  # 300000*0.3 + 150000*0.6
        
        # 验证第一个阶段
        stage1_analysis = result.funnel_stages[0]
        assert stage1_analysis.stage_name == "需求分析"
        assert stage1_analysis.opportunity_count == 2
        assert stage1_analysis.total_value == 300000.0
        assert stage1_analysis.weighted_value == 90000.0
        assert stage1_analysis.conversion_rate == 0.3
        
        # 验证第二个阶段
        stage2_analysis = result.funnel_stages[1]
        assert stage2_analysis.stage_name == "方案提议"
        assert stage2_analysis.opportunity_count == 1
        assert stage2_analysis.total_value == 150000.0
        assert stage2_analysis.weighted_value == 90000.0
        assert stage2_analysis.conversion_rate == 0.6


class TestOpportunityActivityService:
    """销售机会活动服务测试"""
    
    @pytest.mark.asyncio
    async def test_create_activity_success(self, db_session: AsyncSession):
        """测试成功创建活动"""
        activity_service = OpportunityActivityService(db_session)
        
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
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)
        
        # 创建活动数据
        activity_data = ActivityCreate(
            activity_type="meeting",
            title="需求调研会议",
            description="与客户讨论具体需求",
            scheduled_at=datetime.now() + timedelta(days=1),
            duration_minutes=120,
            participants=["张三", "李四", "客户代表"],
            organizer="张三",
            next_actions=[
                NextAction(
                    action="准备方案文档",
                    assignee="李四",
                    due_date=datetime.now() + timedelta(days=3),
                    priority="high"
                )
            ]
        )
        
        result = await activity_service.create_activity(str(opportunity.id), activity_data)
        
        assert result.id is not None
        assert result.opportunity_id == str(opportunity.id)
        assert result.activity_type == "meeting"
        assert result.title == "需求调研会议"
        assert result.duration_minutes == 120
        assert len(result.participants) == 3
        assert result.organizer == "张三"
        assert len(result.next_actions) == 1
        assert result.status == "planned"
        assert result.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_activity_invalid_opportunity(self, db_session: AsyncSession):
        """测试为不存在的机会创建活动"""
        activity_service = OpportunityActivityService(db_session)
        
        activity_data = ActivityCreate(
            activity_type="meeting",
            title="测试活动"
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            await activity_service.create_activity("non-existent-id", activity_data)
        
        assert "销售机会不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_activities(self, db_session: AsyncSession):
        """测试获取机会的所有活动"""
        activity_service = OpportunityActivityService(db_session)
        
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
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建多个活动
        activities = [
            OpportunityActivity(
                opportunity_id=opportunity.id,
                activity_type="meeting",
                title="活动1",
                scheduled_at=datetime.now() + timedelta(days=1)
            ),
            OpportunityActivity(
                opportunity_id=opportunity.id,
                activity_type="call",
                title="活动2",
                scheduled_at=datetime.now() + timedelta(days=2)
            )
        ]
        db_session.add_all(activities)
        await db_session.commit()
        
        result = await activity_service.get_activities(str(opportunity.id))
        
        assert len(result) == 2
        # 验证按时间倒序排列
        assert result[0].title == "活动2"
        assert result[1].title == "活动1"
    
    @pytest.mark.asyncio
    async def test_update_activity_success(self, db_session: AsyncSession):
        """测试成功更新活动"""
        activity_service = OpportunityActivityService(db_session)
        
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
            value=100000.0,
            status=OpportunityStatus.OPEN
        )
        db_session.add(opportunity)
        await db_session.flush()
        
        # 创建活动
        activity = OpportunityActivity(
            opportunity_id=opportunity.id,
            activity_type="meeting",
            title="原始活动",
            status="planned"
        )
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        # 更新活动
        update_data = ActivityUpdate(
            title="更新后的活动",
            status="completed",
            completed_at=datetime.now(),
            outcome="成功",
            next_actions=[
                NextAction(
                    action="跟进客户反馈",
                    assignee="张三",
                    priority="medium"
                )
            ]
        )
        
        result = await activity_service.update_activity(str(activity.id), update_data)
        
        assert result.title == "更新后的活动"
        assert result.status == "completed"
        assert result.completed_at is not None
        assert result.outcome == "成功"
        assert len(result.next_actions) == 1
        assert result.activity_type == "meeting"  # 未更新的字段保持不变
    
    @pytest.mark.asyncio
    async def test_update_activity_not_found(self, db_session: AsyncSession):
        """测试更新不存在的活动"""
        activity_service = OpportunityActivityService(db_session)
        
        update_data = ActivityUpdate(title="测试更新")
        
        with pytest.raises(NotFoundError) as exc_info:
            await activity_service.update_activity("non-existent-id", update_data)
        
        assert "活动不存在" in str(exc_info.value)