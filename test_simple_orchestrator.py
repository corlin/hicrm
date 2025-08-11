#!/usr/bin/env python3
"""
简单的编排器测试（使用pytest）
"""

import pytest
import sys
sys.path.append('.')

from src.agents.orchestrator import (
    AgentOrchestrator, CollaborationTask, CollaborationMode, 
    TaskPriority, TaskStatus, AgentRole, WorkflowState
)
from src.agents.base import AgentMessage, AgentResponse, MessageType
from unittest.mock import Mock, AsyncMock


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
    
    def test_task_creation(self):
        """测试任务创建"""
        agent_roles = [
            AgentRole(
                agent_id="sales-agent",
                role_name="销售专家",
                responsibilities=["客户分析"],
                weight=1.0
            )
        ]
        
        task = CollaborationTask(
            name="测试任务",
            description="测试描述",
            mode=CollaborationMode.PARALLEL,
            agent_roles=agent_roles,
            priority=TaskPriority.HIGH
        )
        
        assert task.name == "测试任务"
        assert task.description == "测试描述"
        assert task.mode == CollaborationMode.PARALLEL
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert len(task.agent_roles) == 1
        assert task.task_id is not None


class TestAgentOrchestrator:
    """测试Agent编排器"""
    
    def test_orchestrator_initialization(self):
        """测试编排器初始化"""
        mock_agent_manager = Mock()
        orchestrator = AgentOrchestrator(mock_agent_manager)
        
        assert orchestrator.agent_manager == mock_agent_manager
        assert orchestrator.active_tasks == {}
        assert orchestrator.workflows == {}
    
    def test_create_collaboration_task(self):
        """测试创建协作任务"""
        mock_agent_manager = Mock()
        orchestrator = AgentOrchestrator(mock_agent_manager)
        
        agent_roles = [
            AgentRole(
                agent_id="sales-agent",
                role_name="销售专家",
                responsibilities=["客户分析"],
                weight=1.0
            )
        ]
        
        task = orchestrator.create_collaboration_task(
            name="测试任务",
            description="测试描述",
            mode=CollaborationMode.SEQUENTIAL,
            agent_roles=agent_roles,
            input_data={"key": "value"},
            priority=TaskPriority.HIGH,
            timeout_minutes=30,
            config={"max_retries": 3}
        )
        
        assert task.name == "测试任务"
        assert task.description == "测试描述"
        assert task.mode == CollaborationMode.SEQUENTIAL
        assert task.priority == TaskPriority.HIGH
        assert task.input_data == {"key": "value"}
        assert task.config == {"max_retries": 3}
        assert task.timeout is not None
        assert task.task_id in orchestrator.active_tasks
    
    def test_build_dependency_layers(self):
        """测试构建依赖层次"""
        mock_agent_manager = Mock()
        orchestrator = AgentOrchestrator(mock_agent_manager)
        
        agent_roles = [
            AgentRole(
                agent_id="sales-agent",
                role_name="销售专家",
                responsibilities=["客户分析"],
                weight=1.0
            ),
            AgentRole(
                agent_id="market-agent",
                role_name="市场专家",
                responsibilities=["市场分析"],
                weight=0.8
            ),
            AgentRole(
                agent_id="product-agent",
                role_name="产品专家",
                responsibilities=["产品匹配"],
                weight=0.9,
                dependencies=["market-agent"]  # 依赖市场分析结果
            )
        ]
        
        layers = orchestrator._build_dependency_layers(agent_roles)
        
        # 应该有两层：第一层是没有依赖的Agent，第二层是有依赖的Agent
        assert len(layers) == 2
        
        # 第一层应该包含sales-agent和market-agent（没有依赖）
        layer_0_ids = {role.agent_id for role in layers[0]}
        assert "sales-agent" in layer_0_ids
        assert "market-agent" in layer_0_ids
        
        # 第二层应该包含product-agent（依赖market-agent）
        layer_1_ids = {role.agent_id for role in layers[1]}
        assert "product-agent" in layer_1_ids
    
    def test_calculate_weighted_consensus(self):
        """测试加权共识计算"""
        mock_agent_manager = Mock()
        orchestrator = AgentOrchestrator(mock_agent_manager)
        
        responses = [
            AgentResponse(content="结果1", confidence=0.8, suggestions=["建议A", "建议B"]),
            AgentResponse(content="结果2", confidence=0.9, suggestions=["建议A", "建议C"]),
            AgentResponse(content="结果3", confidence=0.7, suggestions=["建议B", "建议C"])
        ]
        weights = [1.0, 0.8, 0.6]
        
        consensus = orchestrator._calculate_weighted_consensus(responses, weights)
        
        assert "consensus_confidence" in consensus
        assert "consensus_suggestions" in consensus
        assert "participant_count" in consensus
        assert consensus["participant_count"] == 3
        assert consensus["total_weight"] == 2.4
        
        # 验证置信度是加权平均
        expected_confidence = (0.8 * 1.0 + 0.9 * 0.8 + 0.7 * 0.6) / 2.4
        assert abs(consensus["consensus_confidence"] - expected_confidence) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])