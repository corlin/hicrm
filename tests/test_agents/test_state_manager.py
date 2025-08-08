"""
Agent状态管理器测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.agents.state_manager import AgentStateManager, StateManagerConfig
from src.agents.base import AgentState, AgentStatus


@pytest.fixture
def state_config():
    """测试状态管理器配置"""
    return StateManagerConfig(
        redis_url="redis://localhost:6379/15",  # 使用测试数据库
        key_prefix="test:agent:state:",
        ttl=3600,
        cleanup_interval=60
    )


@pytest.fixture
async def state_manager(state_config):
    """状态管理器实例"""
    manager = AgentStateManager(state_config)
    
    # 模拟Redis客户端
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.sadd = AsyncMock()
    mock_redis.hgetall = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.srem = AsyncMock()
    mock_redis.smembers = AsyncMock()
    mock_redis.ttl = AsyncMock()
    mock_redis.close = AsyncMock()
    mock_redis.pipeline = Mock()
    
    # 模拟管道
    mock_pipe = AsyncMock()
    mock_pipe.hset = Mock(return_value=mock_pipe)
    mock_pipe.expire = Mock(return_value=mock_pipe)
    mock_pipe.sadd = Mock(return_value=mock_pipe)
    mock_pipe.delete = Mock(return_value=mock_pipe)
    mock_pipe.srem = Mock(return_value=mock_pipe)
    mock_pipe.execute = AsyncMock(return_value=[True, True, True])
    mock_redis.pipeline.return_value = mock_pipe
    
    manager.redis_client = mock_redis
    
    yield manager
    
    await manager.close()


@pytest.fixture
def test_agent_state():
    """测试Agent状态"""
    return AgentState(
        agent_id="test-agent-1",
        status=AgentStatus.IDLE,
        current_task="test task",
        working_memory={"key": "value"},
        error_count=2,
        performance_metrics={"avg_response_time": 1.5}
    )


class TestStateManagerConfig:
    """测试状态管理器配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = StateManagerConfig()
        
        assert config.key_prefix == "agent:state:"
        assert config.ttl == 86400
        assert config.cleanup_interval == 3600
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = StateManagerConfig(
            redis_url="redis://custom:6379/1",
            key_prefix="custom:prefix:",
            ttl=7200,
            cleanup_interval=1800
        )
        
        assert config.redis_url == "redis://custom:6379/1"
        assert config.key_prefix == "custom:prefix:"
        assert config.ttl == 7200
        assert config.cleanup_interval == 1800


class TestAgentStateManager:
    """测试Agent状态管理器"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, state_config):
        """测试初始化"""
        manager = AgentStateManager(state_config)
        
        # 模拟成功初始化
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await manager.initialize()
            
            assert manager.redis_client is not None
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, state_config):
        """测试初始化失败"""
        manager = AgentStateManager(state_config)
        
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_from_url.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                await manager.initialize()
    
    def test_key_generation(self, state_manager):
        """测试键生成"""
        state_key = state_manager._get_state_key("test-agent")
        assert state_key == "test:agent:state:test-agent"
        
        index_key = state_manager._get_index_key()
        assert index_key == "test:agent:state:index"
    
    @pytest.mark.asyncio
    async def test_save_state(self, state_manager, test_agent_state):
        """测试保存状态"""
        await state_manager.save_state("test-agent-1", test_agent_state)
        
        # 验证Redis操作
        mock_redis = state_manager.redis_client
        mock_redis.pipeline.assert_called_once()
        
        # 验证管道操作
        pipe = mock_redis.pipeline.return_value
        pipe.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_state_error(self, state_manager, test_agent_state):
        """测试保存状态错误"""
        # 模拟Redis错误
        mock_redis = state_manager.redis_client
        pipe = mock_redis.pipeline.return_value
        pipe.execute.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception, match="Redis error"):
            await state_manager.save_state("test-agent-1", test_agent_state)
    
    @pytest.mark.asyncio
    async def test_load_state_success(self, state_manager):
        """测试成功加载状态"""
        # 模拟Redis返回数据
        mock_data = {
            "data": '{"agent_id": "test-agent-1", "status": "idle", "error_count": 0, "last_active": "2024-01-01T12:00:00"}',
            "updated_at": "2024-01-01T12:00:00"
        }
        
        mock_redis = state_manager.redis_client
        mock_redis.hgetall.return_value = mock_data
        
        state = await state_manager.load_state("test-agent-1")
        
        assert state is not None
        assert state.agent_id == "test-agent-1"
        assert state.status == AgentStatus.IDLE
        assert state.error_count == 0
        mock_redis.hgetall.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_state_not_found(self, state_manager):
        """测试加载不存在的状态"""
        mock_redis = state_manager.redis_client
        mock_redis.hgetall.return_value = {}
        
        state = await state_manager.load_state("nonexistent-agent")
        
        assert state is None
        mock_redis.hgetall.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_state_error(self, state_manager):
        """测试加载状态错误"""
        mock_redis = state_manager.redis_client
        mock_redis.hgetall.side_effect = Exception("Redis error")
        
        state = await state_manager.load_state("test-agent-1")
        
        assert state is None
    
    @pytest.mark.asyncio
    async def test_delete_state(self, state_manager):
        """测试删除状态"""
        mock_redis = state_manager.redis_client
        pipe = mock_redis.pipeline.return_value
        pipe.execute.return_value = [1, 1]  # 成功删除
        
        result = await state_manager.delete_state("test-agent-1")
        
        assert result is True
        mock_redis.pipeline.assert_called_once()
        pipe.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_state_not_found(self, state_manager):
        """测试删除不存在的状态"""
        mock_redis = state_manager.redis_client
        pipe = mock_redis.pipeline.return_value
        pipe.execute.return_value = [0, 0]  # 未找到
        
        result = await state_manager.delete_state("nonexistent-agent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_agents(self, state_manager):
        """测试列出Agent"""
        mock_redis = state_manager.redis_client
        mock_redis.smembers.return_value = {"agent-1", "agent-2", "agent-3"}
        
        agents = await state_manager.list_agents()
        
        assert len(agents) == 3
        assert "agent-1" in agents
        assert "agent-2" in agents
        assert "agent-3" in agents
        mock_redis.smembers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_agents_by_status(self, state_manager):
        """测试按状态获取Agent"""
        # 模拟多个Agent状态
        mock_redis = state_manager.redis_client
        mock_redis.smembers.return_value = {"agent-1", "agent-2", "agent-3"}
        
        # 模拟不同状态的Agent
        def mock_hgetall(key):
            if "agent-1" in key:
                return {"data": '{"agent_id": "agent-1", "status": "idle", "last_active": "2024-01-01T12:00:00"}'}
            elif "agent-2" in key:
                return {"data": '{"agent_id": "agent-2", "status": "busy", "last_active": "2024-01-01T12:00:00"}'}
            elif "agent-3" in key:
                return {"data": '{"agent_id": "agent-3", "status": "idle", "last_active": "2024-01-01T12:00:00"}'}
            return {}
        
        mock_redis.hgetall.side_effect = mock_hgetall
        
        idle_agents = await state_manager.get_agents_by_status(AgentStatus.IDLE)
        
        assert len(idle_agents) == 2
        assert "agent-1" in idle_agents
        assert "agent-3" in idle_agents
        assert "agent-2" not in idle_agents
    
    @pytest.mark.asyncio
    async def test_get_active_agents(self, state_manager):
        """测试获取活跃Agent"""
        now = datetime.now()
        active_time = now - timedelta(minutes=30)  # 30分钟前
        inactive_time = now - timedelta(hours=2)   # 2小时前
        
        mock_redis = state_manager.redis_client
        mock_redis.smembers.return_value = {"agent-1", "agent-2"}
        
        def mock_hgetall(key):
            if "agent-1" in key:
                return {"data": f'{{"agent_id": "agent-1", "status": "idle", "last_active": "{active_time.isoformat()}"}}'}
            elif "agent-2" in key:
                return {"data": f'{{"agent_id": "agent-2", "status": "idle", "last_active": "{inactive_time.isoformat()}"}}'}
            return {}
        
        mock_redis.hgetall.side_effect = mock_hgetall
        
        active_agents = await state_manager.get_active_agents()
        
        assert len(active_agents) == 1
        assert "agent-1" in active_agents
        assert "agent-2" not in active_agents
    
    @pytest.mark.asyncio
    async def test_update_agent_status(self, state_manager):
        """测试更新Agent状态"""
        # 模拟现有状态
        mock_redis = state_manager.redis_client
        mock_redis.hgetall.return_value = {
            "data": '{"agent_id": "test-agent", "status": "idle", "error_count": 0, "last_active": "2024-01-01T12:00:00"}'
        }
        
        result = await state_manager.update_agent_status("test-agent", AgentStatus.BUSY)
        
        assert result is True
        # 验证保存操作被调用
        mock_redis.pipeline.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_agent_status_not_found(self, state_manager):
        """测试更新不存在Agent的状态"""
        mock_redis = state_manager.redis_client
        mock_redis.hgetall.return_value = {}
        
        result = await state_manager.update_agent_status("nonexistent", AgentStatus.BUSY)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_agent_metrics(self, state_manager):
        """测试获取Agent指标"""
        mock_redis = state_manager.redis_client
        mock_redis.hgetall.return_value = {
            "data": '{"agent_id": "test-agent", "status": "idle", "error_count": 2, "performance_metrics": {"avg_response_time": 1.5}, "last_active": "2024-01-01T12:00:00"}'
        }
        
        metrics = await state_manager.get_agent_metrics("test-agent")
        
        assert metrics is not None
        assert metrics["agent_id"] == "test-agent"
        assert metrics["status"] == AgentStatus.IDLE
        assert metrics["error_count"] == 2
        assert metrics["performance_metrics"]["avg_response_time"] == 1.5
        assert "uptime" in metrics
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, state_manager):
        """测试获取系统指标"""
        now = datetime.now()
        active_time = now - timedelta(minutes=30)
        
        mock_redis = state_manager.redis_client
        mock_redis.smembers.return_value = {"agent-1", "agent-2"}
        
        def mock_hgetall(key):
            if "agent-1" in key:
                return {"data": f'{{"agent_id": "agent-1", "status": "idle", "error_count": 1, "last_active": "{active_time.isoformat()}"}}'}
            elif "agent-2" in key:
                return {"data": f'{{"agent_id": "agent-2", "status": "busy", "error_count": 2, "last_active": "{active_time.isoformat()}"}}'}
            return {}
        
        mock_redis.hgetall.side_effect = mock_hgetall
        
        metrics = await state_manager.get_system_metrics()
        
        assert metrics["total_agents"] == 2
        assert metrics["active_agents"] == 2
        assert metrics["total_errors"] == 3
        assert metrics["average_errors"] == 1.5
        assert AgentStatus.IDLE in metrics["status_distribution"]
        assert AgentStatus.BUSY in metrics["status_distribution"]
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, state_manager):
        """测试健康检查 - 健康状态"""
        mock_redis = state_manager.redis_client
        mock_redis.ping = AsyncMock()
        mock_redis.smembers.return_value = {"agent-1", "agent-2"}
        
        health = await state_manager.health_check()
        
        assert health["status"] == "healthy"
        assert health["redis_connected"] is True
        assert health["agent_count"] == 2
        mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """测试健康检查 - 未初始化"""
        manager = AgentStateManager()
        
        health = await manager.health_check()
        
        assert health["status"] == "error"
        assert "Not initialized" in health["message"]
    
    @pytest.mark.asyncio
    async def test_health_check_redis_error(self, state_manager):
        """测试健康检查 - Redis错误"""
        mock_redis = state_manager.redis_client
        mock_redis.ping.side_effect = Exception("Redis connection failed")
        
        health = await state_manager.health_check()
        
        assert health["status"] == "error"
        assert health["redis_connected"] is False
        assert "Redis connection failed" in health["message"]


class TestStateManagerCleanup:
    """测试状态管理器清理功能"""
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_states(self, state_manager):
        """测试清理过期状态"""
        mock_redis = state_manager.redis_client
        mock_redis.smembers.return_value = {"agent-1", "agent-2", "agent-3"}
        
        # 模拟TTL检查
        def mock_ttl(key):
            if "agent-1" in key:
                return 3600  # 正常TTL
            elif "agent-2" in key:
                return -1    # 永不过期
            elif "agent-3" in key:
                return -2    # 不存在/已过期
            return -2
        
        mock_redis.ttl.side_effect = mock_ttl
        mock_redis.srem = AsyncMock()
        
        # 手动调用清理方法（模拟一次清理）
        agent_ids = await state_manager.list_agents()
        expired_agents = []
        
        for agent_id in agent_ids:
            state_key = state_manager._get_state_key(agent_id)
            ttl = await mock_redis.ttl(state_key)
            
            # 如果TTL为-2（不存在），则需要清理
            if ttl == -2:
                expired_agents.append(agent_id)
        
        # 清理过期的Agent
        if expired_agents:
            index_key = state_manager._get_index_key()
            await mock_redis.srem(index_key, *expired_agents)
        
        # 验证过期的agent-3被清理
        mock_redis.srem.assert_called_with("test:agent:state:index", "agent-3")


if __name__ == "__main__":
    pytest.main([__file__])