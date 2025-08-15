"""
客户发现和接触管理流程

集成销售Agent的客户发现功能，实现拜访计划生成和准备清单，
开发客户背景分析和策略推荐。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel

from src.agents.professional.sales_agent import SalesAgent
from src.agents.professional.market_agent import MarketAgent
from src.agents.professional.crm_expert_agent import CRMExpertAgent
from src.services.customer_service import CustomerService
from src.services.lead_service import LeadService
from src.services.rag_service import rag_service
from src.models.customer import Customer
from src.models.lead import Lead
from src.schemas.customer import CustomerCreate, CustomerResponse
from src.core.database import get_db

logger = logging.getLogger(__name__)


class DiscoveryStage(str, Enum):
    """客户发现阶段"""
    RESEARCH = "research"           # 研究阶段
    QUALIFICATION = "qualification" # 资格认证
    CONTACT_PLANNING = "contact_planning"  # 接触规划
    INITIAL_CONTACT = "initial_contact"    # 初次接触
    FOLLOW_UP = "follow_up"        # 跟进
    CONVERSION = "conversion"      # 转化


class ContactMethod(str, Enum):
    """接触方式"""
    PHONE_CALL = "phone_call"      # 电话
    EMAIL = "email"                # 邮件
    SOCIAL_MEDIA = "social_media"  # 社交媒体
    IN_PERSON = "in_person"        # 面对面
    WEBINAR = "webinar"            # 网络研讨会
    REFERRAL = "referral"          # 推荐


class Priority(str, Enum):
    """优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CustomerProfile:
    """客户画像"""
    company_name: str
    industry: str
    company_size: str
    annual_revenue: Optional[float] = None
    location: str = ""
    website: str = ""
    key_contacts: List[Dict[str, Any]] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    current_solutions: List[str] = field(default_factory=list)
    decision_makers: List[Dict[str, Any]] = field(default_factory=list)
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    competitive_landscape: List[str] = field(default_factory=list)


@dataclass
class ContactStrategy:
    """接触策略"""
    primary_method: ContactMethod
    backup_methods: List[ContactMethod]
    messaging: str
    value_proposition: str
    call_to_action: str
    timing_recommendations: List[str]
    personalization_points: List[str]


@dataclass
class VisitPlan:
    """拜访计划"""
    visit_id: str
    customer_profile: CustomerProfile
    objectives: List[str]
    agenda: List[Dict[str, Any]]
    preparation_checklist: List[str]
    materials_needed: List[str]
    key_questions: List[str]
    success_criteria: List[str]
    follow_up_actions: List[str]
    scheduled_time: Optional[datetime] = None
    duration_minutes: int = 60
    location: str = ""
    attendees: List[str] = field(default_factory=list)


@dataclass
class DiscoveryTask:
    """发现任务"""
    task_id: str
    customer_id: Optional[str]
    stage: DiscoveryStage
    priority: Priority
    title: str
    description: str
    assigned_agent: str
    due_date: datetime
    status: str = "pending"
    progress: float = 0.0
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class CustomerDiscoveryWorkflow:
    """客户发现工作流"""
    
    def __init__(
        self,
        sales_agent: SalesAgent,
        market_agent: MarketAgent,
        crm_expert_agent: CRMExpertAgent,
        customer_service: CustomerService,
        lead_service: LeadService
    ):
        self.sales_agent = sales_agent
        self.market_agent = market_agent
        self.crm_expert_agent = crm_expert_agent
        self.customer_service = customer_service
        self.lead_service = lead_service
        
        # 活跃的发现任务
        self.active_tasks: Dict[str, DiscoveryTask] = {}
        
        # 客户画像缓存
        self.customer_profiles: Dict[str, CustomerProfile] = {}
        
        self.logger = logging.getLogger(__name__)
    
    async def start_customer_discovery(
        self,
        target_criteria: Dict[str, Any],
        discovery_goals: List[str],
        timeline_days: int = 30
    ) -> str:
        """
        启动客户发现流程
        
        Args:
            target_criteria: 目标客户标准
            discovery_goals: 发现目标
            timeline_days: 时间线（天）
            
        Returns:
            发现任务ID
        """
        try:
            task_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建发现任务
            discovery_task = DiscoveryTask(
                task_id=task_id,
                customer_id=None,
                stage=DiscoveryStage.RESEARCH,
                priority=Priority.HIGH,
                title=f"客户发现任务 - {target_criteria.get('industry', '通用')}",
                description=f"目标: {', '.join(discovery_goals)}",
                assigned_agent="sales_agent",
                due_date=datetime.now() + timedelta(days=timeline_days)
            )
            
            self.active_tasks[task_id] = discovery_task
            
            # 启动研究阶段
            await self._execute_research_stage(task_id, target_criteria)
            
            self.logger.info(f"启动客户发现流程: {task_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"启动客户发现流程失败: {e}")
            raise
    
    async def _execute_research_stage(
        self,
        task_id: str,
        target_criteria: Dict[str, Any]
    ) -> None:
        """执行研究阶段"""
        try:
            task = self.active_tasks[task_id]
            
            # 使用市场Agent进行市场研究
            market_research = await self.market_agent.analyze_market_segment(
                industry=target_criteria.get('industry'),
                company_size=target_criteria.get('company_size'),
                location=target_criteria.get('location')
            )
            
            # 使用RAG服务获取行业知识
            industry_insights = await rag_service.query(
                question=f"关于{target_criteria.get('industry')}行业的客户特征和痛点",
                mode="hybrid"
            )
            
            # 生成潜在客户列表
            potential_customers = await self._generate_potential_customer_list(
                target_criteria,
                market_research,
                industry_insights
            )
            
            # 更新任务结果
            task.results.update({
                'market_research': market_research,
                'industry_insights': industry_insights.dict(),
                'potential_customers': potential_customers,
                'research_completed_at': datetime.now().isoformat()
            })
            
            task.progress = 0.2
            task.stage = DiscoveryStage.QUALIFICATION
            
            # 继续资格认证阶段
            await self._execute_qualification_stage(task_id)
            
        except Exception as e:
            self.logger.error(f"研究阶段执行失败: {e}")
            raise
    
    async def _execute_qualification_stage(self, task_id: str) -> None:
        """执行资格认证阶段"""
        try:
            task = self.active_tasks[task_id]
            potential_customers = task.results.get('potential_customers', [])
            
            qualified_customers = []
            
            for customer_data in potential_customers:
                # 使用销售Agent进行客户资格认证
                qualification_result = await self.sales_agent.qualify_customer(
                    customer_data=customer_data,
                    qualification_criteria={
                        'budget_threshold': 100000,
                        'decision_timeline': '6_months',
                        'authority_level': 'decision_maker'
                    }
                )
                
                if qualification_result.get('qualified', False):
                    # 创建详细的客户画像
                    customer_profile = await self._create_customer_profile(
                        customer_data,
                        qualification_result
                    )
                    
                    qualified_customers.append({
                        'customer_data': customer_data,
                        'qualification_score': qualification_result.get('score', 0),
                        'customer_profile': customer_profile.__dict__
                    })
            
            # 按资格分数排序
            qualified_customers.sort(
                key=lambda x: x['qualification_score'],
                reverse=True
            )
            
            # 更新任务结果
            task.results['qualified_customers'] = qualified_customers
            task.progress = 0.4
            task.stage = DiscoveryStage.CONTACT_PLANNING
            
            # 继续接触规划阶段
            await self._execute_contact_planning_stage(task_id)
            
        except Exception as e:
            self.logger.error(f"资格认证阶段执行失败: {e}")
            raise
    
    async def _execute_contact_planning_stage(self, task_id: str) -> None:
        """执行接触规划阶段"""
        try:
            task = self.active_tasks[task_id]
            qualified_customers = task.results.get('qualified_customers', [])
            
            contact_plans = []
            
            for customer_info in qualified_customers[:10]:  # 处理前10个高质量客户
                customer_profile = CustomerProfile(**customer_info['customer_profile'])
                
                # 生成接触策略
                contact_strategy = await self._generate_contact_strategy(customer_profile)
                
                # 生成拜访计划
                visit_plan = await self._generate_visit_plan(customer_profile, contact_strategy)
                
                contact_plans.append({
                    'customer_profile': customer_profile.__dict__,
                    'contact_strategy': contact_strategy.__dict__,
                    'visit_plan': visit_plan.__dict__
                })
            
            # 更新任务结果
            task.results['contact_plans'] = contact_plans
            task.progress = 0.6
            task.stage = DiscoveryStage.INITIAL_CONTACT
            
            self.logger.info(f"完成接触规划阶段，生成了{len(contact_plans)}个接触计划")
            
        except Exception as e:
            self.logger.error(f"接触规划阶段执行失败: {e}")
            raise
    
    async def _generate_potential_customer_list(
        self,
        target_criteria: Dict[str, Any],
        market_research: Dict[str, Any],
        industry_insights: Any
    ) -> List[Dict[str, Any]]:
        """生成潜在客户列表"""
        try:
            # 这里可以集成外部数据源，如企业数据库、社交媒体等
            # 目前使用模拟数据
            
            industry = target_criteria.get('industry', '制造业')
            company_size = target_criteria.get('company_size', '中型企业')
            location = target_criteria.get('location', '北京')
            
            # 模拟生成潜在客户
            potential_customers = []
            
            for i in range(20):  # 生成20个潜在客户
                customer = {
                    'company_name': f"{industry}公司{i+1}",
                    'industry': industry,
                    'company_size': company_size,
                    'location': location,
                    'annual_revenue': 5000000 + i * 1000000,
                    'employee_count': 100 + i * 50,
                    'website': f"https://company{i+1}.com",
                    'contact_info': {
                        'phone': f"010-{8000+i:04d}-{1000+i:04d}",
                        'email': f"contact@company{i+1}.com"
                    },
                    'business_description': f"{industry}领域的{company_size}，专注于产品研发和市场拓展",
                    'potential_pain_points': [
                        '客户管理效率低下',
                        '销售流程不规范',
                        '数据分析能力不足'
                    ]
                }
                potential_customers.append(customer)
            
            return potential_customers
            
        except Exception as e:
            self.logger.error(f"生成潜在客户列表失败: {e}")
            return []
    
    async def _create_customer_profile(
        self,
        customer_data: Dict[str, Any],
        qualification_result: Dict[str, Any]
    ) -> CustomerProfile:
        """创建客户画像"""
        try:
            # 使用CRM专家Agent增强客户画像
            profile_enhancement = await self.crm_expert_agent.enhance_customer_profile(
                basic_info=customer_data,
                qualification_data=qualification_result
            )
            
            customer_profile = CustomerProfile(
                company_name=customer_data.get('company_name', ''),
                industry=customer_data.get('industry', ''),
                company_size=customer_data.get('company_size', ''),
                annual_revenue=customer_data.get('annual_revenue'),
                location=customer_data.get('location', ''),
                website=customer_data.get('website', ''),
                key_contacts=profile_enhancement.get('key_contacts', []),
                pain_points=profile_enhancement.get('pain_points', []),
                current_solutions=profile_enhancement.get('current_solutions', []),
                decision_makers=profile_enhancement.get('decision_makers', []),
                budget_range=profile_enhancement.get('budget_range'),
                timeline=profile_enhancement.get('timeline'),
                competitive_landscape=profile_enhancement.get('competitive_landscape', [])
            )
            
            return customer_profile
            
        except Exception as e:
            self.logger.error(f"创建客户画像失败: {e}")
            # 返回基础画像
            return CustomerProfile(
                company_name=customer_data.get('company_name', ''),
                industry=customer_data.get('industry', ''),
                company_size=customer_data.get('company_size', ''),
                location=customer_data.get('location', '')
            )
    
    async def _generate_contact_strategy(self, customer_profile: CustomerProfile) -> ContactStrategy:
        """生成接触策略"""
        try:
            # 使用销售Agent生成接触策略
            strategy_result = await self.sales_agent.generate_contact_strategy(
                customer_profile=customer_profile.__dict__
            )
            
            contact_strategy = ContactStrategy(
                primary_method=ContactMethod(strategy_result.get('primary_method', 'email')),
                backup_methods=[
                    ContactMethod(method) for method in strategy_result.get('backup_methods', ['phone_call'])
                ],
                messaging=strategy_result.get('messaging', ''),
                value_proposition=strategy_result.get('value_proposition', ''),
                call_to_action=strategy_result.get('call_to_action', ''),
                timing_recommendations=strategy_result.get('timing_recommendations', []),
                personalization_points=strategy_result.get('personalization_points', [])
            )
            
            return contact_strategy
            
        except Exception as e:
            self.logger.error(f"生成接触策略失败: {e}")
            # 返回默认策略
            return ContactStrategy(
                primary_method=ContactMethod.EMAIL,
                backup_methods=[ContactMethod.PHONE_CALL],
                messaging="我们的CRM解决方案可以帮助您提升销售效率",
                value_proposition="提升30%的销售转化率",
                call_to_action="预约15分钟的产品演示",
                timing_recommendations=["工作日上午9-11点"],
                personalization_points=[f"针对{customer_profile.industry}行业的定制化方案"]
            )
    
    async def _generate_visit_plan(
        self,
        customer_profile: CustomerProfile,
        contact_strategy: ContactStrategy
    ) -> VisitPlan:
        """生成拜访计划"""
        try:
            visit_id = f"visit_{customer_profile.company_name}_{datetime.now().strftime('%Y%m%d')}"
            
            # 使用销售Agent生成拜访计划
            visit_plan_result = await self.sales_agent.create_visit_plan(
                customer_profile=customer_profile.__dict__,
                contact_strategy=contact_strategy.__dict__
            )
            
            visit_plan = VisitPlan(
                visit_id=visit_id,
                customer_profile=customer_profile,
                objectives=visit_plan_result.get('objectives', [
                    '了解客户需求',
                    '展示产品价值',
                    '建立信任关系',
                    '确定下一步行动'
                ]),
                agenda=visit_plan_result.get('agenda', [
                    {'time': '0-5分钟', 'activity': '开场和自我介绍'},
                    {'time': '5-15分钟', 'activity': '了解客户现状和挑战'},
                    {'time': '15-35分钟', 'activity': '产品演示和价值展示'},
                    {'time': '35-50分钟', 'activity': '讨论解决方案'},
                    {'time': '50-60分钟', 'activity': '总结和下一步计划'}
                ]),
                preparation_checklist=visit_plan_result.get('preparation_checklist', [
                    '研究客户公司背景',
                    '准备产品演示材料',
                    '准备案例研究',
                    '准备报价方案',
                    '确认会议时间和地点'
                ]),
                materials_needed=visit_plan_result.get('materials_needed', [
                    '产品演示PPT',
                    '客户案例手册',
                    '产品宣传册',
                    '报价单模板',
                    '名片'
                ]),
                key_questions=visit_plan_result.get('key_questions', [
                    '目前使用什么CRM系统？',
                    '主要的业务挑战是什么？',
                    '决策流程是怎样的？',
                    '预算范围是多少？',
                    '期望的实施时间？'
                ]),
                success_criteria=visit_plan_result.get('success_criteria', [
                    '客户表现出明确兴趣',
                    '获得关键决策人信息',
                    '确定具体需求',
                    '安排下次会议'
                ]),
                follow_up_actions=visit_plan_result.get('follow_up_actions', [
                    '24小时内发送感谢邮件',
                    '提供详细产品资料',
                    '准备定制化方案',
                    '安排技术演示'
                ])
            )
            
            return visit_plan
            
        except Exception as e:
            self.logger.error(f"生成拜访计划失败: {e}")
            # 返回基础计划
            return VisitPlan(
                visit_id=f"visit_{customer_profile.company_name}_{datetime.now().strftime('%Y%m%d')}",
                customer_profile=customer_profile,
                objectives=['了解客户需求', '展示产品价值'],
                agenda=[
                    {'time': '0-30分钟', 'activity': '需求了解'},
                    {'time': '30-60分钟', 'activity': '产品介绍'}
                ],
                preparation_checklist=['准备产品资料', '研究客户背景'],
                materials_needed=['产品手册', '名片'],
                key_questions=['有什么挑战？', '预算如何？'],
                success_criteria=['客户感兴趣', '获得联系方式'],
                follow_up_actions=['发送资料', '安排下次会议']
            )
    
    async def execute_initial_contact(
        self,
        task_id: str,
        contact_plan_index: int
    ) -> Dict[str, Any]:
        """执行初次接触"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            contact_plans = task.results.get('contact_plans', [])
            if contact_plan_index >= len(contact_plans):
                raise ValueError(f"接触计划索引 {contact_plan_index} 超出范围")
            
            contact_plan = contact_plans[contact_plan_index]
            customer_profile = CustomerProfile(**contact_plan['customer_profile'])
            contact_strategy = ContactStrategy(**contact_plan['contact_strategy'])
            
            # 使用销售Agent执行接触
            contact_result = await self.sales_agent.execute_customer_contact(
                customer_profile=customer_profile.__dict__,
                contact_strategy=contact_strategy.__dict__
            )
            
            # 记录接触结果
            contact_record = {
                'contact_time': datetime.now().isoformat(),
                'method': contact_strategy.primary_method.value,
                'result': contact_result,
                'next_steps': contact_result.get('next_steps', []),
                'follow_up_date': (datetime.now() + timedelta(days=3)).isoformat()
            }
            
            # 更新任务结果
            if 'contact_records' not in task.results:
                task.results['contact_records'] = []
            task.results['contact_records'].append(contact_record)
            
            # 如果接触成功，创建客户记录
            if contact_result.get('success', False):
                await self._create_customer_record(customer_profile, contact_record)
            
            self.logger.info(f"完成初次接触: {customer_profile.company_name}")
            return contact_record
            
        except Exception as e:
            self.logger.error(f"执行初次接触失败: {e}")
            raise
    
    async def _create_customer_record(
        self,
        customer_profile: CustomerProfile,
        contact_record: Dict[str, Any]
    ) -> Optional[str]:
        """创建客户记录"""
        try:
            # 创建客户数据
            customer_data = CustomerCreate(
                company_name=customer_profile.company_name,
                industry=customer_profile.industry,
                company_size=customer_profile.company_size,
                annual_revenue=customer_profile.annual_revenue,
                location=customer_profile.location,
                website=customer_profile.website,
                description=f"通过客户发现流程获得的{customer_profile.industry}客户",
                tags=[customer_profile.industry, customer_profile.company_size, "发现客户"],
                custom_fields={
                    'pain_points': customer_profile.pain_points,
                    'current_solutions': customer_profile.current_solutions,
                    'budget_range': customer_profile.budget_range,
                    'timeline': customer_profile.timeline,
                    'contact_record': contact_record
                }
            )
            
            # 使用数据库会话创建客户
            async with get_db() as db:
                customer_service = CustomerService(db)
                customer = await customer_service.create_customer(customer_data)
                
                self.logger.info(f"创建客户记录: {customer.id}")
                return customer.id
                
        except Exception as e:
            self.logger.error(f"创建客户记录失败: {e}")
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'stage': task.stage.value,
            'priority': task.priority.value,
            'title': task.title,
            'description': task.description,
            'progress': task.progress,
            'status': task.status,
            'due_date': task.due_date.isoformat(),
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'results_summary': {
                'potential_customers_count': len(task.results.get('potential_customers', [])),
                'qualified_customers_count': len(task.results.get('qualified_customers', [])),
                'contact_plans_count': len(task.results.get('contact_plans', [])),
                'contact_records_count': len(task.results.get('contact_records', []))
            }
        }
    
    async def get_visit_plan(self, task_id: str, customer_name: str) -> Optional[Dict[str, Any]]:
        """获取拜访计划"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        contact_plans = task.results.get('contact_plans', [])
        for plan in contact_plans:
            if plan['customer_profile']['company_name'] == customer_name:
                return plan['visit_plan']
        
        return None
    
    async def update_contact_result(
        self,
        task_id: str,
        contact_record_index: int,
        result_update: Dict[str, Any]
    ) -> bool:
        """更新接触结果"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                return False
            
            contact_records = task.results.get('contact_records', [])
            if contact_record_index >= len(contact_records):
                return False
            
            contact_records[contact_record_index].update(result_update)
            contact_records[contact_record_index]['updated_at'] = datetime.now().isoformat()
            
            task.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新接触结果失败: {e}")
            return False
    
    async def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                return False
            
            task.status = "completed"
            task.progress = 1.0
            task.updated_at = datetime.now()
            
            self.logger.info(f"完成客户发现任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"完成任务失败: {e}")
            return False


# 创建全局工作流实例的工厂函数
async def create_customer_discovery_workflow() -> CustomerDiscoveryWorkflow:
    """创建客户发现工作流实例"""
    from src.agents.professional.sales_agent import SalesAgent
    from src.agents.professional.market_agent import MarketAgent
    from src.agents.professional.crm_expert_agent import CRMExpertAgent
    
    # 创建Agent实例
    sales_agent = SalesAgent(
        agent_id="sales_agent",
        name="销售助手",
        specialty="客户管理和销售流程"
    )
    
    market_agent = MarketAgent(
        agent_id="market_agent", 
        name="市场分析师",
        specialty="市场分析和线索管理"
    )
    
    crm_expert_agent = CRMExpertAgent(
        agent_id="crm_expert_agent",
        name="CRM专家",
        specialty="CRM最佳实践和流程优化"
    )
    
    # 获取数据库会话
    async with get_db() as db:
        customer_service = CustomerService(db)
        lead_service = LeadService(db)
        
        workflow = CustomerDiscoveryWorkflow(
            sales_agent=sales_agent,
            market_agent=market_agent,
            crm_expert_agent=crm_expert_agent,
            customer_service=customer_service,
            lead_service=lead_service
        )
        
        return workflow