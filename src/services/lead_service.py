"""
线索管理服务
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from uuid import UUID

from src.models.lead import Lead, LeadScore, LeadInteraction, LeadStatus, LeadSource
from src.schemas.lead import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    InteractionCreate, InteractionResponse, LeadStatistics,
    LeadAssignmentRequest, LeadAssignmentResponse
)
from src.services.lead_scoring_service import LeadScoringService

logger = logging.getLogger(__name__)


class LeadService:
    """线索管理服务"""
    
    def __init__(self):
        self.scoring_service = LeadScoringService()
    
    async def create_lead(
        self, 
        lead_data: LeadCreate, 
        db: AsyncSession
    ) -> LeadResponse:
        """创建线索"""
        try:
            # 创建线索实体
            lead = Lead(
                name=lead_data.name,
                company=lead_data.company,
                title=lead_data.title,
                industry=lead_data.industry,
                contact=lead_data.contact.dict() if lead_data.contact else None,
                company_info=lead_data.company_info.dict() if lead_data.company_info else None,
                requirements=lead_data.requirements,
                budget=lead_data.budget,
                timeline=lead_data.timeline,
                source=lead_data.source,
                status=lead_data.status or LeadStatus.NEW,
                assigned_to=lead_data.assigned_to,
                tags=lead_data.tags,
                notes=lead_data.notes,
                custom_fields=lead_data.custom_fields
            )
            
            if lead.assigned_to:
                lead.assigned_at = datetime.utcnow()
            
            db.add(lead)
            await db.commit()
            await db.refresh(lead)
            
            # 异步计算评分
            try:
                score_detail = await self.scoring_service.calculate_lead_score(lead, db)
                logger.info(f"线索创建成功并完成评分: lead_id={lead.id}, score={score_detail.total_score}")
            except Exception as e:
                logger.warning(f"线索评分计算失败: lead_id={lead.id}, error={str(e)}")
                score_detail = None
            
            # 转换为响应模型
            response = await self._convert_to_response(lead, db, score_detail)
            return response
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建线索失败: error={str(e)}")
            raise
    
    async def get_lead(
        self, 
        lead_id: str, 
        db: AsyncSession,
        include_score: bool = True,
        include_interactions: bool = True
    ) -> Optional[LeadResponse]:
        """获取线索详情"""
        try:
            # 构建查询
            stmt = select(Lead).where(Lead.id == lead_id)
            
            if include_interactions:
                stmt = stmt.options(selectinload(Lead.interactions))
            
            result = await db.execute(stmt)
            lead = result.scalar_one_or_none()
            
            if not lead:
                return None
            
            # 获取评分信息
            score_detail = None
            if include_score:
                try:
                    score_detail = await self.scoring_service.calculate_lead_score(lead, db)
                except Exception as e:
                    logger.warning(f"获取线索评分失败: lead_id={lead_id}, error={str(e)}")
            
            return await self._convert_to_response(lead, db, score_detail)
            
        except Exception as e:
            logger.error(f"获取线索失败: lead_id={lead_id}, error={str(e)}")
            raise
    
    async def update_lead(
        self, 
        lead_id: str, 
        lead_data: LeadUpdate, 
        db: AsyncSession
    ) -> Optional[LeadResponse]:
        """更新线索"""
        try:
            # 获取现有线索
            stmt = select(Lead).where(Lead.id == lead_id)
            result = await db.execute(stmt)
            lead = result.scalar_one_or_none()
            
            if not lead:
                return None
            
            # 记录是否需要重新计算评分
            need_recalculate = False
            
            # 更新字段
            update_data = lead_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['contact', 'company_info'] and value:
                    value = value.dict() if hasattr(value, 'dict') else value
                
                if hasattr(lead, field):
                    old_value = getattr(lead, field)
                    setattr(lead, field, value)
                    
                    # 检查是否影响评分的关键字段
                    if field in ['budget', 'industry', 'timeline', 'company_info', 'contact']:
                        if old_value != value:
                            need_recalculate = True
            
            # 处理分配时间
            if lead_data.assigned_to is not None:
                if lead.assigned_to != lead_data.assigned_to:
                    lead.assigned_at = datetime.utcnow() if lead_data.assigned_to else None
            
            lead.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(lead)
            
            # 重新计算评分（如果需要）
            score_detail = None
            if need_recalculate:
                try:
                    score_detail = await self.scoring_service.calculate_lead_score(
                        lead, db, force_recalculate=True
                    )
                    logger.info(f"线索更新后重新计算评分: lead_id={lead_id}, score={score_detail.total_score}")
                except Exception as e:
                    logger.warning(f"线索评分重新计算失败: lead_id={lead_id}, error={str(e)}")
            
            return await self._convert_to_response(lead, db, score_detail)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新线索失败: lead_id={lead_id}, error={str(e)}")
            raise
    
    async def delete_lead(self, lead_id: str, db: AsyncSession) -> bool:
        """删除线索"""
        try:
            stmt = select(Lead).where(Lead.id == lead_id)
            result = await db.execute(stmt)
            lead = result.scalar_one_or_none()
            
            if not lead:
                return False
            
            await db.delete(lead)
            await db.commit()
            
            logger.info(f"线索删除成功: lead_id={lead_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"删除线索失败: lead_id={lead_id}, error={str(e)}")
            raise
    
    async def list_leads(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        assigned_to: Optional[str] = None,
        industry: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> LeadListResponse:
        """获取线索列表"""
        try:
            # 构建基础查询
            stmt = select(Lead)
            count_stmt = select(func.count(Lead.id))
            
            # 添加过滤条件
            conditions = []
            
            if status:
                conditions.append(Lead.status == status)
            
            if source:
                conditions.append(Lead.source == source)
            
            if assigned_to:
                conditions.append(Lead.assigned_to == assigned_to)
            
            if industry:
                conditions.append(Lead.industry.ilike(f"%{industry}%"))
            
            if search:
                search_condition = or_(
                    Lead.name.ilike(f"%{search}%"),
                    Lead.company.ilike(f"%{search}%"),
                    Lead.requirements.ilike(f"%{search}%")
                )
                conditions.append(search_condition)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))
            
            # 处理评分过滤（需要关联查询）
            if min_score is not None or max_score is not None:
                # 子查询获取最新评分
                latest_score_subq = (
                    select(
                        LeadScore.lead_id,
                        LeadScore.total_score,
                        func.row_number().over(
                            partition_by=LeadScore.lead_id,
                            order_by=desc(LeadScore.calculated_at)
                        ).label('rn')
                    ).subquery()
                )
                
                latest_score = select(
                    latest_score_subq.c.lead_id,
                    latest_score_subq.c.total_score
                ).where(latest_score_subq.c.rn == 1).subquery()
                
                stmt = stmt.join(latest_score, Lead.id == latest_score.c.lead_id)
                count_stmt = count_stmt.join(latest_score, Lead.id == latest_score.c.lead_id)
                
                if min_score is not None:
                    stmt = stmt.where(latest_score.c.total_score >= min_score)
                    count_stmt = count_stmt.where(latest_score.c.total_score >= min_score)
                
                if max_score is not None:
                    stmt = stmt.where(latest_score.c.total_score <= max_score)
                    count_stmt = count_stmt.where(latest_score.c.total_score <= max_score)
            
            # 排序
            if sort_order.lower() == "desc":
                order_func = desc
            else:
                order_func = asc
            
            if hasattr(Lead, sort_by):
                stmt = stmt.order_by(order_func(getattr(Lead, sort_by)))
            else:
                stmt = stmt.order_by(desc(Lead.created_at))
            
            # 分页
            offset = (page - 1) * size
            stmt = stmt.offset(offset).limit(size)
            
            # 执行查询
            result = await db.execute(stmt)
            leads = result.scalars().all()
            
            count_result = await db.execute(count_stmt)
            total = count_result.scalar()
            
            # 转换为响应模型
            lead_responses = []
            for lead in leads:
                try:
                    # 获取最新评分（可选）
                    score_detail = await self.scoring_service.calculate_lead_score(lead, db)
                    response = await self._convert_to_response(lead, db, score_detail)
                    lead_responses.append(response)
                except Exception as e:
                    logger.warning(f"转换线索响应失败: lead_id={lead.id}, error={str(e)}")
                    # 不包含评分信息
                    response = await self._convert_to_response(lead, db, None)
                    lead_responses.append(response)
            
            pages = (total + size - 1) // size
            
            return LeadListResponse(
                leads=lead_responses,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"获取线索列表失败: error={str(e)}")
            raise
    
    async def assign_leads(
        self,
        assignment: LeadAssignmentRequest,
        db: AsyncSession
    ) -> LeadAssignmentResponse:
        """批量分配线索"""
        try:
            success_count = 0
            failed_count = 0
            failed_leads = []
            
            for lead_id in assignment.lead_ids:
                try:
                    stmt = select(Lead).where(Lead.id == lead_id)
                    result = await db.execute(stmt)
                    lead = result.scalar_one_or_none()
                    
                    if lead:
                        lead.assigned_to = assignment.assigned_to
                        lead.assigned_at = datetime.utcnow()
                        lead.updated_at = datetime.utcnow()
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_leads.append(lead_id)
                        
                except Exception as e:
                    logger.error(f"分配线索失败: lead_id={lead_id}, error={str(e)}")
                    failed_count += 1
                    failed_leads.append(lead_id)
            
            await db.commit()
            
            message = f"成功分配 {success_count} 个线索"
            if failed_count > 0:
                message += f"，失败 {failed_count} 个"
            
            logger.info(f"批量分配线索完成: success={success_count}, failed={failed_count}")
            
            return LeadAssignmentResponse(
                success_count=success_count,
                failed_count=failed_count,
                failed_leads=failed_leads,
                message=message
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"批量分配线索失败: error={str(e)}")
            raise
    
    async def add_interaction(
        self,
        lead_id: str,
        interaction_data: InteractionCreate,
        db: AsyncSession
    ) -> Optional[InteractionResponse]:
        """添加线索互动记录"""
        try:
            # 检查线索是否存在
            stmt = select(Lead).where(Lead.id == lead_id)
            result = await db.execute(stmt)
            lead = result.scalar_one_or_none()
            
            if not lead:
                return None
            
            # 创建互动记录
            interaction = LeadInteraction(
                lead_id=lead_id,
                interaction_type=interaction_data.interaction_type,
                channel=interaction_data.channel,
                direction=interaction_data.direction,
                subject=interaction_data.subject,
                content=interaction_data.content,
                outcome=interaction_data.outcome,
                next_action=interaction_data.next_action,
                participant=interaction_data.participant,
                interaction_at=interaction_data.interaction_at or datetime.utcnow()
            )
            
            db.add(interaction)
            
            # 更新线索的最后更新时间
            lead.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(interaction)
            
            logger.info(f"添加线索互动记录成功: lead_id={lead_id}, interaction_id={interaction.id}")
            
            return InteractionResponse(
                id=str(interaction.id),
                lead_id=str(interaction.lead_id),
                interaction_type=interaction.interaction_type,
                channel=interaction.channel,
                direction=interaction.direction,
                subject=interaction.subject,
                content=interaction.content,
                outcome=interaction.outcome,
                next_action=interaction.next_action,
                participant=interaction.participant,
                interaction_at=interaction.interaction_at,
                created_at=interaction.created_at
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"添加线索互动记录失败: lead_id={lead_id}, error={str(e)}")
            raise
    
    async def get_lead_statistics(self, db: AsyncSession) -> LeadStatistics:
        """获取线索统计信息"""
        try:
            # 总线索数
            total_stmt = select(func.count(Lead.id))
            total_result = await db.execute(total_stmt)
            total_leads = total_result.scalar()
            
            # 按状态统计
            status_stmt = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
            status_result = await db.execute(status_stmt)
            by_status = {status: count for status, count in status_result.fetchall()}
            
            # 按来源统计
            source_stmt = select(Lead.source, func.count(Lead.id)).group_by(Lead.source)
            source_result = await db.execute(source_stmt)
            by_source = {source.value: count for source, count in source_result.fetchall()}
            
            # 按分配人统计
            assigned_stmt = select(Lead.assigned_to, func.count(Lead.id)).where(
                Lead.assigned_to.isnot(None)
            ).group_by(Lead.assigned_to)
            assigned_result = await db.execute(assigned_stmt)
            by_assigned = {assigned: count for assigned, count in assigned_result.fetchall()}
            
            # 平均评分
            avg_score_stmt = select(func.avg(LeadScore.total_score)).select_from(
                select(
                    LeadScore.lead_id,
                    LeadScore.total_score,
                    func.row_number().over(
                        partition_by=LeadScore.lead_id,
                        order_by=desc(LeadScore.calculated_at)
                    ).label('rn')
                ).subquery()
            ).where(LeadScore.rn == 1)
            
            avg_score_result = await db.execute(avg_score_stmt)
            average_score = avg_score_result.scalar() or 0.0
            
            # 转化率
            converted_count = by_status.get(LeadStatus.CONVERTED.value, 0)
            conversion_rate = (converted_count / total_leads * 100) if total_leads > 0 else 0.0
            
            # 时间统计
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=now.weekday())
            month_start = today_start.replace(day=1)
            
            # 今日新增
            today_stmt = select(func.count(Lead.id)).where(Lead.created_at >= today_start)
            today_result = await db.execute(today_stmt)
            created_today = today_result.scalar()
            
            # 本周新增
            week_stmt = select(func.count(Lead.id)).where(Lead.created_at >= week_start)
            week_result = await db.execute(week_stmt)
            created_this_week = week_result.scalar()
            
            # 本月新增
            month_stmt = select(func.count(Lead.id)).where(Lead.created_at >= month_start)
            month_result = await db.execute(month_stmt)
            created_this_month = month_result.scalar()
            
            return LeadStatistics(
                total_leads=total_leads,
                by_status=by_status,
                by_source=by_source,
                by_assigned=by_assigned,
                average_score=round(average_score, 2),
                conversion_rate=round(conversion_rate, 2),
                created_today=created_today,
                created_this_week=created_this_week,
                created_this_month=created_this_month
            )
            
        except Exception as e:
            logger.error(f"获取线索统计失败: error={str(e)}")
            raise
    
    async def _convert_to_response(
        self,
        lead: Lead,
        db: AsyncSession,
        score_detail: Optional[Any] = None
    ) -> LeadResponse:
        """转换为响应模型"""
        # 获取互动记录
        interactions = []
        if hasattr(lead, 'interactions') and lead.interactions:
            for interaction in lead.interactions:
                interactions.append(InteractionResponse(
                    id=str(interaction.id),
                    lead_id=str(interaction.lead_id),
                    interaction_type=interaction.interaction_type,
                    channel=interaction.channel,
                    direction=interaction.direction,
                    subject=interaction.subject,
                    content=interaction.content,
                    outcome=interaction.outcome,
                    next_action=interaction.next_action,
                    participant=interaction.participant,
                    interaction_at=interaction.interaction_at,
                    created_at=interaction.created_at
                ))
        
        # 转换联系信息和公司信息
        from src.schemas.lead import ContactInfo, CompanyInfo
        
        contact = None
        if lead.contact:
            contact = ContactInfo(**lead.contact)
        
        company_info = None
        if lead.company_info:
            company_info = CompanyInfo(**lead.company_info)
        
        return LeadResponse(
            id=str(lead.id),
            name=lead.name,
            company=lead.company,
            title=lead.title,
            industry=lead.industry,
            contact=contact,
            company_info=company_info,
            requirements=lead.requirements,
            budget=lead.budget,
            timeline=lead.timeline,
            source=lead.source,
            status=lead.status,
            assigned_to=lead.assigned_to,
            assigned_at=lead.assigned_at,
            tags=lead.tags or [],
            notes=lead.notes,
            custom_fields=lead.custom_fields or {},
            created_at=lead.created_at,
            updated_at=lead.updated_at,
            current_score=score_detail,
            interactions=interactions
        )