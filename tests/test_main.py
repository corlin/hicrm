"""
主应用测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestMainApp:
    """主应用测试类"""
    
    def test_root_endpoint(self, sync_client: TestClient):
        """测试根路径"""
        response = sync_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "HiCRM - 对话式智能CRM系统"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
    
    def test_health_check(self, sync_client: TestClient):
        """测试健康检查"""
        response = sync_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hicrm-api"
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: AsyncClient):
        """测试WebSocket连接"""
        with client.websocket_connect("/ws/test-client") as websocket:
            websocket.send_text("Hello WebSocket")
            data = websocket.receive_text()
            assert "Echo: Hello WebSocket" in data