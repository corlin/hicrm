#!/usr/bin/env python3
"""
简单的编排器测试
"""

from src.agents.orchestrator import (
    AgentOrchestrator, CollaborationTask, CollaborationMode, 
    TaskPriority, TaskStatus, AgentRole
)
from src.agents.manager import AgentManager
from unittest.mock import Mock

def test_basic_functionality():
    """测试基本功能"""
    print("Testing basic orchestrator functionality...")
    
    # 创建模拟的Agent管理器
    mock_manager = Mock(spec=AgentManager)
    
    # 创建编排器
    orchestrator = AgentOrchestrator(mock_manager)
    print("✓ Orchestrator created successfully")
    
    # 创建Agent角色
    roles = [
        AgentRole(
            agent_id="sales-agent",
            role_name="销售专家",
            responsibilities=["客户分析"]
        ),
        AgentRole(
            agent_id="market-agent", 
            role_name="市场专家",
            responsibilities=["市场分析"]
        )
    ]
    print("✓ Agent roles created successfully")
    
    # 创建协作任务
    task = orchestrator.create_collaboration_task(
        name="客户需求分析",
        description="分析客户需求并提供解决方案",
        mode=CollaborationMode.SEQUENTIAL,
        agent_roles=roles,
        priority=TaskPriority.HIGH
    )
    print("✓ Collaboration task created successfully")
    
    # 验证任务属性
    assert task.name == "客户需求分析"
    assert task.mode == CollaborationMode.SEQUENTIAL
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING
    assert len(task.agent_roles) == 2
    print("✓ Task properties verified")
    
    # 验证任务在编排器中
    assert task.task_id in orchestrator.active_tasks
    print("✓ Task registered in orchestrator")
    
    # 测试依赖层次构建
    roles_with_deps = [
        AgentRole(agent_id="a", role_name="A", responsibilities=[], dependencies=[]),
        AgentRole(agent_id="b", role_name="B", responsibilities=[], dependencies=["a"]),
        AgentRole(agent_id="c", role_name="C", responsibilities=[], dependencies=["a", "b"])
    ]
    
    layers = orchestrator._build_dependency_layers(roles_with_deps)
    print(f"✓ Dependency layers built: {len(layers)} layers")
    
    # 验证层次结构
    assert len(layers) == 3  # 应该有3层
    assert layers[0][0].agent_id == "a"  # 第一层是a
    assert layers[1][0].agent_id == "b"  # 第二层是b
    assert layers[2][0].agent_id == "c"  # 第三层是c
    print("✓ Dependency layers verified")
    
    print("\n🎉 All tests passed! Agent orchestration is working correctly.")
    return True

if __name__ == "__main__":
    test_basic_functionality()