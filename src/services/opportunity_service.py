"""
销售机会服务
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging

from src.models.opportunity import (
    Opportunity, OpportunityStage, OpportunityActivity, 
    OpportunityStageHistory, OpportunityStatus
)
from src.models.customer import Customer
from src.schemas.opportunity import (
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    OpportunityStageCreate, OpportunityStageUpdate, OpportunityStageResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
    StageTransitionRequest, StageTransitionResponse,
    OpportunityStatistics, FunnelAnalysis, FunnelAnalysisResponse
)
from src.core.exceptions import NotFoundError, ValidationError, BusinessLogicError

logger = logging.getLogger(__name__)


class OpportunityStageService:
    """销售机会阶段服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_stage(self, stage_data: OpportunityStageCreate) -> OpportunityStageResponse:
        """创建销售机会阶段"""
        try:
            # 检查阶段顺序是否已存在
            existing_stage = await self.db.execute(
                select(OpportunityStage).where(OpportunityStage.order == stage_data.order)
            )
            if existing_stage.scalar_one_or_none():
                raise ValidationError(f"阶段顺序 {stage_data.order} 已存在")
            
            # 创建阶段
            stage = OpportunityStage(**stage_data.model_dump())
            self.db.add(stage)
            await self.db.commit()
            await self.db.refresh(stage)
            
            logger.info(f"创建销售机会阶段成功: {stage.id}")
            return OpportunityStageResponse.model_validate(stage)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建销售机会阶段失败: {e}")
            raise
    
    async def get_stage(self, stage_id: str) -> OpportunityStageResponse:
        """获取销售机会阶段"""
        result = await self.db.execute(
            select(OpportunityStage).where(OpportunityStage.id == stage_id)
        )
        stage = result.scalar_one_or_none()
        
        if not stage:
            raise NotFoundError(f"销售机会阶段不存在: {stage_id}")
        
        return OpportunityStageResponse.model_validate(stage)
    
    async def get_stages(self, active_only: bool = True) -> List[OpportunityStageResponse]:
        """获取销售机会阶段列表"""
        query = select(OpportunityStage).order_by(OpportunityStage.order)
        
        if active_only:
            query = query.where(OpportunityStage.is_active == True)
        
        result = await self.db.execute(query)
        stages = result.scalars().all()
        
        return [OpportunityStageResponse.model_validate(stage) for stage in stages]
    
    async def update_stage(self, stage_id: str, stage_data: OpportunityStageUpdate) -> OpportunityStageResponse:
        """更新销售机会阶段"""
        try:
            result = await self.db.execute(
                select(OpportunityStage).where(OpportunityStage.id == stage_id)
            )
            stage = result.scalar_one_or_none()
            
            if not stage:
                raise NotFoundError(f"销售机会阶段不存在: {stage_id}")
            
            # 检查阶段顺序冲突
            if stage_data.order and stage_data.order != stage.order:
                existing_stage = await self.db.execute(
                    select(OpportunityStage).where(
                        and_(
                            OpportunityStage.order == stage_data.order,
                            OpportunityStage.id != stage_id
                        )
                    )
                )
                if existing_stage.scalar_one_or_none():
                    raise ValidationError(f"阶段顺序 {stage_data.order} 已存在")
            
            # 更新阶段
            update_data = stage_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(stage, field, value)
            
            stage.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(stage)
            
            logger.info(f"更新销售机会阶段成功: {stage_id}")
            return OpportunityStageResponse.model_validate(stage)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新销售机会阶段失败: {e}")
            raise
    
    async def delete_stage(self, stage_id: str) -> bool:
        """删除销售机会阶段"""
        try:
            result = await self.db.execute(
                select(OpportunityStage).where(OpportunityStage.id == stage_id)
            )
            stage = result.scalar_one_or_none()
            
            if not stage:
                raise NotFoundError(f"销售机会阶段不存在: {stage_id}")
            
            # 检查是否有机会使用此阶段
            opportunities_count = await self.db.execute(
                select(func.count(Opportunity.id)).where(Opportunity.stage_id == stage_id)
            )
            if opportunities_count.scalar() > 0:
                raise BusinessLogicError("无法删除正在使用的阶段")
            
            await self.db.delete(stage)
            await self.db.commit()
            
            logger.info(f"删除销售机会阶段成功: {stage_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除销售机会阶段失败: {e}")
            raise


class OpportunityService:
    """销售机会服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.stage_service = OpportunityStageService(db)
    
    async def create_opportunity(self, opportunity_data: OpportunityCreate) -> OpportunityResponse:
        """创建销售机会"""
        try:
            # 验证客户存在
            customer_result = await self.db.execute(
                select(Customer).where(Customer.id == opportunity_data.customer_id)
            )
            if not customer_result.scalar_one_or_none():
                raise NotFoundError(f"客户不存在: {opportunity_data.customer_id}")
            
            # 验证阶段存在
            stage_result = await self.db.execute(
                select(OpportunityStage).where(OpportunityStage.id == opportunity_data.stage_id)
            )
            stage = stage_result.scalar_one_or_none()
            if not stage:
                raise NotFoundError(f"销售机会阶段不存在: {opportunity_data.stage_id}")
            
            # 如果没有设置概率，使用阶段默认概率
            if opportunity_data.probability is None:
                opportunity_data.probability = stage.probability
            
            # 创建机会
            opportunity = Opportunity(**opportunity_data.model_dump())
            self.db.add(opportunity)
            await self.db.flush()
            
            # 创建阶段历史记录
            stage_history = OpportunityStageHistory(
                opportunity_id=opportunity.id,
                to_stage_id=opportunity_data.stage_id,
                reason="初始创建",
                changed_by=opportunity_data.assigned_to or "system"
            )
            self.db.add(stage_history)
            
            await self.db.commit()
            await self.db.refresh(opportunity)
            
            # 加载关联数据
            opportunity_with_relations = await self._get_opportunity_with_relations(opportunity.id)
            
            logger.info(f"创建销售机会成功: {opportunity.id}")
            return OpportunityResponse.model_validate(opportunity_with_relations)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建销售机会失败: {e}")
            raise
    
    async def get_opportunity(self, opportunity_id: str) -> OpportunityResponse:
        """获取销售机会"""
        opportunity = await self._get_opportunity_with_relations(opportunity_id)
        
        if not opportunity:
            raise NotFoundError(f"销售机会不存在: {opportunity_id}")
        
        return OpportunityResponse.model_validate(opportunity)
    
    async def _get_opportunity_with_relations(self, opportunity_id: str) -> Optional[Opportunity]:
        """获取包含关联数据的销售机会"""
        result = await self.db.execute(
            select(Opportunity)
            .options(
                selectinload(Opportunity.stage),
                selectinload(Opportunity.activities),
                selectinload(Opportunity.stage_history).selectinload(OpportunityStageHistory.from_stage),
                selectinload(Opportunity.stage_history).selectinload(OpportunityStageHistory.to_stage)
            )
            .where(Opportunity.id == opportunity_id)
        )
        return result.scalar_one_or_none()
    
    async def get_opportunities(
        self,
        customer_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        status: Optional[OpportunityStatus] = None,
        assigned_to: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """获取销售机会列表"""
        query = select(Opportunity).options(
            selectinload(Opportunity.stage),
            selectinload(Opportunity.activities),
            selectinload(Opportunity.stage_history)
        )
        
        # 添加过滤条件
        conditions = []
        if customer_id:
            conditions.append(Opportunity.customer_id == customer_id)
        if stage_id:
            conditions.append(Opportunity.stage_id == stage_id)
        if status:
            conditions.append(Opportunity.status == status)
        if assigned_to:
            conditions.append(Opportunity.assigned_to == assigned_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 计算总数
        count_query = select(func.count(Opportunity.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.order_by(desc(Opportunity.created_at))
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        opportunities = result.scalars().all()
        
        return {
            "opportunities": [OpportunityResponse.model_validate(opp) for opp in opportunities],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    async def update_opportunity(self, opportunity_id: str, opportunity_data: OpportunityUpdate) -> OpportunityResponse:
        """更新销售机会"""
        try:
            result = await self.db.execute(
                select(Opportunity).where(Opportunity.id == opportunity_id)
            )
            opportunity = result.scalar_one_or_none()
            
            if not opportunity:
                raise NotFoundError(f"销售机会不存在: {opportunity_id}")
            
            # 验证客户存在（如果更新了客户ID）
            if opportunity_data.customer_id and opportunity_data.customer_id != opportunity.customer_id:
                customer_result = await self.db.execute(
                    select(Customer).where(Customer.id == opportunity_data.customer_id)
                )
                if not customer_result.scalar_one_or_none():
                    raise NotFoundError(f"客户不存在: {opportunity_data.customer_id}")
            
            # 处理阶段变更
            if opportunity_data.stage_id and opportunity_data.stage_id != opportunity.stage_id:
                await self._handle_stage_transition(
                    opportunity, 
                    opportunity_data.stage_id,
                    "手动更新",
                    opportunity_data.assigned_to or "system"
                )
            
            # 更新机会
            update_data = opportunity_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(opportunity, field, value)
            
            opportunity.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # 获取更新后的数据
            opportunity_with_relations = await self._get_opportunity_with_relations(opportunity_id)
            
            logger.info(f"更新销售机会成功: {opportunity_id}")
            return OpportunityResponse.model_validate(opportunity_with_relations)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新销售机会失败: {e}")
            raise
    
    async def transition_stage(self, transition_request: StageTransitionRequest) -> StageTransitionResponse:
        """阶段转换"""
        try:
            # 获取机会
            result = await self.db.execute(
                select(Opportunity)
                .options(selectinload(Opportunity.stage))
                .where(Opportunity.id == transition_request.opportunity_id)
            )
            opportunity = result.scalar_one_or_none()
            
            if not opportunity:
                raise NotFoundError(f"销售机会不存在: {transition_request.opportunity_id}")
            
            # 获取目标阶段
            stage_result = await self.db.execute(
                select(OpportunityStage).where(OpportunityStage.id == transition_request.to_stage_id)
            )
            to_stage = stage_result.scalar_one_or_none()
            
            if not to_stage:
                raise NotFoundError(f"目标阶段不存在: {transition_request.to_stage_id}")
            
            # 验证转换标准
            validation_errors = []
            if transition_request.validate_criteria:
                validation_errors = await self._validate_stage_transition(
                    opportunity, to_stage
                )
            
            if validation_errors:
                return StageTransitionResponse(
                    success=False,
                    message="阶段转换验证失败",
                    validation_errors=validation_errors
                )
            
            # 执行阶段转换
            await self._handle_stage_transition(
                opportunity,
                transition_request.to_stage_id,
                transition_request.reason or "阶段转换",
                "system",
                transition_request.notes
            )
            
            # 更新机会概率
            opportunity.probability = to_stage.probability
            opportunity.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # 获取更新后的数据
            opportunity_with_relations = await self._get_opportunity_with_relations(opportunity.id)
            
            logger.info(f"阶段转换成功: {opportunity.id} -> {to_stage.name}")
            return StageTransitionResponse(
                success=True,
                message=f"成功转换到阶段: {to_stage.name}",
                opportunity=OpportunityResponse.model_validate(opportunity_with_relations)
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"阶段转换失败: {e}")
            raise
    
    async def _handle_stage_transition(
        self, 
        opportunity: Opportunity, 
        to_stage_id: str, 
        reason: str,
        changed_by: str,
        notes: Optional[str] = None
    ):
        """处理阶段转换逻辑"""
        # 计算在当前阶段的停留时间
        duration_days = None
        if opportunity.stage_id:
            # 获取最后一次进入当前阶段的时间
            last_entry_result = await self.db.execute(
                select(OpportunityStageHistory)
                .where(
                    and_(
                        OpportunityStageHistory.opportunity_id == opportunity.id,
                        OpportunityStageHistory.to_stage_id == opportunity.stage_id
                    )
                )
                .order_by(desc(OpportunityStageHistory.changed_at))
                .limit(1)
            )
            last_entry = last_entry_result.scalar_one_or_none()
            
            if last_entry:
                duration_days = (datetime.utcnow() - last_entry.changed_at).days
        
        # 创建阶段历史记录
        stage_history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            from_stage_id=opportunity.stage_id,
            to_stage_id=to_stage_id,
            reason=reason,
            notes=notes,
            changed_by=changed_by,
            duration_days=duration_days
        )
        self.db.add(stage_history)
        
        # 更新机会阶段
        opportunity.stage_id = to_stage_id
    
    async def _validate_stage_transition(
        self, 
        opportunity: Opportunity, 
        to_stage: OpportunityStage
    ) -> List[str]:
        """验证阶段转换标准"""
        errors = []
        
        # 检查退出标准（当前阶段）
        if opportunity.stage and opportunity.stage.exit_criteria:
            for criterion in opportunity.stage.exit_criteria:
                # 这里可以实现具体的验证逻辑
                # 例如检查必需的活动是否完成、文档是否上传等
                pass
        
        # 检查进入标准（目标阶段）
        if to_stage.entry_criteria:
            for criterion in to_stage.entry_criteria:
                # 这里可以实现具体的验证逻辑
                pass
        
        return errors
    
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        assigned_to: Optional[str] = None
    ) -> OpportunityStatistics:
        """获取销售机会统计"""
        # 构建基础查询条件
        conditions = []
        if start_date:
            conditions.append(Opportunity.created_at >= start_date)
        if end_date:
            conditions.append(Opportunity.created_at <= end_date)
        if assigned_to:
            conditions.append(Opportunity.assigned_to == assigned_to)
        
        base_query = select(Opportunity)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # 总机会数和总价值
        result = await self.db.execute(base_query)
        opportunities = result.scalars().all()
        
        total_opportunities = len(opportunities)
        total_value = sum(opp.value for opp in opportunities)
        weighted_value = sum(opp.value * (opp.probability or 0) for opp in opportunities)
        
        # 按状态统计
        by_status = {}
        for status in OpportunityStatus:
            count = len([opp for opp in opportunities if opp.status == status])
            by_status[status.value] = count
        
        # 按阶段统计
        stage_counts = {}
        for opp in opportunities:
            stage_name = opp.stage.name if opp.stage else "未知"
            stage_counts[stage_name] = stage_counts.get(stage_name, 0) + 1
        
        # 按负责人统计
        assigned_counts = {}
        for opp in opportunities:
            assignee = opp.assigned_to or "未分配"
            assigned_counts[assignee] = assigned_counts.get(assignee, 0) + 1
        
        # 计算平均值和比率
        average_value = total_value / total_opportunities if total_opportunities > 0 else 0
        won_count = by_status.get("won", 0)
        win_rate = won_count / total_opportunities if total_opportunities > 0 else 0
        
        # 计算平均销售周期
        closed_opportunities = [opp for opp in opportunities if opp.actual_close_date]
        if closed_opportunities:
            total_cycle_days = sum(
                (opp.actual_close_date - opp.created_at).days 
                for opp in closed_opportunities
            )
            average_sales_cycle = total_cycle_days / len(closed_opportunities)
        else:
            average_sales_cycle = 0
        
        # 时间范围统计
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        created_this_month = len([
            opp for opp in opportunities 
            if opp.created_at >= month_start
        ])
        
        expected_close_this_month = len([
            opp for opp in opportunities 
            if opp.expected_close_date and 
            opp.expected_close_date >= month_start and 
            opp.expected_close_date < month_start + timedelta(days=32)
        ])
        
        return OpportunityStatistics(
            total_opportunities=total_opportunities,
            total_value=total_value,
            weighted_value=weighted_value,
            by_status=by_status,
            by_stage=stage_counts,
            by_priority={},  # 可以添加优先级统计
            by_assigned=assigned_counts,
            average_value=average_value,
            win_rate=win_rate,
            average_sales_cycle=average_sales_cycle,
            created_this_month=created_this_month,
            expected_close_this_month=expected_close_this_month
        )
    
    async def get_funnel_analysis(self) -> FunnelAnalysisResponse:
        """获取销售漏斗分析"""
        # 获取所有活跃阶段
        stages_result = await self.db.execute(
            select(OpportunityStage)
            .where(OpportunityStage.is_active == True)
            .order_by(OpportunityStage.order)
        )
        stages = stages_result.scalars().all()
        
        funnel_stages = []
        total_pipeline_value = 0
        weighted_pipeline_value = 0
        
        for stage in stages:
            # 获取该阶段的机会
            opportunities_result = await self.db.execute(
                select(Opportunity)
                .where(
                    and_(
                        Opportunity.stage_id == stage.id,
                        Opportunity.status == OpportunityStatus.OPEN
                    )
                )
            )
            opportunities = opportunities_result.scalars().all()
            
            opportunity_count = len(opportunities)
            stage_total_value = sum(opp.value for opp in opportunities)
            stage_weighted_value = sum(opp.value * (opp.probability or 0) for opp in opportunities)
            
            # 计算转化率（简化版本，可以根据实际需求优化）
            conversion_rate = stage.probability
            
            # 计算平均停留时间
            average_duration = await self._calculate_average_stage_duration(stage.id)
            
            funnel_stages.append(FunnelAnalysis(
                stage_id=str(stage.id),
                stage_name=stage.name,
                opportunity_count=opportunity_count,
                total_value=stage_total_value,
                weighted_value=stage_weighted_value,
                conversion_rate=conversion_rate,
                average_duration=average_duration
            ))
            
            total_pipeline_value += stage_total_value
            weighted_pipeline_value += stage_weighted_value
        
        # 计算整体转化率
        if funnel_stages:
            overall_conversion_rate = sum(stage.conversion_rate for stage in funnel_stages) / len(funnel_stages)
        else:
            overall_conversion_rate = 0
        
        return FunnelAnalysisResponse(
            funnel_stages=funnel_stages,
            overall_conversion_rate=overall_conversion_rate,
            total_pipeline_value=total_pipeline_value,
            weighted_pipeline_value=weighted_pipeline_value,
            analysis_date=datetime.utcnow()
        )
    
    async def _calculate_average_stage_duration(self, stage_id: str) -> float:
        """计算阶段平均停留时间"""
        result = await self.db.execute(
            select(OpportunityStageHistory.duration_days)
            .where(
                and_(
                    OpportunityStageHistory.from_stage_id == stage_id,
                    OpportunityStageHistory.duration_days.isnot(None)
                )
            )
        )
        durations = result.scalars().all()
        
        if durations:
            return sum(durations) / len(durations)
        return 0.0


class OpportunityActivityService:
    """销售机会活动服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_activity(self, opportunity_id: str, activity_data: ActivityCreate) -> ActivityResponse:
        """创建活动"""
        try:
            # 验证机会存在
            opportunity_result = await self.db.execute(
                select(Opportunity).where(Opportunity.id == opportunity_id)
            )
            if not opportunity_result.scalar_one_or_none():
                raise NotFoundError(f"销售机会不存在: {opportunity_id}")
            
            # 创建活动
            activity = OpportunityActivity(
                opportunity_id=opportunity_id,
                **activity_data.model_dump()
            )
            self.db.add(activity)
            await self.db.commit()
            await self.db.refresh(activity)
            
            logger.info(f"创建活动成功: {activity.id}")
            return ActivityResponse.model_validate(activity)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建活动失败: {e}")
            raise
    
    async def get_activities(self, opportunity_id: str) -> List[ActivityResponse]:
        """获取机会的所有活动"""
        result = await self.db.execute(
            select(OpportunityActivity)
            .where(OpportunityActivity.opportunity_id == opportunity_id)
            .order_by(desc(OpportunityActivity.scheduled_at))
        )
        activities = result.scalars().all()
        
        return [ActivityResponse.model_validate(activity) for activity in activities]
    
    async def update_activity(self, activity_id: str, activity_data: ActivityUpdate) -> ActivityResponse:
        """更新活动"""
        try:
            result = await self.db.execute(
                select(OpportunityActivity).where(OpportunityActivity.id == activity_id)
            )
            activity = result.scalar_one_or_none()
            
            if not activity:
                raise NotFoundError(f"活动不存在: {activity_id}")
            
            # 更新活动
            update_data = activity_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(activity, field, value)
            
            activity.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(activity)
            
            logger.info(f"更新活动成功: {activity_id}")
            return ActivityResponse.model_validate(activity)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新活动失败: {e}")
            raise