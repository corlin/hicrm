"""
Agent任务编排器异步测试 - 覆盖异步执行功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

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
        AgentRole(agent_id="agent1", role_name="Agent 1", responsibilities=["task1"]),
        AgentRole(agent_id="agent2", role_name="Agent 2", responsibilities=["task2"]),
        AgentRole(agent_id="agent3", role_name="Agent 3", responsibilities=["task3"])
    ]


class TestAgentExecutor:
    """测试Agent执行器"""
    
    @pytest.mark.asyncio
    async def test_agent_executor_success(self, orchestrator, mock_agent_manager):
        """测试Agent执行器成功执行"""
        role = AgentRole(agent_id="test-agent", role_name="Test Agent", responsibilities=["test"])
        
        # 模拟成功响应
        mock_response = AgentResponse(
            content="执行成功",
            confidence=0.9,
            suggestions=["建议1", "建议2"],
            metadata={"result": "success", "data": "test_data"}
        )
        mock_agent_manager.send_message_to_agent.return_value = mock_response
        
        # 创建执行器
        executor = orchestrator._create_agent_executor(role)
        
        # 创建测试状态
        task = CollaborationTask(
            name="测试任务", description="测试Agent执行器",
            mode=CollaborationMode.SEQUENTIAL, agent_roles=[role]
        )
        state = WorkflowState(task=task)
        
        # 执行
        result = await executor(state.model_dump())
        
        # 验证结果
        result_state = WorkflowState(**result)
        assert role.agent_id in result_state.intermediate_results
        assert result_state.intermediate_results[role.agent_id]["success"] is True
        assert "response" in result_state.intermediate_results[role.agent_id]
        
        # 验证共享上下文更新
        assert "result" in result_state.shared_context
        assert "data" in result_state.shared_context
        assert result_state.shared_context["result"] == "success"
        
        # 验证Agent管理器调用
        mock_agent_manager.send_message_to_agent.assert_called_once()
        call_args = mock_agent_manager.send_message_to_agent.call_args
        assert call_args[0][0] == role.agent_id
        assert isinstance(call_args[0][1], AgentMessage)
        
        # 验证消息内容
        message = call_args[0][1]
        assert message.type == MessageType.TASK
        assert message.sender_id == "orchestrator"
        assert message.receiver_id == role.agent_id
        assert message.metadata["role"] == role.role_name
        assert message.metadata["responsibilities"] == role.responsibilities 
   
    @pytest.mark.asyncio
    async def test_agent_executor_failure(self, orchestrator, mock_agent_manager):
        """测试Agent执行器失败处理"""
        role = AgentRole(agent_id="failing-agent", role_name="Failing Agent", responsibilities=["fail"])
        
        # 模拟Agent返回None（失败）
        mock_agent_manager.send_message_to_agent.return_value = None
        
        executor = orchestrator._create_agent_executor(role)
        
        task = CollaborationTask(
            name="失败测试", description="测试失败处理",
            mode=CollaborationMode.SEQUENTIAL, agent_roles=[role]
        )
        state = WorkflowState(task=task)
        
        result = await executor(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert role.agent_id in result_state.intermediate_results
        assert result_state.intermediate_results[role.agent_id]["success"] is False
        assert "error" in result_state.intermediate_results[role.agent_id]
        assert result_state.error_count == 1
    
    @pytest.mark.asyncio
    async def test_agent_executor_exception(self, orchestrator, mock_agent_manager):
        """测试Agent执行器异常处理"""
        role = AgentRole(agent_id="exception-agent", role_name="Exception Agent", responsibilities=["exception"])
        
        # 模拟Agent管理器抛出异常
        mock_agent_manager.send_message_to_agent.side_effect = Exception("Agent manager error")
        
        executor = orchestrator._create_agent_executor(role)
        
        task = CollaborationTask(
            name="异常测试", description="测试异常处理",
            mode=CollaborationMode.SEQUENTIAL, agent_roles=[role]
        )
        state = WorkflowState(task=task)
        
        result = await executor(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert role.agent_id in result_state.intermediate_results
        assert result_state.intermediate_results[role.agent_id]["success"] is False
        assert "Agent manager error" in result_state.intermediate_results[role.agent_id]["error"]
        assert result_state.error_count == 1


class TestParallelExecution:
    """测试并行执行"""
    
    @pytest.mark.asyncio
    async def test_execute_parallel_agents_success(self, orchestrator, mock_agent_manager, sample_agent_roles):
        """测试并行执行所有Agent成功"""
        # 模拟所有Agent成功响应
        responses = {
            "agent1": AgentResponse(content="结果1", confidence=0.8),
            "agent2": AgentResponse(content="结果2", confidence=0.9),
            "agent3": AgentResponse(content="结果3", confidence=0.7)
        }
        
        def mock_send_message(agent_id, message):
            return AsyncMock(return_value=responses.get(agent_id))()
        
        mock_agent_manager.send_message_to_agent = mock_send_message
        
        task = CollaborationTask(
            name="并行测试", description="测试并行执行",
            mode=CollaborationMode.PARALLEL, agent_roles=sample_agent_roles
        )
        state = WorkflowState(task=task)
        
        result = await orchestrator._execute_parallel_agents(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert len(result_state.intermediate_results) == 3
        assert all(result["success"] for result in result_state.intermediate_results.values())
        assert result_state.error_count == 0
    
    @pytest.mark.asyncio
    async def test_execute_parallel_agents_partial_failure(self, orchestrator, mock_agent_manager, sample_agent_roles):
        """测试并行执行部分失败"""
        # 模拟部分Agent失败
        responses = {
            "agent1": AgentResponse(content="结果1", confidence=0.8),
            "agent2": None,  # 失败
            "agent3": AgentResponse(content="结果3", confidence=0.7)
        }
        
        def mock_send_message(agent_id, message):
            return AsyncMock(return_value=responses.get(agent_id))()
        
        mock_agent_manager.send_message_to_agent = mock_send_message
        
        task = CollaborationTask(
            name="部分失败测试", description="测试部分失败",
            mode=CollaborationMode.PARALLEL, agent_roles=sample_agent_roles
        )
        state = WorkflowState(task=task)
        
        result = await orchestrator._execute_parallel_agents(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert len(result_state.intermediate_results) == 3
        assert result_state.intermediate_results["agent1"]["success"] is True
        assert result_state.intermediate_results["agent2"]["success"] is False
        assert result_state.intermediate_results["agent3"]["success"] is True
        assert result_state.error_count == 1


class TestLayerExecution:
    """测试层执行"""
    
    @pytest.mark.asyncio
    async def test_layer_executor_success(self, orchestrator, mock_agent_manager):
        """测试层执行器成功"""
        layer_agents = [
            AgentRole(agent_id="layer-agent1", role_name="Layer Agent 1", responsibilities=["task1"]),
            AgentRole(agent_id="layer-agent2", role_name="Layer Agent 2", responsibilities=["task2"])
        ]
        
        # 模拟成功响应
        responses = {
            "layer-agent1": AgentResponse(content="层结果1", confidence=0.8),
            "layer-agent2": AgentResponse(content="层结果2", confidence=0.9)
        }
        
        def mock_send_message(agent_id, message):
            return AsyncMock(return_value=responses.get(agent_id))()
        
        mock_agent_manager.send_message_to_agent = mock_send_message
        
        layer_executor = orchestrator._create_layer_executor(layer_agents)
        
        task = CollaborationTask(
            name="层测试", description="测试层执行",
            mode=CollaborationMode.HIERARCHICAL, agent_roles=layer_agents
        )
        state = WorkflowState(task=task)
        
        result = await layer_executor(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert len(result_state.intermediate_results) == 2
        assert all(result["success"] for result in result_state.intermediate_results.values())
        assert result_state.error_count == 0


class TestPipelineExecution:
    """测试流水线执行"""
    
    @pytest.mark.asyncio
    async def test_pipeline_executor_first_stage(self, orchestrator, mock_agent_manager):
        """测试流水线执行器第一阶段"""
        role = AgentRole(agent_id="pipeline-agent1", role_name="Pipeline Agent 1", responsibilities=["stage1"])
        
        mock_response = AgentResponse(content="第一阶段结果", confidence=0.8)
        mock_agent_manager.send_message_to_agent.return_value = mock_response
        
        pipeline_executor = orchestrator._create_pipeline_executor(role, 0)  # 第一阶段
        
        task = CollaborationTask(
            name="流水线测试", description="测试流水线执行",
            mode=CollaborationMode.PIPELINE, agent_roles=[role],
            input_data={"initial_data": "test"}
        )
        state = WorkflowState(task=task)
        
        result = await pipeline_executor(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert role.agent_id in result_state.intermediate_results
        assert result_state.intermediate_results[role.agent_id]["success"] is True
    
    @pytest.mark.asyncio
    async def test_pipeline_executor_second_stage(self, orchestrator, mock_agent_manager):
        """测试流水线执行器第二阶段"""
        roles = [
            AgentRole(agent_id="pipeline-agent1", role_name="Pipeline Agent 1", responsibilities=["stage1"]),
            AgentRole(agent_id="pipeline-agent2", role_name="Pipeline Agent 2", responsibilities=["stage2"])
        ]
        
        mock_response = AgentResponse(content="第二阶段结果", confidence=0.9)
        mock_agent_manager.send_message_to_agent.return_value = mock_response
        
        pipeline_executor = orchestrator._create_pipeline_executor(roles[1], 1)  # 第二阶段
        
        task = CollaborationTask(
            name="流水线测试", description="测试流水线执行",
            mode=CollaborationMode.PIPELINE, agent_roles=roles
        )
        
        # 模拟第一阶段的结果
        state = WorkflowState(
            task=task,
            intermediate_results={
                "pipeline-agent1": {
                    "success": True,
                    "response": {"content": "第一阶段输出", "data": "stage1_data"}
                }
            }
        )
        
        result = await pipeline_executor(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert roles[1].agent_id in result_state.intermediate_results
        assert result_state.intermediate_results[roles[1].agent_id]["success"] is True
        
        # 验证前一阶段的输出被添加到输入数据中
        assert "stage_0_output" in result_state.task.input_data


class TestConsensusExecution:
    """测试共识执行"""
    
    @pytest.mark.asyncio
    async def test_execute_consensus_agents_success(self, orchestrator, mock_agent_manager):
        """测试共识Agent执行成功"""
        consensus_roles = [
            AgentRole(agent_id="expert1", role_name="Expert 1", responsibilities=["expertise1"], weight=1.0),
            AgentRole(agent_id="expert2", role_name="Expert 2", responsibilities=["expertise2"], weight=0.8),
            AgentRole(agent_id="expert3", role_name="Expert 3", responsibilities=["expertise3"], weight=0.6)
        ]
        
        # 模拟专家响应
        responses = {
            "expert1": AgentResponse(content="专家1意见", confidence=0.9, suggestions=["建议A", "建议B"]),
            "expert2": AgentResponse(content="专家2意见", confidence=0.8, suggestions=["建议B", "建议C"]),
            "expert3": AgentResponse(content="专家3意见", confidence=0.7, suggestions=["建议A", "建议C"])
        }
        
        def mock_send_message(agent_id, message):
            return AsyncMock(return_value=responses.get(agent_id))()
        
        mock_agent_manager.send_message_to_agent = mock_send_message
        
        task = CollaborationTask(
            name="共识测试", description="测试共识执行",
            mode=CollaborationMode.CONSENSUS, agent_roles=consensus_roles
        )
        state = WorkflowState(task=task)
        
        result = await orchestrator._execute_consensus_agents(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert len(result_state.intermediate_results) == 3
        assert all(result["success"] for result in result_state.intermediate_results.values())
        assert result_state.error_count == 0
    
    @pytest.mark.asyncio
    async def test_build_consensus_success(self, orchestrator):
        """测试构建共识成功"""
        consensus_roles = [
            AgentRole(agent_id="expert1", role_name="Expert 1", responsibilities=["expertise1"], weight=1.0),
            AgentRole(agent_id="expert2", role_name="Expert 2", responsibilities=["expertise2"], weight=0.8)
        ]
        
        task = CollaborationTask(
            name="共识测试", description="测试共识构建",
            mode=CollaborationMode.CONSENSUS, agent_roles=consensus_roles
        )
        
        # 模拟Agent响应结果
        state = WorkflowState(
            task=task,
            intermediate_results={
                "expert1": {
                    "success": True,
                    "response": AgentResponse(content="意见1", confidence=0.9, suggestions=["建议A"]).model_dump()
                },
                "expert2": {
                    "success": True,
                    "response": AgentResponse(content="意见2", confidence=0.8, suggestions=["建议B"]).model_dump()
                }
            }
        )
        
        result = await orchestrator._build_consensus(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert "consensus_result" in result_state.shared_context
        
        consensus_result = result_state.shared_context["consensus_result"]
        assert "consensus_confidence" in consensus_result
        assert "participant_count" in consensus_result
        assert consensus_result["participant_count"] == 2
    
    @pytest.mark.asyncio
    async def test_build_consensus_no_valid_responses(self, orchestrator):
        """测试构建共识无有效响应"""
        consensus_roles = [
            AgentRole(agent_id="expert1", role_name="Expert 1", responsibilities=["expertise1"], weight=1.0)
        ]
        
        task = CollaborationTask(
            name="共识测试", description="测试无有效响应",
            mode=CollaborationMode.CONSENSUS, agent_roles=consensus_roles
        )
        
        # 模拟无有效响应
        state = WorkflowState(
            task=task,
            intermediate_results={
                "expert1": {"success": False, "error": "失败"}
            }
        )
        
        result = await orchestrator._build_consensus(state.model_dump())
        
        result_state = WorkflowState(**result)
        assert result_state.error_count == 1
        assert "consensus_result" not in result_state.shared_context


class TestTaskExecution:
    """测试任务执行"""
    
    @pytest.mark.asyncio
    async def test_execute_collaboration_task_not_found(self, orchestrator):
        """测试执行不存在的协作任务"""
        with pytest.raises(ValueError, match="Task nonexistent-task not found"):
            await orchestrator.execute_collaboration_task("nonexistent-task")
    
    @pytest.mark.asyncio
    async def test_execute_collaboration_task_timeout(self, orchestrator, sample_agent_roles):
        """测试执行超时的协作任务"""
        # 创建已超时的任务
        task = orchestrator.create_collaboration_task(
            name="超时任务",
            description="测试超时",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        # 设置任务为已超时
        task.timeout = datetime.now() - timedelta(minutes=1)
        
        result = await orchestrator.execute_collaboration_task(task.task_id)
        
        assert result.status == TaskStatus.FAILED
        assert "timeout" in result.errors
    
    @pytest.mark.asyncio
    async def test_execute_collaboration_task_workflow_exception(self, orchestrator, mock_agent_manager, sample_agent_roles):
        """测试工作流执行异常"""
        # 创建任务
        task = orchestrator.create_collaboration_task(
            name="异常任务",
            description="测试工作流异常",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        # 模拟工作流执行异常
        with patch.object(orchestrator, '_create_workflow') as mock_create_workflow:
            mock_workflow = Mock()
            mock_workflow.ainvoke.side_effect = Exception("Workflow execution error")
            mock_create_workflow.return_value = mock_workflow
            
            result = await orchestrator.execute_collaboration_task(task.task_id)
            
            assert result.status == TaskStatus.FAILED
            assert "execution" in result.errors
            assert "Workflow execution error" in result.errors["execution"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])