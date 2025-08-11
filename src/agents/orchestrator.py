"""
Agent任务编排器

使用LangGraph StateGraph实现Multi-Agent协作模式，支持Sequential、Parallel、Hierarchical等协作模式。
"""

import asyncio
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid
import logging

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from .base import BaseAgent, AgentMessage, AgentResponse, MessageType, AgentStatus
from .manager import AgentManager


logger = logging.getLogger(__name__)


class CollaborationMode(str, Enum):
    """协作模式枚举"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    HIERARCHICAL = "hierarchical"  # 层次化执行
    PIPELINE = "pipeline"          # 流水线执行
    CONSENSUS = "consensus"        # 共识决策


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(BaseModel):
    """Agent在协作中的角色"""
    agent_id: str
    role_name: str
    responsibilities: List[str]
    dependencies: List[str] = Field(default_factory=list)  # 依赖的其他Agent
    weight: float = 1.0  # 在决策中的权重
    required: bool = True  # 是否必需


class CollaborationTask(BaseModel):
    """协作任务模型"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    mode: CollaborationMode
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    
    # 参与的Agent角色
    agent_roles: List[AgentRole]
    
    # 任务输入和输出
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    
    # 时间管理
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout: Optional[datetime] = None
    
    # 执行结果
    results: Dict[str, Any] = Field(default_factory=dict)  # agent_id -> result
    errors: Dict[str, str] = Field(default_factory=dict)   # agent_id -> error
    
    # 协作配置
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """工作流状态"""
    task: CollaborationTask
    current_step: int = 0
    agent_states: Dict[str, Any] = Field(default_factory=dict)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    messages: List[AgentMessage] = Field(default_factory=list)
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    error_count: int = 0
    max_errors: int = 5


class AgentOrchestrator:
    """
    Agent任务编排器
    
    使用LangGraph StateGraph实现Multi-Agent协作工作流编排。
    """
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.active_tasks: Dict[str, CollaborationTask] = {}
        self.workflows: Dict[str, StateGraph] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_collaboration_task(
        self,
        name: str,
        description: str,
        mode: CollaborationMode,
        agent_roles: List[AgentRole],
        input_data: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_minutes: Optional[int] = None,
        config: Dict[str, Any] = None
    ) -> CollaborationTask:
        """
        创建协作任务
        
        Args:
            name: 任务名称
            description: 任务描述
            mode: 协作模式
            agent_roles: 参与的Agent角色
            input_data: 输入数据
            priority: 任务优先级
            timeout_minutes: 超时时间（分钟）
            config: 协作配置
            
        Returns:
            协作任务对象
        """
        timeout = None
        if timeout_minutes:
            timeout = datetime.now() + timedelta(minutes=timeout_minutes)
        
        task = CollaborationTask(
            name=name,
            description=description,
            mode=mode,
            agent_roles=agent_roles,
            input_data=input_data or {},
            priority=priority,
            timeout=timeout,
            config=config or {}
        )
        
        self.active_tasks[task.task_id] = task
        self.logger.info(f"Created collaboration task {task.name} ({task.task_id}) with mode {mode}")
        
        return task
    
    def _create_sequential_workflow(self, task: CollaborationTask) -> StateGraph:
        """创建顺序执行工作流"""
        workflow = StateGraph(dict)
        
        # 添加初始化节点
        workflow.add_node("initialize", self._initialize_task)
        
        # 为每个Agent添加执行节点
        for i, role in enumerate(task.agent_roles):
            node_name = f"execute_{role.agent_id}_{i}"
            workflow.add_node(node_name, self._create_agent_executor(role))
        
        # 添加结果聚合节点
        workflow.add_node("aggregate", self._aggregate_results)
        workflow.add_node("finalize", self._finalize_task)
        workflow.add_node("handle_error", self._handle_error)
        
        # 设置入口点
        workflow.set_entry_point("initialize")
        
        # 添加顺序执行的边
        workflow.add_edge("initialize", f"execute_{task.agent_roles[0].agent_id}_0")
        
        for i in range(len(task.agent_roles) - 1):
            current_node = f"execute_{task.agent_roles[i].agent_id}_{i}"
            next_node = f"execute_{task.agent_roles[i+1].agent_id}_{i+1}"
            
            workflow.add_conditional_edges(
                current_node,
                self._check_execution_result,
                {
                    "continue": next_node,
                    "error": "handle_error"
                }
            )
        
        # 最后一个Agent执行完成后聚合结果
        last_node = f"execute_{task.agent_roles[-1].agent_id}_{len(task.agent_roles)-1}"
        workflow.add_conditional_edges(
            last_node,
            self._check_execution_result,
            {
                "continue": "aggregate",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("aggregate", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _create_parallel_workflow(self, task: CollaborationTask) -> StateGraph:
        """创建并行执行工作流"""
        workflow = StateGraph(dict)
        
        # 添加初始化节点
        workflow.add_node("initialize", self._initialize_task)
        
        # 添加并行执行节点（在一个节点中并行执行所有Agent）
        workflow.add_node("execute_parallel", self._execute_parallel_agents)
        
        # 添加结果聚合节点
        workflow.add_node("aggregate", self._aggregate_results)
        workflow.add_node("finalize", self._finalize_task)
        workflow.add_node("handle_error", self._handle_error)
        
        # 设置入口点
        workflow.set_entry_point("initialize")
        
        # 添加边
        workflow.add_edge("initialize", "execute_parallel")
        
        workflow.add_conditional_edges(
            "execute_parallel",
            self._check_parallel_execution,
            {
                "completed": "aggregate",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("aggregate", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _create_hierarchical_workflow(self, task: CollaborationTask) -> StateGraph:
        """创建层次化执行工作流"""
        workflow = StateGraph(dict)
        
        # 添加初始化节点
        workflow.add_node("initialize", self._initialize_task)
        
        # 按依赖关系分层
        layers = self._build_dependency_layers(task.agent_roles)
        
        # 为每层添加执行节点
        for layer_idx, layer_agents in enumerate(layers):
            layer_name = f"layer_{layer_idx}"
            workflow.add_node(layer_name, self._create_layer_executor(layer_agents))
        
        # 添加结果聚合节点
        workflow.add_node("aggregate", self._aggregate_results)
        workflow.add_node("finalize", self._finalize_task)
        workflow.add_node("handle_error", self._handle_error)
        
        # 设置入口点
        workflow.set_entry_point("initialize")
        
        # 连接层次执行
        if layers:
            workflow.add_edge("initialize", "layer_0")
            
            for i in range(len(layers) - 1):
                current_layer = f"layer_{i}"
                next_layer = f"layer_{i+1}"
                
                workflow.add_conditional_edges(
                    current_layer,
                    self._check_layer_result,
                    {
                        "continue": next_layer,
                        "error": "handle_error"
                    }
                )
            
            # 最后一层完成后聚合结果
            last_layer = f"layer_{len(layers)-1}"
            workflow.add_conditional_edges(
                last_layer,
                self._check_layer_result,
                {
                    "continue": "aggregate",
                    "error": "handle_error"
                }
            )
        
        workflow.add_edge("aggregate", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _create_pipeline_workflow(self, task: CollaborationTask) -> StateGraph:
        """创建流水线执行工作流"""
        workflow = StateGraph(dict)
        
        # 添加初始化节点
        workflow.add_node("initialize", self._initialize_task)
        
        # 为每个Agent添加流水线节点
        for i, role in enumerate(task.agent_roles):
            node_name = f"pipeline_{role.agent_id}_{i}"
            workflow.add_node(node_name, self._create_pipeline_executor(role, i))
        
        # 添加结果聚合节点
        workflow.add_node("aggregate", self._aggregate_results)
        workflow.add_node("finalize", self._finalize_task)
        workflow.add_node("handle_error", self._handle_error)
        
        # 设置入口点
        workflow.set_entry_point("initialize")
        
        # 添加流水线执行的边
        workflow.add_edge("initialize", f"pipeline_{task.agent_roles[0].agent_id}_0")
        
        for i in range(len(task.agent_roles) - 1):
            current_node = f"pipeline_{task.agent_roles[i].agent_id}_{i}"
            next_node = f"pipeline_{task.agent_roles[i+1].agent_id}_{i+1}"
            
            workflow.add_conditional_edges(
                current_node,
                self._check_pipeline_result,
                {
                    "continue": next_node,
                    "error": "handle_error"
                }
            )
        
        # 最后一个Agent执行完成后聚合结果
        last_node = f"pipeline_{task.agent_roles[-1].agent_id}_{len(task.agent_roles)-1}"
        workflow.add_conditional_edges(
            last_node,
            self._check_pipeline_result,
            {
                "continue": "aggregate",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("aggregate", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _create_consensus_workflow(self, task: CollaborationTask) -> StateGraph:
        """创建共识决策工作流"""
        workflow = StateGraph(dict)
        
        # 添加初始化节点
        workflow.add_node("initialize", self._initialize_task)
        
        # 添加并行执行节点（在一个节点中并行执行所有Agent）
        workflow.add_node("execute_consensus_agents", self._execute_consensus_agents)
        
        # 添加共识决策节点
        workflow.add_node("consensus", self._build_consensus)
        workflow.add_node("finalize", self._finalize_task)
        workflow.add_node("handle_error", self._handle_error)
        
        # 设置入口点
        workflow.set_entry_point("initialize")
        
        # 添加边
        workflow.add_edge("initialize", "execute_consensus_agents")
        
        workflow.add_conditional_edges(
            "execute_consensus_agents",
            self._check_consensus_execution,
            {
                "completed": "consensus",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "consensus",
            self._check_consensus_result,
            {
                "consensus_reached": "finalize",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _build_dependency_layers(self, agent_roles: List[AgentRole]) -> List[List[AgentRole]]:
        """构建依赖层次"""
        layers = []
        remaining_roles = agent_roles.copy()
        processed_agents = set()
        
        while remaining_roles:
            current_layer = []
            
            # 找到没有未处理依赖的Agent
            for role in remaining_roles[:]:
                # 检查是否所有依赖都已处理
                if not role.dependencies or all(dep in processed_agents for dep in role.dependencies):
                    current_layer.append(role)
            
            # 从剩余角色中移除当前层的角色，并标记为已处理
            for role in current_layer:
                remaining_roles.remove(role)
                processed_agents.add(role.agent_id)
            
            if not current_layer:
                # 如果没有找到可执行的Agent，说明存在循环依赖
                self.logger.error("Circular dependency detected in agent roles")
                # 将剩余的Agent放入一层，忽略依赖
                current_layer = remaining_roles.copy()
                remaining_roles = []
            
            if current_layer:  # 只有当层不为空时才添加
                layers.append(current_layer)
        
        return layers
    
    def _create_agent_executor(self, role: AgentRole) -> Callable:
        """创建Agent执行器"""
        async def executor(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                workflow_state = WorkflowState(**state)
                task = workflow_state.task
                
                self.logger.debug(f"Executing agent {role.agent_id} for task {task.task_id}")
                
                # 创建Agent消息
                message = AgentMessage(
                    type=MessageType.TASK,
                    sender_id="orchestrator",
                    receiver_id=role.agent_id,
                    content=task.description,
                    metadata={
                        "task_id": task.task_id,
                        "role": role.role_name,
                        "responsibilities": role.responsibilities,
                        "input_data": task.input_data,
                        "shared_context": workflow_state.shared_context
                    }
                )
                
                # 发送消息给Agent
                response = await self.agent_manager.send_message_to_agent(role.agent_id, message)
                
                if response:
                    # 保存结果
                    workflow_state.intermediate_results[role.agent_id] = {
                        "response": response.model_dump(),
                        "timestamp": datetime.now(),
                        "success": True
                    }
                    
                    # 更新共享上下文
                    if response.metadata:
                        workflow_state.shared_context.update(response.metadata)
                    
                    self.logger.info(f"Agent {role.agent_id} completed successfully")
                else:
                    # 执行失败
                    error_msg = f"Agent {role.agent_id} failed to respond"
                    workflow_state.intermediate_results[role.agent_id] = {
                        "error": error_msg,
                        "timestamp": datetime.now(),
                        "success": False
                    }
                    workflow_state.error_count += 1
                    
                    self.logger.error(error_msg)
                
                return workflow_state.model_dump()
                
            except Exception as e:
                self.logger.error(f"Error executing agent {role.agent_id}: {e}")
                workflow_state = WorkflowState(**state)
                workflow_state.intermediate_results[role.agent_id] = {
                    "error": str(e),
                    "timestamp": datetime.now(),
                    "success": False
                }
                workflow_state.error_count += 1
                return workflow_state.model_dump()
        
        return executor
    
    def _create_layer_executor(self, layer_agents: List[AgentRole]) -> Callable:
        """创建层执行器（并行执行一层中的所有Agent）"""
        async def layer_executor(state: Dict[str, Any]) -> Dict[str, Any]:
            workflow_state = WorkflowState(**state)
            
            # 并行执行层中的所有Agent
            tasks = []
            for role in layer_agents:
                executor = self._create_agent_executor(role)
                tasks.append(executor(state))
            
            # 等待所有Agent完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    role = layer_agents[i]
                    workflow_state.intermediate_results[role.agent_id] = {
                        "error": str(result),
                        "timestamp": datetime.now(),
                        "success": False
                    }
                    workflow_state.error_count += 1
                elif isinstance(result, dict):
                    # 合并状态
                    result_state = WorkflowState(**result)
                    workflow_state.intermediate_results.update(result_state.intermediate_results)
                    workflow_state.shared_context.update(result_state.shared_context)
                    workflow_state.error_count += result_state.error_count
            
            return workflow_state.model_dump()
        
        return layer_executor
    
    def _create_pipeline_executor(self, role: AgentRole, stage: int) -> Callable:
        """创建流水线执行器"""
        async def pipeline_executor(state: Dict[str, Any]) -> Dict[str, Any]:
            workflow_state = WorkflowState(**state)
            
            # 获取前一阶段的输出作为输入
            if stage > 0:
                prev_agent_id = workflow_state.task.agent_roles[stage - 1].agent_id
                prev_result = workflow_state.intermediate_results.get(prev_agent_id)
                if prev_result and prev_result.get("success"):
                    # 将前一阶段的输出添加到输入数据中
                    workflow_state.task.input_data[f"stage_{stage-1}_output"] = prev_result["response"]
            
            # 执行当前Agent
            executor = self._create_agent_executor(role)
            return await executor(workflow_state.model_dump())
        
        return pipeline_executor
    
    async def _initialize_task(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """初始化任务"""
        workflow_state = WorkflowState(**state)
        task = workflow_state.task
        
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        self.logger.info(f"Initialized collaboration task {task.name} ({task.task_id})")
        
        return workflow_state.model_dump()
    
    async def _aggregate_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """聚合结果"""
        workflow_state = WorkflowState(**state)
        task = workflow_state.task
        
        # 聚合所有Agent的结果
        aggregated_results = {}
        successful_agents = []
        failed_agents = []
        
        for agent_id, result in workflow_state.intermediate_results.items():
            if result.get("success"):
                aggregated_results[agent_id] = result["response"]
                successful_agents.append(agent_id)
            else:
                failed_agents.append(agent_id)
        
        # 更新任务结果
        task.results = aggregated_results
        task.output_data = {
            "aggregated_results": aggregated_results,
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "success_rate": len(successful_agents) / len(workflow_state.intermediate_results) if workflow_state.intermediate_results else 0
        }
        
        self.logger.info(f"Aggregated results for task {task.task_id}: {len(successful_agents)} successful, {len(failed_agents)} failed")
        
        return workflow_state.model_dump()
    
    async def _finalize_task(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """完成任务"""
        workflow_state = WorkflowState(**state)
        task = workflow_state.task
        
        # 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        self.logger.info(f"Finalized collaboration task {task.name} ({task.task_id})")
        
        return workflow_state.model_dump()
    
    async def _handle_error(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理错误"""
        workflow_state = WorkflowState(**state)
        task = workflow_state.task
        
        # 更新任务状态
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        
        # 收集错误信息
        errors = {}
        for agent_id, result in workflow_state.intermediate_results.items():
            if not result.get("success") and "error" in result:
                errors[agent_id] = result["error"]
        
        task.errors = errors
        
        self.logger.error(f"Task {task.task_id} failed with {len(errors)} errors")
        
        return workflow_state.model_dump()
    
    async def _execute_parallel_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行所有Agent"""
        workflow_state = WorkflowState(**state)
        task = workflow_state.task
        
        self.logger.debug(f"Executing {len(task.agent_roles)} agents in parallel")
        
        # 创建所有Agent的执行任务
        tasks = []
        for role in task.agent_roles:
            executor = self._create_agent_executor(role)
            tasks.append(executor(state))
        
        # 并行执行所有Agent
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        final_state = WorkflowState(**state)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                role = task.agent_roles[i]
                final_state.intermediate_results[role.agent_id] = {
                    "error": str(result),
                    "timestamp": datetime.now(),
                    "success": False
                }
                final_state.error_count += 1
                self.logger.error(f"Agent {role.agent_id} failed: {result}")
            elif isinstance(result, dict):
                # 合并状态
                result_state = WorkflowState(**result)
                final_state.intermediate_results.update(result_state.intermediate_results)
                final_state.shared_context.update(result_state.shared_context)
                final_state.error_count += result_state.error_count
        
        return final_state.model_dump()
    
    def _check_parallel_execution(self, state: Dict[str, Any]) -> str:
        """检查并行执行结果"""
        workflow_state = WorkflowState(**state)
        
        if workflow_state.error_count >= workflow_state.max_errors:
            return "error"
        
        # 检查是否所有Agent都有结果
        expected_count = len(workflow_state.task.agent_roles)
        completed_count = len(workflow_state.intermediate_results)
        
        if completed_count >= expected_count:
            return "completed"
        
        return "error"
    
    async def _wait_for_all_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """等待所有Agent完成（并行模式使用）"""
        workflow_state = WorkflowState(**state)
        
        # 检查是否所有Agent都已完成
        expected_agents = {role.agent_id for role in workflow_state.task.agent_roles}
        completed_agents = set(workflow_state.intermediate_results.keys())
        
        if expected_agents.issubset(completed_agents):
            self.logger.debug(f"All agents completed for task {workflow_state.task.task_id}")
        else:
            missing_agents = expected_agents - completed_agents
            self.logger.warning(f"Missing results from agents: {missing_agents}")
        
        return workflow_state.model_dump()
    
    async def _build_consensus(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """构建共识决策"""
        workflow_state = WorkflowState(**state)
        task = workflow_state.task
        
        # 收集所有Agent的响应
        responses = []
        weights = []
        
        for role in task.agent_roles:
            result = workflow_state.intermediate_results.get(role.agent_id)
            if result and result.get("success"):
                responses.append(result["response"])
                weights.append(role.weight)
        
        if not responses:
            workflow_state.error_count += 1
            self.logger.error(f"No valid responses for consensus in task {task.task_id}")
            return workflow_state.model_dump()
        
        # 简单的加权共识算法（可以根据需要扩展）
        consensus_result = self._calculate_weighted_consensus(responses, weights)
        
        # 保存共识结果
        workflow_state.shared_context["consensus_result"] = consensus_result
        
        self.logger.info(f"Built consensus for task {task.task_id} from {len(responses)} responses")
        
        return workflow_state.model_dump()
    
    def _calculate_weighted_consensus(self, responses: List[AgentResponse], weights: List[float]) -> Dict[str, Any]:
        """计算加权共识"""
        # 这里实现一个简单的加权平均共识算法
        # 实际应用中可以根据具体需求实现更复杂的共识算法
        
        total_weight = sum(weights)
        if total_weight == 0:
            return {"consensus": "No valid weights"}
        
        # 计算置信度的加权平均
        weighted_confidence = sum(
            response.confidence * weight 
            for response, weight in zip(responses, weights)
        ) / total_weight
        
        # 收集所有建议
        all_suggestions = []
        for response in responses:
            all_suggestions.extend(response.suggestions)
        
        # 去重并按出现频率排序
        suggestion_counts = {}
        for suggestion in all_suggestions:
            suggestion_counts[suggestion] = suggestion_counts.get(suggestion, 0) + 1
        
        consensus_suggestions = sorted(
            suggestion_counts.keys(),
            key=lambda x: suggestion_counts[x],
            reverse=True
        )[:5]  # 取前5个最常见的建议
        
        return {
            "consensus_confidence": weighted_confidence,
            "consensus_suggestions": consensus_suggestions,
            "participant_count": len(responses),
            "total_weight": total_weight
        }
    
    def _check_execution_result(self, state: Dict[str, Any]) -> str:
        """检查执行结果"""
        workflow_state = WorkflowState(**state)
        
        if workflow_state.error_count >= workflow_state.max_errors:
            return "error"
        
        return "continue"
    
    def _check_all_completed(self, state: Dict[str, Any]) -> str:
        """检查是否所有Agent都已完成"""
        workflow_state = WorkflowState(**state)
        
        expected_count = len(workflow_state.task.agent_roles)
        completed_count = len(workflow_state.intermediate_results)
        
        if workflow_state.error_count >= workflow_state.max_errors:
            return "error"
        
        if completed_count >= expected_count:
            return "completed"
        
        return "continue"
    
    def _check_layer_result(self, state: Dict[str, Any]) -> str:
        """检查层执行结果"""
        return self._check_execution_result(state)
    
    def _check_pipeline_result(self, state: Dict[str, Any]) -> str:
        """检查流水线执行结果"""
        return self._check_execution_result(state)
    
    async def _execute_consensus_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行共识Agent"""
        workflow_state = WorkflowState(**state)
        task = workflow_state.task
        
        self.logger.debug(f"Executing {len(task.agent_roles)} consensus agents in parallel")
        
        # 创建所有Agent的执行任务
        tasks = []
        for role in task.agent_roles:
            executor = self._create_agent_executor(role)
            tasks.append(executor(state))
        
        # 并行执行所有Agent
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        final_state = WorkflowState(**state)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                role = task.agent_roles[i]
                final_state.intermediate_results[role.agent_id] = {
                    "error": str(result),
                    "timestamp": datetime.now(),
                    "success": False
                }
                final_state.error_count += 1
                self.logger.error(f"Consensus agent {role.agent_id} failed: {result}")
            elif isinstance(result, dict):
                # 合并状态
                result_state = WorkflowState(**result)
                final_state.intermediate_results.update(result_state.intermediate_results)
                final_state.shared_context.update(result_state.shared_context)
                final_state.error_count += result_state.error_count
        
        return final_state.model_dump()
    
    def _check_consensus_execution(self, state: Dict[str, Any]) -> str:
        """检查共识执行结果"""
        workflow_state = WorkflowState(**state)
        
        if workflow_state.error_count >= workflow_state.max_errors:
            return "error"
        
        # 检查是否所有Agent都有结果
        expected_count = len(workflow_state.task.agent_roles)
        completed_count = len(workflow_state.intermediate_results)
        
        if completed_count >= expected_count:
            return "completed"
        
        return "error"
    
    def _check_consensus_result(self, state: Dict[str, Any]) -> str:
        """检查共识结果"""
        workflow_state = WorkflowState(**state)
        
        if workflow_state.error_count >= workflow_state.max_errors:
            return "error"
        
        if "consensus_result" in workflow_state.shared_context:
            return "consensus_reached"
        
        return "error"
    
    async def execute_collaboration_task(self, task_id: str) -> CollaborationTask:
        """
        执行协作任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行完成的任务对象
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.active_tasks[task_id]
        
        # 检查超时
        if task.timeout and datetime.now() > task.timeout:
            task.status = TaskStatus.FAILED
            task.errors["timeout"] = "Task execution timeout"
            return task
        
        # 创建工作流
        if task.task_id not in self.workflows:
            workflow = self._create_workflow(task)
            self.workflows[task.task_id] = workflow
        else:
            workflow = self.workflows[task.task_id]
        
        # 初始化工作流状态
        initial_state = WorkflowState(task=task)
        
        try:
            # 执行工作流
            result = await workflow.ainvoke(initial_state.model_dump())
            
            # 更新任务状态
            final_state = WorkflowState(**result)
            self.active_tasks[task_id] = final_state.task
            
            self.logger.info(f"Collaboration task {task.name} ({task_id}) completed with status {final_state.task.status}")
            
            return final_state.task
            
        except Exception as e:
            self.logger.error(f"Error executing collaboration task {task_id}: {e}")
            task.status = TaskStatus.FAILED
            task.errors["execution"] = str(e)
            task.completed_at = datetime.now()
            
            return task
    
    def _create_workflow(self, task: CollaborationTask) -> StateGraph:
        """根据协作模式创建工作流"""
        if task.mode == CollaborationMode.SEQUENTIAL:
            return self._create_sequential_workflow(task)
        elif task.mode == CollaborationMode.PARALLEL:
            return self._create_parallel_workflow(task)
        elif task.mode == CollaborationMode.HIERARCHICAL:
            return self._create_hierarchical_workflow(task)
        elif task.mode == CollaborationMode.PIPELINE:
            return self._create_pipeline_workflow(task)
        elif task.mode == CollaborationMode.CONSENSUS:
            return self._create_consensus_workflow(task)
        else:
            raise ValueError(f"Unsupported collaboration mode: {task.mode}")
    
    def get_task_status(self, task_id: str) -> Optional[CollaborationTask]:
        """获取任务状态"""
        return self.active_tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        self.logger.info(f"Cancelled collaboration task {task.name} ({task_id})")
        
        return True
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """清理已完成的任务"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        completed_tasks = []
        for task_id, task in self.active_tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at < cutoff_time):
                completed_tasks.append(task_id)
        
        # 清理任务和工作流
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
            if task_id in self.workflows:
                del self.workflows[task_id]
        
        self.logger.info(f"Cleaned up {len(completed_tasks)} completed tasks")
        
        return len(completed_tasks)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status] = 0
        
        for task in self.active_tasks.values():
            status_counts[task.status] += 1
        
        return {
            "total_tasks": len(self.active_tasks),
            "active_workflows": len(self.workflows),
            "status_distribution": status_counts,
            "collaboration_modes": {
                mode: sum(1 for task in self.active_tasks.values() if task.mode == mode)
                for mode in CollaborationMode
            }
        }