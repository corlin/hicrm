"""
线索管理工作流测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from src.workflows.lead_management import (
    LeadManagementWorkflow,
    SalesRep,
    LeadScore,
    AssignmentRule,
    LeadWorkflowTask,
    WorkflowStage,
    LeadPriority,
    AssignmentStrategy
)
from src.agents.professional.market_agent import MarketAgent
from src.agents.professional.sales_management_agent import SalesManagementAgent
from src.agents.professional.sales_agent import SalesAgent
from src.services.lead_service import LeadService
from src.services.customer_service import CustomerService
from src.models.lead import LeadStatus, LeadSource


class TestSalesRep:
    """销售代表测试"""
    
    def test_sales_rep_creation(self):
        """测试销售代表创建"""
        rep = SalesRep(
            rep_id="rep_001",
            name="张销售",
            email="zhang@company.com",
            territory=["北京", "天津"],
            skills=["企业销售", "技术方案"],
            specialties=["制造业", "金融业"],
            current_load=5,
            max_capacity=20,
            performance_score=0.85
        )
        
        assert rep.rep_id == "rep_001"
        assert rep.name == "张销售"
        assert rep.email == "zhang@company.com"
        assert len(rep.territory) == 2
        assert len(rep.skills) == 2
        assert len(rep.specialties) == 2
        assert rep.current_load == 5
        assert rep.max_capacity == 20
        assert rep.performance_score == 0.85
        assert rep.availability is True


class TestLeadScore:
    """线索评分测试"""
    
    def test_lead_score_creation(self):
        """测试线索评分创建"""
        score = LeadScore(
            total_score=85.5,
            demographic_score=80.0,
            behavioral_score=90.0,
            firmographic_score=85.0,
            engagement_score=87.0,
            scoring_factors={
                "job_title": 0.8,
                "company_size": 0.9,
                "industry": 0.7
            },
            confidence=0.92,
            scored_at=datetime.now()
        )
        
        assert score.total_score == 85.5
        assert score.demographic_score == 80.0
        assert score.behavioral_score == 90.0
        assert score.firmographic_score == 85.0
        assert score.engagement_score == 87.0
        assert len(score.scoring_factors) == 3
        assert score.confidence == 0.92


class TestAssignmentRule:
    """分配规则测试"""
    
    def test_assignment_rule_creation(self):
        """测试分配规则创建"""
        rule = AssignmentRule(
            rule_id="rule_001",
            name="高分线索优先分配",
            conditions={"score_min": 80},
            actions={"strategy": "skill_based", "priority": "high"},
            priority=1
        )
        
        assert rule.rule_id == "rule_001"
        assert rule.name == "高分线索优先分配"
        assert rule.conditions["score_min"] == 80
        assert rule.actions["strategy"] == "skill_based"
        assert rule.priority == 1
        assert rule.enabled is True


class TestLeadWorkflowTask:
    """线索工作流任务测试"""
    
    def test_workflow_task_creation(self):
        """测试工作流任务创建"""
        task = LeadWorkflowTask(
            task_id="task_001",
            lead_id="lead_123",
            stage=WorkflowStage.SCORING,
            priority=LeadPriority.HIGH,
            assigned_to="rep_001",
            title="处理高分线索",
            description="来自网站的高质量线索",
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        assert task.task_id == "task_001"
        assert task.lead_id == "lead_123"
        assert task.stage == WorkflowStage.SCORING
        assert task.priority == LeadPriority.HIGH
        assert task.assigned_to == "rep_001"
        assert task.status == "pending"
        assert task.progress == 0.0


class TestLeadManagementWorkflow:
    """线索管理工作流测试"""
    
    @pytest.fixture
    def mock_market_agent(self):
        """模拟市场Agent"""
        agent = Mock(spec=MarketAgent)
        agent.score_lead = AsyncMock(return_value={
            'total_score': 85.0,
            'demographic_score': 80.0,
            'behavioral_score': 90.0,
            'firmographic_score': 85.0,
            'engagement_score': 87.0,
            'factors': {
                'job_title': 0.8,
                'company_size': 0.9,
                'industry': 0.7
            },
            'confidence': 0.92
        })
        return agent
    
    @pytest.fixture
    def mock_sales_management_agent(self):
        """模拟销售管理Agent"""
        agent = Mock(spec=SalesManagementAgent)
        agent.assign_lead = AsyncMock(return_value={
            'assigned_rep_id': 'rep_001',
            'reason': '技能匹配度最高',
            'strategy': 'skill_based',
            'confidence': 0.9
        })
        return agent
    
    @pytest.fixture
    def mock_sales_agent(self):
        """模拟销售Agent"""
        agent = Mock(spec=SalesAgent)
        agent.qualify_lead = AsyncMock(return_value={
            'qualified': True,
            'score': 0.85,
            'reasons': ['符合预算要求', '有决策权', '需求明确'],
            'next_steps': ['安排演示', '发送方案']
        })
        agent.create_follow_up_plan = AsyncMock(return_value={
            'plan_id': 'plan_001',
            'activities': [
                {'type': 'call', 'scheduled_at': '2024-02-01T10:00:00Z', 'description': '初次接触电话'},
                {'type': 'email', 'scheduled_at': '2024-02-02T09:00:00Z', 'description': '发送产品资料'},
                {'type': 'demo', 'scheduled_at': '2024-02-05T14:00:00Z', 'description': '产品演示'}
            ],
            'success_criteria': ['客户响应', '安排会议', '获得需求确认'],
            'timeline_days': 14
        })
        return agent
    
    @pytest.fixture
    def mock_lead_service(self):
        """模拟线索服务"""
        service = Mock(spec=LeadService)
        service.create_lead = AsyncMock(return_value=Mock(id="lead_123"))
        service.get_lead = AsyncMock(return_value=Mock(
            id="lead_123",
            company_name="测试公司",
            contact_name="张三",
            email="zhang@test.com",
            job_title="技术总监",
            industry="制造业",
            company_size="中型企业",
            annual_revenue=5000000,
            location="北京",
            source=LeadSource.WEBSITE,
            status=LeadStatus.NEW,
            score=None,
            custom_fields={}
        ))
        service.update_lead = AsyncMock(return_value=True)
        return service
    
    @pytest.fixture
    def mock_customer_service(self):
        """模拟客户服务"""
        return Mock(spec=CustomerService)
    
    @pytest.fixture
    def workflow(
        self,
        mock_market_agent,
        mock_sales_management_agent,
        mock_sales_agent,
        mock_lead_service,
        mock_customer_service
    ):
        """创建工作流实例"""
        workflow = LeadManagementWorkflow(
            market_agent=mock_market_agent,
            sales_management_agent=mock_sales_management_agent,
            sales_agent=mock_sales_agent,
            lead_service=mock_lead_service,
            customer_service=mock_customer_service
        )
        
        # 手动初始化销售代表（避免异步初始化问题）
        workflow.sales_reps = {
            "rep_001": SalesRep(
                rep_id="rep_001",
                name="张销售",
                email="zhang@company.com",
                territory=["北京", "天津"],
                skills=["企业销售", "技术方案"],
                specialties=["制造业", "金融业"],
                current_load=5,
                max_capacity=20,
                performance_score=0.85
            ),
            "rep_002": SalesRep(
                rep_id="rep_002",
                name="李销售",
                email="li@company.com",
                territory=["上海", "江苏"],
                skills=["大客户销售", "关系维护"],
                specialties=["互联网", "教育"],
                current_load=8,
                max_capacity=25,
                performance_score=0.92
            )
        }
        
        return workflow
    
    @pytest.mark.asyncio
    async def test_process_new_lead(self, workflow, mock_lead_service):
        """测试处理新线索"""
        lead_data = {
            'company_name': '测试公司',
            'contact_name': '张三',
            'email': 'zhang@test.com',
            'phone': '13800138000',
            'job_title': '技术总监',
            'industry': '制造业',
            'company_size': '中型企业',
            'annual_revenue': 5000000,
            'location': '北京'
        }
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            task_id = await workflow.process_new_lead(lead_data, "website")
        
        assert task_id.startswith('lead_task_')
        assert task_id in workflow.active_tasks
        
        task = workflow.active_tasks[task_id]
        assert task.lead_id == "lead_123"
        assert task.stage == WorkflowStage.FOLLOW_UP  # 应该已经进展到跟进阶段
        assert '测试公司' in task.title
        
        # 验证线索服务被调用
        mock_lead_service.create_lead.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_scoring_stage(self, workflow, mock_market_agent, mock_lead_service):
        """测试执行评分阶段"""
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.INTAKE,
            priority=LeadPriority.MEDIUM,
            assigned_to=None,
            title="测试任务",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        workflow.active_tasks["test_task"] = task
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await workflow._execute_scoring_stage("test_task")
        
        # 验证市场Agent被调用
        mock_market_agent.score_lead.assert_called_once()
        
        # 验证任务状态更新
        assert task.stage == WorkflowStage.QUALIFICATION
        assert task.progress == 0.3
        assert task.priority == LeadPriority.CRITICAL  # 高分应该提升优先级
        assert 'lead_score' in task.results
        
        # 验证线索服务更新被调用
        mock_lead_service.update_lead.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_qualification_stage(self, workflow, mock_sales_agent, mock_lead_service):
        """测试执行资格认证阶段"""
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.QUALIFICATION,
            priority=LeadPriority.HIGH,
            assigned_to=None,
            title="测试任务",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        # 添加评分结果
        task.results['lead_score'] = {
            'total_score': 85.0,
            'demographic_score': 80.0,
            'behavioral_score': 90.0,
            'firmographic_score': 85.0,
            'engagement_score': 87.0,
            'scoring_factors': {'job_title': 0.8},
            'confidence': 0.92,
            'scored_at': datetime.now().isoformat()
        }
        
        workflow.active_tasks["test_task"] = task
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await workflow._execute_qualification_stage("test_task")
        
        # 验证销售Agent被调用
        mock_sales_agent.qualify_lead.assert_called_once()
        
        # 验证任务状态更新
        assert task.stage == WorkflowStage.FOLLOW_UP  # 应该进展到跟进阶段
        assert task.progress >= 0.5
        assert 'qualification_result' in task.results
    
    @pytest.mark.asyncio
    async def test_execute_assignment_stage(self, workflow, mock_sales_management_agent, mock_lead_service):
        """测试执行分配阶段"""
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.ASSIGNMENT,
            priority=LeadPriority.HIGH,
            assigned_to=None,
            title="测试任务",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        # 添加评分结果
        task.results['lead_score'] = {
            'total_score': 85.0,
            'demographic_score': 80.0,
            'behavioral_score': 90.0,
            'firmographic_score': 85.0,
            'engagement_score': 87.0,
            'scoring_factors': {'job_title': 0.8},
            'confidence': 0.92,
            'scored_at': datetime.now().isoformat()
        }
        
        workflow.active_tasks["test_task"] = task
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await workflow._execute_assignment_stage("test_task")
        
        # 验证销售管理Agent被调用
        mock_sales_management_agent.assign_lead.assert_called_once()
        
        # 验证任务状态更新
        assert task.assigned_to == "rep_001"
        assert task.stage == WorkflowStage.FOLLOW_UP
        assert task.progress == 0.7
        assert 'assignment_result' in task.results
        
        # 验证销售代表负载更新
        assert workflow.sales_reps["rep_001"].current_load == 6  # 原来5 + 1
        
        # 验证线索服务更新被调用
        mock_lead_service.update_lead.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_follow_up_stage(self, workflow, mock_sales_agent, mock_lead_service):
        """测试执行跟进阶段"""
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.FOLLOW_UP,
            priority=LeadPriority.HIGH,
            assigned_to="rep_001",
            title="测试任务",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        # 添加分配结果
        task.results['assignment_result'] = {
            'assigned_rep_id': 'rep_001',
            'assigned_rep_name': '张销售',
            'assignment_reason': '技能匹配',
            'assignment_strategy': 'skill_based'
        }
        
        workflow.active_tasks["test_task"] = task
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await workflow._execute_follow_up_stage("test_task")
        
        # 验证销售Agent被调用
        mock_sales_agent.create_follow_up_plan.assert_called_once()
        
        # 验证任务状态更新
        assert task.progress == 0.9
        assert 'follow_up_plan' in task.results
        
        # 验证线索服务更新被调用
        mock_lead_service.update_lead.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_lead_status(self, workflow, mock_lead_service):
        """测试更新线索状态"""
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.FOLLOW_UP,
            priority=LeadPriority.HIGH,
            assigned_to="rep_001",
            title="测试任务",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        workflow.active_tasks["test_task"] = task
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            success = await workflow.update_lead_status(
                "test_task",
                LeadStatus.CONVERTED,
                "客户已签约",
                "安排实施"
            )
        
        assert success is True
        
        # 验证任务状态更新
        assert 'status_updates' in task.results
        assert len(task.results['status_updates']) == 1
        
        status_update = task.results['status_updates'][0]
        assert status_update['status'] == 'converted'
        assert status_update['notes'] == '客户已签约'
        assert status_update['next_action'] == '安排实施'
        
        # 如果转化成功，任务应该完成
        assert task.stage == WorkflowStage.CONVERSION
        assert task.progress == 1.0
        assert task.status == "completed"
        
        # 验证线索服务更新被调用
        mock_lead_service.update_lead.assert_called()
    
    @pytest.mark.asyncio
    async def test_reassign_lead(self, workflow, mock_lead_service):
        """测试重新分配线索"""
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.FOLLOW_UP,
            priority=LeadPriority.HIGH,
            assigned_to="rep_001",
            title="测试任务",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        workflow.active_tasks["test_task"] = task
        
        # 记录原始负载
        original_load_rep1 = workflow.sales_reps["rep_001"].current_load
        original_load_rep2 = workflow.sales_reps["rep_002"].current_load
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            success = await workflow.reassign_lead(
                "test_task",
                "rep_002",
                "原销售代表休假"
            )
        
        assert success is True
        
        # 验证任务分配更新
        assert task.assigned_to == "rep_002"
        assert 'reassignment_history' in task.results
        assert len(task.results['reassignment_history']) == 1
        
        reassignment = task.results['reassignment_history'][0]
        assert reassignment['from_rep_id'] == "rep_001"
        assert reassignment['to_rep_id'] == "rep_002"
        assert reassignment['reason'] == "原销售代表休假"
        
        # 验证销售代表负载更新
        assert workflow.sales_reps["rep_001"].current_load == original_load_rep1 - 1
        assert workflow.sales_reps["rep_002"].current_load == original_load_rep2 + 1
        
        # 验证线索服务更新被调用
        mock_lead_service.update_lead.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, workflow):
        """测试获取任务状态"""
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.SCORING,
            priority=LeadPriority.HIGH,
            assigned_to="rep_001",
            title="测试任务",
            description="测试描述",
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        task.results = {
            'lead_score': {'total_score': 85.0},
            'qualification_result': {'qualified': True}
        }
        task.progress = 0.6
        
        workflow.active_tasks["test_task"] = task
        
        status = await workflow.get_task_status("test_task")
        
        assert status is not None
        assert status['task_id'] == "test_task"
        assert status['lead_id'] == "lead_123"
        assert status['stage'] == 'scoring'
        assert status['priority'] == 'high'
        assert status['assigned_to'] == "rep_001"
        assert status['progress'] == 0.6
        assert 'lead_score' in status['results']
        assert 'qualification_result' in status['results']
    
    @pytest.mark.asyncio
    async def test_get_sales_rep_workload(self, workflow):
        """测试获取销售代表工作负载"""
        # 创建一些分配给rep_001的任务
        task1 = LeadWorkflowTask(
            task_id="task_001",
            lead_id="lead_123",
            stage=WorkflowStage.FOLLOW_UP,
            priority=LeadPriority.HIGH,
            assigned_to="rep_001",
            title="任务1",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        task2 = LeadWorkflowTask(
            task_id="task_002",
            lead_id="lead_456",
            stage=WorkflowStage.ASSIGNMENT,
            priority=LeadPriority.MEDIUM,
            assigned_to="rep_001",
            title="任务2",
            description="测试",
            due_date=datetime.now() + timedelta(hours=48)
        )
        
        workflow.active_tasks["task_001"] = task1
        workflow.active_tasks["task_002"] = task2
        
        workload = await workflow.get_sales_rep_workload("rep_001")
        
        assert workload is not None
        assert workload['rep_id'] == "rep_001"
        assert workload['name'] == "张销售"
        assert workload['current_load'] == 5
        assert workload['max_capacity'] == 20
        assert workload['utilization_rate'] == 0.25  # 5/20
        assert workload['assigned_tasks_count'] == 2
        assert len(workload['territory']) == 2
        assert len(workload['skills']) == 2
        assert len(workload['specialties']) == 2
    
    @pytest.mark.asyncio
    async def test_get_workflow_metrics(self, workflow):
        """测试获取工作流指标"""
        # 创建一些测试任务
        tasks = [
            LeadWorkflowTask(
                task_id="task_001",
                lead_id="lead_123",
                stage=WorkflowStage.SCORING,
                priority=LeadPriority.HIGH,
                assigned_to="rep_001",
                title="任务1",
                description="测试",
                due_date=datetime.now() + timedelta(hours=24)
            ),
            LeadWorkflowTask(
                task_id="task_002",
                lead_id="lead_456",
                stage=WorkflowStage.ASSIGNMENT,
                priority=LeadPriority.MEDIUM,
                assigned_to="rep_002",
                title="任务2",
                description="测试",
                due_date=datetime.now() + timedelta(hours=48)
            ),
            LeadWorkflowTask(
                task_id="task_003",
                lead_id="lead_789",
                stage=WorkflowStage.CONVERSION,
                priority=LeadPriority.CRITICAL,
                assigned_to="rep_001",
                title="任务3",
                description="测试",
                due_date=datetime.now() + timedelta(hours=72),
                status="completed",
                progress=1.0
            )
        ]
        
        for task in tasks:
            workflow.active_tasks[task.task_id] = task
        
        # 设置一些进度
        tasks[0].progress = 0.3
        tasks[1].progress = 0.6
        
        metrics = await workflow.get_workflow_metrics()
        
        assert metrics['total_tasks'] == 3
        assert metrics['tasks_by_stage']['scoring'] == 1
        assert metrics['tasks_by_stage']['assignment'] == 1
        assert metrics['tasks_by_stage']['conversion'] == 1
        assert metrics['tasks_by_priority']['high'] == 1
        assert metrics['tasks_by_priority']['medium'] == 1
        assert metrics['tasks_by_priority']['critical'] == 1
        assert metrics['average_progress'] == (0.3 + 0.6 + 1.0) / 3
        assert metrics['completion_rate'] == 1 / 3
        assert 'sales_rep_utilization' in metrics
        assert len(metrics['sales_rep_utilization']) == 2
    
    @pytest.mark.asyncio
    async def test_low_score_lead_nurturing(self, workflow, mock_market_agent, mock_lead_service):
        """测试低分线索进入培育流程"""
        # 设置低分评分结果
        mock_market_agent.score_lead.return_value = {
            'total_score': 30.0,  # 低分
            'demographic_score': 25.0,
            'behavioral_score': 35.0,
            'firmographic_score': 30.0,
            'engagement_score': 28.0,
            'factors': {'job_title': 0.3},
            'confidence': 0.6
        }
        
        # 创建测试任务
        task = LeadWorkflowTask(
            task_id="test_task",
            lead_id="lead_123",
            stage=WorkflowStage.INTAKE,
            priority=LeadPriority.MEDIUM,
            assigned_to=None,
            title="测试任务",
            description="测试",
            due_date=datetime.now() + timedelta(hours=24)
        )
        workflow.active_tasks["test_task"] = task
        
        with patch('src.workflows.lead_management.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await workflow._execute_scoring_stage("test_task")
        
        # 验证低分线索进入培育阶段
        assert task.stage == WorkflowStage.NURTURING
        assert task.priority == LeadPriority.LOW
        assert task.progress == 0.8
        assert 'qualification_result' in task.results
        assert task.results['qualification_result']['qualified'] is False
        assert '培育' in task.results['qualification_result']['reason']


if __name__ == "__main__":
    pytest.main([__file__])