"""
WebSocket管理器测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket
import json

from src.websocket.manager import ConnectionManager


class TestConnectionManager:
    """WebSocket连接管理器测试类"""
    
    @pytest.fixture
    def connection_manager(self):
        """连接管理器实例"""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """模拟WebSocket连接"""
        websocket = AsyncMock(spec=WebSocket)
        websocket.client = MagicMock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_client(self, connection_manager: ConnectionManager, mock_websocket):
        """测试客户端连接"""
        client_id = "test-client-1"
        
        await connection_manager.connect(mock_websocket, client_id)
        
        assert client_id in connection_manager.active_connections
        assert connection_manager.active_connections[client_id] == mock_websocket
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_client(self, connection_manager: ConnectionManager, mock_websocket):
        """测试客户端断开连接"""
        client_id = "test-client-1"
        
        # 先连接
        await connection_manager.connect(mock_websocket, client_id)
        assert client_id in connection_manager.active_connections
        
        # 断开连接
        connection_manager.disconnect(client_id)
        assert client_id not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager: ConnectionManager, mock_websocket):
        """测试发送个人消息"""
        client_id = "test-client-1"
        message = "Hello, client!"
        
        # 连接客户端
        await connection_manager.connect(mock_websocket, client_id)
        
        # 发送消息
        await connection_manager.send_personal_message(message, client_id)
        
        mock_websocket.send_text.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_personal_message_to_nonexistent_client(self, connection_manager: ConnectionManager):
        """测试向不存在的客户端发送消息"""
        client_id = "nonexistent-client"
        message = "Hello, client!"
        
        # 发送消息到不存在的客户端（应该不会抛出异常）
        await connection_manager.send_personal_message(message, client_id)
        
        # 验证没有活跃连接
        assert client_id not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, connection_manager: ConnectionManager):
        """测试广播消息"""
        # 创建多个模拟客户端
        clients = []
        for i in range(3):
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.client = MagicMock()
            mock_websocket.client.host = "127.0.0.1"
            mock_websocket.client.port = 12345 + i
            
            client_id = f"test-client-{i}"
            await connection_manager.connect(mock_websocket, client_id)
            clients.append((client_id, mock_websocket))
        
        message = "Broadcast message"
        
        # 广播消息
        await connection_manager.broadcast(message)
        
        # 验证所有客户端都收到消息
        for client_id, mock_websocket in clients:
            mock_websocket.send_text.assert_called_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_empty_connections(self, connection_manager: ConnectionManager):
        """测试向空连接列表广播"""
        message = "Broadcast message"
        
        # 广播消息（没有连接的客户端）
        await connection_manager.broadcast(message)
        
        # 验证没有异常抛出
        assert len(connection_manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_send_json_message(self, connection_manager: ConnectionManager, mock_websocket):
        """测试发送JSON消息"""
        client_id = "test-client-1"
        data = {"type": "notification", "message": "Hello", "timestamp": "2024-01-01T00:00:00Z"}
        
        # 连接客户端
        await connection_manager.connect(mock_websocket, client_id)
        
        # 发送JSON消息
        await connection_manager.send_json(data, client_id)
        
        expected_json = json.dumps(data, ensure_ascii=False)
        mock_websocket.send_text.assert_called_once_with(expected_json)
    
    @pytest.mark.asyncio
    async def test_broadcast_json_message(self, connection_manager: ConnectionManager):
        """测试广播JSON消息"""
        # 创建多个模拟客户端
        clients = []
        for i in range(2):
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.client = MagicMock()
            mock_websocket.client.host = "127.0.0.1"
            mock_websocket.client.port = 12345 + i
            
            client_id = f"test-client-{i}"
            await connection_manager.connect(mock_websocket, client_id)
            clients.append((client_id, mock_websocket))
        
        data = {"type": "broadcast", "message": "Hello everyone"}
        
        # 广播JSON消息
        await connection_manager.broadcast_json(data)
        
        expected_json = json.dumps(data, ensure_ascii=False)
        
        # 验证所有客户端都收到JSON消息
        for client_id, mock_websocket in clients:
            mock_websocket.send_text.assert_called_with(expected_json)
    
    @pytest.mark.asyncio
    async def test_get_connection_count(self, connection_manager: ConnectionManager):
        """测试获取连接数量"""
        assert connection_manager.get_connection_count() == 0
        
        # 添加连接
        for i in range(3):
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.client = MagicMock()
            client_id = f"test-client-{i}"
            await connection_manager.connect(mock_websocket, client_id)
        
        assert connection_manager.get_connection_count() == 3
        
        # 断开一个连接
        connection_manager.disconnect("test-client-1")
        assert connection_manager.get_connection_count() == 2
    
    @pytest.mark.asyncio
    async def test_get_connected_clients(self, connection_manager: ConnectionManager):
        """测试获取已连接客户端列表"""
        assert connection_manager.get_connected_clients() == []
        
        # 添加连接
        client_ids = ["client-1", "client-2", "client-3"]
        for client_id in client_ids:
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.client = MagicMock()
            await connection_manager.connect(mock_websocket, client_id)
        
        connected_clients = connection_manager.get_connected_clients()
        assert set(connected_clients) == set(client_ids)
        assert len(connected_clients) == 3
    
    @pytest.mark.asyncio
    async def test_is_client_connected(self, connection_manager: ConnectionManager, mock_websocket):
        """测试检查客户端是否已连接"""
        client_id = "test-client-1"
        
        # 客户端未连接
        assert not connection_manager.is_client_connected(client_id)
        
        # 连接客户端
        await connection_manager.connect(mock_websocket, client_id)
        assert connection_manager.is_client_connected(client_id)
        
        # 断开连接
        connection_manager.disconnect(client_id)
        assert not connection_manager.is_client_connected(client_id)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, connection_manager: ConnectionManager):
        """测试连接错误处理"""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.client = MagicMock()
        mock_websocket.send_text.side_effect = Exception("连接已断开")
        
        client_id = "test-client-1"
        
        # 连接客户端
        await connection_manager.connect(mock_websocket, client_id)
        
        # 尝试发送消息（应该处理异常）
        await connection_manager.send_personal_message("test message", client_id)
        
        # 验证连接仍然存在（错误处理不应该自动断开连接）
        assert connection_manager.is_client_connected(client_id)
    
    @pytest.mark.asyncio
    async def test_duplicate_client_connection(self, connection_manager: ConnectionManager):
        """测试重复客户端连接"""
        client_id = "test-client-1"
        
        # 第一次连接
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket1.client = MagicMock()
        await connection_manager.connect(mock_websocket1, client_id)
        
        # 第二次连接（相同client_id）
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket2.client = MagicMock()
        await connection_manager.connect(mock_websocket2, client_id)
        
        # 验证新连接替换了旧连接
        assert connection_manager.active_connections[client_id] == mock_websocket2
        assert connection_manager.get_connection_count() == 1