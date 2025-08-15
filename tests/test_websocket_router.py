"""
WebSocket路由器单元测试

测试WebSocket路由、消息处理、Agent集成等功能。
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.websocket.router import (
    WebSocketConnectionHandler,
    connection_handler,
    router,
    setup_message_handlers,
    initialize_websocket_router,
    shutdown_websocket_router
)
from src.websocket.enhanced_manager import (
    enhanced_websocket_manager,
    MessageType,
    WebSocketMessage
)
from src.services.agent_conversation_integration import AgentConversationIntegration
from src.schemas.conversation import MessageResponse


class MockAgentConversationIntegration:
    """模拟Agent对话集成服务"""
    
    def __init__(self):
        self.process_calls = []
    
    async def process_user_message(
        self,
        conversation_id: str,
        user_message: str,
        user_id: str,
        context: Dict[str, Any] = None
    ) -> MessageResponse:
        """模拟处理用户消息"""
        self.process_calls.append({
            'conversation_id': conversation_id,
            'user_message': user_message,
            'user_id': user_id,
            'context': context
        })
        
        # 创建模拟响应
        return MessageResponse(
            id="msg-123",
            conversation_id=conversation_id,
            role="assistant",
            content=f"Agent响应: {user_message}",
            agent_type="test_agent",
            metadata={
                'confidence': 0.9,
                'suggestions': ['建议1', '建议2'],
                'next_actions': ['行动1'],
                'intent': 'test_intent',
                'processing_time': 1.2,
                'rag_used': True
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


@pytest.fixture
def mock_integration_service():
    """创建模拟集成服务"""
    return MockAgentConversationIntegration()


@pytest.fixture
def app():
    """创建FastAPI应用"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestWebSocketConnectionHandler:
    """WebSocket连接处理器测试类"""
    
    @pytest.mark.asyncio
    async def test_handle_user_message_success(self, mock_integration_service):
        """测试成功处理用户消息"""
        handler = WebSocketConnectionHandler()
        handler.set_integration_service(mock_integration_service)
        
        # 模拟WebSocket管理器方法
        with patch.object(enhanced_websocket_manager, 'send_typing_indicator') as mock_typing, \
             patch.object(enhanced_websocket_manager, 'send_agent_thinking') as mock_thinking, \
             patch.object(enhanced_websocket_manager, 'send_agent_response') as mock_response:
            
            # 创建测试消息
            message = WebSocketMessage(
                type=MessageType.USER_MESSAGE,
                data={
                    'content': '帮我找一些客户',
                    'context': {'test': 'context'}
                },
                timestamp=datetime.now(),
                message_id='test-msg-1',
                conversation_id='conv-123',
                user_id='user-456'
            )
            
            # 处理消息
            await handler.handle_user_message('client-1', message)
            
            # 验证集成服务被调用
            assert len(mock_integration_service.process_calls) == 1
            call = mock_integration_service.process_calls[0]
            assert call['conversation_id'] == 'conv-123'
            assert call['user_message'] == '帮我找一些客户'
            assert call['user_id'] == 'user-456'
            
            # 验证WebSocket消息发送
            mock_typing.assert_called()
            mock_thinking.assert_called()
            mock_response.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_user_message_missing_params(self, mock_integration_service):
        """测试处理缺少参数的用户消息"""
        handler = WebSocketConnectionHandler()
        handler.set_integration_service(mock_integration_service)
        
        with patch.object(enhanced_websocket_manager, '_send_error') as mock_error:
            # 创建缺少参数的消息
            message = WebSocketMessage(
                type=MessageType.USER_MESSAGE,
                data={'content': '测试消息'},  # 缺少conversation_id和user_id
                timestamp=datetime.now(),
                message_id='test-msg-1'
            )
            
            await handler.handle_user_message('client-1', message)
            
            # 验证发送了错误消息
            mock_error.assert_called_once()
            error_call = mock_error.call_args[0]
            assert error_call[0] == 'client-1'
            assert '缺少必要的消息参数' in error_call[1]
    
    @pytest.mark.asyncio
    async def test_handle_user_message_no_integration_service(self):
        """测试没有设置集成服务时的处理"""
        handler = WebSocketConnectionHandler()
        # 不设置集成服务
        
        message = WebSocketMessage(
            type=MessageType.USER_MESSAGE,
            data={'content': '测试消息'},
            timestamp=datetime.now(),
            message_id='test-msg-1',
            conversation_id='conv-123',
            user_id='user-456'
        )
        
        # 处理消息应该不会抛出异常
        await handler.handle_user_message('client-1', message)
    
    @pytest.mark.asyncio
    async def test_handle_subscription(self):
        """测试处理订阅请求"""
        handler = WebSocketConnectionHandler()
        
        # 模拟连接信息
        mock_connection_info = Mock()
        mock_connection_info.subscriptions = set()
        
        with patch.object(enhanced_websocket_manager, 'get_connection_info', return_value=mock_connection_info), \
             patch.object(enhanced_websocket_manager, '_send_message') as mock_send:
            
            message = WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={'event_types': ['agent_response', 'typing_indicator']},
                timestamp=datetime.now(),
                message_id='sub-msg-1'
            )
            
            await handler.handle_subscription('client-1', message)
            
            # 验证订阅被添加
            assert 'agent_response' in mock_connection_info.subscriptions
            assert 'typing_indicator' in mock_connection_info.subscriptions
            
            # 验证发送了确认消息
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_conversation_join(self):
        """测试处理加入对话请求"""
        handler = WebSocketConnectionHandler()
        
        # 模拟连接信息
        mock_connection_info = Mock()
        mock_connection_info.conversation_id = None
        
        with patch.object(enhanced_websocket_manager, 'get_connection_info', return_value=mock_connection_info), \
             patch.object(enhanced_websocket_manager, '_send_message') as mock_send:
            
            # 模拟对话连接索引
            enhanced_websocket_manager.conversation_connections = {}
            
            message = WebSocketMessage(
                type=MessageType.CONVERSATION_STATE,
                data={'conversation_id': 'new-conv-123'},
                timestamp=datetime.now(),
                message_id='join-msg-1'
            )
            
            await handler.handle_conversation_join('client-1', message)
            
            # 验证连接信息更新
            assert mock_connection_info.conversation_id == 'new-conv-123'
            
            # 验证对话连接索引更新
            assert 'new-conv-123' in enhanced_websocket_manager.conversation_connections
            assert 'client-1' in enhanced_websocket_manager.conversation_connections['new-conv-123']
            
            # 验证发送了确认消息
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_conversation_join_missing_id(self):
        """测试处理缺少对话ID的加入请求"""
        handler = WebSocketConnectionHandler()
        
        with patch.object(enhanced_websocket_manager, '_send_error') as mock_error:
            message = WebSocketMessage(
                type=MessageType.CONVERSATION_STATE,
                data={},  # 缺少conversation_id
                timestamp=datetime.now(),
                message_id='join-msg-1'
            )
            
            await handler.handle_conversation_join('client-1', message)
            
            # 验证发送了错误消息
            mock_error.assert_called_once()
            error_call = mock_error.call_args[0]
            assert error_call[0] == 'client-1'
            assert '缺少conversation_id参数' in error_call[1]


class TestWebSocketRouter:
    """WebSocket路由器测试类"""
    
    def test_get_websocket_stats(self, client):
        """测试获取WebSocket统计信息"""
        with patch.object(enhanced_websocket_manager, 'get_stats', return_value={
            'total_connections': 5,
            'active_connections': 3,
            'messages_sent': 100,
            'messages_received': 80
        }):
            response = client.get("/ws/stats")
            assert response.status_code == 200
            data = response.json()
            assert data['total_connections'] == 5
            assert data['active_connections'] == 3
    
    def test_websocket_health_check(self, client):
        """测试WebSocket健康检查"""
        with patch.object(enhanced_websocket_manager, 'health_check', return_value={
            'status': 'healthy',
            'active_connections': 3,
            'total_connections': 5
        }):
            response = client.get("/ws/health")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['active_connections'] == 3
    
    def test_broadcast_message(self, client):
        """测试广播消息"""
        with patch.object(enhanced_websocket_manager, '_broadcast', return_value=3) as mock_broadcast:
            message_data = {
                'type': 'notification',
                'title': '系统通知',
                'message': '系统将进行维护'
            }
            
            response = client.post("/ws/broadcast", json=message_data)
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['sent_count'] == 3
            
            # 验证广播被调用
            mock_broadcast.assert_called_once()
    
    def test_send_user_message(self, client):
        """测试发送用户消息"""
        with patch.object(enhanced_websocket_manager, '_send_to_user', return_value=2) as mock_send:
            message_data = {
                'type': 'notification',
                'title': '个人通知',
                'message': '您有新的消息'
            }
            
            response = client.post("/ws/send/user-123", json=message_data)
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['sent_count'] == 2
            
            # 验证发送被调用
            mock_send.assert_called_once()
    
    def test_get_active_connections(self, client):
        """测试获取活跃连接列表"""
        # 模拟连接数据
        mock_connections = {
            'client-1': Mock(
                client_id='client-1',
                user_id='user-1',
                conversation_id='conv-1',
                status=Mock(value='connected'),
                connected_at=datetime.now(),
                last_heartbeat=datetime.now(),
                subscriptions=set(['agent_response']),
                is_active=Mock(return_value=True)
            ),
            'client-2': Mock(
                client_id='client-2',
                user_id='user-2',
                conversation_id='conv-2',
                status=Mock(value='connected'),
                connected_at=datetime.now(),
                last_heartbeat=datetime.now(),
                subscriptions=set(['typing_indicator']),
                is_active=Mock(return_value=True)
            )
        }
        
        with patch.object(enhanced_websocket_manager, 'connections', mock_connections):
            response = client.get("/ws/connections")
            assert response.status_code == 200
            data = response.json()
            assert len(data['connections']) == 2
            assert data['total_count'] == 2
            assert data['active_count'] == 2
    
    @pytest.mark.asyncio
    async def test_initialize_websocket_router(self, mock_integration_service):
        """测试初始化WebSocket路由器"""
        with patch.object(enhanced_websocket_manager, 'start') as mock_start:
            await initialize_websocket_router(mock_integration_service)
            
            # 验证管理器启动被调用
            mock_start.assert_called_once()
            
            # 验证集成服务被设置
            assert connection_handler.integration_service == mock_integration_service
    
    @pytest.mark.asyncio
    async def test_shutdown_websocket_router(self):
        """测试关闭WebSocket路由器"""
        with patch.object(enhanced_websocket_manager, 'stop') as mock_stop:
            await shutdown_websocket_router()
            
            # 验证管理器停止被调用
            mock_stop.assert_called_once()
    
    def test_setup_message_handlers(self):
        """测试设置消息处理器"""
        # 清空现有处理器
        enhanced_websocket_manager.message_handlers.clear()
        
        # 设置处理器
        setup_message_handlers()
        
        # 验证处理器被注册
        assert MessageType.USER_MESSAGE in enhanced_websocket_manager.message_handlers
        assert MessageType.NOTIFICATION in enhanced_websocket_manager.message_handlers
        assert MessageType.CONVERSATION_STATE in enhanced_websocket_manager.message_handlers
        
        # 验证每个类型都有处理器
        assert len(enhanced_websocket_manager.message_handlers[MessageType.USER_MESSAGE]) > 0
        assert len(enhanced_websocket_manager.message_handlers[MessageType.NOTIFICATION]) > 0
        assert len(enhanced_websocket_manager.message_handlers[MessageType.CONVERSATION_STATE]) > 0


class TestWebSocketIntegration:
    """WebSocket集成测试类"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_message_flow(self, mock_integration_service):
        """测试端到端消息流"""
        # 设置集成服务
        connection_handler.set_integration_service(mock_integration_service)
        
        # 模拟WebSocket管理器方法
        with patch.object(enhanced_websocket_manager, 'send_typing_indicator') as mock_typing, \
             patch.object(enhanced_websocket_manager, 'send_agent_thinking') as mock_thinking, \
             patch.object(enhanced_websocket_manager, 'send_agent_response') as mock_response, \
             patch.object(enhanced_websocket_manager, 'get_connection_info') as mock_get_conn:
            
            # 模拟连接信息
            mock_connection_info = Mock()
            mock_connection_info.conversation_id = 'conv-123'
            mock_connection_info.user_id = 'user-456'
            mock_get_conn.return_value = mock_connection_info
            
            # 创建用户消息
            user_message = {
                'type': 'user_message',
                'data': {
                    'content': '帮我分析客户数据',
                    'context': {'source': 'web'}
                },
                'message_id': 'msg-123',
                'timestamp': datetime.now().isoformat()
            }
            
            # 处理消息
            await enhanced_websocket_manager.handle_message('client-1', user_message)
            
            # 验证完整的消息流
            # 1. 发送打字指示器
            mock_typing.assert_called()
            typing_calls = mock_typing.call_args_list
            assert any(call[1]['is_typing'] is True for call in typing_calls)
            assert any(call[1]['is_typing'] is False for call in typing_calls)
            
            # 2. 发送思考状态
            mock_thinking.assert_called()
            
            # 3. 发送Agent响应
            mock_response.assert_called()
            response_call = mock_response.call_args
            assert response_call[1]['conversation_id'] == 'conv-123'
            assert response_call[1]['agent_id'] == 'test_agent'
            
            # 4. 验证集成服务被调用
            assert len(mock_integration_service.process_calls) == 1
            process_call = mock_integration_service.process_calls[0]
            assert process_call['user_message'] == '帮我分析客户数据'
            assert process_call['conversation_id'] == 'conv-123'
            assert process_call['user_id'] == 'user-456'
    
    @pytest.mark.asyncio
    async def test_error_handling_in_message_flow(self, mock_integration_service):
        """测试消息流中的错误处理"""
        # 设置集成服务抛出异常
        async def failing_process(*args, **kwargs):
            raise Exception("处理失败")
        
        mock_integration_service.process_user_message = failing_process
        connection_handler.set_integration_service(mock_integration_service)
        
        with patch.object(enhanced_websocket_manager, '_send_error') as mock_error, \
             patch.object(enhanced_websocket_manager, 'get_connection_info') as mock_get_conn:
            
            # 模拟连接信息
            mock_connection_info = Mock()
            mock_connection_info.conversation_id = 'conv-123'
            mock_connection_info.user_id = 'user-456'
            mock_get_conn.return_value = mock_connection_info
            
            # 创建用户消息
            user_message = {
                'type': 'user_message',
                'data': {
                    'content': '测试错误处理',
                    'context': {}
                },
                'message_id': 'error-msg-123',
                'timestamp': datetime.now().isoformat()
            }
            
            # 处理消息
            await enhanced_websocket_manager.handle_message('client-1', user_message)
            
            # 验证发送了错误消息
            mock_error.assert_called()
            error_call = mock_error.call_args[0]
            assert error_call[0] == 'client-1'
            assert '处理消息失败' in error_call[1]
    
    @pytest.mark.asyncio
    async def test_multiple_agent_responses(self, mock_integration_service):
        """测试多Agent响应场景"""
        # 修改集成服务返回多Agent响应
        original_process = mock_integration_service.process_user_message
        
        async def multi_agent_process(*args, **kwargs):
            response = await original_process(*args, **kwargs)
            response.metadata['collaborating_agents'] = ['sales_agent', 'market_agent']
            return response
        
        mock_integration_service.process_user_message = multi_agent_process
        connection_handler.set_integration_service(mock_integration_service)
        
        with patch.object(enhanced_websocket_manager, 'send_agent_collaboration') as mock_collab, \
             patch.object(enhanced_websocket_manager, 'send_agent_response') as mock_response, \
             patch.object(enhanced_websocket_manager, 'get_connection_info') as mock_get_conn:
            
            # 模拟连接信息
            mock_connection_info = Mock()
            mock_connection_info.conversation_id = 'conv-multi'
            mock_connection_info.user_id = 'user-multi'
            mock_get_conn.return_value = mock_connection_info
            
            # 创建复杂查询消息
            user_message = {
                'type': 'user_message',
                'data': {
                    'content': '我需要一个完整的客户分析和市场策略',
                    'context': {'complexity': 'high'}
                },
                'message_id': 'multi-msg-123',
                'timestamp': datetime.now().isoformat()
            }
            
            # 处理消息
            await enhanced_websocket_manager.handle_message('client-1', user_message)
            
            # 验证Agent响应包含协作信息
            mock_response.assert_called()
            response_call = mock_response.call_args
            processing_info = response_call[1]['processing_info']
            assert 'rag_used' in processing_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])