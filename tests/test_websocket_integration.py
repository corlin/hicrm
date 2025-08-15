"""
WebSocket集成测试

测试WebSocket的完整功能，包括连接管理、消息传递、Agent集成等。
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
import websockets
from fastapi import FastAPI
from fastapi.testclient import TestClient
import uvicorn
import threading
import time

from src.websocket.enhanced_manager import (
    EnhancedWebSocketManager,
    MessageType,
    WebSocketMessage,
    ConnectionStatus
)
from src.websocket.router import router, initialize_websocket_router, shutdown_websocket_router
from src.services.agent_conversation_integration import AgentConversationIntegration
from src.schemas.conversation import MessageResponse


class MockAgentIntegrationService:
    """模拟Agent集成服务"""
    
    def __init__(self):
        self.processed_messages = []
        self.response_delay = 0.1  # 模拟处理延迟
    
    async def process_user_message(
        self,
        conversation_id: str,
        user_message: str,
        user_id: str,
        context: Dict[str, Any] = None
    ) -> MessageResponse:
        """模拟处理用户消息"""
        await asyncio.sleep(self.response_delay)
        
        self.processed_messages.append({
            'conversation_id': conversation_id,
            'user_message': user_message,
            'user_id': user_id,
            'context': context,
            'timestamp': datetime.now()
        })
        
        # 根据消息内容生成不同类型的响应
        if '客户' in user_message:
            agent_type = 'sales_agent'
            content = f"我来帮您分析客户信息：{user_message}"
        elif '线索' in user_message:
            agent_type = 'market_agent'
            content = f"我来处理线索相关问题：{user_message}"
        elif '报告' in user_message:
            agent_type = 'management_strategy_agent'
            content = f"我来生成分析报告：{user_message}"
        else:
            agent_type = 'crm_expert_agent'
            content = f"我来协助您：{user_message}"
        
        return MessageResponse(
            id=f"msg-{len(self.processed_messages)}",
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            agent_type=agent_type,
            metadata={
                'confidence': 0.9,
                'suggestions': ['建议1', '建议2'],
                'next_actions': ['下一步行动'],
                'intent': 'test_intent',
                'processing_time': self.response_delay,
                'rag_used': True
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


@pytest.fixture
async def websocket_manager():
    """创建WebSocket管理器"""
    manager = Enhan