"""
Agent基础框架

提供BaseAgent抽象类和核心数据结构，基于LangGraph框架构建Agent工作流。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import logging
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class MessageType(str, Enum):
    """消息类型枚举"""
    TASK = "task"
    RESPONSE = "response"
    COLLABORATION = "collaboration"
    STATUS = "status"
    ERROR = "error"


class AgentMessage(BaseModel):
    """Agent消息模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    sender_id: str
    receiver_id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # 用于关联请求和响应


class AgentResponse(BaseModel):
    """Agent响应模型"""
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    suggestions: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    collaboration_needed: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentCapability(BaseModel):
    """Agent能力描述"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class AgentState(BaseModel):
    """Agent状态模型"""
    agent_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    working_memory: Dict[str, Any] = Field(default_factory=dict)
    conversation_context: Dict[str, Any] = Field(default_factory=dict)
    knowledge_cache: List[Dict[str, Any]] = Field(default_factory=list)
    collaboration_state: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    last_active: datetime = Field(default_factory=datetime.now)
    error_count: int = 0
    max_errors: int = 5


class BaseAgent(ABC):
    """
    基础Agent抽象类
    
    基于LangGraph框架构建，提供Agent的核心功能和工作流管理。
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        specialty: str,
        capabilities: Optional[List[AgentCapability]] = None,
        state_manager: Optional['AgentStateManager'] = None,
        communicator: Optional['AgentCommunicator'] = None
    ):
        self.id = agent_id
        self.name = name
        self.specialty = specialty
        self.capabilities = capabilities or []
        self.state_manager = state_manager
        self.communicator = communicator
        
        # 初始化状态
        self.state = AgentState(agent_id=agent_id)
        
        # 创建LangGraph工作流
        self.workflow = self._create_workflow()
        
        # 日志记录器
        self.logger = logging.getLogger(f"agent.{self.name}")
        
        self.logger.info(f"Agent {self.name} ({self.id}) initialized with specialty: {self.specialty}")
    
    def _create_workflow(self) -> StateGraph:
        """创建LangGraph工作流"""
        workflow = StateGraph(dict)
        
        # 添加节点
        workflow.add_node("process_input", self._process_input_node)
        workflow.add_node("analyze_task", self._analyze_task_node)
        workflow.add_node("execute_task", self._execute_task_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("handle_collaboration", self._handle_collaboration_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # 设置入口点
        workflow.set_entry_point("process_input")
        
        # 添加边
        workflow.add_edge("process_input", "analyze_task")
        workflow.add_conditional_edges(
            "analyze_task",
            self._should_collaborate,
            {
                "collaborate": "handle_collaboration",
                "execute": "execute_task",
                "error": "handle_error"
            }
        )
        workflow.add_edge("execute_task", "generate_response")
        workflow.add_edge("handle_collaboration", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _process_input_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入节点"""
        try:
            message = state.get("message")
            if not message:
                raise ValueError("No message provided")
            
            self.logger.debug(f"Processing input: {message.content[:100]}...")
            
            # 更新Agent状态
            self.state.status = AgentStatus.BUSY
            self.state.current_task = message.content
            self.state.last_active = datetime.now()
            
            # 保存状态
            if self.state_manager:
                await self.state_manager.save_state(self.id, self.state)
            
            state["processed_message"] = message
            state["agent_id"] = self.id
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            state["error"] = str(e)
            return state
    
    async def _analyze_task_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """分析任务节点"""
        try:
            message = state.get("processed_message")
            if not message:
                raise ValueError("No processed message found")
            
            # 调用子类实现的任务分析方法
            analysis = await self.analyze_task(message)
            state["task_analysis"] = analysis
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error analyzing task: {e}")
            state["error"] = str(e)
            return state
    
    async def _execute_task_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务节点"""
        try:
            message = state.get("processed_message")
            analysis = state.get("task_analysis")
            
            if not message or not analysis:
                raise ValueError("Missing message or task analysis")
            
            # 调用子类实现的任务执行方法
            result = await self.execute_task(message, analysis)
            state["task_result"] = result
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            state["error"] = str(e)
            return state
    
    async def _generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成响应节点"""
        try:
            result = state.get("task_result")
            collaboration_result = state.get("collaboration_result")
            
            # 调用子类实现的响应生成方法
            response = await self.generate_response(result, collaboration_result)
            state["response"] = response
            
            # 更新Agent状态
            self.state.status = AgentStatus.IDLE
            self.state.current_task = None
            self.state.last_active = datetime.now()
            
            # 保存状态
            if self.state_manager:
                await self.state_manager.save_state(self.id, self.state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            state["error"] = str(e)
            return state
    
    async def _handle_collaboration_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理协作节点"""
        try:
            message = state.get("processed_message")
            analysis = state.get("task_analysis")
            
            if not message or not analysis:
                raise ValueError("Missing message or task analysis")
            
            # 调用子类实现的协作处理方法
            collaboration_result = await self.handle_collaboration(message, analysis)
            state["collaboration_result"] = collaboration_result
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error handling collaboration: {e}")
            state["error"] = str(e)
            return state
    
    async def _handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理错误节点"""
        error = state.get("error", "Unknown error")
        self.logger.error(f"Agent {self.name} encountered error: {error}")
        
        # 更新错误计数
        self.state.error_count += 1
        self.state.status = AgentStatus.ERROR if self.state.error_count >= self.state.max_errors else AgentStatus.IDLE
        self.state.last_active = datetime.now()
        
        # 保存状态
        if self.state_manager:
            await self.state_manager.save_state(self.id, self.state)
        
        # 生成错误响应
        state["response"] = AgentResponse(
            content=f"抱歉，处理您的请求时遇到了问题：{error}",
            confidence=0.0,
            suggestions=["请稍后重试", "联系系统管理员"],
            metadata={"error": error, "error_count": self.state.error_count}
        )
        
        return state
    
    def _should_collaborate(self, state: Dict[str, Any]) -> str:
        """判断是否需要协作"""
        if state.get("error"):
            return "error"
        
        analysis = state.get("task_analysis", {})
        if analysis.get("needs_collaboration", False):
            return "collaborate"
        
        return "execute"
    
    async def process_message(self, message: AgentMessage) -> AgentResponse:
        """
        处理消息的主要入口点
        
        Args:
            message: 输入消息
            
        Returns:
            Agent响应
        """
        try:
            # 运行工作流
            result = await self.workflow.ainvoke({
                "message": message,
                "agent_state": self.state.dict()
            })
            
            response = result.get("response")
            if not response:
                raise ValueError("No response generated")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return AgentResponse(
                content=f"处理消息时发生错误：{str(e)}",
                confidence=0.0,
                suggestions=["请检查输入格式", "稍后重试"],
                metadata={"error": str(e)}
            )
    
    @abstractmethod
    async def analyze_task(self, message: AgentMessage) -> Dict[str, Any]:
        """
        分析任务
        
        Args:
            message: 输入消息
            
        Returns:
            任务分析结果
        """
        pass
    
    @abstractmethod
    async def execute_task(self, message: AgentMessage, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            message: 输入消息
            analysis: 任务分析结果
            
        Returns:
            任务执行结果
        """
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        task_result: Optional[Dict[str, Any]] = None,
        collaboration_result: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        生成响应
        
        Args:
            task_result: 任务执行结果
            collaboration_result: 协作结果
            
        Returns:
            Agent响应
        """
        pass
    
    async def handle_collaboration(
        self, 
        message: AgentMessage, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理协作（默认实现）
        
        Args:
            message: 输入消息
            analysis: 任务分析结果
            
        Returns:
            协作结果
        """
        if not self.communicator:
            self.logger.warning("No communicator available for collaboration")
            return {"error": "Collaboration not available"}
        
        # 获取需要协作的Agent列表
        required_agents = analysis.get("required_agents", [])
        if not required_agents:
            return {"error": "No required agents specified"}
        
        # 发送协作请求
        collaboration_results = []
        for agent_id in required_agents:
            try:
                collab_message = AgentMessage(
                    type=MessageType.COLLABORATION,
                    sender_id=self.id,
                    receiver_id=agent_id,
                    content=message.content,
                    metadata={
                        "original_message_id": message.id,
                        "collaboration_type": analysis.get("collaboration_type", "general")
                    },
                    correlation_id=message.id
                )
                
                result = await self.communicator.send_message(collab_message)
                collaboration_results.append({
                    "agent_id": agent_id,
                    "result": result
                })
                
            except Exception as e:
                self.logger.error(f"Error collaborating with agent {agent_id}: {e}")
                collaboration_results.append({
                    "agent_id": agent_id,
                    "error": str(e)
                })
        
        return {
            "collaboration_results": collaboration_results,
            "success": len([r for r in collaboration_results if "error" not in r]) > 0
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """获取Agent能力列表"""
        return self.capabilities
    
    def add_capability(self, capability: AgentCapability) -> None:
        """添加Agent能力"""
        self.capabilities.append(capability)
        self.logger.info(f"Added capability: {capability.name}")
    
    def remove_capability(self, capability_name: str) -> bool:
        """移除Agent能力"""
        for i, cap in enumerate(self.capabilities):
            if cap.name == capability_name:
                del self.capabilities[i]
                self.logger.info(f"Removed capability: {capability_name}")
                return True
        return False
    
    def get_state(self) -> AgentState:
        """获取Agent状态"""
        return self.state
    
    async def update_state(self, **kwargs) -> None:
        """更新Agent状态"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        
        self.state.last_active = datetime.now()
        
        # 保存状态
        if self.state_manager:
            await self.state_manager.save_state(self.id, self.state)
    
    async def reset_state(self) -> None:
        """重置Agent状态"""
        self.state = AgentState(agent_id=self.id)
        
        if self.state_manager:
            await self.state_manager.save_state(self.id, self.state)
        
        self.logger.info(f"Agent {self.name} state reset")
    
    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return (
            self.state.status in [AgentStatus.IDLE, AgentStatus.BUSY] and
            self.state.error_count < self.state.max_errors
        )
    
    def __str__(self) -> str:
        return f"Agent({self.name}, {self.specialty}, {self.state.status})"
    
    def __repr__(self) -> str:
        return f"Agent(id={self.id}, name={self.name}, specialty={self.specialty}, status={self.state.status})"