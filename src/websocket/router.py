"""
WebSocket路由器

处理WebSocket连接和消息路由，集成Agent响应的实时推送功能。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
import uuid

from src.websocket.enhanced_manager import (
    enhanced_websocket_manager,
    MessageType,
    WebSocketMessage,
    ConnectionInfo
)
from src.services.agent_conversation_integration import AgentConversationIntegration
from src.core.auth import get_current_user_optional
from src.core.database import get_db

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/ws", tags=["websocket"])

# 安全方案
security = HTTPBearer(auto_error=False)


class WebSocketConnectionHandler:
    """WebSocket连接处理器"""
    
    def __init__(self):
        self.integration_service: Optional[AgentConversationIntegration] = None
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
    
    def set_integration_service(self, integration_service: AgentConversationIntegration):
        """设置集成服务"""
        self.integration_service = integration_service
    
    async def handle_user_message(self, client_id: str, message: WebSocketMessage) -> None:
        """处理用户消息"""
        try:
            if not self.integration_service:
                logger.error("集成服务未设置")
                return
            
            conversation_id = message.conversation_id
            user_id = message.user_id
            content = message.data.get('content', '')
            
            if not conversation_id or not user_id or not content:
                await enhanced_websocket_manager._send_error(
                    client_id, 
                    "缺少必要的消息参数: conversation_id, user_id, content"
                )
                return
            
            # 发送打字指示器
            await enhanced_websocket_manager.send_typing_indicator(
                conversation_id, 
                "system", 
                True
            )
            
            # 发送Agent思考状态
            await enhanced_websocket_manager.send_agent_thinking(
                conversation_id,
                "system",
                "正在分析您的消息...",
                0.1
            )
            
            # 处理用户消息
            response = await self.integration_service.process_user_message(
                conversation_id=conversation_id,
                user_message=content,
                user_id=user_id,
                context=message.data.get('context', {})
            )
            
            # 停止打字指示器
            await enhanced_websocket_manager.send_typing_indicator(
                conversation_id, 
                "system", 
                False
            )
            
            # 发送Agent响应
            await enhanced_websocket_manager.send_agent_response(
                conversation_id=conversation_id,
                agent_response=type('AgentResponse', (), {
                    'content': response.content,
                    'confidence': response.metadata.get('confidence', 0.8),
                    'suggestions': response.metadata.get('suggestions', []),
                    'next_actions': response.metadata.get('next_actions', []),
                    'metadata': response.metadata
                })(),
                agent_id=response.agent_type or "unknown",
                processing_info={
                    'processing_time': response.metadata.get('processing_time', 0),
                    'intent': response.metadata.get('intent'),
                    'rag_used': response.metadata.get('rag_used', False)
                }
            )
            
        except Exception as e:
            logger.error(f"处理用户消息失败: {e}")
            await enhanced_websocket_manager._send_error(
                client_id, 
                f"处理消息失败: {str(e)}"
            )
    
    async def handle_subscription(self, client_id: str, message: WebSocketMessage) -> None:
        """处理订阅请求"""
        try:
            connection_info = enhanced_websocket_manager.get_connection_info(client_id)
            if not connection_info:
                return
            
            event_types = message.data.get('event_types', [])
            for event_type in event_types:
                connection_info.subscriptions.add(event_type)
            
            # 发送订阅确认
            await enhanced_websocket_manager._send_message(client_id, WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    'message': f'已订阅事件: {", ".join(event_types)}',
                    'subscriptions': list(connection_info.subscriptions)
                },
                timestamp=message.timestamp,
                message_id=str(uuid.uuid4())
            ))
            
        except Exception as e:
            logger.error(f"处理订阅请求失败: {e}")
    
    async def handle_conversation_join(self, client_id: str, message: WebSocketMessage) -> None:
        """处理加入对话请求"""
        try:
            conversation_id = message.data.get('conversation_id')
            if not conversation_id:
                await enhanced_websocket_manager._send_error(
                    client_id, 
                    "缺少conversation_id参数"
                )
                return
            
            connection_info = enhanced_websocket_manager.get_connection_info(client_id)
            if not connection_info:
                return
            
            # 更新连接的对话ID
            old_conversation_id = connection_info.conversation_id
            connection_info.conversation_id = conversation_id
            
            # 更新对话连接索引
            if old_conversation_id and old_conversation_id in enhanced_websocket_manager.conversation_connections:
                enhanced_websocket_manager.conversation_connections[old_conversation_id].discard(client_id)
            
            if conversation_id not in enhanced_websocket_manager.conversation_connections:
                enhanced_websocket_manager.conversation_connections[conversation_id] = set()
            enhanced_websocket_manager.conversation_connections[conversation_id].add(client_id)
            
            # 发送加入确认
            await enhanced_websocket_manager._send_message(client_id, WebSocketMessage(
                type=MessageType.CONVERSATION_STATE,
                data={
                    'action': 'joined',
                    'conversation_id': conversation_id,
                    'message': f'已加入对话 {conversation_id}'
                },
                timestamp=message.timestamp,
                message_id=str(uuid.uuid4()),
                conversation_id=conversation_id
            ))
            
        except Exception as e:
            logger.error(f"处理加入对话请求失败: {e}")


# 创建连接处理器实例
connection_handler = WebSocketConnectionHandler()


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    conversation_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """WebSocket连接端点"""
    
    # 生成客户端ID（如果未提供）
    if not client_id:
        client_id = str(uuid.uuid4())
    
    try:
        # 建立连接
        success = await enhanced_websocket_manager.connect(
            websocket=websocket,
            client_id=client_id,
            user_id=user_id,
            conversation_id=conversation_id,
            metadata={
                'user_agent': websocket.headers.get('user-agent', ''),
                'origin': websocket.headers.get('origin', ''),
                'connected_at': websocket.headers.get('date', '')
            }
        )
        
        if not success:
            logger.error(f"建立WebSocket连接失败: {client_id}")
            return
        
        # 消息处理循环
        try:
            while True:
                # 接收消息
                data = await websocket.receive_json()
                
                # 处理消息
                await enhanced_websocket_manager.handle_message(client_id, data)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket客户端 {client_id} 正常断开连接")
        except Exception as e:
            logger.error(f"WebSocket消息处理错误: {e}")
        
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    
    finally:
        # 断开连接
        await enhanced_websocket_manager.disconnect(client_id, "connection_closed")


@router.get("/stats")
async def get_websocket_stats():
    """获取WebSocket统计信息"""
    return enhanced_websocket_manager.get_stats()


@router.get("/health")
async def websocket_health_check():
    """WebSocket健康检查"""
    return await enhanced_websocket_manager.health_check()


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    current_user = Depends(get_current_user_optional)
):
    """广播消息（管理员功能）"""
    
    # 这里可以添加权限检查
    # if not current_user or not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        ws_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data=message,
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4())
        )
        
        sent_count = await enhanced_websocket_manager._broadcast(ws_message)
        
        return {
            'success': True,
            'message': '消息已广播',
            'sent_count': sent_count
        }
        
    except Exception as e:
        logger.error(f"广播消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"广播失败: {str(e)}")


@router.post("/send/{user_id}")
async def send_user_message(
    user_id: str,
    message: Dict[str, Any],
    current_user = Depends(get_current_user_optional)
):
    """发送消息给指定用户"""
    
    try:
        ws_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data=message,
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            user_id=user_id
        )
        
        sent_count = await enhanced_websocket_manager._send_to_user(user_id, ws_message)
        
        return {
            'success': True,
            'message': f'消息已发送给用户 {user_id}',
            'sent_count': sent_count
        }
        
    except Exception as e:
        logger.error(f"发送用户消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")


@router.get("/connections")
async def get_active_connections(current_user = Depends(get_current_user_optional)):
    """获取活跃连接列表（管理员功能）"""
    
    try:
        connections = []
        for client_id, connection_info in enhanced_websocket_manager.connections.items():
            connections.append({
                'client_id': client_id,
                'user_id': connection_info.user_id,
                'conversation_id': connection_info.conversation_id,
                'status': connection_info.status.value,
                'connected_at': connection_info.connected_at.isoformat(),
                'last_heartbeat': connection_info.last_heartbeat.isoformat(),
                'subscriptions': list(connection_info.subscriptions),
                'is_active': connection_info.is_active()
            })
        
        return {
            'connections': connections,
            'total_count': len(connections),
            'active_count': len([c for c in connections if c['is_active']])
        }
        
    except Exception as e:
        logger.error(f"获取连接列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# 注册消息处理器
def setup_message_handlers():
    """设置消息处理器"""
    
    # 注册用户消息处理器
    enhanced_websocket_manager.register_message_handler(
        MessageType.USER_MESSAGE,
        connection_handler.handle_user_message
    )
    
    # 注册订阅处理器
    enhanced_websocket_manager.register_message_handler(
        MessageType.NOTIFICATION,  # 使用通知类型处理订阅
        connection_handler.handle_subscription
    )
    
    # 注册对话加入处理器
    enhanced_websocket_manager.register_message_handler(
        MessageType.CONVERSATION_STATE,
        connection_handler.handle_conversation_join
    )
    
    logger.info("WebSocket消息处理器已设置")


# 启动时设置处理器
setup_message_handlers()


# 初始化函数
async def initialize_websocket_router(integration_service: AgentConversationIntegration):
    """初始化WebSocket路由器"""
    try:
        # 设置集成服务
        connection_handler.set_integration_service(integration_service)
        
        # 启动WebSocket管理器
        await enhanced_websocket_manager.start()
        
        logger.info("WebSocket路由器初始化完成")
        
    except Exception as e:
        logger.error(f"WebSocket路由器初始化失败: {e}")
        raise


# 关闭函数
async def shutdown_websocket_router():
    """关闭WebSocket路由器"""
    try:
        await enhanced_websocket_manager.stop()
        logger.info("WebSocket路由器已关闭")
        
    except Exception as e:
        logger.error(f"WebSocket路由器关闭失败: {e}")