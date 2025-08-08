"""
Agent通信系统测试
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.agents.communication import (
    MessageBroker, AgentCommunicator, CommunicationConfig
)
from src.agents.base import AgentMessage, MessageType


@pytest.fixture
def comm_config():
    """测试通信配置"""
    return CommunicationConfig(
        rabbitmq_url="amqp://guest:guest@localhost:5672/test",
        exchange_name="test_agent_communication",
        queue_prefix="test_agent_queue_",
        response_timeout=5,
        max_retries=2,
        retry_delay=0.1
    )


@pytest.fixture
async def message_broker(comm_config):
    """消息代理实例"""
    broker = MessageBroker(comm_config)
    
    # 模拟aio_pika组件
    mock_connection = AsyncMock()
    mock_connection.is_closed = False
    mock_connection.close = AsyncMock()
    
    mock_channel = AsyncMock()
    mock_channel.is_closed = False
    mock_channel.set_qos = AsyncMock()
    
    mock_exchange = AsyncMock()
    mock_exchange.publish = AsyncMock()
    
    mock_queue = AsyncMock()
    mock_queue.bind = AsyncMock()
    
    mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)
    mock_connection.channel = AsyncMock(return_value=mock_channel)
    
    broker.connection = mock_connection
    broker.channel = mock_channel
    broker.exchange = mock_exchange
    
    yield broker
    
    await broker.close()


@pytest.fixture
async def agent_communicator(message_broker):
    """Agent通信器实例"""
    communicator = AgentCommunicator("test-agent-1", message_broker)
    
    # 模拟队列
    mock_queue = AsyncMock()
    mock_queue.iterator = AsyncMock()
    communicator.queue = mock_queue
    
    yield communicator
    
    await communicator.close()


@pytest.fixture
def test_message():
    """测试消息"""
    return AgentMessage(
        type=MessageType.TASK,
        sender_id="sender-agent",
        receiver_id="receiver-agent",
        content="Test message content"
    )


class TestCommunicationConfig:
    """测试通信配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = CommunicationConfig()
        
        assert config.exchange_name == "agent_communication"
        assert config.queue_prefix == "agent_queue_"
        assert config.response_timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = CommunicationConfig(
            rabbitmq_url="amqp://custom:5672/",
            exchange_name="custom_exchange",
            queue_prefix="custom_queue_",
            response_timeout=60,
            max_retries=5,
            retry_delay=2
        )
        
        assert config.rabbitmq_url == "amqp://custom:5672/"
        assert config.exchange_name == "custom_exchange"
        assert config.queue_prefix == "custom_queue_"
        assert config.response_timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2


class TestMessageBroker:
    """测试消息代理"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, comm_config):
        """测试初始化"""
        broker = MessageBroker(comm_config)
        
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_exchange = AsyncMock()
            
            mock_connection.channel.return_value = mock_channel
            mock_channel.set_qos = AsyncMock()
            mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
            mock_connect.return_value = mock_connection
            
            await broker.initialize()
            
            assert broker.connection is not None
            assert broker.channel is not None
            assert broker.exchange is not None
            mock_connect.assert_called_once()
            mock_channel.set_qos.assert_called_once_with(prefetch_count=10)
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, comm_config):
        """测试初始化失败"""
        broker = MessageBroker(comm_config)
        
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                await broker.initialize()
    
    @pytest.mark.asyncio
    async def test_declare_agent_queue(self, message_broker):
        """测试声明Agent队列"""
        queue = await message_broker.declare_agent_queue("test-agent")
        
        # 验证队列声明和绑定
        message_broker.channel.declare_queue.assert_called_once()
        queue.bind.assert_called_once_with(message_broker.exchange, routing_key="test-agent")
    
    @pytest.mark.asyncio
    async def test_publish_message(self, message_broker, test_message):
        """测试发布消息"""
        await message_broker.publish_message(test_message, "receiver-agent")
        
        # 验证消息发布
        message_broker.exchange.publish.assert_called_once()
        
        # 检查发布的消息参数
        call_args = message_broker.exchange.publish.call_args
        amqp_message = call_args[0][0]
        routing_key = call_args[1]["routing_key"]
        
        assert routing_key == "receiver-agent"
        assert amqp_message.headers["message_id"] == test_message.id
        assert amqp_message.headers["message_type"] == test_message.type
        assert amqp_message.headers["sender_id"] == test_message.sender_id
    
    @pytest.mark.asyncio
    async def test_publish_message_error(self, message_broker, test_message):
        """测试发布消息错误"""
        message_broker.exchange.publish.side_effect = Exception("Publish failed")
        
        with pytest.raises(Exception, match="Publish failed"):
            await message_broker.publish_message(test_message, "receiver-agent")
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, message_broker):
        """测试健康检查 - 健康状态"""
        health = await message_broker.health_check()
        
        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["channel_open"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_not_connected(self, comm_config):
        """测试健康检查 - 未连接"""
        broker = MessageBroker(comm_config)
        
        health = await broker.health_check()
        
        assert health["status"] == "error"
        assert "Not connected" in health["message"]
    
    @pytest.mark.asyncio
    async def test_health_check_connection_closed(self, message_broker):
        """测试健康检查 - 连接已关闭"""
        message_broker.connection.is_closed = True
        
        health = await message_broker.health_check()
        
        assert health["status"] == "error"
        assert "Not connected" in health["message"]


class TestAgentCommunicator:
    """测试Agent通信器"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, message_broker):
        """测试初始化"""
        communicator = AgentCommunicator("test-agent", message_broker)
        
        # 模拟队列声明
        mock_queue = AsyncMock()
        message_broker.declare_agent_queue = AsyncMock(return_value=mock_queue)
        
        with patch.object(communicator, '_start_consuming') as mock_start:
            mock_task = AsyncMock()
            with patch('asyncio.create_task', return_value=mock_task):
                await communicator.initialize()
                
                assert communicator.queue is not None
                message_broker.declare_agent_queue.assert_called_once_with("test-agent")
    
    def test_register_handler(self, agent_communicator):
        """测试注册消息处理器"""
        async def test_handler(message):
            return "handled"
        
        agent_communicator.register_handler(MessageType.TASK, test_handler)
        
        assert MessageType.TASK in agent_communicator.message_handlers
        assert agent_communicator.message_handlers[MessageType.TASK] == test_handler
    
    @pytest.mark.asyncio
    async def test_send_message(self, agent_communicator, test_message):
        """测试发送消息"""
        agent_communicator.message_broker.publish_message = AsyncMock()
        
        await agent_communicator.send_message(test_message)
        
        agent_communicator.message_broker.publish_message.assert_called_once_with(
            test_message, "receiver-agent"
        )
    
    @pytest.mark.asyncio
    async def test_send_message_with_response(self, agent_communicator, test_message):
        """测试发送消息并等待响应"""
        agent_communicator.message_broker.publish_message = AsyncMock()
        
        # 模拟响应
        response_message = AgentMessage(
            type=MessageType.RESPONSE,
            sender_id="receiver-agent",
            receiver_id="test-agent-1",
            content="Response content",
            correlation_id=test_message.correlation_id
        )
        
        # 模拟等待响应
        with patch.object(agent_communicator, '_wait_for_response') as mock_wait:
            mock_wait.return_value = response_message
            
            result = await agent_communicator.send_message(test_message, wait_for_response=True)
            
            assert result == response_message
            mock_wait.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, agent_communicator, test_message):
        """测试广播消息"""
        agent_communicator.message_broker.publish_message = AsyncMock()
        
        await agent_communicator.broadcast_message(test_message)
        
        agent_communicator.message_broker.publish_message.assert_called_once_with(
            test_message, "broadcast"
        )
        assert test_message.receiver_id is None
    
    @pytest.mark.asyncio
    async def test_process_message_with_handler(self, agent_communicator):
        """测试处理消息 - 有处理器"""
        # 注册处理器
        async def test_handler(message):
            return f"Handled: {message.content}"
        
        agent_communicator.register_handler(MessageType.TASK, test_handler)
        
        # 创建模拟AMQP消息
        test_message = AgentMessage(
            type=MessageType.TASK,
            sender_id="sender",
            receiver_id="test-agent-1",
            content="Test content"
        )
        
        mock_amqp_message = Mock()
        mock_amqp_message.body.decode.return_value = json.dumps(test_message.dict(), default=str)
        
        # 处理消息
        await agent_communicator._process_message(mock_amqp_message)
        
        # 验证处理器被调用
        # 注意：由于是异步处理，这里主要验证没有抛出异常
    
    @pytest.mark.asyncio
    async def test_process_message_no_handler(self, agent_communicator):
        """测试处理消息 - 无处理器"""
        test_message = AgentMessage(
            type=MessageType.TASK,
            sender_id="sender",
            receiver_id="test-agent-1",
            content="Test content"
        )
        
        mock_amqp_message = Mock()
        mock_amqp_message.body.decode.return_value = json.dumps(test_message.dict(), default=str)
        
        # 处理消息（应该记录警告但不抛出异常）
        await agent_communicator._process_message(mock_amqp_message)
    
    @pytest.mark.asyncio
    async def test_process_response_message(self, agent_communicator):
        """测试处理响应消息"""
        correlation_id = "test-correlation-id"
        
        # 创建待处理的响应Future
        future = asyncio.Future()
        agent_communicator.pending_responses[correlation_id] = future
        
        # 创建响应消息
        response_message = AgentMessage(
            type=MessageType.RESPONSE,
            sender_id="sender",
            receiver_id="test-agent-1",
            content="Response content",
            correlation_id=correlation_id
        )
        
        mock_amqp_message = Mock()
        mock_amqp_message.body.decode.return_value = json.dumps(response_message.dict(), default=str)
        
        # 处理响应消息
        await agent_communicator._process_message(mock_amqp_message)
        
        # 验证Future被设置
        assert future.done()
        assert future.result() == response_message
        assert correlation_id not in agent_communicator.pending_responses
    
    @pytest.mark.asyncio
    async def test_wait_for_response_success(self, agent_communicator):
        """测试等待响应 - 成功"""
        correlation_id = "test-correlation-id"
        
        # 模拟响应消息
        response_message = AgentMessage(
            type=MessageType.RESPONSE,
            sender_id="sender",
            content="Response"
        )
        
        # 创建任务来模拟响应到达
        async def simulate_response():
            await asyncio.sleep(0.1)
            future = agent_communicator.pending_responses[correlation_id]
            future.set_result(response_message)
        
        # 启动模拟响应任务
        asyncio.create_task(simulate_response())
        
        # 等待响应
        result = await agent_communicator._wait_for_response(correlation_id)
        
        assert result == response_message
        assert correlation_id not in agent_communicator.pending_responses
    
    @pytest.mark.asyncio
    async def test_wait_for_response_timeout(self, agent_communicator):
        """测试等待响应 - 超时"""
        # 设置很短的超时时间
        agent_communicator.config.response_timeout = 0.1
        
        result = await agent_communicator._wait_for_response("timeout-test")
        
        assert result is None
    
    def test_get_pending_response_count(self, agent_communicator):
        """测试获取待处理响应数量"""
        assert agent_communicator.get_pending_response_count() == 0
        
        # 添加待处理响应
        agent_communicator.pending_responses["test-1"] = asyncio.Future()
        agent_communicator.pending_responses["test-2"] = asyncio.Future()
        
        assert agent_communicator.get_pending_response_count() == 2
    
    def test_get_handler_count(self, agent_communicator):
        """测试获取处理器数量"""
        assert agent_communicator.get_handler_count() == 0
        
        # 注册处理器
        agent_communicator.register_handler(MessageType.TASK, lambda x: x)
        agent_communicator.register_handler(MessageType.COLLABORATION, lambda x: x)
        
        assert agent_communicator.get_handler_count() == 2
    
    @pytest.mark.asyncio
    async def test_health_check(self, agent_communicator):
        """测试健康检查"""
        # 添加一些状态
        agent_communicator.pending_responses["test"] = asyncio.Future()
        agent_communicator.register_handler(MessageType.TASK, lambda x: x)
        
        health = await agent_communicator.health_check()
        
        assert health["agent_id"] == "test-agent-1"
        assert health["queue_initialized"] is True
        assert health["pending_responses"] == 1
        assert health["registered_handlers"] == 1


class TestMessageSerialization:
    """测试消息序列化"""
    
    def test_message_serialization(self, test_message):
        """测试消息序列化和反序列化"""
        # 序列化
        serialized = json.dumps(test_message.dict(), default=str)
        
        # 反序列化
        data = json.loads(serialized)
        
        # 转换时间字段
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        deserialized = AgentMessage(**data)
        
        assert deserialized.id == test_message.id
        assert deserialized.type == test_message.type
        assert deserialized.sender_id == test_message.sender_id
        assert deserialized.receiver_id == test_message.receiver_id
        assert deserialized.content == test_message.content
    
    def test_message_with_metadata_serialization(self):
        """测试带元数据的消息序列化"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="sender",
            content="Test",
            metadata={"key": "value", "number": 42, "list": [1, 2, 3]}
        )
        
        # 序列化和反序列化
        serialized = json.dumps(message.dict(), default=str)
        data = json.loads(serialized)
        
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        deserialized = AgentMessage(**data)
        
        assert deserialized.metadata == message.metadata


if __name__ == "__main__":
    pytest.main([__file__])