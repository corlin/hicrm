"""
线索管理和分配流程

集成市场Agent和销售管理Agent协作，实现自动线索评分和智能分配，
开发线索跟踪和状态更新机制。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel

from src.agents.professional.market_agent import MarketAgent
from src.agents.professional.sales_management_agent import SalesManagementAgent
from src.agents.professional.sales_agent import SalesAgent
from src.services.lead_service import LeadService
from src.services.customer_service import CustomerService
from src.models.lead import Lead, LeadStatus, LeadSource
from src.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from src.core.database import get_db

logger = logging.getLogger(__name__)


class AssignmentStrategy(str, Enum):
    """分配策略"""
    ROUND_ROBIN = "round_robin"        # 轮询分配
    LOAD_BALANCED = "load_balanced"    # 负载均衡
    SKILL_BASED = "skill_based"        # 技能匹配
    TERRITORY_BASED = "territory_based" # 区域分配
    SCORE_BASED = "score_based"        # 分数优先


class LeadPriority(str, Enum):
    """线索优先级"""
    CRITICAL = "critical"  # 关键
    HIGH = "high"         # 高
    MEDIUM = "medium"     # 中
    LOW = "low"          # 低


class WorkflowStage(str, Enum):
    """工作流阶段"""
    INTAKE = "intake"                    # 接收
    SCORING = "scoring"                  # 评分
    QUALIFICATION = "qualification"      # 资格认证
    ASSIGNMENT = "assignment"            # 分配
    FOLLOW_UP = "follow_up"             # 跟进
    CONVERSION = "conversion"            # 转化
    NURTURING = "nurturing"             # 培育


@dataclass
class SalesRep:
    """销售代表"""
    rep_id: str
    name: str
    email: str
    territory: List[str]
    skills: List[str]
    specialties: List[str]
    current_load: int
    max_capacity: int
    performance_score: float
    availability: bool = True
    last_assignment: Optional[datetime] = None


@dataclass
class LeadScore:
    """线索评分"""
    total_score: float
    demographic_score: float
    behavioral_score: float
    firmographic_score: float
    engagement_score: float
    scoring_factors: Dict[str, float]
    confidence: float
    scored_at: datetime


@dataclass
class AssignmentRule:
    """分配规则"""
    rule_id: str
    name: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LeadWorkflowTask:
    """线索工作流任务"""
    task_id: str
    lead_id: str
    stage: WorkflowStage
    priority: LeadPriority
    assigned_to: Optional[str]
    title: str
    description: str
    due_date: datetime
    status: str = "pending"
    progress: float = 0.0
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class LeadManagementWorkflow:
    """线索管理工作流"""
    
    def __init__(
        self,
        market_agent: MarketAgent,
        sales_management_agent: SalesManagementAgent,
        sales_agent: SalesAgent,
        lead_service: LeadService,
        customer_service: CustomerService
    ):
        self.market_agent = market_agent
        self.sales_management_agent = sales_management_agent
        self.sales_agent = sales_agent
        self.lead_service = lead_service
        self.customer_service = customer_service
        
        # 活跃任务
        self.active_tasks: Dict[str, LeadWorkflowTask] = {}
        
        # 销售代表信息
        self.sales_reps: Dict[str, SalesRep] = {}
        
        # 分配规则
        self.assignment_rules: List[AssignmentRule] = []
        
        # 评分模型配置
        self.scoring_config = self._initialize_scoring_config()
        
        self.logger = logging.getLogger(__name__)
        
        # 初始化默认数据
        asyncio.create_task(self._initialize_default_data())
    
    def _initialize_scoring_config(self) -> Dict[str, Any]:
        """初始化评分配置"""
        return {
            "demographic_weights": {
                "job_title": 0.3,
                "seniority_level": 0.4,
                "department": 0.3
            },
            "firmographic_weights": {
                "company_size": 0.4,
                "industry": 0.3,
                "annual_revenue": 0.3
            },
            "behavioral_weights": {
                "website_visits": 0.2,
                "email_opens": 0.2,
                "content_downloads": 0.3,
                "demo_requests": 0.3
            },
            "engagement_weights": {
                "response_rate": 0.4,
                "meeting_attendance": 0.3,
                "follow_up_engagement": 0.3
            },
            "score_thresholds": {
                "hot": 80,
                "warm": 60,
                "cold": 40
            }
        }
    
    async def _initialize_default_data(self):
        """初始化默认数据"""
        try:
            # 初始化销售代表
            await self._load_sales_reps()
            
            # 初始化分配规则
            await self._load_assignment_rules()
            
        except Exception as e:
            self.logger.error(f"初始化默认数据失败: {e}")
    
    async def _load_sales_reps(self):
        """加载销售代表信息"""
        # 这里可以从数据库或外部系统加载
        # 目前使用模拟数据
        default_reps = [
            SalesRep(
                rep_id="rep_001",
                name="张销售",
                email="zhang@company.com",
                territory=["北京", "天津", "河北"],
                skills=["企业销售", "技术方案"],
                specialties=["制造业", "金融业"],
                current_load=5,
                max_capacity=20,
                performance_score=0.85
            ),
            SalesRep(
                rep_id="rep_002",
                name="李销售",
                email="li@company.com",
                territory=["上海", "江苏", "浙江"],
                skills=["大客户销售", "关系维护"],
                specialties=["互联网", "教育"],
                current_load=8,
                max_capacity=25,
                performance_score=0.92
            ),
            SalesRep(
                rep_id="rep_003",
                name="王销售",
                email="wang@company.com",
                territory=["广州", "深圳", "东莞"],
                skills=["新客户开发", "产品演示"],
                specialties=["零售业", "物流"],
                current_load=3,
                max_capacity=18,
                performance_score=0.78
            )
        ]
        
        for rep in default_reps:
            self.sales_reps[rep.rep_id] = rep
    
    async def _load_assignment_rules(self):
        """加载分配规则"""
        default_rules = [
            AssignmentRule(
                rule_id="rule_001",
                name="高分线索优先分配",
                conditions={"score_min": 80},
                actions={"strategy": "skill_based", "priority": "high"},
                priority=1
            ),
            AssignmentRule(
                rule_id="rule_002",
                name="区域匹配分配",
                conditions={"has_territory": True},
                actions={"strategy": "territory_based"},
                priority=2
            ),
            AssignmentRule(
                rule_id="rule_003",
                name="负载均衡分配",
                conditions={"default": True},
                actions={"strategy": "load_balanced"},
                priority=3
            )
        ]
        
        self.assignment_rules = default_rules
    
    async def process_new_lead(
        self,
        lead_data: Dict[str, Any],
        source: str = "website"
    ) -> str:
        """
        处理新线索
        
        Args:
            lead_data: 线索数据
            source: 线索来源
            
        Returns:
            任务ID
        """
        try:
            task_id = f"lead_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建线索记录
            lead_create = LeadCreate(
                company_name=lead_data.get('company_name', ''),
                contact_name=lead_data.get('contact_name', ''),
                email=lead_data.get('email', ''),
                phone=lead_data.get('phone', ''),
                job_title=lead_data.get('job_title', ''),
                industry=lead_data.get('industry', ''),
                company_size=lead_data.get('company_size', ''),
                annual_revenue=lead_data.get('annual_revenue'),
                location=lead_data.get('location', ''),
                source=LeadSource(source),
                status=LeadStatus.NEW,
                description=lead_data.get('description', ''),
                tags=lead_data.get('tags', []),
                custom_fields=lead_data.get('custom_fields', {})
            )
            
            # 保存线索到数据库
            async with get_db() as db:
                lead_service = LeadService(db)
                lead = await lead_service.create_lead(lead_create)
                lead_id = lead.id
            
            # 创建工作流任务
            workflow_task = LeadWorkflowTask(
                task_id=task_id,
                lead_id=lead_id,
                stage=WorkflowStage.INTAKE,
                priority=LeadPriority.MEDIUM,
                assigned_to=None,
                title=f"处理新线索 - {lead_data.get('company_name', '未知公司')}",
                description=f"来源: {source}, 联系人: {lead_data.get('contact_name', '未知')}",
                due_date=datetime.now() + timedelta(hours=24)
            )
            
            self.active_tasks[task_id] = workflow_task
            
            # 启动评分阶段
            await self._execute_scoring_stage(task_id)
            
            self.logger.info(f"开始处理新线索: {task_id}, 线索ID: {lead_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"处理新线索失败: {e}")
            raise
    
    async def _execute_scoring_stage(self, task_id: str) -> None:
        """执行评分阶段"""
        try:
            task = self.active_tasks[task_id]
            task.stage = WorkflowStage.SCORING
            task.updated_at = datetime.now()
            
            # 获取线索详细信息
            async with get_db() as db:
                lead_service = LeadService(db)
                lead = await lead_service.get_lead(task.lead_id)
                
                if not lead:
                    raise ValueError(f"线索 {task.lead_id} 不存在")
            
            # 使用市场Agent进行线索评分
            scoring_result = await self.market_agent.score_lead(
                lead_data={
                    'company_name': lead.company_name,
                    'contact_name': lead.contact_name,
                    'job_title': lead.job_title,
                    'industry': lead.industry,
                    'company_size': lead.company_size,
                    'annual_revenue': lead.annual_revenue,
                    'location': lead.location,
                    'source': lead.source.value,
                    'custom_fields': lead.custom_fields or {}
                },
                scoring_config=self.scoring_config
            )
            
            # 创建评分记录
            lead_score = LeadScore(
                total_score=scoring_result.get('total_score', 0),
                demographic_score=scoring_result.get('demographic_score', 0),
                behavioral_score=scoring_result.get('behavioral_score', 0),
                firmographic_score=scoring_result.get('firmographic_score', 0),
                engagement_score=scoring_result.get('engagement_score', 0),
                scoring_factors=scoring_result.get('factors', {}),
                confidence=scoring_result.get('confidence', 0.5),
                scored_at=datetime.now()
            )
            
            # 更新任务结果
            task.results['lead_score'] = lead_score.__dict__
            task.progress = 0.3
            
            # 根据分数确定优先级
            if lead_score.total_score >= 80:
                task.priority = LeadPriority.CRITICAL
            elif lead_score.total_score >= 60:
                task.priority = LeadPriority.HIGH
            elif lead_score.total_score >= 40:
                task.priority = LeadPriority.MEDIUM
            else:
                task.priority = LeadPriority.LOW
            
            # 更新线索状态和分数
            async with get_db() as db:
                lead_service = LeadService(db)
                await lead_service.update_lead(
                    task.lead_id,
                    LeadUpdate(
                        status=LeadStatus.QUALIFIED if lead_score.total_score >= 60 else LeadStatus.UNQUALIFIED,
                        score=lead_score.total_score,
                        custom_fields={
                            **(lead.custom_fields or {}),
                            'lead_score_details': lead_score.__dict__
                        }
                    )
                )
            
            # 继续资格认证阶段
            await self._execute_qualification_stage(task_id)
            
        except Exception as e:
            self.logger.error(f"评分阶段执行失败: {e}")
            raise
    
    async def _execute_qualification_stage(self, task_id: str) -> None:
        """执行资格认证阶段"""
        try:
            task = self.active_tasks[task_id]
            task.stage = WorkflowStage.QUALIFICATION
            task.updated_at = datetime.now()
            
            lead_score = LeadScore(**task.results['lead_score'])
            
            # 如果分数太低，直接进入培育流程
            if lead_score.total_score < 40:
                task.stage = WorkflowStage.NURTURING
                task.results['qualification_result'] = {
                    'qualified': False,
                    'reason': '分数过低，需要培育',
                    'recommended_actions': ['邮件培育', '内容推送', '定期跟进']
                }
                task.progress = 0.8
                return
            
            # 获取线索信息
            async with get_db() as db:
                lead_service = LeadService(db)
                lead = await lead_service.get_lead(task.lead_id)
            
            # 使用销售Agent进行深度资格认证
            qualification_result = await self.sales_agent.qualify_lead(
                lead_data={
                    'company_name': lead.company_name,
                    'contact_name': lead.contact_name,
                    'job_title': lead.job_title,
                    'industry': lead.industry,
                    'company_size': lead.company_size,
                    'annual_revenue': lead.annual_revenue,
                    'score': lead_score.total_score,
                    'scoring_factors': lead_score.scoring_factors
                },
                qualification_criteria={
                    'budget_threshold': 50000,
                    'authority_level': 'influencer',
                    'need_urgency': 'medium',
                    'timeline': '12_months'
                }
            )
            
            task.results['qualification_result'] = qualification_result
            task.progress = 0.5
            
            # 根据资格认证结果决定下一步
            if qualification_result.get('qualified', False):
                # 继续分配阶段
                await self._execute_assignment_stage(task_id)
            else:
                # 进入培育阶段
                task.stage = WorkflowStage.NURTURING
                task.progress = 0.8
            
        except Exception as e:
            self.logger.error(f"资格认证阶段执行失败: {e}")
            raise
    
    async def _execute_assignment_stage(self, task_id: str) -> None:
        """执行分配阶段"""
        try:
            task = self.active_tasks[task_id]
            task.stage = WorkflowStage.ASSIGNMENT
            task.updated_at = datetime.now()
            
            # 获取线索信息
            async with get_db() as db:
                lead_service = LeadService(db)
                lead = await lead_service.get_lead(task.lead_id)
            
            lead_score = LeadScore(**task.results['lead_score'])
            
            # 使用销售管理Agent进行智能分配
            assignment_result = await self.sales_management_agent.assign_lead(
                lead_data={
                    'lead_id': task.lead_id,
                    'company_name': lead.company_name,
                    'industry': lead.industry,
                    'location': lead.location,
                    'score': lead_score.total_score,
                    'priority': task.priority.value
                },
                sales_reps=[rep.__dict__ for rep in self.sales_reps.values()],
                assignment_rules=[rule.__dict__ for rule in self.assignment_rules]
            )
            
            # 选择最佳销售代表
            assigned_rep_id = assignment_result.get('assigned_rep_id')
            assignment_reason = assignment_result.get('reason', '')
            assignment_strategy = assignment_result.get('strategy', '')
            
            if assigned_rep_id and assigned_rep_id in self.sales_reps:
                # 更新销售代表负载
                self.sales_reps[assigned_rep_id].current_load += 1
                self.sales_reps[assigned_rep_id].last_assignment = datetime.now()
                
                # 更新任务分配
                task.assigned_to = assigned_rep_id
                task.results['assignment_result'] = {
                    'assigned_rep_id': assigned_rep_id,
                    'assigned_rep_name': self.sales_reps[assigned_rep_id].name,
                    'assignment_reason': assignment_reason,
                    'assignment_strategy': assignment_strategy,
                    'assigned_at': datetime.now().isoformat()
                }
                
                # 更新线索分配信息
                async with get_db() as db:
                    lead_service = LeadService(db)
                    await lead_service.update_lead(
                        task.lead_id,
                        LeadUpdate(
                            assigned_to=assigned_rep_id,
                            status=LeadStatus.ASSIGNED,
                            custom_fields={
                                **(lead.custom_fields or {}),
                                'assignment_details': task.results['assignment_result']
                            }
                        )
                    )
                
                task.progress = 0.7
                
                # 继续跟进阶段
                await self._execute_follow_up_stage(task_id)
                
            else:
                # 分配失败，记录原因
                task.results['assignment_error'] = assignment_result.get('error', '无可用销售代表')
                self.logger.warning(f"线索分配失败: {task_id}, 原因: {task.results['assignment_error']}")
            
        except Exception as e:
            self.logger.error(f"分配阶段执行失败: {e}")
            raise
    
    async def _execute_follow_up_stage(self, task_id: str) -> None:
        """执行跟进阶段"""
        try:
            task = self.active_tasks[task_id]
            task.stage = WorkflowStage.FOLLOW_UP
            task.updated_at = datetime.now()
            
            # 获取分配信息
            assignment_result = task.results.get('assignment_result', {})
            assigned_rep_id = assignment_result.get('assigned_rep_id')
            
            if not assigned_rep_id:
                raise ValueError("未找到分配的销售代表")
            
            # 获取线索信息
            async with get_db() as db:
                lead_service = LeadService(db)
                lead = await lead_service.get_lead(task.lead_id)
            
            # 生成跟进计划
            follow_up_plan = await self.sales_agent.create_follow_up_plan(
                lead_data={
                    'lead_id': task.lead_id,
                    'company_name': lead.company_name,
                    'contact_name': lead.contact_name,
                    'job_title': lead.job_title,
                    'industry': lead.industry,
                    'score': lead.score or 0
                },
                assigned_rep={
                    'rep_id': assigned_rep_id,
                    'name': self.sales_reps[assigned_rep_id].name,
                    'skills': self.sales_reps[assigned_rep_id].skills,
                    'specialties': self.sales_reps[assigned_rep_id].specialties
                }
            )
            
            task.results['follow_up_plan'] = follow_up_plan
            task.progress = 0.9
            
            # 更新线索状态
            async with get_db() as db:
                lead_service = LeadService(db)
                await lead_service.update_lead(
                    task.lead_id,
                    LeadUpdate(
                        status=LeadStatus.IN_PROGRESS,
                        custom_fields={
                            **(lead.custom_fields or {}),
                            'follow_up_plan': follow_up_plan
                        }
                    )
                )
            
            self.logger.info(f"线索跟进计划已生成: {task_id}")
            
        except Exception as e:
            self.logger.error(f"跟进阶段执行失败: {e}")
            raise
    
    async def update_lead_status(
        self,
        task_id: str,
        new_status: LeadStatus,
        notes: str = "",
        next_action: Optional[str] = None
    ) -> bool:
        """更新线索状态"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                return False
            
            # 更新数据库中的线索状态
            async with get_db() as db:
                lead_service = LeadService(db)
                lead = await lead_service.get_lead(task.lead_id)
                
                if not lead:
                    return False
                
                update_data = LeadUpdate(
                    status=new_status,
                    custom_fields={
                        **(lead.custom_fields or {}),
                        'status_update': {
                            'updated_at': datetime.now().isoformat(),
                            'notes': notes,
                            'next_action': next_action,
                            'updated_by': task.assigned_to
                        }
                    }
                )
                
                await lead_service.update_lead(task.lead_id, update_data)
            
            # 更新任务状态
            task.results['status_updates'] = task.results.get('status_updates', [])
            task.results['status_updates'].append({
                'status': new_status.value,
                'notes': notes,
                'next_action': next_action,
                'updated_at': datetime.now().isoformat()
            })
            task.updated_at = datetime.now()
            
            # 如果转化成功，进入转化阶段
            if new_status == LeadStatus.CONVERTED:
                task.stage = WorkflowStage.CONVERSION
                task.progress = 1.0
                task.status = "completed"
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新线索状态失败: {e}")
            return False
    
    async def reassign_lead(
        self,
        task_id: str,
        new_rep_id: str,
        reason: str = ""
    ) -> bool:
        """重新分配线索"""
        try:
            task = self.active_tasks.get(task_id)
            if not task or new_rep_id not in self.sales_reps:
                return False
            
            old_rep_id = task.assigned_to
            
            # 更新销售代表负载
            if old_rep_id and old_rep_id in self.sales_reps:
                self.sales_reps[old_rep_id].current_load -= 1
            
            self.sales_reps[new_rep_id].current_load += 1
            self.sales_reps[new_rep_id].last_assignment = datetime.now()
            
            # 更新任务分配
            task.assigned_to = new_rep_id
            task.results['reassignment_history'] = task.results.get('reassignment_history', [])
            task.results['reassignment_history'].append({
                'from_rep_id': old_rep_id,
                'to_rep_id': new_rep_id,
                'reason': reason,
                'reassigned_at': datetime.now().isoformat()
            })
            task.updated_at = datetime.now()
            
            # 更新数据库
            async with get_db() as db:
                lead_service = LeadService(db)
                await lead_service.update_lead(
                    task.lead_id,
                    LeadUpdate(
                        assigned_to=new_rep_id,
                        custom_fields={
                            'reassignment_history': task.results['reassignment_history']
                        }
                    )
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"重新分配线索失败: {e}")
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'lead_id': task.lead_id,
            'stage': task.stage.value,
            'priority': task.priority.value,
            'assigned_to': task.assigned_to,
            'title': task.title,
            'description': task.description,
            'progress': task.progress,
            'status': task.status,
            'due_date': task.due_date.isoformat(),
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'results': task.results
        }
    
    async def get_sales_rep_workload(self, rep_id: str) -> Optional[Dict[str, Any]]:
        """获取销售代表工作负载"""
        rep = self.sales_reps.get(rep_id)
        if not rep:
            return None
        
        # 统计分配给该代表的活跃任务
        assigned_tasks = [
            task for task in self.active_tasks.values()
            if task.assigned_to == rep_id and task.status != "completed"
        ]
        
        return {
            'rep_id': rep.rep_id,
            'name': rep.name,
            'current_load': rep.current_load,
            'max_capacity': rep.max_capacity,
            'utilization_rate': rep.current_load / rep.max_capacity if rep.max_capacity > 0 else 0,
            'performance_score': rep.performance_score,
            'assigned_tasks_count': len(assigned_tasks),
            'territory': rep.territory,
            'skills': rep.skills,
            'specialties': rep.specialties,
            'availability': rep.availability,
            'last_assignment': rep.last_assignment.isoformat() if rep.last_assignment else None
        }
    
    async def get_workflow_metrics(self) -> Dict[str, Any]:
        """获取工作流指标"""
        try:
            total_tasks = len(self.active_tasks)
            if total_tasks == 0:
                return {
                    'total_tasks': 0,
                    'tasks_by_stage': {},
                    'tasks_by_priority': {},
                    'average_progress': 0,
                    'completion_rate': 0,
                    'sales_rep_utilization': {}
                }
            
            # 按阶段统计
            tasks_by_stage = {}
            tasks_by_priority = {}
            total_progress = 0
            completed_tasks = 0
            
            for task in self.active_tasks.values():
                stage = task.stage.value
                priority = task.priority.value
                
                tasks_by_stage[stage] = tasks_by_stage.get(stage, 0) + 1
                tasks_by_priority[priority] = tasks_by_priority.get(priority, 0) + 1
                total_progress += task.progress
                
                if task.status == "completed":
                    completed_tasks += 1
            
            # 销售代表利用率
            sales_rep_utilization = {}
            for rep_id, rep in self.sales_reps.items():
                utilization = rep.current_load / rep.max_capacity if rep.max_capacity > 0 else 0
                sales_rep_utilization[rep_id] = {
                    'name': rep.name,
                    'utilization_rate': utilization,
                    'current_load': rep.current_load,
                    'max_capacity': rep.max_capacity
                }
            
            return {
                'total_tasks': total_tasks,
                'tasks_by_stage': tasks_by_stage,
                'tasks_by_priority': tasks_by_priority,
                'average_progress': total_progress / total_tasks,
                'completion_rate': completed_tasks / total_tasks,
                'sales_rep_utilization': sales_rep_utilization
            }
            
        except Exception as e:
            self.logger.error(f"获取工作流指标失败: {e}")
            return {}


# 创建全局工作流实例的工厂函数
async def create_lead_management_workflow() -> LeadManagementWorkflow:
    """创建线索管理工作流实例"""
    from src.agents.professional.market_agent import MarketAgent
    from src.agents.professional.sales_management_agent import SalesManagementAgent
    from src.agents.professional.sales_agent import SalesAgent
    
    # 创建Agent实例
    market_agent = MarketAgent(
        agent_id="market_agent",
        name="市场分析师",
        specialty="市场分析和线索管理"
    )
    
    sales_management_agent = SalesManagementAgent(
        agent_id="sales_management_agent",
        name="销售管理专家",
        specialty="销售团队管理和绩效优化"
    )
    
    sales_agent = SalesAgent(
        agent_id="sales_agent",
        name="销售助手",
        specialty="客户管理和销售流程"
    )
    
    # 获取数据库会话
    async with get_db() as db:
        lead_service = LeadService(db)
        customer_service = CustomerService(db)
        
        workflow = LeadManagementWorkflow(
            market_agent=market_agent,
            sales_management_agent=sales_management_agent,
            sales_agent=sales_agent,
            lead_service=lead_service,
            customer_service=customer_service
        )
        
        return workflow