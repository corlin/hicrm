"""
Agent任务编排器测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.agents.orchestrator import (
    AgentOrchestrator, CollaborationTask, CollaborationMode, TaskPriority, 
    TaskStatus, AgentRole, WorkflowState
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
            dependencies=["market-agent"]  # 依赖市场分析结果
        )
    ]


class TestAgentRole:
    """测试Agent角色"""
    
    def test_agent_role_creation(self):
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
    
    def test_agent_role_defaults(self):
        """测试Agent角色默认值"""
        role = AgentRole(
            agent_id="test-agent",
            role_name="测试专家",
            responsibilities=["测试任务"]
        )
        
        assert role.dependencies == []
        assert role.weight == 1.0
        assert role.required is True


class TestCollaborationTask:
    """测试协作任务"""
    
    def test_task_creation(self, sample_agent_roles):
        """测试任务创建"""
        task = CollaborationTask(
            name="测试任务",
            description="测试描述",
            mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles,
            priority=TaskPriority.HIGH
        )
        
        assert task.name == "测试任务"
        assert task.description == "测试描述"
        assert task.mode == CollaborationMode.PARALLEL
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert len(task.agent_roles) == 3
        assert task.task_id is not None
        assert isinstance(task.created_at, datetime)
    
    def test_task_defaults(self, sample_agent_roles):
        """测试任务默认值"""
        task = CollaborationTask(
            name="测试任务",
            description="测试描述",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=sample_agent_roles
        )
        
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING
        assert task.input_data == {}
        assert task.output_data == {}
        assert task.results == {}
        assert task.errors == {}
        assert task.config == {}


class TestAgentOrchestrator:
    """测试Agent编排器"""
    
    def test_orchestrator_initialization(self, mock_agent_manager):
        """测试编排器初始化"""
        orchestrator = AgentOrchestrator(mock_agent_manager)
        
        assert orchestrator.agent_manager == mock_agent_manager
        assert orchestrator.active_tasks == {}
        assert orchestrator.workflows == {}
    
    def test_create_collaboration_task(self, orchestrator, sample_agent_roles):
        """测试创建协作任务"""
        task = orchestrator.create_collaboration_task(
            name="测试任务",
            description="测试描述",
            mode=CollaborationMode.PARALLEL,
            agent_roles=sample_agent_roles,
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


if __name__ == "__main__":
    pytest.main([__file__])