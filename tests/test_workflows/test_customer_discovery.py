"""
客户发现工作流测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from src.workflows.customer_discovery import (
    CustomerDiscoveryWorkflow,
    CustomerProfile,
    ContactStrategy,
    VisitPlan,
    DiscoveryTask,
    DiscoveryStage,
    ContactMethod,
    Priority
)
from src.agents.professional.sales_agent import SalesAgent
from src.agents.professional.market_agent import MarketAgent
from src.agents.professional.crm_expert_agent import CRMExpertAgent
from src.services.customer_service import CustomerService
from src.services.lead_service import LeadService


class TestCustomerProfile:
    """客户画像测试"""
    
    def test_customer_profile_creation(self):
        """测试客户画像创建"""
        profile = CustomerProfile(
            company_name="测试公司",
            industry="制造业",
            company_size="中型企业",
            annual_revenue=5000000,
            location="北京",
            website="https://test.com"
        )
        
        assert profile.company_name == "测试公司"
        assert profile.industry == "制造业"
        assert profile.company_size == "中型企业"
        assert profile.annual_revenue == 5000000
        assert profile.location == "北京"
        assert profile.website == "https://test.com"
        assert isinstance(profile.key_contacts, list)
        assert isinstance(profile.pain_points, list)


class TestContactStrategy:
    """接触策略测试"""
    
    def test_contact_strategy_creation(self):
        """测试接触策略创建"""
        strategy = ContactStrategy(
            primary_method=ContactMethod.EMAIL,
            backup_methods=[ContactMethod.PHONE_CALL, ContactMethod.SOCIAL_MEDIA],
            messaging="我们的CRM解决方案可以帮助您",
            value_proposition="提升30%销售效率",
            call_to_action="预约产品演示",
            timing_recommendations=["工作日上午"],
            personalization_points=["针对制造业定制"]
        )
        
        assert strategy.primary_method == ContactMethod.EMAIL
        assert len(strategy.backup_methods) == 2
        assert ContactMethod.PHONE_CALL in strategy.backup_methods
        assert "CRM解决方案" in strategy.messaging
        assert "30%" in strategy.value_proposition


class TestVisitPlan:
    """拜访计划测试"""
    
    def test_visit_plan_creation(self):
        """测试拜访计划创建"""
        customer_profile = CustomerProfile(
            company_name="测试公司",
            industry="制造业",
            company_size="中型企业"
        )
        
        visit_plan = VisitPlan(
            visit_id="visit_test_20240101",
            customer_profile=customer_profile,
            objectives=["了解需求", "展示价值"],
            agenda=[
                {"time": "0-30分钟", "activity": "需求了解"},
                {"time": "30-60分钟", "activity": "产品演示"}
            ],
            preparation_checklist=["准备资料", "研究背景"],
            materials_needed=["产品手册", "案例"],
            key_questions=["主要挑战？", "预算范围？"],
            success_criteria=["客户感兴趣", "获得联系方式"],
            follow_up_actions=["发送资料", "安排下次会议"]
        )
        
        assert visit_plan.visit_id == "visit_test_20240101"
        assert visit_plan.customer_profile.company_name == "测试公司"
        assert len(visit_plan.objectives) == 2
        assert len(visit_plan.agenda) == 2
        assert visit_plan.duration_minutes == 60


class TestDiscoveryTask:
    """发现任务测试"""
    
    def test_discovery_task_creation(self):
        """测试发现任务创建"""
        task = DiscoveryTask(
            task_id="discovery_test",
            customer_id="customer_123",
            stage=DiscoveryStage.RESEARCH,
            priority=Priority.HIGH,
            title="测试发现任务",
            description="测试描述",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        assert task.task_id == "discovery_test"
        assert task.customer_id == "customer_123"
        assert task.stage == DiscoveryStage.RESEARCH
        assert task.priority == Priority.HIGH
        assert task.status == "pending"
        assert task.progress == 0.0


class TestCustomerDiscoveryWorkflow:
    """客户发现工作流测试"""
    
    @pytest.fixture
    def mock_sales_agent(self):
        """模拟销售Agent"""
        agent = Mock(spec=SalesAgent)
        agent.qualify_customer = AsyncMock(return_value={
            'qualified': True,
            'score': 0.8,
            'reasons': ['符合预算要求', '有决策权']
        })
        agent.generate_contact_strategy = AsyncMock(return_value={
            'primary_method': 'email',
            'backup_methods': ['phone_call'],
            'messaging': '测试消息',
            'value_proposition': '测试价值主张',
            'call_to_action': '预约演示',
            'timing_recommendations': ['工作日上午'],
            'personalization_points': ['行业定制']
        })
        agent.create_visit_plan = AsyncMock(return_value={
            'objectives': ['了解需求', '展示价值'],
            'agenda': [{'time': '0-30分钟', 'activity': '需求了解'}],
            'preparation_checklist': ['准备资料'],
            'materials_needed': ['产品手册'],
            'key_questions': ['主要挑战？'],
            'success_criteria': ['客户感兴趣'],
            'follow_up_actions': ['发送资料']
        })
        agent.execute_customer_contact = AsyncMock(return_value={
            'success': True,
            'response': '客户表示感兴趣',
            'next_steps': ['安排演示']
        })
        return agent
    
    @pytest.fixture
    def mock_market_agent(self):
        """模拟市场Agent"""
        agent = Mock(spec=MarketAgent)
        agent.analyze_market_segment = AsyncMock(return_value={
            'market_size': '大型市场',
            'growth_rate': '15%',
            'key_players': ['竞争对手A', '竞争对手B'],
            'opportunities': ['数字化转型需求']
        })
        return agent
    
    @pytest.fixture
    def mock_crm_expert_agent(self):
        """模拟CRM专家Agent"""
        agent = Mock(spec=CRMExpertAgent)
        agent.enhance_customer_profile = AsyncMock(return_value={
            'key_contacts': [{'name': '张总', 'role': '决策者'}],
            'pain_points': ['效率低下', '数据分散'],
            'current_solutions': ['Excel表格'],
            'decision_makers': [{'name': '李总', 'influence': 'high'}],
            'budget_range': '50-100万',
            'timeline': '6个月内',
            'competitive_landscape': ['竞争对手A']
        })
        return agent
    
    @pytest.fixture
    def mock_customer_service(self):
        """模拟客户服务"""
        service = Mock(spec=CustomerService)
        service.create_customer = AsyncMock(return_value=Mock(id="customer_123"))
        return service
    
    @pytest.fixture
    def mock_lead_service(self):
        """模拟线索服务"""
        return Mock(spec=LeadService)
    
    @pytest.fixture
    def workflow(
        self,
        mock_sales_agent,
        mock_market_agent,
        mock_crm_expert_agent,
        mock_customer_service,
        mock_lead_service
    ):
        """创建工作流实例"""
        return CustomerDiscoveryWorkflow(
            sales_agent=mock_sales_agent,
            market_agent=mock_market_agent,
            crm_expert_agent=mock_crm_expert_agent,
            customer_service=mock_customer_service,
            lead_service=mock_lead_service
        )
    
    @pytest.mark.asyncio
    async def test_start_customer_discovery(self, workflow):
        """测试启动客户发现流程"""
        target_criteria = {
            'industry': '制造业',
            'company_size': '中型企业',
            'location': '北京'
        }
        discovery_goals = ['找到10个潜在客户', '完成5个客户接触']
        
        with patch('src.workflows.customer_discovery.rag_service') as mock_rag:
            mock_rag.query = AsyncMock(return_value=Mock(
                dict=lambda: {'answer': '行业洞察', 'sources': []}
            ))
            
            task_id = await workflow.start_customer_discovery(
                target_criteria=target_criteria,
                discovery_goals=discovery_goals,
                timeline_days=30
            )
        
        assert task_id.startswith('discovery_')
        assert task_id in workflow.active_tasks
        
        task = workflow.active_tasks[task_id]
        assert task.stage == DiscoveryStage.CONTACT_PLANNING  # 应该已经进展到接触规划阶段
        assert task.priority == Priority.HIGH
        assert '制造业' in task.title
    
    @pytest.mark.asyncio
    async def test_execute_research_stage(self, workflow, mock_market_agent):
        """测试研究阶段执行"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.RESEARCH,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        workflow.active_tasks["test_task"] = task
        
        target_criteria = {
            'industry': '制造业',
            'company_size': '中型企业',
            'location': '北京'
        }
        
        with patch('src.workflows.customer_discovery.rag_service') as mock_rag:
            mock_rag.query = AsyncMock(return_value=Mock(
                dict=lambda: {'answer': '行业洞察', 'sources': []}
            ))
            
            await workflow._execute_research_stage("test_task", target_criteria)
        
        # 验证市场Agent被调用
        mock_market_agent.analyze_market_segment.assert_called_once()
        
        # 验证任务状态更新
        assert task.progress == 0.2
        assert task.stage == DiscoveryStage.QUALIFICATION
        assert 'market_research' in task.results
        assert 'potential_customers' in task.results
    
    @pytest.mark.asyncio
    async def test_execute_qualification_stage(self, workflow, mock_sales_agent):
        """测试资格认证阶段执行"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.QUALIFICATION,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        # 添加潜在客户数据
        task.results['potential_customers'] = [
            {
                'company_name': '测试公司1',
                'industry': '制造业',
                'company_size': '中型企业'
            },
            {
                'company_name': '测试公司2',
                'industry': '制造业',
                'company_size': '大型企业'
            }
        ]
        
        workflow.active_tasks["test_task"] = task
        
        await workflow._execute_qualification_stage("test_task")
        
        # 验证销售Agent被调用
        assert mock_sales_agent.qualify_customer.call_count == 2
        
        # 验证任务状态更新
        assert task.progress == 0.4
        assert task.stage == DiscoveryStage.CONTACT_PLANNING
        assert 'qualified_customers' in task.results
    
    @pytest.mark.asyncio
    async def test_execute_contact_planning_stage(self, workflow, mock_sales_agent):
        """测试接触规划阶段执行"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.CONTACT_PLANNING,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        # 添加合格客户数据
        task.results['qualified_customers'] = [
            {
                'customer_data': {'company_name': '测试公司1'},
                'qualification_score': 0.8,
                'customer_profile': {
                    'company_name': '测试公司1',
                    'industry': '制造业',
                    'company_size': '中型企业',
                    'annual_revenue': None,
                    'location': '',
                    'website': '',
                    'key_contacts': [],
                    'pain_points': [],
                    'current_solutions': [],
                    'decision_makers': [],
                    'budget_range': None,
                    'timeline': None,
                    'competitive_landscape': []
                }
            }
        ]
        
        workflow.active_tasks["test_task"] = task
        
        await workflow._execute_contact_planning_stage("test_task")
        
        # 验证销售Agent被调用
        mock_sales_agent.generate_contact_strategy.assert_called()
        mock_sales_agent.create_visit_plan.assert_called()
        
        # 验证任务状态更新
        assert task.progress == 0.6
        assert task.stage == DiscoveryStage.INITIAL_CONTACT
        assert 'contact_plans' in task.results
    
    @pytest.mark.asyncio
    async def test_execute_initial_contact(self, workflow, mock_sales_agent):
        """测试执行初次接触"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.INITIAL_CONTACT,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        # 添加接触计划数据
        task.results['contact_plans'] = [
            {
                'customer_profile': {
                    'company_name': '测试公司1',
                    'industry': '制造业',
                    'company_size': '中型企业',
                    'annual_revenue': None,
                    'location': '',
                    'website': '',
                    'key_contacts': [],
                    'pain_points': [],
                    'current_solutions': [],
                    'decision_makers': [],
                    'budget_range': None,
                    'timeline': None,
                    'competitive_landscape': []
                },
                'contact_strategy': {
                    'primary_method': 'email',
                    'backup_methods': ['phone_call'],
                    'messaging': '测试消息',
                    'value_proposition': '测试价值',
                    'call_to_action': '预约演示',
                    'timing_recommendations': ['工作日'],
                    'personalization_points': ['定制']
                },
                'visit_plan': {}
            }
        ]
        
        workflow.active_tasks["test_task"] = task
        
        with patch('src.workflows.customer_discovery.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            contact_record = await workflow.execute_initial_contact("test_task", 0)
        
        # 验证销售Agent被调用
        mock_sales_agent.execute_customer_contact.assert_called_once()
        
        # 验证接触记录
        assert 'contact_time' in contact_record
        assert contact_record['method'] == 'email'
        assert 'result' in contact_record
        assert 'next_steps' in contact_record
        
        # 验证任务结果更新
        assert 'contact_records' in task.results
        assert len(task.results['contact_records']) == 1
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, workflow):
        """测试获取任务状态"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.RESEARCH,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试描述",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        task.results = {
            'potential_customers': [1, 2, 3],
            'qualified_customers': [1, 2],
            'contact_plans': [1],
            'contact_records': []
        }
        
        workflow.active_tasks["test_task"] = task
        
        status = await workflow.get_task_status("test_task")
        
        assert status is not None
        assert status['task_id'] == "test_task"
        assert status['stage'] == 'research'
        assert status['priority'] == 'high'
        assert status['title'] == "测试任务"
        assert status['results_summary']['potential_customers_count'] == 3
        assert status['results_summary']['qualified_customers_count'] == 2
        assert status['results_summary']['contact_plans_count'] == 1
        assert status['results_summary']['contact_records_count'] == 0
    
    @pytest.mark.asyncio
    async def test_get_visit_plan(self, workflow):
        """测试获取拜访计划"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.CONTACT_PLANNING,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        task.results['contact_plans'] = [
            {
                'customer_profile': {'company_name': '测试公司1'},
                'visit_plan': {
                    'visit_id': 'visit_test_1',
                    'objectives': ['了解需求'],
                    'agenda': [{'time': '0-30分钟', 'activity': '需求了解'}]
                }
            }
        ]
        
        workflow.active_tasks["test_task"] = task
        
        visit_plan = await workflow.get_visit_plan("test_task", "测试公司1")
        
        assert visit_plan is not None
        assert visit_plan['visit_id'] == 'visit_test_1'
        assert len(visit_plan['objectives']) == 1
        assert visit_plan['objectives'][0] == '了解需求'
    
    @pytest.mark.asyncio
    async def test_update_contact_result(self, workflow):
        """测试更新接触结果"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.INITIAL_CONTACT,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        task.results['contact_records'] = [
            {
                'contact_time': datetime.now().isoformat(),
                'method': 'email',
                'result': {'success': True},
                'status': 'pending'
            }
        ]
        
        workflow.active_tasks["test_task"] = task
        
        result_update = {
            'status': 'completed',
            'customer_response': '客户表示感兴趣'
        }
        
        success = await workflow.update_contact_result("test_task", 0, result_update)
        
        assert success is True
        
        contact_record = task.results['contact_records'][0]
        assert contact_record['status'] == 'completed'
        assert contact_record['customer_response'] == '客户表示感兴趣'
        assert 'updated_at' in contact_record
    
    @pytest.mark.asyncio
    async def test_complete_task(self, workflow):
        """测试完成任务"""
        # 创建测试任务
        task = DiscoveryTask(
            task_id="test_task",
            customer_id=None,
            stage=DiscoveryStage.FOLLOW_UP,
            priority=Priority.HIGH,
            title="测试任务",
            description="测试",
            assigned_agent="sales_agent",
            due_date=datetime.now() + timedelta(days=30)
        )
        
        workflow.active_tasks["test_task"] = task
        
        success = await workflow.complete_task("test_task")
        
        assert success is True
        assert task.status == "completed"
        assert task.progress == 1.0
    
    @pytest.mark.asyncio
    async def test_generate_potential_customer_list(self, workflow):
        """测试生成潜在客户列表"""
        target_criteria = {
            'industry': '制造业',
            'company_size': '中型企业',
            'location': '北京'
        }
        
        market_research = {
            'market_size': '大型市场',
            'growth_rate': '15%'
        }
        
        industry_insights = Mock()
        
        customers = await workflow._generate_potential_customer_list(
            target_criteria,
            market_research,
            industry_insights
        )
        
        assert len(customers) == 20
        assert all('company_name' in customer for customer in customers)
        assert all(customer['industry'] == '制造业' for customer in customers)
        assert all(customer['company_size'] == '中型企业' for customer in customers)
        assert all(customer['location'] == '北京' for customer in customers)
    
    @pytest.mark.asyncio
    async def test_create_customer_profile(self, workflow, mock_crm_expert_agent):
        """测试创建客户画像"""
        customer_data = {
            'company_name': '测试公司',
            'industry': '制造业',
            'company_size': '中型企业',
            'location': '北京'
        }
        
        qualification_result = {
            'qualified': True,
            'score': 0.8
        }
        
        profile = await workflow._create_customer_profile(customer_data, qualification_result)
        
        # 验证CRM专家Agent被调用
        mock_crm_expert_agent.enhance_customer_profile.assert_called_once()
        
        # 验证客户画像
        assert profile.company_name == '测试公司'
        assert profile.industry == '制造业'
        assert profile.company_size == '中型企业'
        assert profile.location == '北京'
        assert len(profile.key_contacts) == 1
        assert len(profile.pain_points) == 2


if __name__ == "__main__":
    pytest.main([__file__])