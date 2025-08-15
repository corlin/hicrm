"""
增强WebSocket管理器测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from src.websocket.enhanced_manager import (
    EnhancedWebSocketManager,
    WebSocketMessage,
    ConnectionInfo,
    MessageType,
    ConnectionStatus
)
from src.agents.base import AgentResponse


class MockWebSocket:
    """模拟WebSocket连接"""
    
    def __init__(self):
        self.messages_sent = []
        self.closed = False
        self.accept_called = False
    
    async def accept(self):
        """模拟接受连接"""
        self.accept_called = True
    
    async def send_json(self, data: Dict[str, Any]):
        """模拟发送JSON消息"""
        if self.closed:
            raise Exception("WebSocket已关闭")
        self.messages_sent.append(data)
    
    async def send_text(self, text: str):
        """模拟发送文本消息"""
        if self.closed:
            raise Exception("WebSocket已关闭")
        self.messages_sent.append(text)
    
    def close(self):
        """模拟关闭连接"""
        self.closed = True


class TestWebSocketMessage:
    """WebSocket消息测试"""
    
    def test_websocket_message_creation(self):
        """测试WebSocket消息创建"""
        message = WebSocketMessage(
            type=MessageType.USER_MESSAGE,
            data={'content': '测试消息'},
            timestamp=datetime.now(),
            message_id='msg_123',
            conversation_id='conv_123',
            user_id='user_456'
        )
        
        assert message.type == MessageType.USER_MESSAGE
        assert message.data['content'] == '测试消息'
        assert message.message_id == 'msg_123'
        assert message.conversation_id == 'conv_123'
        assert message.user_id == 'user_456'
    
    def test_websocket_message_to_dict(self):
        """测试WebSocket消息转换为字典"""
        timestamp = datetime.now()
        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            data={'content': 'Agent响应'},
            timestamp=timestamp,
            message_id='msg_123'
        )
        
        result = message.to_dict()
        
        assert result['type'] == 'agent_response'
        assert result['data']['content'] == 'Agent响应'
        assert result['timestamp'] == timestamp.isoformat()
        assert result['message_id'] == 'msg_123'


class TestConnectionInfo:
    """连接信息测试"""
    
    def test_connection_info_creation(self):
        """测试连接信息创建"""
        websocket = MockWebSocket()
        connection = ConnectionInfo(
            client_id='client_123',
            user_id='user_456',
            conversation_id='conv_789',
            websocket=websocket,
            status=ConnectionStatus.CONNECTED,
            connected_at=datetime.now(),
            last_heartbeat=datetime.now(),
            subscriptions=set(),
            metadata={}
        )
        
        assert connection.client_id == 'client_123'
        assert connection.user_id == 'user_456'
        assert connection.conversation_id == 'conv_789'
        assert connection.status == ConnectionStatus.CONNECTED
        assert connection.is_active() is True
    
    def test_connection_is_expired(self):
        """测试连接过期检查"""
        websocket = MockWebSocket()
        old_time = datetime.now() - timedelta(minutes=10)
        
        connection = ConnectionInfo(
            client_id='client_123',
            user_id='user_456',
            conversation_id=None,
            websocket=websocket,
            status=ConnectionStatus.CONNECTED,
            connected_at=old_time,
            last_heartbeat=old_time,
            subscriptions=set(),
            metadata={}
        )
        
        # 5分钟超时，10分钟前的连接应该过期
        assert connection.is_expired(300) is True
        
        # 15分钟超时，10分钟前的连接不应该过期
        assert connection.is_expired(900) is False


class TestEnhancedWebSocketManager:
    """增强WebSocket管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建WebSocket管理器实例"""
        return EnhancedWebSocketManager(heartbeat_interval=1, connection_timeout=60)
    
    @pytest.fixture
    def mock_websocket(self):
        """创建模拟WebSocket"""
        return MockWebSocket()
    
    @pytest.mark.asyncio
    async def test_manager_start_stop(self, manager):
        """测试管理器启动和停止"""
        await manager.start()
        
        # 验证后台任务已启动
        assert manager._heartbeat_task is not None
        assert manager._cleanup_task is not None
        assert not manager._heartbeat_task.done()
        assert not manager._cleanup_task.done()
        
        await manager.stop()
        
        # 验证后台任务已停止
        assert manager._heartbeat_task.done()
        assert manager._cleanup_task.done()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, manager, mock_websocket):
        """测试成功建立连接"""
        client_id = 'client_123'
        user_id = 'user_456'
        conversation_id = 'conv_789'
        
        success = await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            user_id=user_id,
            conversation_id=conversation_id,
            metadata={'test': 'data'}
        )
        
        assert success is True
        assert mock_websocket.accept_called is True
        assert client_id in manager.connections
        assert user_id in manager.user_connections
        assert conversation_id in manager.conversation_connections
        
        # 验证连接信息
        connection_info = manager.connections[client_id]
        assert connection_info.user_id == user_id
        assert connection_info.conversation_id == conversation_id
        assert connection_info.status == ConnectionStatus.CONNECTED
        
        # 验证发送了连接确认消息
        assert len(mock_websocket.messages_sent) == 1
        ack_message = mock_websocket.messages_sent[0]
        assert ack_message['type'] == 'connection_ack'
        assert ack_message['data']['client_id'] == client_id
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """测试断开连接"""
        client_id = 'client_123'
        user_id = 'user_456'
        conversation_id = 'conv_789'
        
        # 先建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # 断开连接
        await manager.disconnect(client_id, "test_disconnect")
        
        # 验证连接已移除
        assert client_id not in manager.connections
        assert user_id not in manager.user_connections
        assert conversation_id not in manager.conversation_connections
    
    @pytest.mark.asyncio
    async def test_send_agent_response(self, manager, mock_websocket):
        """测试发送Agent响应"""
        client_id = 'client_123'
        conversation_id = 'conv_789'
        
        # 建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 创建Agent响应
        agent_response = AgentResponse(
            content="这是Agent的响应",
            confidence=0.9,
            suggestions=["建议1", "建议2"],
            next_actions=["行动1"],
            metadata={"test": "data"}
        )
        
        # 发送Agent响应
        await manager.send_agent_response(
            conversation_id=conversation_id,
            agent_response=agent_response,
            agent_id="test_agent",
            processing_info={"time": 1.5}
        )
        
        # 验证消息已发送
        assert len(mock_websocket.messages_sent) == 2  # 连接确认 + Agent响应
        response_message = mock_websocket.messages_sent[1]
        
        assert response_message['type'] == 'agent_response'
        assert response_message['data']['content'] == "这是Agent的响应"
        assert response_message['data']['confidence'] == 0.9
        assert response_message['data']['agent_id'] == "test_agent"
        assert response_message['data']['suggestions'] == ["建议1", "建议2"]
        assert response_message['data']['next_actions'] == ["行动1"]
    
    @pytest.mark.asyncio
    async def test_send_typing_indicator(self, manager, mock_websocket):
        """测试发送打字指示器"""
        client_id = 'client_123'
        conversation_id = 'conv_789'
        
        # 建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送打字指示器
        await manager.send_typing_indicator(
            conversation_id=conversation_id,
            agent_id="test_agent",
            is_typing=True
        )
        
        # 验证消息已发送
        assert len(mock_websocket.messages_sent) == 2
        typing_message = mock_websocket.messages_sent[1]
        
        assert typing_message['type'] == 'typing_indicator'
        assert typing_message['data']['agent_id'] == "test_agent"
        assert typing_message['data']['is_typing'] is True
    
    @pytest.mark.asyncio
    async def test_send_agent_thinking(self, manager, mock_websocket):
        """测试发送Agent思考状态"""
        client_id = 'client_123'
        conversation_id = 'conv_789'
        
        # 建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送Agent思考状态
        await manager.send_agent_thinking(
            conversation_id=conversation_id,
            agent_id="test_agent",
            thinking_message="正在分析问题...",
            progress=0.5
        )
        
        # 验证消息已发送
        assert len(mock_websocket.messages_sent) == 2
        thinking_message = mock_websocket.messages_sent[1]
        
        assert thinking_message['type'] == 'agent_thinking'
        assert thinking_message['data']['agent_id'] == "test_agent"
        assert thinking_message['data']['message'] == "正在分析问题..."
        assert thinking_message['data']['progress'] == 0.5
    
    @pytest.mark.asyncio
    async def test_send_agent_collaboration(self, manager, mock_websocket):
        """测试发送Agent协作状态"""
        client_id = 'client_123'
        conversation_id = 'conv_789'
        
        # 建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送Agent协作状态
        await manager.send_agent_collaboration(
            conversation_id=conversation_id,
            collaborating_agents=["agent1", "agent2"],
            collaboration_type="analysis",
            status="in_progress"
        )
        
        # 验证消息已发送
        assert len(mock_websocket.messages_sent) == 2
        collab_message = mock_websocket.messages_sent[1]
        
        assert collab_message['type'] == 'agent_collaboration'
        assert collab_message['data']['collaborating_agents'] == ["agent1", "agent2"]
        assert collab_message['data']['collaboration_type'] == "analysis"
        assert collab_message['data']['status'] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_send_knowledge_retrieval_status(self, manager, mock_websocket):
        """测试发送知识检索状态"""
        client_id = 'client_123'
        conversation_id = 'conv_789'
        
        # 建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            conversation_id=conversation_id
        )
        
        # 发送知识检索状态
        await manager.send_knowledge_retrieval_status(
            conversation_id=conversation_id,
            status="searching",
            query="客户管理最佳实践",
            results_count=5,
            confidence=0.8
        )
        
        # 验证消息已发送
        assert len(mock_websocket.messages_sent) == 2
        retrieval_message = mock_websocket.messages_sent[1]
        
        assert retrieval_message['type'] == 'knowledge_retrieval'
        assert retrieval_message['data']['status'] == "searching"
        assert retrieval_message['data']['query'] == "客户管理最佳实践"
        assert retrieval_message['data']['results_count'] == 5
        assert retrieval_message['data']['confidence'] == 0.8
    
    @pytest.mark.asyncio
    async def test_send_system_notification(self, manager, mock_websocket):
        """测试发送系统通知"""
        client_id = 'client_123'
        user_id = 'user_456'
        
        # 建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id,
            user_id=user_id
        )
        
        # 发送系统通知
        await manager.send_system_notification(
            user_id=user_id,
            notification_type="info",
            title="系统通知",
            message="这是一条测试通知",
            data={"key": "value"}
        )
        
        # 验证消息已发送
        assert len(mock_websocket.messages_sent) == 2
        notification_message = mock_websocket.messages_sent[1]
        
        assert notification_message['type'] == 'notification'
        assert notification_message['data']['notification_type'] == "info"
        assert notification_message['data']['title'] == "系统通知"
        assert notification_message['data']['message'] == "这是一条测试通知"
        assert notification_message['data']['data']['key'] == "value"
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self, manager, mock_websocket):
        """测试处理心跳消息"""
        client_id = 'client_123'
        
        # 建立连接
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id
        )
        
        # 获取连接信息
        connection_info = manager.connections[client_id]
        original_heartbeat = connection_info.last_heartbeat
        
        # 等待一小段时间
        await asyncio.sleep(0.01)
        
        # 发送心跳消息
        heartbeat_message = {
            'type': 'heartbeat',
            'data': {},
            'message_id': 'heartbeat_123'
        }
        
        await manager.handle_message(client_id, heartbeat_message)
        
        # 验证心跳时间已更新
        assert connection_info.last_heartbeat > original_heartbeat
        
        # 验证发送了心跳确认
        assert len(mock_websocket.messages_sent) == 2  # 连接确认 + 心跳确认
        heartbeat_ack = mock_websocket.messages_sent[1]
        assert heartbeat_ack['type'] == 'heartbeat_ack'
    
    @pytest.mark.asyncio
    async def test_message_handlers(self, manager):
        """测试消息处理器注册和调用"""
        handler_called = False
        received_message = None
        
        async def test_handler(client_id: str, message: WebSocketMessage):
            nonlocal handler_called, received_message
            handler_called = True
            received_message = message
        
        # 注册处理器
        manager.register_message_handler(MessageType.USER_MESSAGE, test_handler)
        
        # 建立连接
        mock_websocket = MockWebSocket()
        client_id = 'client_123'
        await manager.connect(
            websocket=mock_websocket,
            client_id=client_id
        )
        
        # 发送用户消息
        user_message = {
            'type': 'user_message',
            'data': {'content': '测试消息'},
            'message_id': 'msg_123'
        }
        
        await manager.handle_message(client_id, user_message)
        
        # 验证处理器被调用
        assert handler_called is True
        assert received_message is not None
        assert received_message.type == MessageType.USER_MESSAGE
        assert received_message.data['content'] == '测试消息'
    
    @pytest.mark.asyncio
    async def test_connection_handlers(self, manager):
        """测试连接处理器"""
        connection_handler_called = False
        disconnection_handler_called = False
        
        async def connection_handler(connection_info: ConnectionInfo):
            nonlocal connection_handler_called
            connection_handler_called = True
        
        async def disconnection_handler(connection_info: ConnectionInfo, reason: str):
            nonlocal disconnection_handler_called
            disconnection_handler_called = True
        
        # 注册处理器
        manager.register_connection_handler(connection_handler)
        manager.register_disconnection_handler(disconnection_handler)
        
        # 建立和断开连接
        mock_websocket = MockWebSocket()
        client_id = 'client_123'
        
        await manager.connect(websocket=mock_websocket, client_id=client_id)
        await manager.disconnect(client_id, "test")
        
        # 验证处理器被调用
        assert connection_handler_called is True
        assert disconnection_handler_called is True
    
    def test_get_stats(self, manager):
        """测试获取统计信息"""
        stats = manager.get_stats()
        
        assert 'total_connections' in stats
        assert 'active_connections' in stats
        assert 'messages_sent' in stats
        assert 'messages_received' in stats
        assert 'errors' in stats
        assert 'connection_count' in stats
        assert 'user_count' in stats
        assert 'conversation_count' in stats
    
    @pytest.mark.asyncio
    async def test_health_check(self, manager):
        """测试健康检查"""
        health = await manager.health_check()
        
        assert 'status' in health
        assert 'active_connections' in health
        assert 'total_connections' in health
        assert 'heartbeat_task_running' in health
        assert 'cleanup_task_running' in health
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self, manager):
        """测试同一用户的多个连接"""
        user_id = 'user_456'
        client_id_1 = 'client_123'
        client_id_2 = 'client_456'
        
        mock_websocket_1 = MockWebSocket()
        mock_websocket_2 = MockWebSocket()
        
        # 建立两个连接
        await manager.connect(
            websocket=mock_websocket_1,
            client_id=client_id_1,
            user_id=user_id
        )
        
        await manager.connect(
            websocket=mock_websocket_2,
            client_id=client_id_2,
            user_id=user_id
        )
        
        # 验证用户连接索引
        user_connections = manager.get_user_connections(user_id)
        assert len(user_connections) == 2
        assert client_id_1 in user_connections
        assert client_id_2 in user_connections
        
        # 发送用户消息
        await manager.send_system_notification(
            user_id=user_id,
            message="测试通知"
        )
        
        # 验证两个连接都收到消息
        assert len(mock_websocket_1.messages_sent) == 2  # 连接确认 + 通知
        assert len(mock_websocket_2.messages_sent) == 2  # 连接确认 + 通知


if __name__ == "__main__":
    pytest.main([__file__])