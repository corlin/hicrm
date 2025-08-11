#!/usr/bin/env python3
"""
异步编排器测试
"""

import asyncio
from unittest.mock import Mock, AsyncMock
from src.agents.orchestrator import (
    AgentOrchestrator, CollaborationTask, CollaborationMode, 
    TaskPriority, TaskStatus, AgentRole, WorkflowState
)
from src.agents.manager import AgentManager
from src.agents.base import AgentMessage, AgentResponse

async def test_agent_executor():
    """测试Agent执行器"""
    print("Testing agent executor...")
    
    # 创建模拟的Agent管理器
    mock_manager = Mock(spec=AgentManager)
    mock_response = AgentResponse(
        content="分析完成",
        confidence=0.9,
        suggestions=["建议1", "建议2"],
        metadata={"result": "success"}
    )
    mock_manager.send_message_to_agent = AsyncMock(return_value=mock_response)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(mock_manager)
    
    # 创建Agent角色
    role = AgentRole(
        agent_id="test-agent",
        role_name="测试专家",
        responsibilities=["测试任务"]
    )
    
    # 创建任务
    task = CollaborationTask(
        name="测试任务",
        description="测试描述",
        mode=CollaborationMode.SEQUENTIAL,
        agent_roles=[role]
    )
    
    # 创建工作流状态
    state = WorkflowState(task=task)
    
    # 创建并执行Agent执行器
    executor = orchestrator._create_agent_executor(role)
    result = await executor(state.model_dump())
    
    # 验证结果
    result_state = WorkflowState(**result)
    assert role.agent_id in result_state.intermediate_results
    assert result_state.intermediate_results[role.agent_id]["success"] is True
    assert "result" in result_state.shared_context
    
    print("✓ Agent executor test passed")
    
    # 验证Agent管理器被调用
    mock_manager.send_message_to_agent.assert_called_once()
    call_args = mock_manager.send_message_to_agent.call_args
    assert call_args[0][0] == role.agent_id
    assert isinstance(call_args[0][1], AgentMessage)
    
    print("✓ Agent manager interaction verified")

async def test_consensus_calculation():
    """测试共识计算"""
    print("Testing consensus calculation...")
    
    mock_manager = Mock(spec=AgentManager)
    orchestrator = AgentOrchestrator(mock_manager)
    
    # 创建模拟响应
    responses = [
        AgentResponse(content="结果1", confidence=0.9, suggestions=["建议A", "建议B"]),
        AgentResponse(content="结果2", confidence=0.8, suggestions=["建议B", "建议C"]),
        AgentResponse(content="结果3", confidence=0.7, suggestions=["建议A", "建议C"])
    ]
    
    weights = [1.0, 0.8, 0.6]
    
    # 计算共识
    consensus = orchestrator._calculate_weighted_consensus(responses, weights)
    
    # 验证共识结果
    assert "consensus_confidence" in consensus
    assert "consensus_suggestions" in consensus
    assert "participant_count" in consensus
    assert consensus["participant_count"] == 3
    
    # 验证加权置信度计算
    expected_confidence = (0.9 * 1.0 + 0.8 * 0.8 + 0.7 * 0.6) / (1.0 + 0.8 + 0.6)
    assert abs(consensus["consensus_confidence"] - expected_confidence) < 0.001
    
    print("✓ Consensus calculation test passed")

async def test_workflow_creation():
    """测试工作流创建"""
    print("Testing workflow creation...")
    
    mock_manager = Mock(spec=AgentManager)
    orchestrator = AgentOrchestrator(mock_manager)
    
    # 创建不同模式的任务
    roles = [
        AgentRole(agent_id="agent1", role_name="Agent 1", responsibilities=["task1"]),
        AgentRole(agent_id="agent2", role_name="Agent 2", responsibilities=["task2"])
    ]
    
    # 测试顺序工作流
    sequential_task = CollaborationTask(
        name="Sequential Task",
        description="Test sequential",
        mode=CollaborationMode.SEQUENTIAL,
        agent_roles=roles
    )
    
    sequential_workflow = orchestrator._create_sequential_workflow(sequential_task)
    assert sequential_workflow is not None
    print("✓ Sequential workflow created")
    
    # 测试并行工作流
    parallel_task = CollaborationTask(
        name="Parallel Task", 
        description="Test parallel",
        mode=CollaborationMode.PARALLEL,
        agent_roles=roles
    )
    
    parallel_workflow = orchestrator._create_parallel_workflow(parallel_task)
    assert parallel_workflow is not None
    print("✓ Parallel workflow created")
    
    # 测试层次化工作流
    hierarchical_roles = [
        AgentRole(agent_id="agent1", role_name="Agent 1", responsibilities=["task1"]),
        AgentRole(agent_id="agent2", role_name="Agent 2", responsibilities=["task2"], dependencies=["agent1"])
    ]
    
    hierarchical_task = CollaborationTask(
        name="Hierarchical Task",
        description="Test hierarchical", 
        mode=CollaborationMode.HIERARCHICAL,
        agent_roles=hierarchical_roles
    )
    
    hierarchical_workflow = orchestrator._create_hierarchical_workflow(hierarchical_task)
    assert hierarchical_workflow is not None
    print("✓ Hierarchical workflow created")

async def main():
    """主测试函数"""
    print("Running async orchestrator tests...\n")
    
    try:
        await test_agent_executor()
        print()
        
        await test_consensus_calculation()
        print()
        
        await test_workflow_creation()
        print()
        
        print("🎉 All async tests passed! Agent orchestration async functionality is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())