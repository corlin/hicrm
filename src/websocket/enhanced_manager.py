"""
增强的WebSocket管理器

扩展现有WebSocket管理器支持Agent消息推送、实时对话更新和状态同步机制。
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect
import uuid

from src.websocket.manager import ConnectionManager
from src.agents.base import AgentResponse
from src.schemas.conversation import MessageResponse

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket消息类型"""
    # 连接管理
    CONNECTION_ACK = "connection_ack"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    
    # 对话消息
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    TYPING_INDICATOR = "typing_indicator"
    
    # 状态更新
    CONVERSATION_STATE = "conversation_state"
    AGENT_STATUS = "agent_status"
    SYSTEM_STATUS = "system_status"
    
    # 错误和通知
    ERROR = "error"
    NOTIFICATION = "notification"
    WARNING = "warning"
    
    # Agent特定消息
    AGENT_THINKING = "agent_thinking"
    AGENT_COLLABORATION = "agent_collaboration"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"


class ConnectionStatus(str, Enum):
    """连接状态"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket消息结构"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id
        }


@dataclass
class ConnectionInfo:
    """连接信息"""
    client_id: str
    user_id: Optional[str]
    conversation_id: Optional[str]
    websocket: WebSocket
    status: ConnectionStatus
    connected_at: datetime
    last_heartbeat: datetime
    subscriptions: Set[str]  # 订阅的事件类型
    metadata: Dict[str, Any]
    
    def is_active(self) -> bool:
        """检查连接是否活跃"""
        return self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED]
    
    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """检查连接是否过期（5分钟无心跳）"""
        return (datetime.now() - self.last_heartbeat).total_seconds() > timeout_seconds


class EnhancedWebSocketManager:
    """增强的WebSocket管理器"""
    
    def __init__(self, heartbeat_interval: int = 30, connection_timeout: int = 300):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> client_ids
        self.conversation_connections: Dict[str, Set[str]] = {}  # conversation_id -> client_ids
        
        # 配置
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        
        # 事件处理器
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.connection_handlers: List[Callable] = []
        self.disconnection_handlers: List[Callable] = []
        
        # 后台任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """启动WebSocket管理器"""
        try:
            # 启动心跳任务
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 启动清理任务
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("增强WebSocket管理器已启动")
            
        except Exception as e:
            self.logger.error(f"启动WebSocket管理器失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止WebSocket管理器"""
        try:
            # 停止后台任务
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭所有连接
            await self._close_all_connections()
            
            self.logger.info("增强WebSocket管理器已停止")
            
        except Exception as e:
            self.logger.error(f"停止WebSocket管理器失败: {e}")
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            
            # 创建连接信息
            connection_info = ConnectionInfo(
                client_id=client_id,
                user_id=user_id,
                conversation_id=conversation_id,
                websocket=websocket,
                status=ConnectionStatus.CONNECTED,
                connected_at=datetime.now(),
                last_heartbeat=datetime.now(),
                subscriptions=set(),
                metadata=metadata or {}
            )
            
            # 保存连接
            self.connections[client_id] = connection_info
            
            # 更新索引
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(client_id)
            
            if conversation_id:
                if conversation_id not in self.conversation_connections:
                    self.conversation_connections[conversation_id] = set()
                self.conversation_connections[conversation_id].add(client_id)
            
            # 发送连接确认
            await self._send_message(client_id, WebSocketMessage(
                type=MessageType.CONNECTION_ACK,
                data={
                    'client_id': client_id,
                    'server_time': datetime.now().isoformat(),
                    'heartbeat_interval': self.heartbeat_interval
                },
                timestamp=datetime.now(),
                message_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                user_id=user_id
            ))
            
            # 更新统计
            self.stats['total_connections'] += 1
            self.stats['active_connections'] = len([
                conn for conn in self.connections.values() if conn.is_active()
            ])
            
            # 调用连接处理器
            for handler in self.connection_handlers:
                try:
                    await handler(connection_info)
                except Exception as e:
                    self.logger.error(f"连接处理器错误: {e}")
            
            self.logger.info(f"客户端 {client_id} 已连接 (用户: {user_id}, 对话: {conversation_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"建立WebSocket连接失败: {e}")
            return False
    
    async def disconnect(self, client_id: str, reason: str = "normal") -> None:
        """断开WebSocket连接"""
        if client_id not in self.connections:
            return
        
        try:
            connection_info = self.connections[client_id]
            connection_info.status = ConnectionStatus.DISCONNECTING
            
            # 从索引中移除
            if connection_info.user_id and connection_info.user_id in self.user_connections:
                self.user_connections[connection_info.user_id].discard(client_id)
                if not self.user_connections[connection_info.user_id]:
                    del self.user_connections[connection_info.user_id]
            
            if connection_info.conversation_id and connection_info.conversation_id in self.conversation_connections:
                self.conversation_connections[connection_info.conversation_id].discard(client_id)
                if not self.conversation_connections[connection_info.conversation_id]:
                    del self.conversation_connections[connection_info.conversation_id]
            
            # 调用断开处理器
            for handler in self.disconnection_handlers:
                try:
                    await handler(connection_info, reason)
                except Exception as e:
                    self.logger.error(f"断开处理器错误: {e}")
            
            # 移除连接
            del self.connections[client_id]
            
            # 更新统计
            self.stats['active_connections'] = len([
                conn for conn in self.connections.values() if conn.is_active()
            ])
            
            self.logger.info(f"客户端 {client_id} 已断开连接 (原因: {reason})")
            
        except Exception as e:
            self.logger.error(f"断开WebSocket连接失败: {e}")
    
    async def handle_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """处理接收到的WebSocket消息"""
        try:
            if client_id not in self.connections:
                self.logger.warning(f"收到来自未知客户端 {client_id} 的消息")
                return
            
            connection_info = self.connections[client_id]
            
            # 解析消息
            message_type = MessageType(message.get('type', 'unknown'))
            message_data = message.get('data', {})
            
            # 更新心跳时间
            if message_type == MessageType.HEARTBEAT:
                connection_info.last_heartbeat = datetime.now()
                await self._send_message(client_id, WebSocketMessage(
                    type=MessageType.HEARTBEAT_ACK,
                    data={'server_time': datetime.now().isoformat()},
                    timestamp=datetime.now(),
                    message_id=str(uuid.uuid4())
                ))
                return
            
            # 创建WebSocket消息对象
            ws_message = WebSocketMessage(
                type=message_type,
                data=message_data,
                timestamp=datetime.now(),
                message_id=message.get('message_id', str(uuid.uuid4())),
                conversation_id=connection_info.conversation_id,
                user_id=connection_info.user_id
            )
            
            # 调用消息处理器
            handlers = self.message_handlers.get(message_type, [])
            for handler in handlers:
                try:
                    await handler(client_id, ws_message)
                except Exception as e:
                    self.logger.error(f"消息处理器错误: {e}")
            
            # 更新统计
            self.stats['messages_received'] += 1
            
        except Exception as e:
            self.logger.error(f"处理WebSocket消息失败: {e}")
            self.stats['errors'] += 1
            
            # 发送错误消息
            await self._send_error(client_id, f"消息处理失败: {str(e)}")
    
    async def send_agent_response(
        self,
        conversation_id: str,
        agent_response: AgentResponse,
        agent_id: str,
        processing_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """发送Agent响应到对话"""
        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            data={
                'content': agent_response.content,
                'confidence': agent_response.confidence,
                'suggestions': agent_response.suggestions,
                'next_actions': agent_response.next_actions,
                'agent_id': agent_id,
                'processing_info': processing_info or {},
                'metadata': agent_response.metadata
            },
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id
        )
        
        await self._send_to_conversation(conversation_id, message)
    
    async def send_agent_thinking(
        self,
        conversation_id: str,
        agent_id: str,
        thinking_message: str,
        progress: Optional[float] = None
    ) -> None:
        """发送Agent思考状态"""
        message = WebSocketMessage(
            type=MessageType.AGENT_THINKING,
            data={
                'agent_id': agent_id,
                'message': thinking_message,
                'progress': progress,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id
        )
        
        await self._send_to_conversation(conversation_id, message)
    
    async def send_typing_indicator(
        self,
        conversation_id: str,
        agent_id: str,
        is_typing: bool = True
    ) -> None:
        """发送打字指示器"""
        message = WebSocketMessage(
            type=MessageType.TYPING_INDICATOR,
            data={
                'agent_id': agent_id,
                'is_typing': is_typing,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id
        )
        
        await self._send_to_conversation(conversation_id, message)
    
    async def send_agent_collaboration(
        self,
        conversation_id: str,
        collaborating_agents: List[str],
        collaboration_type: str,
        status: str
    ) -> None:
        """发送Agent协作状态"""
        message = WebSocketMessage(
            type=MessageType.AGENT_COLLABORATION,
            data={
                'collaborating_agents': collaborating_agents,
                'collaboration_type': collaboration_type,
                'status': status,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id
        )
        
        await self._send_to_conversation(conversation_id, message)
    
    async def send_knowledge_retrieval_status(
        self,
        conversation_id: str,
        status: str,
        query: str,
        results_count: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> None:
        """发送知识检索状态"""
        message = WebSocketMessage(
            type=MessageType.KNOWLEDGE_RETRIEVAL,
            data={
                'status': status,
                'query': query,
                'results_count': results_count,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id
        )
        
        await self._send_to_conversation(conversation_id, message)
    
    async def send_conversation_state_update(
        self,
        conversation_id: str,
        state_data: Dict[str, Any]
    ) -> None:
        """发送对话状态更新"""
        message = WebSocketMessage(
            type=MessageType.CONVERSATION_STATE,
            data=state_data,
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id
        )
        
        await self._send_to_conversation(conversation_id, message)
    
    async def send_system_notification(
        self,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        notification_type: str = "info",
        title: str = "",
        message: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """发送系统通知"""
        ws_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                'notification_type': notification_type,
                'title': title,
                'message': message,
                'data': data or {},
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if conversation_id:
            await self._send_to_conversation(conversation_id, ws_message)
        elif user_id:
            await self._send_to_user(user_id, ws_message)
        else:
            await self._broadcast(ws_message)
    
    async def _send_message(self, client_id: str, message: WebSocketMessage) -> bool:
        """发送消息给指定客户端"""
        if client_id not in self.connections:
            return False
        
        try:
            connection_info = self.connections[client_id]
            if not connection_info.is_active():
                return False
            
            await connection_info.websocket.send_json(message.to_dict())
            self.stats['messages_sent'] += 1
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(client_id, "websocket_disconnect")
            return False
        except Exception as e:
            self.logger.error(f"发送消息给客户端 {client_id} 失败: {e}")
            self.stats['errors'] += 1
            await self.disconnect(client_id, "send_error")
            return False
    
    async def _send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """发送消息给用户的所有连接"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        client_ids = list(self.user_connections[user_id])  # 复制列表避免并发修改
        
        for client_id in client_ids:
            if await self._send_message(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def _send_to_conversation(self, conversation_id: str, message: WebSocketMessage) -> int:
        """发送消息给对话的所有连接"""
        if conversation_id not in self.conversation_connections:
            return 0
        
        sent_count = 0
        client_ids = list(self.conversation_connections[conversation_id])  # 复制列表避免并发修改
        
        for client_id in client_ids:
            if await self._send_message(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def _broadcast(self, message: WebSocketMessage) -> int:
        """广播消息给所有活跃连接"""
        sent_count = 0
        client_ids = list(self.connections.keys())  # 复制列表避免并发修改
        
        for client_id in client_ids:
            if await self._send_message(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def _send_error(self, client_id: str, error_message: str) -> None:
        """发送错误消息"""
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            data={
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4())
        )
        
        await self._send_message(client_id, error_msg)
    
    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # 检查过期连接
                expired_clients = []
                for client_id, connection_info in self.connections.items():
                    if connection_info.is_expired(self.connection_timeout):
                        expired_clients.append(client_id)
                
                # 断开过期连接
                for client_id in expired_clients:
                    await self.disconnect(client_id, "heartbeat_timeout")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳循环错误: {e}")
    
    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                
                # 清理空的索引
                empty_users = [
                    user_id for user_id, client_ids in self.user_connections.items()
                    if not client_ids
                ]
                for user_id in empty_users:
                    del self.user_connections[user_id]
                
                empty_conversations = [
                    conv_id for conv_id, client_ids in self.conversation_connections.items()
                    if not client_ids
                ]
                for conv_id in empty_conversations:
                    del self.conversation_connections[conv_id]
                
                self.logger.debug(f"清理了 {len(empty_users)} 个空用户索引和 {len(empty_conversations)} 个空对话索引")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理循环错误: {e}")
    
    async def _close_all_connections(self) -> None:
        """关闭所有连接"""
        client_ids = list(self.connections.keys())
        for client_id in client_ids:
            await self.disconnect(client_id, "server_shutdown")
    
    def register_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """注册消息处理器"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def register_connection_handler(self, handler: Callable) -> None:
        """注册连接处理器"""
        self.connection_handlers.append(handler)
    
    def register_disconnection_handler(self, handler: Callable) -> None:
        """注册断开处理器"""
        self.disconnection_handlers.append(handler)
    
    def get_connection_info(self, client_id: str) -> Optional[ConnectionInfo]:
        """获取连接信息"""
        return self.connections.get(client_id)
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """获取用户的所有连接"""
        return list(self.user_connections.get(user_id, set()))
    
    def get_conversation_connections(self, conversation_id: str) -> List[str]:
        """获取对话的所有连接"""
        return list(self.conversation_connections.get(conversation_id, set()))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'connection_count': len(self.connections),
            'user_count': len(self.user_connections),
            'conversation_count': len(self.conversation_connections),
            'active_connections': len([
                conn for conn in self.connections.values() if conn.is_active()
            ])
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            active_connections = len([
                conn for conn in self.connections.values() if conn.is_active()
            ])
            
            return {
                'status': 'healthy',
                'active_connections': active_connections,
                'total_connections': len(self.connections),
                'heartbeat_task_running': self._heartbeat_task and not self._heartbeat_task.done(),
                'cleanup_task_running': self._cleanup_task and not self._cleanup_task.done()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# 全局增强WebSocket管理器实例
enhanced_websocket_manager = EnhancedWebSocketManager()