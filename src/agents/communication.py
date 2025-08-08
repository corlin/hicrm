"""
Agent间消息通信系统

使用RabbitMQ实现Agent间的异步消息通信和协作。
"""

import json
import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import logging
import uuid

import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractExchange, AbstractQueue
from pydantic import BaseModel

from .base import AgentMessage, MessageType, AgentResponse
from ..core.config import settings


logger = logging.getLogger(__name__)


class CommunicationConfig(BaseModel):
    """通信配置"""
    rabbitmq_url: str = settings.RABBITMQ_URL
    exchange_name: str = "agent_communication"
    queue_prefix: str = "agent_queue_"
    response_timeout: int = 30  # 响应超时时间（秒）
    max_retries: int = 3
    retry_delay: float = 1.0


class MessageBroker:
    """
    消息代理
    
    负责RabbitMQ连接管理和消息路由。
    """
    
    def __init__(self, config: Optional[CommunicationConfig] = None):
        self.config = config or CommunicationConfig()
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange: Optional[AbstractExchange] = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> None:
        """初始化消息代理"""
        try:
            # 建立连接
            self.connection = await aio_pika.connect_robust(
                self.config.rabbitmq_url,
                client_properties={"connection_name": "agent_communication"}
            )
            
            # 创建通道
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            # 声明交换机
            self.exchange = await self.channel.declare_exchange(
                self.config.exchange_name,
                ExchangeType.DIRECT,
                durable=True
            )
            
            self.logger.info("Message broker initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize message broker: {e}")
            raise
    
    async def close(self) -> None:
        """关闭消息代理"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.logger.info("Message broker closed")
    
    async def declare_agent_queue(self, agent_id: str) -> AbstractQueue:
        """
        为Agent声明队列
        
        Args:
            agent_id: Agent ID
            
        Returns:
            队列对象
        """
        if not self.channel:
            raise RuntimeError("Message broker not initialized")
        
        queue_name = f"{self.config.queue_prefix}{agent_id}"
        
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={"x-message-ttl": 300000}  # 5分钟TTL
        )
        
        # 绑定队列到交换机
        await queue.bind(self.exchange, routing_key=agent_id)
        
        self.logger.debug(f"Declared queue for agent {agent_id}")
        return queue
    
    async def publish_message(
        self, 
        message: AgentMessage, 
        routing_key: str
    ) -> None:
        """
        发布消息
        
        Args:
            message: 要发送的消息
            routing_key: 路由键（通常是接收者Agent ID）
        """
        if not self.exchange:
            raise RuntimeError("Message broker not initialized")
        
        try:
            # 序列化消息
            message_body = json.dumps(message.dict(), default=str)
            
            # 创建AMQP消息
            amqp_message = Message(
                message_body.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "message_id": message.id,
                    "message_type": message.type,
                    "sender_id": message.sender_id,
                    "timestamp": message.timestamp.isoformat()
                }
            )
            
            # 发布消息
            await self.exchange.publish(
                amqp_message,
                routing_key=routing_key
            )
            
            self.logger.debug(f"Published message {message.id} to {routing_key}")
            
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            if not self.connection or self.connection.is_closed:
                return {"status": "error", "message": "Not connected"}
            
            return {
                "status": "healthy",
                "connected": True,
                "channel_open": self.channel and not self.channel.is_closed
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "connected": False
            }


class AgentCommunicator:
    """
    Agent通信器
    
    为单个Agent提供消息发送和接收功能。
    """
    
    def __init__(
        self, 
        agent_id: str, 
        message_broker: MessageBroker,
        config: Optional[CommunicationConfig] = None
    ):
        self.agent_id = agent_id
        self.message_broker = message_broker
        self.config = config or CommunicationConfig()
        self.queue: Optional[AbstractQueue] = None
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger(f"communicator.{agent_id}")
        self._consumer_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """初始化通信器"""
        try:
            # 声明Agent队列
            self.queue = await self.message_broker.declare_agent_queue(self.agent_id)
            
            # 启动消息消费者
            self._consumer_task = asyncio.create_task(self._start_consuming())
            
            self.logger.info(f"Agent communicator initialized for {self.agent_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize communicator: {e}")
            raise
    
    async def close(self) -> None:
        """关闭通信器"""
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        # 取消所有待处理的响应
        for future in self.pending_responses.values():
            if not future.done():
                future.cancel()
        
        self.logger.info(f"Agent communicator closed for {self.agent_id}")
    
    def register_handler(
        self, 
        message_type: MessageType, 
        handler: Callable[[AgentMessage], Any]
    ) -> None:
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self.message_handlers[message_type] = handler
        self.logger.debug(f"Registered handler for {message_type}")
    
    async def send_message(
        self, 
        message: AgentMessage, 
        wait_for_response: bool = False
    ) -> Optional[AgentMessage]:
        """
        发送消息
        
        Args:
            message: 要发送的消息
            wait_for_response: 是否等待响应
            
        Returns:
            如果wait_for_response为True，返回响应消息
        """
        try:
            # 如果需要等待响应，设置correlation_id
            if wait_for_response and not message.correlation_id:
                message.correlation_id = str(uuid.uuid4())
            
            # 发送消息
            await self.message_broker.publish_message(
                message, 
                message.receiver_id or "broadcast"
            )
            
            # 如果需要等待响应
            if wait_for_response and message.correlation_id:
                return await self._wait_for_response(message.correlation_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise
    
    async def broadcast_message(self, message: AgentMessage) -> None:
        """
        广播消息
        
        Args:
            message: 要广播的消息
        """
        message.receiver_id = None  # 广播消息没有特定接收者
        await self.message_broker.publish_message(message, "broadcast")
    
    async def _start_consuming(self) -> None:
        """开始消费消息"""
        if not self.queue:
            raise RuntimeError("Queue not initialized")
        
        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        await self._process_message(message)
                        await message.ack()
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        await message.nack(requeue=False)
                        
        except asyncio.CancelledError:
            self.logger.info("Message consumer cancelled")
        except Exception as e:
            self.logger.error(f"Error in message consumer: {e}")
    
    async def _process_message(self, amqp_message) -> None:
        """处理接收到的消息"""
        try:
            # 反序列化消息
            message_data = json.loads(amqp_message.body.decode())
            
            # 转换时间字段
            if "timestamp" in message_data:
                message_data["timestamp"] = datetime.fromisoformat(message_data["timestamp"])
            
            agent_message = AgentMessage(**message_data)
            
            self.logger.debug(f"Received message {agent_message.id} from {agent_message.sender_id}")
            
            # 检查是否是响应消息
            if (agent_message.type == MessageType.RESPONSE and 
                agent_message.correlation_id and 
                agent_message.correlation_id in self.pending_responses):
                
                future = self.pending_responses.pop(agent_message.correlation_id)
                if not future.done():
                    future.set_result(agent_message)
                return
            
            # 查找并调用消息处理器
            handler = self.message_handlers.get(agent_message.type)
            if handler:
                try:
                    result = await handler(agent_message)
                    
                    # 如果消息需要响应，发送响应
                    if agent_message.correlation_id and result:
                        response_message = AgentMessage(
                            type=MessageType.RESPONSE,
                            sender_id=self.agent_id,
                            receiver_id=agent_message.sender_id,
                            content=str(result),
                            correlation_id=agent_message.correlation_id,
                            metadata={"original_message_id": agent_message.id}
                        )
                        
                        await self.send_message(response_message)
                        
                except Exception as e:
                    self.logger.error(f"Error in message handler: {e}")
                    
                    # 发送错误响应
                    if agent_message.correlation_id:
                        error_response = AgentMessage(
                            type=MessageType.ERROR,
                            sender_id=self.agent_id,
                            receiver_id=agent_message.sender_id,
                            content=f"Error processing message: {str(e)}",
                            correlation_id=agent_message.correlation_id,
                            metadata={"error": str(e)}
                        )
                        
                        await self.send_message(error_response)
            else:
                self.logger.warning(f"No handler for message type {agent_message.type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    async def _wait_for_response(self, correlation_id: str) -> Optional[AgentMessage]:
        """
        等待响应消息
        
        Args:
            correlation_id: 关联ID
            
        Returns:
            响应消息
        """
        future = asyncio.Future()
        self.pending_responses[correlation_id] = future
        
        try:
            # 等待响应，设置超时
            response = await asyncio.wait_for(
                future, 
                timeout=self.config.response_timeout
            )
            return response
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Response timeout for correlation_id {correlation_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for response: {e}")
            return None
        finally:
            # 清理待处理的响应
            self.pending_responses.pop(correlation_id, None)
    
    def get_pending_response_count(self) -> int:
        """获取待处理响应数量"""
        return len(self.pending_responses)
    
    def get_handler_count(self) -> int:
        """获取注册的处理器数量"""
        return len(self.message_handlers)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        return {
            "agent_id": self.agent_id,
            "queue_initialized": self.queue is not None,
            "consumer_running": self._consumer_task and not self._consumer_task.done(),
            "pending_responses": len(self.pending_responses),
            "registered_handlers": len(self.message_handlers)
        }