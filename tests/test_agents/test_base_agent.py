"""
BaseAgent基础框架测试
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.agents.base import (
    BaseAgent, AgentState, AgentMessage, AgentResponse, 
    MessageType, AgentStatus, AgentCapability
)
from src.agents.state_manager import AgentStateManager
from src.agents.communication import AgentCommunicator


class TestAgent(BaseAgent):
    """测试用的Agent实现"""
    
    async def analyze_task(self, message: AgentMessage) -> dict:
        """分析任务"""
        return {
            "task_type": "test",
            "complexity": "low",
            "needs_collaboration": "collaborate" in message.content.lower()
        }
    
    async def execute_task(self, message: AgentMessage, analysis: dict) -> dict:
        """执行任务"""
        return {
            "result": f"Processed: {message.content}",
            "success": True
        }
    
    async def generate_response(
        self, 
        task_result: dict = None, 
        collaboration_result: dict = None
    ) -> AgentResponse:
        """生成响应"""
        if task_result:
            content = task_result.get("result", "No result")
        elif collaboration_result:
            content = f"Collaboration result: {collaboration_result}"
        else:
            content = "No result available"
        
        return AgentResponse(
            content=content,
            confidence=0.9,
            suggestions=["suggestion1", "suggestion2"],
            next_actions=["action1"]
        )


@pytest.fixture
def mock_state_manager():
    """模拟状态管理器"""
    manager = Mock(spec=AgentStateManager)
    manager.save_state = AsyncMock()
    manager.load_state = AsyncMock()
    return manager


@pytest.fixture
def mock_communicator():
    """模拟通信器"""
    communicator = Mock(spec=AgentCommunicator)
    communicator.send_message = AsyncMock()
    return communicator


@pytest.fixture
def test_agent(mock_state_manager, mock_communicator):
    """测试Agent实例"""
    capabilities = [
        AgentCapability(name="test_capability", description="Test capability")
    ]
    
    return TestAgent(
        agent_id="test-agent-1",
        name="Test Agent",
        specialty="Testing",
        capabilities=capabilities,
        state_manager=mock_state_manager,
        communicator=mock_communicator
    )


@pytest.fixture
def test_message():
    """测试消息"""
    return AgentMessage(
        type=MessageType.TASK,
        sender_id="user",
        receiver_id="test-agent-1",
        content="Test task message"
    )


class TestAgentState:
    """测试Agent状态"""
    
    def test_agent_state_creation(self):
        """测试Agent状态创建"""
        state = AgentState(agent_id="test-agent")
        
        assert state.agent_id == "test-agent"
        assert state.status == AgentStatus.IDLE
        assert state.current_task is None
        assert state.error_count == 0
        assert isinstance(state.last_active, datetime)
    
    def test_agent_state_validation(self):
        """测试Agent状态验证"""
        # 测试有效状态
        state = AgentState(
            agent_id="test-agent",
            status=AgentStatus.BUSY,
            error_count=2
        )
        assert state.status == AgentStatus.BUSY
        assert state.error_count == 2


class TestAgentMessage:
    """测试Agent消息"""
    
    def test_message_creation(self):
        """测试消息创建"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="sender",
            receiver_id="receiver",
            content="Test content"
        )
        
        assert message.type == MessageType.TASK
        assert message.sender_id == "sender"
        assert message.receiver_id == "receiver"
        assert message.content == "Test content"
        assert message.id is not None
        assert isinstance(message.timestamp, datetime)
    
    def test_message_with_metadata(self):
        """测试带元数据的消息"""
        metadata = {"key": "value", "number": 42}
        message = AgentMessage(
            type=MessageType.COLLABORATION,
            sender_id="sender",
            content="Test",
            metadata=metadata
        )
        
        assert message.metadata == metadata


class TestAgentResponse:
    """测试Agent响应"""
    
    def test_response_creation(self):
        """测试响应创建"""
        response = AgentResponse(
            content="Test response",
            confidence=0.8,
            suggestions=["suggestion1", "suggestion2"],
            next_actions=["action1"]
        )
        
        assert response.content == "Test response"
        assert response.confidence == 0.8
        assert response.suggestions == ["suggestion1", "suggestion2"]
        assert response.next_actions == ["action1"]
    
    def test_response_confidence_validation(self):
        """测试响应置信度验证"""
        # 测试有效置信度
        response = AgentResponse(content="Test", confidence=0.5)
        assert response.confidence == 0.5
        
        # 测试边界值
        response = AgentResponse(content="Test", confidence=0.0)
        assert response.confidence == 0.0
        
        response = AgentResponse(content="Test", confidence=1.0)
        assert response.confidence == 1.0


class TestBaseAgent:
    """测试BaseAgent基础功能"""
    
    def test_agent_initialization(self, test_agent):
        """测试Agent初始化"""
        assert test_agent.id == "test-agent-1"
        assert test_agent.name == "Test Agent"
        assert test_agent.specialty == "Testing"
        assert len(test_agent.capabilities) == 1
        assert test_agent.capabilities[0].name == "test_capability"
        assert test_agent.state.agent_id == "test-agent-1"
        assert test_agent.workflow is not None
    
    def test_agent_state_management(self, test_agent):
        """测试Agent状态管理"""
        # 获取初始状态
        state = test_agent.get_state()
        assert state.status == AgentStatus.IDLE
        assert state.agent_id == "test-agent-1"
    
    @pytest.mark.asyncio
    async def test_agent_state_update(self, test_agent, mock_state_manager):
        """测试Agent状态更新"""
        await test_agent.update_state(
            status=AgentStatus.BUSY,
            current_task="test task"
        )
        
        assert test_agent.state.status == AgentStatus.BUSY
        assert test_agent.state.current_task == "test task"
        mock_state_manager.save_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_state_reset(self, test_agent, mock_state_manager):
        """测试Agent状态重置"""
        # 先修改状态
        test_agent.state.status = AgentStatus.BUSY
        test_agent.state.error_count = 5
        
        # 重置状态
        await test_agent.reset_state()
        
        assert test_agent.state.status == AgentStatus.IDLE
        assert test_agent.state.error_count == 0
        mock_state_manager.save_state.assert_called()
    
    def test_agent_availability(self, test_agent):
        """测试Agent可用性检查"""
        # 初始状态应该可用
        assert test_agent.is_available() is True
        
        # 错误过多时不可用
        test_agent.state.error_count = 10
        assert test_agent.is_available() is False
        
        # 离线状态不可用
        test_agent.state.error_count = 0
        test_agent.state.status = AgentStatus.OFFLINE
        assert test_agent.is_available() is False
    
    def test_capability_management(self, test_agent):
        """测试能力管理"""
        # 添加能力
        new_capability = AgentCapability(
            name="new_capability",
            description="New test capability"
        )
        test_agent.add_capability(new_capability)
        
        capabilities = test_agent.get_capabilities()
        assert len(capabilities) == 2
        assert any(cap.name == "new_capability" for cap in capabilities)
        
        # 移除能力
        removed = test_agent.remove_capability("new_capability")
        assert removed is True
        
        capabilities = test_agent.get_capabilities()
        assert len(capabilities) == 1
        assert not any(cap.name == "new_capability" for cap in capabilities)
        
        # 移除不存在的能力
        removed = test_agent.remove_capability("nonexistent")
        assert removed is False
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, test_agent, test_message, mock_state_manager):
        """测试成功处理消息"""
        response = await test_agent.process_message(test_message)
        
        assert isinstance(response, AgentResponse)
        assert "Processed: Test task message" in response.content
        assert response.confidence == 0.9
        assert len(response.suggestions) == 2
        assert len(response.next_actions) == 1
        
        # 验证状态管理器被调用
        assert mock_state_manager.save_state.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_process_message_with_collaboration(self, test_agent, mock_communicator):
        """测试需要协作的消息处理"""
        # 创建需要协作的消息
        collab_message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user",
            receiver_id="test-agent-1",
            content="Test collaborate message"
        )
        
        # 模拟协作响应
        mock_communicator.send_message.return_value = AgentMessage(
            type=MessageType.RESPONSE,
            sender_id="other-agent",
            content="Collaboration response"
        )
        
        response = await test_agent.process_message(collab_message)
        
        assert isinstance(response, AgentResponse)
        # 由于协作逻辑，响应内容会不同
        assert response.content is not None
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, test_agent):
        """测试消息处理错误处理"""
        # 创建会导致错误的消息（None消息）
        response = await test_agent.process_message(None)
        
        assert isinstance(response, AgentResponse)
        assert "错误" in response.content or "error" in response.content.lower() or "问题" in response.content
        assert response.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_collaboration_without_communicator(self, mock_state_manager):
        """测试没有通信器时的协作处理"""
        # 创建没有通信器的Agent
        agent = TestAgent(
            agent_id="test-agent-no-comm",
            name="Test Agent No Comm",
            specialty="Testing",
            state_manager=mock_state_manager,
            communicator=None
        )
        
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user",
            content="Test collaborate message"
        )
        
        analysis = {"needs_collaboration": True}
        
        result = await agent.handle_collaboration(message, analysis)
        
        assert "error" in result
        assert "Collaboration not available" in result["error"]
    
    def test_agent_string_representation(self, test_agent):
        """测试Agent字符串表示"""
        str_repr = str(test_agent)
        assert "Test Agent" in str_repr
        assert "Testing" in str_repr
        assert "idle" in str_repr.lower()
        
        repr_str = repr(test_agent)
        assert "test-agent-1" in repr_str
        assert "Test Agent" in repr_str


class TestAgentWorkflow:
    """测试Agent工作流"""
    
    @pytest.mark.asyncio
    async def test_workflow_nodes_execution(self, test_agent, test_message):
        """测试工作流节点执行"""
        # 测试各个节点的执行
        state = {"message": test_message}
        
        # 测试输入处理节点
        result = await test_agent._process_input_node(state)
        assert "processed_message" in result
        assert result["agent_id"] == "test-agent-1"
        
        # 测试任务分析节点
        result = await test_agent._analyze_task_node(result)
        assert "task_analysis" in result
        assert result["task_analysis"]["task_type"] == "test"
        
        # 测试任务执行节点
        result = await test_agent._execute_task_node(result)
        assert "task_result" in result
        assert result["task_result"]["success"] is True
        
        # 测试响应生成节点
        result = await test_agent._generate_response_node(result)
        assert "response" in result
        assert isinstance(result["response"], AgentResponse)
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, test_agent):
        """测试工作流错误处理"""
        # 测试没有消息的情况
        state = {}
        
        result = await test_agent._process_input_node(state)
        assert "error" in result
        
        # 测试错误处理节点
        result = await test_agent._handle_error_node(result)
        assert "response" in result
        assert isinstance(result["response"], AgentResponse)
        assert result["response"].confidence == 0.0
    
    def test_should_collaborate_logic(self, test_agent):
        """测试协作判断逻辑"""
        # 测试错误状态
        state = {"error": "Some error"}
        result = test_agent._should_collaborate(state)
        assert result == "error"
        
        # 测试需要协作
        state = {
            "task_analysis": {"needs_collaboration": True}
        }
        result = test_agent._should_collaborate(state)
        assert result == "collaborate"
        
        # 测试正常执行
        state = {
            "task_analysis": {"needs_collaboration": False}
        }
        result = test_agent._should_collaborate(state)
        assert result == "execute"


if __name__ == "__main__":
    pytest.main([__file__])     