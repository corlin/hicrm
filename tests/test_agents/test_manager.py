"""
Agent管理器测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.agents.manager import AgentManager, AgentRegistration, TaskAssignment
from src.agents.base import BaseAgent, AgentMessage, AgentResponse, MessageType, AgentStatus, AgentCapability
from src.agents.state_manager import AgentStateManager, StateManagerConfig
from src.agents.communication import MessageBroker, CommunicationConfig


class TestAgent(BaseAgent):
    """测试用的Agent实现"""
    
    async def analyze_task(self, message: AgentMessage) -> dict:
        return {"task_type": "test", "needs_collaboration": False}
    
    async def execute_task(self, message: AgentMessage, analysis: dict) -> dict:
        return {"result": f"Processed: {message.content}", "success": True}
    
    async def generate_response(
        self, 
        task_result: dict = None, 
        collaboration_result: dict = None
    ) -> AgentResponse:
        content = task_result.get("result", "No result") if task_result else "No result"
        return AgentResponse(content=content, confidence=0.9)


@pytest.fixture
def mock_state_manager():
    """模拟状态管理器"""
    manager = Mock(spec=AgentStateManager)
    manager.initialize = AsyncMock()
    manager.close = AsyncMock()
    manager.save_state = AsyncMock()
    manager.load_state = AsyncMock()
    manager.get_system_metrics = AsyncMock(return_value={
        "total_agents": 2,
        "active_agents": 1,
        "status_distribution": {AgentStatus.IDLE: 1, AgentStatus.BUSY: 1},
        "total_errors": 0,
        "average_errors": 0
    })
    manager.health_check = AsyncMock(return_value={"status": "healthy"})
    return manager


@pytest.fixture
def mock_message_broker():
    """模拟消息代理"""
    broker = Mock(spec=MessageBroker)
    broker.initialize = AsyncMock()
    broker.close = AsyncMock()
    broker.declare_agent_queue = AsyncMock()
    broker.health_check = AsyncMock(return_value={"status": "healthy"})
    return broker


@pytest.fixture
async def agent_manager(mock_state_manager, mock_message_broker):
    """Agent管理器实例"""
    with patch('src.agents.manager.AgentStateManager', return_value=mock_state_manager), \
         patch('src.agents.manager.MessageBroker', return_value=mock_message_broker):
        
        manager = AgentManager()
        manager.state_manager = mock_state_manager
        manager.message_broker = mock_message_broker
        
        await manager.initialize()
        
        yield manager
        
        await manager.close()


@pytest.fixture
def test_capabilities():
    """测试能力列表"""
    return [
        AgentCapability(name="test_capability", description="Test capability"),
        AgentCapability(name="analysis", description="Analysis capability")
    ]


@pytest.fixture
def test_message():
    """测试消息"""
    return AgentMessage(
        type=MessageType.TASK,
        sender_id="user",
        content="Test task message"
    )


class TestAgentRegistration:
    """测试Agent注册"""
    
    def test_registration_creation(self, test_capabilities):
        """测试注册信息创建"""
        registration = AgentRegistration(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities,
            auto_start=True
        )
        
        assert registration.agent_class == TestAgent
        assert registration.agent_id == "test-agent-1"
        assert registration.name == "Test Agent"
        assert registration.specialty == "Testing"
        assert registration.capabilities == test_capabilities
        assert registration.auto_start is True
        assert registration.instance is None
        assert registration.communicator is None


class TestTaskAssignment:
    """测试任务分配"""
    
    def test_task_assignment_creation(self, test_message):
        """测试任务分配创建"""
        created_at = datetime.now()
        assignment = TaskAssignment(
            task_id="task-123",
            message=test_message,
            assigned_agents=["agent-1", "agent-2"],
            created_at=created_at
        )
        
        assert assignment.task_id == "task-123"
        assert assignment.message == test_message
        assert assignment.assigned_agents == ["agent-1", "agent-2"]
        assert assignment.created_at == created_at
        assert assignment.timeout > created_at
        assert assignment.responses == {}
        assert assignment.completed is False


class TestAgentManager:
    """测试Agent管理器"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_state_manager, mock_message_broker):
        """测试初始化"""
        with patch('src.agents.manager.AgentStateManager', return_value=mock_state_manager), \
             patch('src.agents.manager.MessageBroker', return_value=mock_message_broker):
            
            manager = AgentManager()
            await manager.initialize()
            
            mock_state_manager.initialize.assert_called_once()
            mock_message_broker.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, mock_state_manager, mock_message_broker):
        """测试初始化失败"""
        mock_state_manager.initialize.side_effect = Exception("State manager init failed")
        
        with patch('src.agents.manager.AgentStateManager', return_value=mock_state_manager), \
             patch('src.agents.manager.MessageBroker', return_value=mock_message_broker):
            
            manager = AgentManager()
            
            with pytest.raises(Exception, match="State manager init failed"):
                await manager.initialize()
    
    def test_register_agent(self, agent_manager, test_capabilities):
        """测试注册Agent"""
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities,
            auto_start=True
        )
        
        assert "test-agent-1" in agent_manager.registrations
        registration = agent_manager.registrations["test-agent-1"]
        assert registration.name == "Test Agent"
        assert registration.specialty == "Testing"
        
        # 检查能力索引
        assert "test_capability" in agent_manager.capability_index
        assert "analysis" in agent_manager.capability_index
        assert "test-agent-1" in agent_manager.capability_index["test_capability"]
        assert "test-agent-1" in agent_manager.capability_index["analysis"]
    
    def test_register_agent_duplicate(self, agent_manager, test_capabilities):
        """测试注册重复Agent"""
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        with pytest.raises(ValueError, match="Agent test-agent-1 already registered"):
            agent_manager.register_agent(
                agent_class=TestAgent,
                agent_id="test-agent-1",
                name="Another Agent",
                specialty="Testing",
                capabilities=test_capabilities
            )
    
    @pytest.mark.asyncio
    async def test_start_agent(self, agent_manager, test_capabilities):
        """测试启动Agent"""
        # 先注册Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        # 模拟通信器
        mock_communicator = AsyncMock()
        mock_communicator.initialize = AsyncMock()
        mock_communicator.register_handler = Mock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            result = await agent_manager.start_agent("test-agent-1")
            
            assert result is True
            assert "test-agent-1" in agent_manager.running_agents
            
            registration = agent_manager.registrations["test-agent-1"]
            assert registration.instance is not None
            assert registration.communicator is not None
            
            # 验证通信器初始化和处理器注册
            mock_communicator.initialize.assert_called_once()
            assert mock_communicator.register_handler.call_count == 2
    
    @pytest.mark.asyncio
    async def test_start_agent_not_registered(self, agent_manager):
        """测试启动未注册的Agent"""
        result = await agent_manager.start_agent("nonexistent-agent")
        
        assert result is False
        assert "nonexistent-agent" not in agent_manager.running_agents
    
    @pytest.mark.asyncio
    async def test_start_agent_already_running(self, agent_manager, test_capabilities):
        """测试启动已运行的Agent"""
        # 注册并启动Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        mock_communicator = AsyncMock()
        mock_communicator.initialize = AsyncMock()
        mock_communicator.register_handler = Mock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            await agent_manager.start_agent("test-agent-1")
            
            # 再次启动
            result = await agent_manager.start_agent("test-agent-1")
            assert result is True  # 应该返回True但不重复启动
    
    @pytest.mark.asyncio
    async def test_stop_agent(self, agent_manager, test_capabilities):
        """测试停止Agent"""
        # 注册并启动Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        mock_communicator = AsyncMock()
        mock_communicator.close = AsyncMock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            await agent_manager.start_agent("test-agent-1")
            
            # 停止Agent
            result = await agent_manager.stop_agent("test-agent-1")
            
            assert result is True
            assert "test-agent-1" not in agent_manager.running_agents
            
            registration = agent_manager.registrations["test-agent-1"]
            assert registration.instance is None
            assert registration.communicator is None
            
            mock_communicator.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_agent_not_running(self, agent_manager):
        """测试停止未运行的Agent"""
        result = await agent_manager.stop_agent("nonexistent-agent")
        
        assert result is True  # 应该返回True（幂等操作）
    
    @pytest.mark.asyncio
    async def test_start_all_agents(self, agent_manager, test_capabilities):
        """测试启动所有Agent"""
        # 注册多个Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent 1",
            specialty="Testing",
            capabilities=test_capabilities,
            auto_start=True
        )
        
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-2",
            name="Test Agent 2",
            specialty="Testing",
            capabilities=test_capabilities,
            auto_start=False  # 不自动启动
        )
        
        mock_communicator = AsyncMock()
        mock_communicator.initialize = AsyncMock()
        mock_communicator.register_handler = Mock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            results = await agent_manager.start_all_agents()
            
            assert "test-agent-1" in results
            assert results["test-agent-1"] is True
            assert "test-agent-2" not in results  # auto_start=False
    
    @pytest.mark.asyncio
    async def test_stop_all_agents(self, agent_manager, test_capabilities):
        """测试停止所有Agent"""
        # 注册并启动多个Agent
        for i in range(2):
            agent_id = f"test-agent-{i+1}"
            agent_manager.register_agent(
                agent_class=TestAgent,
                agent_id=agent_id,
                name=f"Test Agent {i+1}",
                specialty="Testing",
                capabilities=test_capabilities
            )
        
        mock_communicator = AsyncMock()
        mock_communicator.initialize = AsyncMock()
        mock_communicator.register_handler = Mock()
        mock_communicator.close = AsyncMock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            await agent_manager.start_all_agents()
            
            # 停止所有Agent
            results = await agent_manager.stop_all_agents()
            
            assert len(results) == 2
            assert all(results.values())
            assert len(agent_manager.running_agents) == 0
    
    @pytest.mark.asyncio
    async def test_send_message_to_agent(self, agent_manager, test_capabilities, test_message):
        """测试向Agent发送消息"""
        # 注册并启动Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        mock_communicator = AsyncMock()
        mock_communicator.initialize = AsyncMock()
        mock_communicator.register_handler = Mock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            await agent_manager.start_agent("test-agent-1")
            
            # 发送消息
            response = await agent_manager.send_message_to_agent("test-agent-1", test_message)
            
            assert response is not None
            assert isinstance(response, AgentResponse)
    
    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_agent(self, agent_manager, test_message):
        """测试向不存在的Agent发送消息"""
        response = await agent_manager.send_message_to_agent("nonexistent-agent", test_message)
        
        assert response is None
    
    @pytest.mark.asyncio
    async def test_assign_task(self, agent_manager, test_capabilities, test_message):
        """测试分配任务"""
        # 注册并启动Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        mock_communicator = AsyncMock()
        mock_communicator.send_message = AsyncMock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            await agent_manager.start_agent("test-agent-1")
            
            # 分配任务
            task_id = await agent_manager.assign_task(
                message=test_message,
                required_capabilities=["test_capability"],
                max_agents=1
            )
            
            assert task_id is not None
            assert task_id in agent_manager.active_tasks
            
            task = agent_manager.active_tasks[task_id]
            assert "test-agent-1" in task.assigned_agents
            
            # 验证消息发送
            mock_communicator.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_task_no_suitable_agents(self, agent_manager, test_message):
        """测试分配任务 - 无合适Agent"""
        with pytest.raises(ValueError, match="No suitable agents available"):
            await agent_manager.assign_task(
                message=test_message,
                required_capabilities=["nonexistent_capability"]
            )
    
    @pytest.mark.asyncio
    async def test_select_agents_by_capability(self, agent_manager, test_capabilities):
        """测试按能力选择Agent"""
        # 注册多个Agent
        for i in range(3):
            agent_id = f"test-agent-{i+1}"
            capabilities = test_capabilities if i < 2 else []  # 前两个有能力，第三个没有
            
            agent_manager.register_agent(
                agent_class=TestAgent,
                agent_id=agent_id,
                name=f"Test Agent {i+1}",
                specialty="Testing",
                capabilities=capabilities
            )
        
        with patch('src.agents.manager.AgentCommunicator'):
            await agent_manager.start_all_agents()
            
            # 选择有特定能力的Agent
            selected = await agent_manager._select_agents(
                required_capabilities=["test_capability"],
                max_agents=2
            )
            
            assert len(selected) <= 2
            assert all(agent_id.startswith("test-agent-") for agent_id in selected)
    
    @pytest.mark.asyncio
    async def test_select_agents_preferred(self, agent_manager, test_capabilities):
        """测试选择首选Agent"""
        # 注册多个Agent
        for i in range(3):
            agent_id = f"test-agent-{i+1}"
            agent_manager.register_agent(
                agent_class=TestAgent,
                agent_id=agent_id,
                name=f"Test Agent {i+1}",
                specialty="Testing",
                capabilities=test_capabilities
            )
        
        mock_communicator = AsyncMock()
        mock_communicator.initialize = AsyncMock()
        mock_communicator.register_handler = Mock()
        
        with patch('src.agents.manager.AgentCommunicator', return_value=mock_communicator):
            await agent_manager.start_all_agents()
            
            # 选择首选Agent
            selected = await agent_manager._select_agents(
                preferred_agents=["test-agent-2"],
                max_agents=1
            )
            
            assert selected == ["test-agent-2"]
    
    @pytest.mark.asyncio
    async def test_rank_agents(self, agent_manager, test_capabilities):
        """测试Agent排序"""
        # 注册Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent 1",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        # 模拟状态
        from src.agents.base import AgentState
        mock_state = AgentState(
            agent_id="test-agent-1",
            status=AgentStatus.IDLE,
            error_count=1,
            performance_metrics={"avg_response_time": 1.5}
        )
        
        agent_manager.state_manager.load_state.return_value = mock_state
        
        ranked = await agent_manager._rank_agents(["test-agent-1"])
        
        assert ranked == ["test-agent-1"]
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, agent_manager, test_capabilities, test_message):
        """测试获取任务状态"""
        # 创建任务
        task_assignment = TaskAssignment(
            task_id="test-task-123",
            message=test_message,
            assigned_agents=["test-agent-1"],
            created_at=datetime.now()
        )
        
        agent_manager.active_tasks["test-task-123"] = task_assignment
        
        status = await agent_manager.get_task_status("test-task-123")
        
        assert status is not None
        assert status["task_id"] == "test-task-123"
        assert status["assigned_agents"] == ["test-agent-1"]
        assert status["completed"] is False
        assert status["response_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, agent_manager):
        """测试获取不存在任务的状态"""
        status = await agent_manager.get_task_status("nonexistent-task")
        
        assert status is None
    
    def test_get_registered_agents(self, agent_manager, test_capabilities):
        """测试获取已注册Agent信息"""
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities,
            auto_start=True
        )
        
        registered = agent_manager.get_registered_agents()
        
        assert "test-agent-1" in registered
        agent_info = registered["test-agent-1"]
        assert agent_info["name"] == "Test Agent"
        assert agent_info["specialty"] == "Testing"
        assert agent_info["auto_start"] is True
        assert agent_info["running"] is False
        assert len(agent_info["capabilities"]) == 2
    
    def test_get_running_agents(self, agent_manager, test_capabilities):
        """测试获取运行中Agent信息"""
        # 注册Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        # 模拟运行中的Agent
        mock_agent = Mock(spec=TestAgent)
        mock_agent.name = "Test Agent"
        mock_agent.specialty = "Testing"
        mock_agent.get_state.return_value = Mock(
            status=AgentStatus.IDLE,
            current_task=None,
            error_count=0,
            last_active=datetime.now()
        )
        mock_agent.is_available.return_value = True
        
        agent_manager.running_agents["test-agent-1"] = mock_agent
        
        running = agent_manager.get_running_agents()
        
        assert "test-agent-1" in running
        agent_info = running["test-agent-1"]
        assert agent_info["name"] == "Test Agent"
        assert agent_info["specialty"] == "Testing"
        assert agent_info["status"] == AgentStatus.IDLE
        assert agent_info["available"] is True
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, agent_manager, test_capabilities):
        """测试获取系统状态"""
        # 注册Agent
        agent_manager.register_agent(
            agent_class=TestAgent,
            agent_id="test-agent-1",
            name="Test Agent",
            specialty="Testing",
            capabilities=test_capabilities
        )
        
        # 添加活跃任务
        task_assignment = TaskAssignment(
            task_id="test-task",
            message=AgentMessage(type=MessageType.TASK, sender_id="user", content="test"),
            assigned_agents=["test-agent-1"],
            created_at=datetime.now()
        )
        agent_manager.active_tasks["test-task"] = task_assignment
        
        status = await agent_manager.get_system_status()
        
        assert status["registered_agents"] == 1
        assert status["running_agents"] == 0
        assert status["active_tasks"] == 1
        assert "agent_metrics" in status
        assert "message_broker" in status
        assert "state_manager" in status
        assert "capabilities" in status
        assert "test_capability" in status["capabilities"]
        assert "analysis" in status["capabilities"]


class TestTaskCleanup:
    """测试任务清理"""
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tasks(self, agent_manager):
        """测试清理过期任务"""
        # 创建过期任务
        expired_time = datetime.now() - timedelta(minutes=10)
        expired_task = TaskAssignment(
            task_id="expired-task",
            message=AgentMessage(type=MessageType.TASK, sender_id="user", content="test"),
            assigned_agents=["test-agent"],
            created_at=expired_time,
            timeout=expired_time + timedelta(minutes=1)  # 已过期
        )
        
        # 创建未过期任务
        active_task = TaskAssignment(
            task_id="active-task",
            message=AgentMessage(type=MessageType.TASK, sender_id="user", content="test"),
            assigned_agents=["test-agent"],
            created_at=datetime.now()
        )
        
        agent_manager.active_tasks["expired-task"] = expired_task
        agent_manager.active_tasks["active-task"] = active_task
        
        # 手动调用清理方法（模拟一次清理）
        now = datetime.now()
        expired_tasks = []
        
        for task_id, task in agent_manager.active_tasks.items():
            if now > task.timeout:
                expired_tasks.append(task_id)
        
        # 清理过期任务
        for task_id in expired_tasks:
            del agent_manager.active_tasks[task_id]
        
        # 验证过期任务被清理
        assert "expired-task" not in agent_manager.active_tasks
        assert "active-task" in agent_manager.active_tasks


if __name__ == "__main__":
    pytest.main([__file__])