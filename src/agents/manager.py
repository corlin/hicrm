"""
Agent管理器

负责Agent的生命周期管理、任务分发和协作协调。
"""

import asyncio
from typing import Dict, List, Optional, Type, Any, Callable
from datetime import datetime, timedelta
import logging
import uuid

from .base import BaseAgent, AgentMessage, AgentResponse, MessageType, AgentStatus, AgentCapability
from .state_manager import AgentStateManager, StateManagerConfig
from .communication import MessageBroker, AgentCommunicator, CommunicationConfig


logger = logging.getLogger(__name__)


class AgentRegistration:
    """Agent注册信息"""
    
    def __init__(
        self,
        agent_class: Type[BaseAgent],
        agent_id: str,
        name: str,
        specialty: str,
        capabilities: List[AgentCapability],
        auto_start: bool = True
    ):
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.name = name
        self.specialty = specialty
        self.capabilities = capabilities
        self.auto_start = auto_start
        self.instance: Optional[BaseAgent] = None
        self.communicator: Optional[AgentCommunicator] = None


class TaskAssignment:
    """任务分配"""
    
    def __init__(
        self,
        task_id: str,
        message: AgentMessage,
        assigned_agents: List[str],
        created_at: datetime,
        timeout: Optional[datetime] = None
    ):
        self.task_id = task_id
        self.message = message
        self.assigned_agents = assigned_agents
        self.created_at = created_at
        self.timeout = timeout or (created_at + timedelta(minutes=5))
        self.responses: Dict[str, AgentResponse] = {}
        self.completed = False


class AgentManager:
    """
    Agent管理器
    
    负责Agent的注册、启动、停止、任务分发和协作协调。
    """
    
    def __init__(
        self,
        state_config: Optional[StateManagerConfig] = None,
        comm_config: Optional[CommunicationConfig] = None
    ):
        self.state_manager = AgentStateManager(state_config)
        self.message_broker = MessageBroker(comm_config)
        
        # Agent注册表
        self.registrations: Dict[str, AgentRegistration] = {}
        self.running_agents: Dict[str, BaseAgent] = {}
        
        # 任务管理
        self.active_tasks: Dict[str, TaskAssignment] = {}
        
        # 能力索引
        self.capability_index: Dict[str, List[str]] = {}  # capability_name -> [agent_ids]
        
        self.logger = logging.getLogger(__name__)
        self._task_cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """初始化Agent管理器"""
        try:
            # 初始化状态管理器
            await self.state_manager.initialize()
            
            # 初始化消息代理
            await self.message_broker.initialize()
            
            # 启动任务清理
            self._task_cleanup_task = asyncio.create_task(self._cleanup_expired_tasks())
            
            self.logger.info("Agent manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent manager: {e}")
            raise
    
    async def close(self) -> None:
        """关闭Agent管理器"""
        # 停止所有Agent
        await self.stop_all_agents()
        
        # 停止任务清理
        if self._task_cleanup_task:
            self._task_cleanup_task.cancel()
            try:
                await self._task_cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 关闭状态管理器和消息代理
        await self.state_manager.close()
        await self.message_broker.close()
        
        self.logger.info("Agent manager closed")
    
    def register_agent(
        self,
        agent_class: Type[BaseAgent],
        agent_id: str,
        name: str,
        specialty: str,
        capabilities: List[AgentCapability],
        auto_start: bool = True
    ) -> None:
        """
        注册Agent
        
        Args:
            agent_class: Agent类
            agent_id: Agent ID
            name: Agent名称
            specialty: 专业领域
            capabilities: 能力列表
            auto_start: 是否自动启动
        """
        if agent_id in self.registrations:
            raise ValueError(f"Agent {agent_id} already registered")
        
        registration = AgentRegistration(
            agent_class=agent_class,
            agent_id=agent_id,
            name=name,
            specialty=specialty,
            capabilities=capabilities,
            auto_start=auto_start
        )
        
        self.registrations[agent_id] = registration
        
        # 更新能力索引
        for capability in capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = []
            self.capability_index[capability.name].append(agent_id)
        
        self.logger.info(f"Registered agent {name} ({agent_id}) with specialty: {specialty}")
    
    async def start_agent(self, agent_id: str) -> bool:
        """
        启动Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功启动
        """
        if agent_id not in self.registrations:
            self.logger.error(f"Agent {agent_id} not registered")
            return False
        
        if agent_id in self.running_agents:
            self.logger.warning(f"Agent {agent_id} already running")
            return True
        
        try:
            registration = self.registrations[agent_id]
            
            # 创建通信器
            communicator = AgentCommunicator(agent_id, self.message_broker)
            await communicator.initialize()
            
            # 创建Agent实例
            agent = registration.agent_class(
                agent_id=agent_id,
                name=registration.name,
                specialty=registration.specialty,
                capabilities=registration.capabilities,
                state_manager=self.state_manager,
                communicator=communicator
            )
            
            # 注册消息处理器
            communicator.register_handler(MessageType.TASK, agent.process_message)
            communicator.register_handler(MessageType.COLLABORATION, agent.process_message)
            
            # 保存引用
            registration.instance = agent
            registration.communicator = communicator
            self.running_agents[agent_id] = agent
            
            # 更新状态
            await agent.update_state(status=AgentStatus.IDLE)
            
            self.logger.info(f"Started agent {registration.name} ({agent_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start agent {agent_id}: {e}")
            return False
    
    async def stop_agent(self, agent_id: str) -> bool:
        """
        停止Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功停止
        """
        if agent_id not in self.running_agents:
            self.logger.warning(f"Agent {agent_id} not running")
            return True
        
        try:
            agent = self.running_agents[agent_id]
            registration = self.registrations[agent_id]
            
            # 更新状态
            await agent.update_state(status=AgentStatus.OFFLINE)
            
            # 关闭通信器
            if registration.communicator:
                await registration.communicator.close()
                registration.communicator = None
            
            # 清理引用
            registration.instance = None
            del self.running_agents[agent_id]
            
            self.logger.info(f"Stopped agent {agent.name} ({agent_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent {agent_id}: {e}")
            return False
    
    async def start_all_agents(self) -> Dict[str, bool]:
        """
        启动所有注册的Agent
        
        Returns:
            启动结果字典
        """
        results = {}
        
        for agent_id, registration in self.registrations.items():
            if registration.auto_start:
                results[agent_id] = await self.start_agent(agent_id)
        
        return results
    
    async def stop_all_agents(self) -> Dict[str, bool]:
        """
        停止所有运行中的Agent
        
        Returns:
            停止结果字典
        """
        results = {}
        
        for agent_id in list(self.running_agents.keys()):
            results[agent_id] = await self.stop_agent(agent_id)
        
        return results
    
    async def send_message_to_agent(
        self, 
        agent_id: str, 
        message: AgentMessage
    ) -> Optional[AgentResponse]:
        """
        向指定Agent发送消息
        
        Args:
            agent_id: 目标Agent ID
            message: 消息
            
        Returns:
            Agent响应
        """
        if agent_id not in self.running_agents:
            self.logger.error(f"Agent {agent_id} not running")
            return None
        
        try:
            agent = self.running_agents[agent_id]
            return await agent.process_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending message to agent {agent_id}: {e}")
            return None
    
    async def assign_task(
        self,
        message: AgentMessage,
        required_capabilities: Optional[List[str]] = None,
        preferred_agents: Optional[List[str]] = None,
        max_agents: int = 1
    ) -> str:
        """
        分配任务给合适的Agent
        
        Args:
            message: 任务消息
            required_capabilities: 必需的能力列表
            preferred_agents: 首选Agent列表
            max_agents: 最大Agent数量
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        # 选择合适的Agent
        selected_agents = await self._select_agents(
            required_capabilities,
            preferred_agents,
            max_agents
        )
        
        if not selected_agents:
            self.logger.error("No suitable agents found for task")
            raise ValueError("No suitable agents available")
        
        # 创建任务分配
        task_assignment = TaskAssignment(
            task_id=task_id,
            message=message,
            assigned_agents=selected_agents,
            created_at=datetime.now()
        )
        
        self.active_tasks[task_id] = task_assignment
        
        # 发送任务给选中的Agent
        for agent_id in selected_agents:
            try:
                task_message = AgentMessage(
                    type=MessageType.TASK,
                    sender_id="manager",
                    receiver_id=agent_id,
                    content=message.content,
                    metadata={
                        "task_id": task_id,
                        "original_message_id": message.id
                    },
                    correlation_id=task_id
                )
                
                registration = self.registrations[agent_id]
                if registration.communicator:
                    await registration.communicator.send_message(task_message)
                
            except Exception as e:
                self.logger.error(f"Error sending task to agent {agent_id}: {e}")
        
        self.logger.info(f"Assigned task {task_id} to agents: {selected_agents}")
        return task_id
    
    async def _select_agents(
        self,
        required_capabilities: Optional[List[str]] = None,
        preferred_agents: Optional[List[str]] = None,
        max_agents: int = 1
    ) -> List[str]:
        """选择合适的Agent"""
        candidates = []
        
        # 如果指定了首选Agent，优先考虑
        if preferred_agents:
            for agent_id in preferred_agents:
                if agent_id in self.running_agents:
                    agent = self.running_agents[agent_id]
                    if agent.is_available():
                        candidates.append(agent_id)
        
        # 如果需要特定能力，从能力索引中查找
        if required_capabilities and not candidates:
            capability_agents = set()
            
            for capability in required_capabilities:
                if capability in self.capability_index:
                    capability_agents.update(self.capability_index[capability])
            
            # 过滤可用的Agent
            for agent_id in capability_agents:
                if agent_id in self.running_agents:
                    agent = self.running_agents[agent_id]
                    if agent.is_available():
                        candidates.append(agent_id)
        
        # 如果还没有候选者，选择所有可用的Agent
        if not candidates:
            for agent_id, agent in self.running_agents.items():
                if agent.is_available():
                    candidates.append(agent_id)
        
        # 根据负载和性能排序
        candidates = await self._rank_agents(candidates)
        
        # 返回前max_agents个
        return candidates[:max_agents]
    
    async def _rank_agents(self, agent_ids: List[str]) -> List[str]:
        """根据负载和性能对Agent排序"""
        agent_scores = []
        
        for agent_id in agent_ids:
            try:
                state = await self.state_manager.load_state(agent_id)
                if not state:
                    continue
                
                # 计算分数（越低越好）
                score = 0
                
                # 错误计数权重
                score += state.error_count * 10
                
                # 状态权重
                if state.status == AgentStatus.BUSY:
                    score += 5
                elif state.status == AgentStatus.ERROR:
                    score += 100
                
                # 性能指标权重
                avg_response_time = state.performance_metrics.get("avg_response_time", 1.0)
                score += avg_response_time
                
                agent_scores.append((agent_id, score))
                
            except Exception as e:
                self.logger.error(f"Error ranking agent {agent_id}: {e}")
                agent_scores.append((agent_id, 1000))  # 高分数表示不可用
        
        # 按分数排序
        agent_scores.sort(key=lambda x: x[1])
        
        return [agent_id for agent_id, _ in agent_scores]
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        if task_id not in self.active_tasks:
            return None
        
        task = self.active_tasks[task_id]
        
        return {
            "task_id": task_id,
            "assigned_agents": task.assigned_agents,
            "created_at": task.created_at,
            "timeout": task.timeout,
            "completed": task.completed,
            "response_count": len(task.responses),
            "responses": {
                agent_id: response.dict() 
                for agent_id, response in task.responses.items()
            }
        }
    
    async def _cleanup_expired_tasks(self) -> None:
        """清理过期任务"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                now = datetime.now()
                expired_tasks = []
                
                for task_id, task in self.active_tasks.items():
                    if now > task.timeout:
                        expired_tasks.append(task_id)
                
                # 清理过期任务
                for task_id in expired_tasks:
                    del self.active_tasks[task_id]
                    self.logger.info(f"Cleaned up expired task {task_id}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error during task cleanup: {e}")
    
    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """获取已注册的Agent信息"""
        return {
            agent_id: {
                "name": reg.name,
                "specialty": reg.specialty,
                "capabilities": [cap.dict() for cap in reg.capabilities],
                "auto_start": reg.auto_start,
                "running": agent_id in self.running_agents
            }
            for agent_id, reg in self.registrations.items()
        }
    
    def get_running_agents(self) -> Dict[str, Dict[str, Any]]:
        """获取运行中的Agent信息"""
        result = {}
        
        for agent_id, agent in self.running_agents.items():
            state = agent.get_state()
            result[agent_id] = {
                "name": agent.name,
                "specialty": agent.specialty,
                "status": state.status,
                "current_task": state.current_task,
                "error_count": state.error_count,
                "last_active": state.last_active,
                "available": agent.is_available()
            }
        
        return result
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        # 获取Agent指标
        agent_metrics = await self.state_manager.get_system_metrics()
        
        # 获取消息代理状态
        broker_health = await self.message_broker.health_check()
        
        # 获取状态管理器状态
        state_health = await self.state_manager.health_check()
        
        return {
            "registered_agents": len(self.registrations),
            "running_agents": len(self.running_agents),
            "active_tasks": len(self.active_tasks),
            "agent_metrics": agent_metrics,
            "message_broker": broker_health,
            "state_manager": state_health,
            "capabilities": list(self.capability_index.keys())
        }