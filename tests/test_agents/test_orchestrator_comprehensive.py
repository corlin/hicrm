"""
Agent任务编排器全面测试 - 提高测试覆盖率
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.agents.orchestrator import (
    AgentOrchestrator, CollaborationTask, CollaborationMode, 
    TaskPriority, TaskStatus, AgentRole, WorkflowState
)
from src.agents.manager import AgentManager
from src.agents.base import AgentMessage, AgentResponse, MessageType


@pytest.fixture
def mock_agent_manager():
    """模拟Agent管理器"""
    manager = Mock(spec=AgentManager)
    manager.send_message_to_agent = AsyncMock()
    return manager


@pytest.fixture
def orchestrator(mock_agent_manager):
    """任务编排器实例"""
    return AgentOrchestrator(mock_agent_manager)


@pytest.fixture
def sample_agent_roles():
    """示例Agent角色"""
    return [
        AgentRole(
            agent_id="sales-agent",
            role_name="销售专家",
            responsibilities=["客户分析", "需求识别"],
            weight=1.0
        ),
        AgentRole(
            agent_id="market-agent",
            role_name="市场专家",
            responsibilities=["市场分析", "竞争分析"],
            weight=0.8
        ),
        AgentRole(
            agent_id="product-agent",
            role_name="产品专家",
            responsibilities=["产品匹配", "技术方案"],
            weight=0.9,
            dependencies=["market-agent"]
        )
    ]


@pytest.fixture
def sample_task(orchestrator, sample_agent_roles):
    """示例协作任务"""
    return orchestrator.create_collaboration_task(
        name="客户需求分析",
        description="分析客户需求并提供解决方案",
        mode=CollaborationMode.SEQUENTIAL,
        agent_roles=sample_agent_roles,
        input_data={"customer_id": "cust-123", "inquiry": "需要CRM系统"},
        priority=TaskPriority.HIGH
    )


class TestCollaborationTask:
    """测试协作任务模型"""
    
    def test_task_creation_with_all_parameters(self, sample_agent_roles):
        """测试使用所有参数创建任务"""
        task = CollaborationTask(
            name="完整测试任务",
            description="测试所有参数",
            mode=CollaborationMode.CONSENSUS,
            agent_roles=sample_agent_roles,
            priority=TaskPriority.URGENT,
            input_data={"key": "value"},
            output_data={"result": "output"},
            timeout=datetime.now() + timedelta(hours=1),
            results={"agent1": "result1"},
            errors={"agent2": "error2"},
            config={"setting": "value"}
        )
        
        assert task.name == "完整测试任务"
        assert task.mode == CollaborationMode.CONSENSUS
        assert task.priority == TaskPriority.URGENT
        assert task.input_data == {"key": "value"}
        assert task.output_data == {"result": "output"}
        assert task.timeout is not None
        assert task.results == {"agent1": "result1"}
        assert task.errors == {"agent2": "error2"}
        assert task.config == {"setting": "value"}
    
    def test_task_status_transitions(self, sample_agent_roles):
        """测试任务状态转换"""
        task = CollaborationTask(
            name="状态测试",
            description="测试状态转换",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        # 初始状态
        assert task.status == TaskStatus.PENDING
        assert task.started_at is None
        assert task.completed_at is None
        
        # 运行状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        
        # 完成状态
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None


class TestWorkflowState:
    """测试工作流状态"""
    
    def test_workflow_state_creation(self, sample_task):
        """测试工作流状态创建"""
        state = WorkflowState(
            task=sample_task,
            current_step=2,
            agent_states={"agent1": "state1"},
            shared_context={"context": "value"},
            intermediate_results={"agent1": {"result": "success"}},
            error_count=1,
            max_errors=3
        )
        
        assert state.task == sample_task
        assert state.current_step == 2
        assert state.agent_states == {"agent1": "state1"}
        assert state.shared_context == {"context": "value"}
        assert state.intermediate_results == {"agent1": {"result": "success"}}
        assert state.error_count == 1
        assert state.max_errors == 3
    
    def test_workflow_state_defaults(self, sample_task):
        """测试工作流状态默认值"""
        state = WorkflowState(task=sample_task)
        
        assert state.current_step == 0
        assert state.agent_states == {}
        assert state.shared_context == {}
        assert state.messages == []
        assert state.intermediate_results == {}
        assert state.error_count == 0
        assert state.max_errors == 5


class TestAgentRole:
    """测试Agent角色"""
    
    def test_agent_role_with_all_parameters(self):
        """测试使用所有参数创建Agent角色"""
        role = AgentRole(
            agent_id="complex-agent",
            role_name="复杂专家",
            responsibilities=["任务1", "任务2", "任务3"],
            dependencies=["agent1", "agent2"],
            weight=0.75,
            required=False
        )
        
        assert role.agent_id == "complex-agent"
        assert role.role_name == "复杂专家"
        assert role.responsibilities == ["任务1", "任务2", "任务3"]
        assert role.dependencies == ["agent1", "agent2"]
        assert role.weight == 0.75
        assert role.required is False
    
    def test_agent_role_defaults(self):
        """测试Agent角色默认值"""
        role = AgentRole(
            agent_id="simple-agent",
            role_name="简单专家",
            responsibilities=["基础任务"]
        )
        
        assert role.dependencies == []
        assert role.weight == 1.0
        assert role.required is True


class TestAgentOrchestrator:
    """测试Agent编排器核心功能"""
    
    def test_orchestrator_initialization(self, mock_agent_manager):
        """测试编排器初始化"""
        orchestrator = AgentOrchestrator(mock_agent_manager)
        
        assert orchestrator.agent_manager == mock_agent_manager
        assert orchestrator.active_tasks == {}
        assert orchestrator.workflows == {}
        assert orchestrator.logger is not None
    
    def test_create_collaboration_task_with_timeout(self, orchestrator, sample_agent_roles):
        """测试创建带超时的协作任务"""
        task = orchestrator.create_collaboration_task(
            name="超时测试任务",
            description="测试超时功能",
            mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles,
            timeout_minutes=60
        )
        
        assert task.timeout is not None
        assert task.timeout > datetime.now()
        assert task.task_id in orchestrator.active_tasks
    
    def test_create_collaboration_task_without_timeout(self, orchestrator, sample_agent_roles):
        """测试创建不带超时的协作任务"""
        task = orchestrator.create_collaboration_task(
            name="无超时任务",
            description="测试无超时",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        assert task.timeout is None
    
    def test_get_task_status_existing(self, orchestrator, sample_task):
        """测试获取存在任务的状态"""
        status = orchestrator.get_task_status(sample_task.task_id)
        
        assert status is not None
        assert status.task_id == sample_task.task_id
        assert status.name == sample_task.name
    
    def test_get_task_status_nonexistent(self, orchestrator):
        """测试获取不存在任务的状态"""
        status = orchestrator.get_task_status("nonexistent-task-id")
        
        assert status is None
    
    def test_cancel_task_success(self, orchestrator, sample_task):
        """测试成功取消任务"""
        result = orchestrator.cancel_task(sample_task.task_id)
        
        assert result is True
        
        # 验证任务状态已更新
        cancelled_task = orchestrator.get_task_status(sample_task.task_id)
        assert cancelled_task.status == TaskStatus.CANCELLED
        assert cancelled_task.completed_at is not None
    
    def test_cancel_task_nonexistent(self, orchestrator):
        """测试取消不存在的任务"""
        result = orchestrator.cancel_task("nonexistent-task-id")
        
        assert result is False
    
    def test_cancel_already_completed_task(self, orchestrator, sample_task):
        """测试取消已完成的任务"""
        # 先将任务标记为完成
        sample_task.status = TaskStatus.COMPLETED
        sample_task.completed_at = datetime.now()
        
        result = orchestrator.cancel_task(sample_task.task_id)
        
        assert result is False
    
    def test_cleanup_completed_tasks(self, orchestrator, sample_agent_roles):
        """测试清理已完成的任务"""
        # 创建多个任务
        old_task = orchestrator.create_collaboration_task(
            name="旧任务",
            description="旧的已完成任务",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        new_task = orchestrator.create_collaboration_task(
            name="新任务",
            description="新的进行中任务",
            mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles
        )
        
        # 将旧任务标记为完成并设置旧的完成时间
        old_task.status = TaskStatus.COMPLETED
        old_task.completed_at = datetime.now() - timedelta(hours=25)  # 25小时前
        
        # 清理24小时前的任务
        cleaned_count = orchestrator.cleanup_completed_tasks(max_age_hours=24)
        
        assert cleaned_count == 1
        assert old_task.task_id not in orchestrator.active_tasks
        assert new_task.task_id in orchestrator.active_tasks
    
    def test_get_system_metrics(self, orchestrator, sample_agent_roles):
        """测试获取系统指标"""
        # 创建不同状态的任务
        task1 = orchestrator.create_collaboration_task(
            name="任务1", description="描述1", mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        task2 = orchestrator.create_collaboration_task(
            name="任务2", description="描述2", mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles
        )
        
        task3 = orchestrator.create_collaboration_task(
            name="任务3", description="描述3", mode=CollaborationMode.CONSENSUS,
            agent_roles=sample_agent_roles
        )
        
        # 设置不同状态
        task2.status = TaskStatus.RUNNING
        task3.status = TaskStatus.COMPLETED
        
        metrics = orchestrator.get_system_metrics()
        
        assert metrics["total_tasks"] == 3
        assert metrics["active_workflows"] == 0
        assert TaskStatus.PENDING in metrics["status_distribution"]
        assert TaskStatus.RUNNING in metrics["status_distribution"]
        assert TaskStatus.COMPLETED in metrics["status_distribution"]
        assert CollaborationMode.SEQUENTIAL in metrics["collaboration_modes"]
        assert CollaborationMode.PARALLEL in metrics["collaboration_modes"]
        assert CollaborationMode.CONSENSUS in metrics["collaboration_modes"]


class TestDependencyLayers:
    """测试依赖层次构建"""
    
    def test_build_simple_dependency_layers(self, orchestrator):
        """测试构建简单依赖层次"""
        roles = [
            AgentRole(agent_id="a", role_name="A", responsibilities=[], dependencies=[]),
            AgentRole(agent_id="b", role_name="B", responsibilities=[], dependencies=["a"]),
            AgentRole(agent_id="c", role_name="C", responsibilities=[], dependencies=["b"])
        ]
        
        layers = orchestrator._build_dependency_layers(roles)
        
        assert len(layers) == 3
        assert layers[0][0].agent_id == "a"
        assert layers[1][0].agent_id == "b"
        assert layers[2][0].agent_id == "c"
    
    def test_build_complex_dependency_layers(self, orchestrator):
        """测试构建复杂依赖层次"""
        roles = [
            AgentRole(agent_id="a", role_name="A", responsibilities=[], dependencies=[]),
            AgentRole(agent_id="b", role_name="B", responsibilities=[], dependencies=[]),
            AgentRole(agent_id="c", role_name="C", responsibilities=[], dependencies=["a"]),
            AgentRole(agent_id="d", role_name="D", responsibilities=[], dependencies=["a", "b"]),
            AgentRole(agent_id="e", role_name="E", responsibilities=[], dependencies=["c", "d"])
        ]
        
        layers = orchestrator._build_dependency_layers(roles)
        
        assert len(layers) == 3
        # 第一层：a, b (无依赖)
        layer_0_ids = {role.agent_id for role in layers[0]}
        assert layer_0_ids == {"a", "b"}
        
        # 第二层：c, d (依赖第一层)
        layer_1_ids = {role.agent_id for role in layers[1]}
        assert layer_1_ids == {"c", "d"}
        
        # 第三层：e (依赖第二层)
        layer_2_ids = {role.agent_id for role in layers[2]}
        assert layer_2_ids == {"e"}
    
    def test_build_circular_dependency_layers(self, orchestrator):
        """测试构建循环依赖层次"""
        roles = [
            AgentRole(agent_id="a", role_name="A", responsibilities=[], dependencies=["b"]),
            AgentRole(agent_id="b", role_name="B", responsibilities=[], dependencies=["a"])
        ]
        
        with patch.object(orchestrator.logger, 'error') as mock_error:
            layers = orchestrator._build_dependency_layers(roles)
            
            # 应该检测到循环依赖并记录错误
            mock_error.assert_called_with("Circular dependency detected in agent roles")
            
            # 应该将所有Agent放在一层
            assert len(layers) == 1
            assert len(layers[0]) == 2
    
    def test_build_empty_dependency_layers(self, orchestrator):
        """测试构建空依赖层次"""
        layers = orchestrator._build_dependency_layers([])
        
        assert layers == []


class TestWorkflowCreation:
    """测试工作流创建"""
    
    def test_create_workflow_sequential(self, orchestrator, sample_agent_roles):
        """测试创建顺序工作流"""
        task = CollaborationTask(
            name="顺序任务",
            description="测试顺序工作流",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        workflow = orchestrator._create_sequential_workflow(task)
        
        assert workflow is not None
        assert hasattr(workflow, 'ainvoke')
    
    def test_create_workflow_parallel(self, orchestrator, sample_agent_roles):
        """测试创建并行工作流"""
        task = CollaborationTask(
            name="并行任务",
            description="测试并行工作流",
            mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles
        )
        
        workflow = orchestrator._create_parallel_workflow(task)
        
        assert workflow is not None
        assert hasattr(workflow, 'ainvoke')
    
    def test_create_workflow_hierarchical(self, orchestrator, sample_agent_roles):
        """测试创建层次化工作流"""
        task = CollaborationTask(
            name="层次化任务",
            description="测试层次化工作流",
            mode=CollaborationMode.HIERARCHICAL,
            agent_roles=sample_agent_roles
        )
        
        workflow = orchestrator._create_hierarchical_workflow(task)
        
        assert workflow is not None
        assert hasattr(workflow, 'ainvoke')
    
    def test_create_workflow_pipeline(self, orchestrator, sample_agent_roles):
        """测试创建流水线工作流"""
        task = CollaborationTask(
            name="流水线任务",
            description="测试流水线工作流",
            mode=CollaborationMode.PIPELINE,
            agent_roles=sample_agent_roles
        )
        
        workflow = orchestrator._create_pipeline_workflow(task)
        
        assert workflow is not None
        assert hasattr(workflow, 'ainvoke')
    
    def test_create_workflow_consensus(self, orchestrator, sample_agent_roles):
        """测试创建共识工作流"""
        task = CollaborationTask(
            name="共识任务",
            description="测试共识工作流",
            mode=CollaborationMode.CONSENSUS,
            agent_roles=sample_agent_roles
        )
        
        workflow = orchestrator._create_consensus_workflow(task)
        
        assert workflow is not None
        assert hasattr(workflow, 'ainvoke')
    
    def test_create_workflow_unsupported_mode(self, orchestrator, sample_agent_roles):
        """测试创建不支持的工作流模式"""
        # 创建一个有效的任务，然后修改其模式为不支持的值
        task = CollaborationTask(
            name="不支持的任务",
            description="测试不支持的工作流",
            mode=CollaborationMode.SEQUENTIAL,  # 先用有效模式创建
            agent_roles=sample_agent_roles
        )
        
        # 直接修改模式为不支持的值（绕过Pydantic验证）
        task.__dict__['mode'] = "unsupported_mode"
        
        with pytest.raises(ValueError, match="Unsupported collaboration mode"):
            orchestrator._create_workflow(task)


class TestWorkflowNodes:
    """测试工作流节点"""
    
    @pytest.mark.asyncio
    async def test_initialize_task(self, orchestrator, sample_task):
        """测试初始化任务节点"""
        state = WorkflowState(task=sample_task)
        
        result = await orchestrator._initialize_task(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert result_state.task.status == TaskStatus.RUNNING
        assert result_state.task.started_at is not None
    
    @pytest.mark.asyncio
    async def test_aggregate_results(self, orchestrator, sample_task):
        """测试聚合结果节点"""
        state = WorkflowState(
            task=sample_task,
            intermediate_results={
                "agent1": {"success": True, "response": {"content": "结果1"}},
                "agent2": {"success": True, "response": {"content": "结果2"}},
                "agent3": {"success": False, "error": "失败"}
            }
        )
        
        result = await orchestrator._aggregate_results(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert len(result_state.task.results) == 2  # 只有成功的结果
        assert "agent1" in result_state.task.results
        assert "agent2" in result_state.task.results
        assert "agent3" not in result_state.task.results
        
        # 检查输出数据
        output_data = result_state.task.output_data
        assert output_data["successful_agents"] == ["agent1", "agent2"]
        assert output_data["failed_agents"] == ["agent3"]
        assert output_data["success_rate"] == 2/3
    
    @pytest.mark.asyncio
    async def test_aggregate_results_empty(self, orchestrator, sample_task):
        """测试聚合空结果"""
        state = WorkflowState(task=sample_task, intermediate_results={})
        
        result = await orchestrator._aggregate_results(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert result_state.task.results == {}
        assert result_state.task.output_data["success_rate"] == 0
    
    @pytest.mark.asyncio
    async def test_finalize_task(self, orchestrator, sample_task):
        """测试完成任务节点"""
        state = WorkflowState(task=sample_task)
        
        result = await orchestrator._finalize_task(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert result_state.task.status == TaskStatus.COMPLETED
        assert result_state.task.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_handle_error(self, orchestrator, sample_task):
        """测试错误处理节点"""
        state = WorkflowState(
            task=sample_task,
            intermediate_results={
                "agent1": {"success": False, "error": "错误1"},
                "agent2": {"success": False, "error": "错误2"},
                "agent3": {"success": True, "response": {"content": "成功"}}
            }
        )
        
        result = await orchestrator._handle_error(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert result_state.task.status == TaskStatus.FAILED
        assert result_state.task.completed_at is not None
        assert len(result_state.task.errors) == 2
        assert "agent1" in result_state.task.errors
        assert "agent2" in result_state.task.errors
        assert "agent3" not in result_state.task.errors


class TestExecutionCheckers:
    """测试执行检查器"""
    
    def test_check_execution_result_continue(self, orchestrator, sample_task):
        """测试执行结果检查 - 继续"""
        state = WorkflowState(task=sample_task, error_count=2, max_errors=5)
        
        result = orchestrator._check_execution_result(state.model_dump())
        
        assert result == "continue"
    
    def test_check_execution_result_error(self, orchestrator, sample_task):
        """测试执行结果检查 - 错误"""
        state = WorkflowState(task=sample_task, error_count=5, max_errors=5)
        
        result = orchestrator._check_execution_result(state.model_dump())
        
        assert result == "error"
    
    def test_check_parallel_execution_completed(self, orchestrator, sample_agent_roles):
        """测试并行执行检查 - 完成"""
        task = CollaborationTask(
            name="测试", description="测试", mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles
        )
        state = WorkflowState(
            task=task,
            intermediate_results={
                "sales-agent": {"success": True},
                "market-agent": {"success": True},
                "product-agent": {"success": True}
            }
        )
        
        result = orchestrator._check_parallel_execution(state.model_dump())
        
        assert result == "completed"
    
    def test_check_parallel_execution_error(self, orchestrator, sample_agent_roles):
        """测试并行执行检查 - 错误"""
        task = CollaborationTask(
            name="测试", description="测试", mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles
        )
        state = WorkflowState(task=task, error_count=10, max_errors=5)
        
        result = orchestrator._check_parallel_execution(state.model_dump())
        
        assert result == "error"
    
    def test_check_all_completed_success(self, orchestrator, sample_agent_roles):
        """测试检查全部完成 - 成功"""
        task = CollaborationTask(
            name="测试", description="测试", mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles
        )
        state = WorkflowState(
            task=task,
            intermediate_results={
                "sales-agent": {"success": True},
                "market-agent": {"success": True},
                "product-agent": {"success": True}
            }
        )
        
        result = orchestrator._check_all_completed(state.model_dump())
        
        assert result == "completed"
    
    def test_check_all_completed_continue(self, orchestrator, sample_agent_roles):
        """测试检查全部完成 - 继续"""
        task = CollaborationTask(
            name="测试", description="测试", mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles
        )
        state = WorkflowState(
            task=task,
            intermediate_results={
                "sales-agent": {"success": True}
                # 缺少其他Agent的结果
            }
        )
        
        result = orchestrator._check_all_completed(state.model_dump())
        
        assert result == "continue"


class TestConsensusCalculation:
    """测试共识计算"""
    
    def test_calculate_weighted_consensus_normal(self, orchestrator):
        """测试正常的加权共识计算"""
        responses = [
            AgentResponse(content="结果1", confidence=0.8, suggestions=["建议A", "建议B"]),
            AgentResponse(content="结果2", confidence=0.9, suggestions=["建议B", "建议C"]),
            AgentResponse(content="结果3", confidence=0.7, suggestions=["建议A", "建议C"])
        ]
        weights = [1.0, 0.8, 0.6]
        
        consensus = orchestrator._calculate_weighted_consensus(responses, weights)
        
        assert "consensus_confidence" in consensus
        assert "consensus_suggestions" in consensus
        assert "participant_count" in consensus
        assert "total_weight" in consensus
        
        assert consensus["participant_count"] == 3
        assert consensus["total_weight"] == 2.4
        
        # 验证加权置信度计算
        expected_confidence = (0.8 * 1.0 + 0.9 * 0.8 + 0.7 * 0.6) / 2.4
        assert abs(consensus["consensus_confidence"] - expected_confidence) < 0.001
        
        # 验证建议排序（按频率）
        assert "建议A" in consensus["consensus_suggestions"]
        assert "建议B" in consensus["consensus_suggestions"]
        assert "建议C" in consensus["consensus_suggestions"]
    
    def test_calculate_weighted_consensus_zero_weight(self, orchestrator):
        """测试零权重的共识计算"""
        responses = [
            AgentResponse(content="结果1", confidence=0.8, suggestions=["建议A"])
        ]
        weights = [0.0]
        
        consensus = orchestrator._calculate_weighted_consensus(responses, weights)
        
        assert consensus["consensus"] == "No valid weights"
    
    def test_calculate_weighted_consensus_empty(self, orchestrator):
        """测试空响应的共识计算"""
        responses = []
        weights = []
        
        consensus = orchestrator._calculate_weighted_consensus(responses, weights)
        
        assert consensus["consensus"] == "No valid weights"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])