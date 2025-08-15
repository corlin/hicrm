"""
增强WebSocket管理器单元测试

测试WebSocket连接管理、消息处理、Agent响应推送等功能。
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.websocket.enhanced_manager import (
    EnhancedWebSocketManager,
    MessageType,
    ConnectionStatus,
    WebSocketMessage,
    ConnectionInfo
)
from src.agents.base import AgentResponse


class MockWebSocket:
    """模拟WebSocket连接"""
    
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_messages: List[Dict[str, Any]] = []
        self.closed = False
        self.headers = {
            'user-agent': 'test-client',
            'origin': 'http://localhost:3000'
        }
    
    async def accept(self):
        """接受连接"""
        if self.should_fail:
            raise Exception("Connection failed")
    
    async def send_json(self, data: Dict[str, Any]):
        """发送JSON消息"""
        if self.closed or self.should_fail:
            raise Exception("WebSocket connection closed")
        self.sent_messages.append(data)
    
    async def send_text(self, text: str):
        """发送文本消息"""
        if self.closed or self.should_fail:
            raise Exception("WebSocket connection closed")
        self.sent_messages.append({"text": text})
    
    async def receive_json(self) -> Dict[str, Any]:
        """接收JSON消息"""
        if self.closed:
            raise Exception("WebSocket connection closed")
        # 模拟接收消息
        return {
            "type": "heartbeat",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }
    
    def close(self):
        """关闭连接"""
        self.closed = True


@pytest.fixture
async def websocket_manager():
    """创建WebSocket管理器实例"""
    manager = EnhancedWebSocketManager(heartbeat_interval=1, connection_timeout=5)
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
def mock_websocket():
    """创建模拟WebSocket"""
    return MockWebSocket()


@pytest.fixture
def mock_failing_websocket():
    """创建失败的模拟WebSocket"""
    return MockWebSocket(should_fail=True)


class TestEnhancedWebSocketManager:
    """增强WebSocket管理器测试类"""
    
    @pytest.mark.asyncio
    async def test_manager_start_stop(self):
        """测试管理器启动和停止"""
        manager = EnhancedWebSocketManager()
        
        # 测试启动
        await manager.start()
        assert manager._heartbeat_task is not None
        assert manager._cleanup_task is not None
        assert not manager._heartbeat_task.done()
        assert not manager._cleanup_task.done()
        
        # 测试停止
        await manager.stop()
        assert manager._heartbeat_task.done()
        assert manager._cleanup_task.done()
    
    @pytest.mark.asyncio
    async def test_successful_connection(self, websocket_manager, mock_websocket):
        """测试成功建立连接"""
        client_id = "test-client-1"
        user_id = "user-123"
        conversation_id = "conv-456"
        
        # 建立连接
        success = await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            user_id=user_id,
            conversation_id=conversation_id,
            metadata={"test": "data"}
        )
        
        assert success is True
        assert client_id in websocket_manager.connections
        assert user_id in websocket_manager.user_connections
        assert conversation_id in websocket_manager.conversation_connections
        
        # 检查连接信息
        connection_info = websocket_manager.connections[client_id]
        assert connection_info.client_id == client_id
        assert connection_info.user_id == user_id
        assert connection_info.conversation_id == conversation_id
        assert connection_info.status == ConnectionStatus.CONNECTED
        assert connection_info.is_active()
        
        # 检查发送的连接确认消息
        assert len(mock_websocket.sent_messages) == 1
        ack_message = mock_websocket.sent_messages[0]
        assert ack_message['type'] == MessageType.CONNECTION_ACK.value
        assert ack_message['data']['client_id'] == client_id
    
    @pytest.mark.asyncio
    async def test_failed_connection(self, websocket_manager, mock_failing_websocket):
        """测试连接失败"""
        client_id = "test-client-fail"
        
        success = await websocket_manager.connect(
            websocket=mock_failing_websocket,
            client_id=client_id
        )
        
        assert success is False
        assert client_id not in websocket_manager.connections
    
    @pytest.mark.asyncio
    async def test_disconnect(self, websocket_manager, mock_websocket):
        """测试断开连接"""
        client_id = "test-client-disconnect"
        user_id = "user-disconnect"
        conversation_id = "conv-disconnect"
        
        # 先建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        assert client_id in websocket_manager.connections
        assert user_id in websocket_manager.user_connections
        assert conversation_id in websocket_manager.conversation_connections
        
        # 断开连接
        await websocket_manager.disconnect(client_id, "test_disconnect")
        
        assert client_id not in websocket_manager.connections
        assert user_id not in websocket_manager.user_connections
        assert conversation_id not in websocket_manager.conversation_connections
    
    @pytest.mark.asyncio
    async def test_heartbeat_handling(self, websocket_manager, mock_websocket):
        """测试心跳处理"""
        client_id = "test-client-heartbeat"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id
        )
        
        # 发送心跳消息
        heartbeat_message = {
            "type": "heartbeat",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket_manager.handle_message(client_id, heartbeat_message)
        
        # 检查心跳响应
        sent_messages = mock_websocket.sent_messages
        heartbeat_ack = next(
            (msg for msg in sent_messages if msg.get('type') == MessageType.HEARTBEAT_ACK.value),
            None
        )
        assert heartbeat_ack is not None
        assert 'server_time' in heartbeat_ack['data']
        
        # 检查心跳时间更新
        connection_info = websocket_manager.connections[client_id]
        assert connection_info.last_heartbeat is not None
    
    @pytest.mark.asyncio
    async def test_send_agent_response(self, websocket_manager, mock_websocket):
        """测试发送Agent响应"""
        client_id = "test-client-agent"
        conversation_id = "conv-agent"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 创建Agent响应
        agent_response = AgentResponse(
            content="这是Agent的响应",
            confidence=0.9,
            suggestions=["建议1", "建议2"],
            next_actions=["行动1", "行动2"],
            metadata={"test": "metadata"}
        )
        
        # 发送Agent响应
        await websocket_manager.send_agent_response(
            conversation_id=conversation_id,
            agent_response=agent_response,
            agent_id="test_agent",
            processing_info={"time": 1.5}
        )
        
        # 检查发送的消息
        sent_messages = mock_websocket.sent_messages
        agent_message = next(
            (msg for msg in sent_messages if msg.get('type') == MessageType.AGENT_RESPONSE.value),
            None
        )
        
        assert agent_message is not None
        assert agent_message['data']['content'] == "这是Agent的响应"
        assert agent_message['data']['confidence'] == 0.9
        assert agent_message['data']['agent_id'] == "test_agent"
        assert agent_message['data']['suggestions'] == ["建议1", "建议2"]
        assert agent_message['data']['next_actions'] == ["行动1", "行动2"]
    
    @pytest.mark.asyncio
    async def test_send_typing_indicator(self, websocket_manager, mock_websocket):
        """测试发送打字指示器"""
        client_id = "test-client-typing"
        conversation_id = "conv-typing"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送打字指示器
        await websocket_manager.send_typing_indicator(
            conversation_id=conversation_id,
            agent_id="typing_agent",
            is_typing=True
        )
        
        # 检查发送的消息
        sent_messages = mock_websocket.sent_messages
        typing_message = next(
            (msg for msg in sent_messages if msg.get('type') == MessageType.TYPING_INDICATOR.value),
            None
        )
        
        assert typing_message is not None
        assert typing_message['data']['agent_id'] == "typing_agent"
        assert typing_message['data']['is_typing'] is True
    
    @pytest.mark.asyncio
    async def test_send_agent_thinking(self, websocket_manager, mock_websocket):
        """测试发送Agent思考状态"""
        client_id = "test-client-thinking"
        conversation_id = "conv-thinking"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送Agent思考状态
        await websocket_manager.send_agent_thinking(
            conversation_id=conversation_id,
            agent_id="thinking_agent",
            thinking_message="正在分析数据...",
            progress=0.5
        )
        
        # 检查发送的消息
        sent_messages = mock_websocket.sent_messages
        thinking_message = next(
            (msg for msg in sent_messages if msg.get('type') == MessageType.AGENT_THINKING.value),
            None
        )
        
        assert thinking_message is not None
        assert thinking_message['data']['agent_id'] == "thinking_agent"
        assert thinking_message['data']['message'] == "正在分析数据..."
        assert thinking_message['data']['progress'] == 0.5
    
    @pytest.mark.asyncio
    async def test_send_agent_collaboration(self, websocket_manager, mock_websocket):
        """测试发送Agent协作状态"""
        client_id = "test-client-collab"
        conversation_id = "conv-collab"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送Agent协作状态
        await websocket_manager.send_agent_collaboration(
            conversation_id=conversation_id,
            collaborating_agents=["agent1", "agent2", "agent3"],
            collaboration_type="parallel",
            status="in_progress"
        )
        
        # 检查发送的消息
        sent_messages = mock_websocket.sent_messages
        collab_message = next(
            (msg for msg in sent_messages if msg.get('type') == MessageType.AGENT_COLLABORATION.value),
            None
        )
        
        assert collab_message is not None
        assert collab_message['data']['collaborating_agents'] == ["agent1", "agent2", "agent3"]
        assert collab_message['data']['collaboration_type'] == "parallel"
        assert collab_message['data']['status'] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_send_knowledge_retrieval_status(self, websocket_manager, mock_websocket):
        """测试发送知识检索状态"""
        client_id = "test-client-knowledge"
        conversation_id = "conv-knowledge"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送知识检索状态
        await websocket_manager.send_knowledge_retrieval_status(
            conversation_id=conversation_id,
            status="completed",
            query="客户管理最佳实践",
            results_count=5,
            confidence=0.85
        )
        
        # 检查发送的消息
        sent_messages = mock_websocket.sent_messages
        knowledge_message = next(
            (msg for msg in sent_messages if msg.get('type') == MessageType.KNOWLEDGE_RETRIEVAL.value),
            None
        )
        
        assert knowledge_message is not None
        assert knowledge_message['data']['status'] == "completed"
        assert knowledge_message['data']['query'] == "客户管理最佳实践"
        assert knowledge_message['data']['results_count'] == 5
        assert knowledge_message['data']['confidence'] == 0.85
    
    @pytest.mark.asyncio
    async def test_send_system_notification(self, websocket_manager, mock_websocket):
        """测试发送系统通知"""
        client_id = "test-client-notification"
        user_id = "user-notification"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            user_id=user_id
        )
        
        # 发送系统通知
        await websocket_manager.send_system_notification(
            user_id=user_id,
            notification_type="info",
            title="系统更新",
            message="系统将在5分钟后进行维护",
            data={"maintenance_time": "2024-01-01 02:00:00"}
        )
        
        # 检查发送的消息
        sent_messages = mock_websocket.sent_messages
        notification_message = next(
            (msg for msg in sent_messages if msg.get('type') == MessageType.NOTIFICATION.value),
            None
        )
        
        assert notification_message is not None
        assert notification_message['data']['notification_type'] == "info"
        assert notification_message['data']['title'] == "系统更新"
        assert notification_message['data']['message'] == "系统将在5分钟后进行维护"
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self, websocket_manager, mock_websocket):
        """测试连接超时"""
        client_id = "test-client-timeout"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id
        )
        
        # 模拟连接过期
        connection_info = websocket_manager.connections[client_id]
        connection_info.last_heartbeat = datetime.now() - timedelta(seconds=10)
        
        # 检查连接是否过期
        assert connection_info.is_expired(5)  # 5秒超时
        
        # 手动触发清理（模拟心跳循环）
        expired_clients = []
        for cid, conn_info in websocket_manager.connections.items():
            if conn_info.is_expired(5):
                expired_clients.append(cid)
        
        for cid in expired_clients:
            await websocket_manager.disconnect(cid, "heartbeat_timeout")
        
        assert client_id not in websocket_manager.connections
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self, websocket_manager):
        """测试同一用户的多个连接"""
        user_id = "multi-user"
        client_ids = ["client-1", "client-2", "client-3"]
        websockets = [MockWebSocket() for _ in client_ids]
        
        # 建立多个连接
        for i, client_id in enumerate(client_ids):
            await websocket_manager.connect(
                websocket=websockets[i],
                client_id=client_id,
                user_id=user_id
            )
        
        # 检查用户连接索引
        user_connections = websocket_manager.get_user_connections(user_id)
        assert len(user_connections) == 3
        assert set(user_connections) == set(client_ids)
        
        # 发送用户消息
        test_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={"message": "测试消息"},
            timestamp=datetime.now(),
            message_id="test-msg-1",
            user_id=user_id
        )
        
        sent_count = await websocket_manager._send_to_user(user_id, test_message)
        assert sent_count == 3
        
        # 检查所有连接都收到了消息
        for websocket in websockets:
            notification_messages = [
                msg for msg in websocket.sent_messages 
                if msg.get('type') == MessageType.NOTIFICATION.value
            ]
            assert len(notification_messages) >= 1
    
    @pytest.mark.asyncio
    async def test_conversation_connections(self, websocket_manager):
        """测试对话连接管理"""
        conversation_id = "test-conversation"
        client_ids = ["conv-client-1", "conv-client-2"]
        websockets = [MockWebSocket() for _ in client_ids]
        
        # 建立连接到同一对话
        for i, client_id in enumerate(client_ids):
            await websocket_manager.connect(
                websocket=websockets[i],
                client_id=client_id,
                conversation_id=conversation_id
            )
        
        # 检查对话连接索引
        conv_connections = websocket_manager.get_conversation_connections(conversation_id)
        assert len(conv_connections) == 2
        assert set(conv_connections) == set(client_ids)
        
        # 发送对话消息
        test_message = WebSocketMessage(
            type=MessageType.CONVERSATION_STATE,
            data={"state": "updated"},
            timestamp=datetime.now(),
            message_id="conv-msg-1",
            conversation_id=conversation_id
        )
        
        sent_count = await websocket_manager._send_to_conversation(conversation_id, test_message)
        assert sent_count == 2
    
    @pytest.mark.asyncio
    async def test_message_handlers(self, websocket_manager, mock_websocket):
        """测试消息处理器注册和调用"""
        client_id = "test-client-handlers"
        handler_called = False
        received_message = None
        
        # 定义消息处理器
        async def test_handler(client_id: str, message: WebSocketMessage):
            nonlocal handler_called, received_message
            handler_called = True
            received_message = message
        
        # 注册处理器
        websocket_manager.register_message_handler(MessageType.USER_MESSAGE, test_handler)
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id
        )
        
        # 发送用户消息
        user_message = {
            "type": "user_message",
            "data": {"content": "测试消息"},
            "message_id": "test-msg-1"
        }
        
        await websocket_manager.handle_message(client_id, user_message)
        
        # 检查处理器是否被调用
        assert handler_called is True
        assert received_message is not None
        assert received_message.type == MessageType.USER_MESSAGE
        assert received_message.data["content"] == "测试消息"
    
    @pytest.mark.asyncio
    async def test_connection_handlers(self, websocket_manager, mock_websocket):
        """测试连接处理器"""
        connection_handler_called = False
        disconnection_handler_called = False
        
        # 定义处理器
        async def connection_handler(connection_info: ConnectionInfo):
            nonlocal connection_handler_called
            connection_handler_called = True
        
        async def disconnection_handler(connection_info: ConnectionInfo, reason: str):
            nonlocal disconnection_handler_called
            disconnection_handler_called = True
        
        # 注册处理器
        websocket_manager.register_connection_handler(connection_handler)
        websocket_manager.register_disconnection_handler(disconnection_handler)
        
        client_id = "test-client-conn-handlers"
        
        # 建立连接
        await websocket_manager.connect(
            websocket=mock_websocket,
            client_id=client_id
        )
        
        assert connection_handler_called is True
        
        # 断开连接
        await websocket_manager.disconnect(client_id, "test")
        
        assert disconnection_handler_called is True
    
    @pytest.mark.asyncio
    async def test_stats_and_health_check(self, websocket_manager, mock_websocket):
        """测试统计信息和健康检查"""
        # 建立几个连接
        for i in range(3):
            await websocket_manager.connect(
                websocket=MockWebSocket(),
                client_id=f"stats-client-{i}",
                user_id=f"stats-user-{i}"
            )
        
        # 获取统计信息
        stats = websocket_manager.get_stats()
        assert stats['connection_count'] == 3
        assert stats['user_count'] == 3
        assert stats['active_connections'] == 3
        
        # 健康检查
        health = await websocket_manager.health_check()
        assert health['status'] == 'healthy'
        assert health['active_connections'] == 3
        assert health['total_connections'] == 3
    
    @pytest.mark.asyncio
    async def test_error_handling(self, websocket_manager, mock_failing_websocket):
        """测试错误处理"""
        client_id = "test-client-error"
        
        # 建立连接（应该失败）
        success = await websocket_manager.connect(
            websocket=mock_failing_websocket,
            client_id=client_id
        )
        
        assert success is False
        assert client_id not in websocket_manager.connections
        
        # 测试发送消息到不存在的客户端
        test_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={"message": "测试"},
            timestamp=datetime.now(),
            message_id="error-msg-1"
        )
        
        result = await websocket_manager._send_message("non-existent-client", test_message)
        assert result is False
    
    def test_websocket_message_serialization(self):
        """测试WebSocket消息序列化"""
        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            data={"content": "测试内容", "confidence": 0.9},
            timestamp=datetime.now(),
            message_id="test-msg-1",
            conversation_id="conv-123",
            user_id="user-456"
        )
        
        # 序列化
        serialized = message.to_dict()
        
        assert serialized['type'] == MessageType.AGENT_RESPONSE.value
        assert serialized['data']['content'] == "测试内容"
        assert serialized['data']['confidence'] == 0.9
        assert serialized['message_id'] == "test-msg-1"
        assert serialized['conversation_id'] == "conv-123"
        assert serialized['user_id'] == "user-456"
        assert 'timestamp' in serialized
    
    def test_connection_info_methods(self):
        """测试连接信息方法"""
        mock_ws = MockWebSocket()
        connection_info = ConnectionInfo(
            client_id="test-client",
            user_id="test-user",
            conversation_id="test-conv",
            websocket=mock_ws,
            status=ConnectionStatus.CONNECTED,
            connected_at=datetime.now(),
            last_heartbeat=datetime.now(),
            subscriptions=set(),
            metadata={}
        )
        
        # 测试活跃状态
        assert connection_info.is_active() is True
        
        # 测试过期检查
        assert connection_info.is_expired(300) is False
        
        # 模拟过期
        connection_info.last_heartbeat = datetime.now() - timedelta(seconds=400)
        assert connection_info.is_expired(300) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])