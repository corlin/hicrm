#!/usr/bin/env python3
"""
核心编排器功能测试
"""

import pytest
from unittest.mock import Mock
from src.agents.orchestrator import (
    AgentOrchestrator, CollaborationTask, CollaborationMode, 
    TaskPriority, TaskStatus, AgentRole
)
from src.agents.manager import AgentManager

def test_agent_role_creation():
    """测试Agent角色创建"""
    role = AgentRole(
        agent_id="test-agent",
        role_name="测试专家",
        responsibilities=["测试任务"],
        dependencies=["other-agent"],
        weight=0.8,
        required=True
    )
    
    assert role.agent_id == "test-agent"
    assert role.role_name == "测试专家"
    assert role.responsibilities == ["测试任务"]
    assert role.dependencies == ["other-agent"]
    assert role.weight == 0.8
    assert role.required is True

def test_collaboration_task_creation():
    """测试协作任务创建"""
    roles = [
        AgentRole(
            agent_id="sales-agent",
            role_name="销售专家",
            responsibilities=["客户分析"]
        )
    ]
    
    task = CollaborationTask(
        name="测试任务",
        description="测试描述",
        mode=CollaborationMode.PARALLEL,
        agent_roles=roles,
        priority=TaskPriority.HIGH
    )
    
    assert task.name == "测试任务"
    assert task.description == "测试描述"
    assert task.mode == CollaborationMode.PARALLEL
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING
    assert len(task.agent_roles) == 1

def test_orchestrator_initialization():
    """测试编排器初始化"""
    mock_manager = Mock(spec=AgentManager)
    orchestrator = AgentOrchestrator(mock_manager)
    
    assert orchestrator.agent_manager == mock_manager
    assert orchestrator.active_tasks == {}
    assert orchestrator.workflows == {}

def test_create_collaboration_task():
    """测试创建协作任务"""
    mock_manager = Mock(spec=AgentManager)
    orchestrator = AgentOrchestrator(mock_manager)
    
    roles = [
        AgentRole(
            agent_id="sales-agent",
            role_name="销售专家",
            responsibilities=["客户分析"]
        )
    ]
    
    task = orchestrator.create_collaboration_task(
        name="测试任务",
        description="测试描述",
        mode=CollaborationMode.PARALLEL,
        agent_roles=roles,
        input_data={"key": "value"},
        priority=TaskPriority.HIGH,
        timeout_minutes=30,
        config={"max_retries": 3}
    )
    
    assert task.name == "测试任务"
    assert task.description == "测试描述"
    assert task.mode == CollaborationMode.PARALLEL
    assert task.priority == TaskPriority.HIGH
    assert task.input_data == {"key": "value"}
    assert task.config == {"max_retries": 3}
    assert task.timeout is not None
    assert task.task_id in orchestrator.active_tasks

def test_dependency_layers():
    """测试依赖层次构建"""
    mock_manager = Mock(spec=AgentManager)
    orchestrator = AgentOrchestrator(mock_manager)
    
    roles = [
        AgentRole(agent_id="a", role_name="A", responsibilities=[], dependencies=[]),
        AgentRole(agent_id="b", role_name="B", responsibilities=[], dependencies=["a"]),
        AgentRole(agent_id="c", role_name="C", responsibilities=[], dependencies=["a", "b"])
    ]
    
    layers = orchestrator._build_dependency_layers(roles)
    
    # 验证层次结构
    assert len(layers) == 3  # 应该有3层
    assert layers[0][0].agent_id == "a"  # 第一层是a
    assert layers[1][0].agent_id == "b"  # 第二层是b
    assert layers[2][0].agent_id == "c"  # 第三层是c

if __name__ == "__main__":
    pytest.main([__file__, "-v"])