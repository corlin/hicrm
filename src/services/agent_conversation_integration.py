"""
Agent与对话服务集成层

负责Agent与ConversationService的集成，实现NLU服务与Agent的消息路由，
开发多Agent对话协调和任务分发机制，集成RAG服务为Agent提供知识支持。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from enum import Enum
import uuid

from src.agents.base import BaseAgent, AgentMessage, AgentResponse, MessageType, AgentStatus
from src.agents.manager import AgentManager
from src.services.conversation_service import ConversationService
from src.services.nlu_service import NLUService, NLUResult, IntentType
from src.services.rag_service import RAGService, RAGResult, RAGMode
from src.schemas.conversation import MessageCreate, MessageResponse, ConversationCreate
from src.models.conversation import MessageRole
from src.core.database import get_db

logger = logging.getLogger(__name__)


class ConversationMode(str, Enum):
    """对话模式"""
    SINGLE_AGENT = "single_agent"  # 单Agent模式
    MULTI_AGENT = "multi_agent"    # 多Agent协作模式
    AUTO_ROUTING = "auto_routing"  # 自动路由模式


class AgentRoutingStrategy(str, Enum):
    """Agent路由策略"""
    INTENT_BASED = "intent_based"      # 基于意图路由
    CAPABILITY_BASED = "capability_based"  # 基于能力路由
    LOAD_BALANCED = "load_balanced"    # 负载均衡路由
    ROUND_ROBIN = "round_robin"        # 轮询路由


class ConversationContext:
    """对话上下文"""
    
    def __init__(self, conversation_id: str, user_id: str):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.active_agents: List[str] = []
        self.current_intent: Optional[IntentType] = None
        self.conversation_mode = ConversationMode.AUTO_ROUTING
        self.routing_strategy = AgentRoutingStrategy.INTENT_BASED
        self.context_variables: Dict[str, Any] = {}
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.last_rag_results: Optional[RAGResult] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update(self, **kwargs):
        """更新上下文"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()


class AgentConversationIntegration:
    """Agent与对话服务集成器"""
    
    def __init__(
        self,
        agent_manager: AgentManager,
        conversation_service: ConversationService,
        nlu_service: NLUService,
        rag_service: RAGService
    ):
        self.agent_manager = agent_manager
        self.conversation_service = conversation_service
        self.nlu_service = nlu_service
        self.rag_service = rag_service
        
        # 对话上下文管理
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        
        # Agent路由映射
        self.intent_agent_mapping = self._initialize_intent_agent_mapping()
        
        # 性能指标
        self.metrics = {
            'total_conversations': 0,
            'successful_routings': 0,
            'failed_routings': 0,
            'avg_response_time': 0.0,
            'agent_usage': {}
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _initialize_intent_agent_mapping(self) -> Dict[IntentType, List[str]]:
        """初始化意图到Agent的映射"""
        return {
            # 客户管理相关意图 -> 销售Agent
            IntentType.CUSTOMER_SEARCH: ['sales_agent'],
            IntentType.CUSTOMER_CREATE: ['sales_agent'],
            IntentType.CUSTOMER_UPDATE: ['sales_agent'],
            IntentType.CUSTOMER_ANALYSIS: ['sales_agent', 'crm_expert_agent'],
            
            # 线索管理相关意图 -> 市场Agent + 销售管理Agent
            IntentType.LEAD_SEARCH: ['market_agent'],
            IntentType.LEAD_CREATE: ['market_agent'],
            IntentType.LEAD_UPDATE: ['market_agent'],
            IntentType.LEAD_SCORING: ['market_agent'],
            IntentType.LEAD_ASSIGNMENT: ['sales_management_agent'],
            
            # 销售机会相关意图 -> 销售Agent + 产品Agent
            IntentType.OPPORTUNITY_SEARCH: ['sales_agent'],
            IntentType.OPPORTUNITY_CREATE: ['sales_agent', 'product_agent'],
            IntentType.OPPORTUNITY_UPDATE: ['sales_agent'],
            IntentType.OPPORTUNITY_ANALYSIS: ['sales_agent', 'management_strategy_agent'],
            
            # 任务和活动相关意图 -> 销售Agent
            IntentType.TASK_CREATE: ['sales_agent'],
            IntentType.TASK_SEARCH: ['sales_agent'],
            IntentType.SCHEDULE_MEETING: ['sales_agent'],
            
            # 报告和分析相关意图 -> 管理策略Agent
            IntentType.REPORT_GENERATE: ['management_strategy_agent'],
            IntentType.PERFORMANCE_ANALYSIS: ['management_strategy_agent', 'sales_management_agent'],
            IntentType.FORECAST_ANALYSIS: ['management_strategy_agent'],
            
            # 通用意图 -> CRM专家Agent
            IntentType.GREETING: ['crm_expert_agent'],
            IntentType.HELP: ['crm_expert_agent'],
            IntentType.UNKNOWN: ['crm_expert_agent']
        }
    
    async def initialize(self) -> None:
        """初始化集成服务"""
        try:
            # 确保所有依赖服务已初始化
            if not self.agent_manager.running_agents:
                await self.agent_manager.start_all_agents()
            
            if not self.rag_service.config:
                await self.rag_service.initialize()
            
            self.logger.info("Agent对话集成服务初始化完成")
            
        except Exception as e:
            self.logger.error(f"Agent对话集成服务初始化失败: {e}")
            raise
    
    async def process_user_message(
        self,
        conversation_id: str,
        user_message: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MessageResponse:
        """
        处理用户消息的主要入口点
        
        Args:
            conversation_id: 对话ID
            user_message: 用户消息内容
            user_id: 用户ID
            context: 额外上下文信息
            
        Returns:
            Agent响应消息
        """
        start_time = datetime.now()
        
        try:
            # 1. 获取或创建对话上下文
            conv_context = await self._get_or_create_context(
                conversation_id, user_id, context
            )
            
            # 2. 保存用户消息
            user_msg = await self.conversation_service.add_message(
                conversation_id,
                MessageCreate(
                    role=MessageRole.USER,
                    content=user_message,
                    metadata=context or {}
                )
            )
            
            # 3. NLU分析
            nlu_result = await self.nlu_service.analyze(
                user_message,
                context={
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'previous_intent': conv_context.current_intent
                }
            )
            
            # 4. 更新对话上下文
            conv_context.current_intent = nlu_result.intent.type
            conv_context.update()
            
            # 5. RAG知识检索（如果需要）
            rag_result = None
            if self._should_use_rag(nlu_result):
                rag_result = await self.rag_service.query(
                    question=user_message,
                    mode=RAGMode.HYBRID
                )
                conv_context.last_rag_results = rag_result
            
            # 6. Agent路由和处理
            agent_response = await self._route_and_process_message(
                conv_context,
                user_message,
                nlu_result,
                rag_result
            )
            
            # 7. 保存Agent响应
            response_msg = await self.conversation_service.add_message(
                conversation_id,
                MessageCreate(
                    role=MessageRole.ASSISTANT,
                    content=agent_response.content,
                    agent_type=conv_context.active_agents[0] if conv_context.active_agents else "unknown",
                    metadata={
                        'confidence': agent_response.confidence,
                        'suggestions': agent_response.suggestions,
                        'next_actions': agent_response.next_actions,
                        'intent': nlu_result.intent.type.value,
                        'processing_time': (datetime.now() - start_time).total_seconds(),
                        'rag_used': rag_result is not None
                    }
                )
            )
            
            # 8. 更新性能指标
            self._update_metrics(start_time, True)
            
            return response_msg
            
        except Exception as e:
            self.logger.error(f"处理用户消息失败: {e}")
            
            # 保存错误响应
            error_msg = await self.conversation_service.add_message(
                conversation_id,
                MessageCreate(
                    role=MessageRole.ASSISTANT,
                    content=f"抱歉，处理您的消息时遇到了问题：{str(e)}",
                    metadata={
                        'error': str(e),
                        'processing_time': (datetime.now() - start_time).total_seconds()
                    }
                )
            )
            
            self._update_metrics(start_time, False)
            return error_msg
    
    async def _get_or_create_context(
        self,
        conversation_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """获取或创建对话上下文"""
        if conversation_id not in self.conversation_contexts:
            # 创建新的对话上下文
            conv_context = ConversationContext(conversation_id, user_id)
            
            # 从数据库加载历史上下文（如果存在）
            conversation = await self.conversation_service.get_conversation(conversation_id)
            if conversation and conversation.context:
                conv_context.context_variables.update(conversation.context)
            
            self.conversation_contexts[conversation_id] = conv_context
            self.metrics['total_conversations'] += 1
        
        return self.conversation_contexts[conversation_id]
    
    def _should_use_rag(self, nlu_result: NLUResult) -> bool:
        """判断是否需要使用RAG检索"""
        # 基于意图类型判断是否需要知识检索
        knowledge_required_intents = {
            IntentType.CUSTOMER_ANALYSIS,
            IntentType.OPPORTUNITY_ANALYSIS,
            IntentType.PERFORMANCE_ANALYSIS,
            IntentType.FORECAST_ANALYSIS,
            IntentType.HELP,
            IntentType.UNKNOWN
        }
        
        return (
            nlu_result.intent.type in knowledge_required_intents or
            nlu_result.confidence < 0.7  # 低置信度时使用RAG辅助
        )
    
    async def _route_and_process_message(
        self,
        conv_context: ConversationContext,
        user_message: str,
        nlu_result: NLUResult,
        rag_result: Optional[RAGResult] = None
    ) -> AgentResponse:
        """路由消息到合适的Agent并处理"""
        
        # 1. 选择合适的Agent
        selected_agents = await self._select_agents(
            conv_context,
            nlu_result,
            rag_result
        )
        
        if not selected_agents:
            return AgentResponse(
                content="抱歉，当前没有可用的Agent来处理您的请求。",
                confidence=0.0,
                suggestions=["请稍后重试", "联系系统管理员"]
            )
        
        # 2. 更新活跃Agent列表
        conv_context.active_agents = selected_agents
        
        # 3. 构建Agent消息
        agent_message = AgentMessage(
            type=MessageType.TASK,
            sender_id="conversation_service",
            receiver_id=selected_agents[0],  # 主要处理Agent
            content=user_message,
            metadata={
                'conversation_id': conv_context.conversation_id,
                'user_id': conv_context.user_id,
                'intent': nlu_result.intent.type.value,
                'entities': [entity.dict() for entity in nlu_result.entities],
                'slots': {name: slot.dict() for name, slot in nlu_result.slots.items()},
                'rag_context': rag_result.dict() if rag_result else None,
                'conversation_context': conv_context.context_variables
            }
        )
        
        # 4. 处理消息
        if len(selected_agents) == 1:
            # 单Agent处理
            response = await self._process_single_agent(
                selected_agents[0],
                agent_message
            )
        else:
            # 多Agent协作处理
            response = await self._process_multi_agent(
                selected_agents,
                agent_message,
                conv_context
            )
        
        # 5. 更新Agent使用统计
        for agent_id in selected_agents:
            self.metrics['agent_usage'][agent_id] = (
                self.metrics['agent_usage'].get(agent_id, 0) + 1
            )
        
        return response
    
    async def _select_agents(
        self,
        conv_context: ConversationContext,
        nlu_result: NLUResult,
        rag_result: Optional[RAGResult] = None
    ) -> List[str]:
        """选择合适的Agent处理消息"""
        
        if conv_context.routing_strategy == AgentRoutingStrategy.INTENT_BASED:
            return await self._select_agents_by_intent(nlu_result.intent.type)
        
        elif conv_context.routing_strategy == AgentRoutingStrategy.CAPABILITY_BASED:
            return await self._select_agents_by_capability(nlu_result, rag_result)
        
        elif conv_context.routing_strategy == AgentRoutingStrategy.LOAD_BALANCED:
            return await self._select_agents_by_load()
        
        else:  # ROUND_ROBIN
            return await self._select_agents_round_robin()
    
    async def _select_agents_by_intent(self, intent: IntentType) -> List[str]:
        """基于意图选择Agent"""
        candidate_agents = self.intent_agent_mapping.get(intent, ['crm_expert_agent'])
        
        # 过滤可用的Agent
        available_agents = []
        for agent_id in candidate_agents:
            if agent_id in self.agent_manager.running_agents:
                agent = self.agent_manager.running_agents[agent_id]
                if agent.is_available():
                    available_agents.append(agent_id)
        
        return available_agents[:2]  # 最多选择2个Agent协作
    
    async def _select_agents_by_capability(
        self,
        nlu_result: NLUResult,
        rag_result: Optional[RAGResult] = None
    ) -> List[str]:
        """基于能力选择Agent"""
        required_capabilities = []
        
        # 根据NLU结果推断需要的能力
        if nlu_result.intent.type in [IntentType.CUSTOMER_SEARCH, IntentType.CUSTOMER_CREATE]:
            required_capabilities.append("customer_management")
        
        if nlu_result.intent.type in [IntentType.LEAD_SEARCH, IntentType.LEAD_CREATE]:
            required_capabilities.append("lead_management")
        
        if nlu_result.intent.type in [IntentType.OPPORTUNITY_SEARCH, IntentType.OPPORTUNITY_CREATE]:
            required_capabilities.append("opportunity_management")
        
        if rag_result and rag_result.confidence > 0.7:
            required_capabilities.append("knowledge_retrieval")
        
        # 使用Agent管理器选择Agent
        task_id = await self.agent_manager.assign_task(
            AgentMessage(
                type=MessageType.TASK,
                sender_id="integration_service",
                content="capability_check",
                metadata={'required_capabilities': required_capabilities}
            ),
            required_capabilities=required_capabilities,
            max_agents=2
        )
        
        # 获取分配的Agent
        task_status = await self.agent_manager.get_task_status(task_id)
        if task_status:
            return task_status['assigned_agents']
        
        return ['crm_expert_agent']  # 默认Agent
    
    async def _select_agents_by_load(self) -> List[str]:
        """基于负载选择Agent"""
        running_agents = self.agent_manager.get_running_agents()
        
        # 按负载排序（错误数量和状态）
        sorted_agents = sorted(
            running_agents.items(),
            key=lambda x: (
                x[1]['error_count'],
                0 if x[1]['status'] == AgentStatus.IDLE else 1
            )
        )
        
        # 选择负载最低的Agent
        available_agents = [
            agent_id for agent_id, info in sorted_agents
            if info['available']
        ]
        
        return available_agents[:1]  # 选择一个负载最低的Agent
    
    async def _select_agents_round_robin(self) -> List[str]:
        """轮询选择Agent"""
        available_agents = [
            agent_id for agent_id, agent in self.agent_manager.running_agents.items()
            if agent.is_available()
        ]
        
        if not available_agents:
            return []
        
        # 简单的轮询实现
        current_index = getattr(self, '_round_robin_index', 0)
        selected_agent = available_agents[current_index % len(available_agents)]
        self._round_robin_index = (current_index + 1) % len(available_agents)
        
        return [selected_agent]
    
    async def _process_single_agent(
        self,
        agent_id: str,
        message: AgentMessage
    ) -> AgentResponse:
        """单Agent处理消息"""
        try:
            response = await self.agent_manager.send_message_to_agent(agent_id, message)
            
            if response:
                self.metrics['successful_routings'] += 1
                return response
            else:
                self.metrics['failed_routings'] += 1
                return AgentResponse(
                    content=f"Agent {agent_id} 处理消息失败。",
                    confidence=0.0,
                    suggestions=["请稍后重试"]
                )
                
        except Exception as e:
            self.logger.error(f"单Agent处理失败: {e}")
            self.metrics['failed_routings'] += 1
            return AgentResponse(
                content=f"处理消息时出现错误：{str(e)}",
                confidence=0.0,
                suggestions=["请检查系统状态", "联系管理员"]
            )
    
    async def _process_multi_agent(
        self,
        agent_ids: List[str],
        message: AgentMessage,
        conv_context: ConversationContext
    ) -> AgentResponse:
        """多Agent协作处理消息"""
        try:
            # 并行发送消息给所有Agent
            tasks = []
            for agent_id in agent_ids:
                agent_message = AgentMessage(
                    type=message.type,
                    sender_id=message.sender_id,
                    receiver_id=agent_id,
                    content=message.content,
                    metadata={
                        **message.metadata,
                        'collaboration_mode': True,
                        'other_agents': [aid for aid in agent_ids if aid != agent_id]
                    }
                )
                tasks.append(self.agent_manager.send_message_to_agent(agent_id, agent_message))
            
            # 等待所有Agent响应
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理响应
            valid_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    self.logger.error(f"Agent {agent_ids[i]} 响应异常: {response}")
                elif response:
                    valid_responses.append((agent_ids[i], response))
            
            if not valid_responses:
                self.metrics['failed_routings'] += 1
                return AgentResponse(
                    content="所有Agent都无法处理您的请求。",
                    confidence=0.0,
                    suggestions=["请稍后重试", "简化您的问题"]
                )
            
            # 融合多个Agent的响应
            fused_response = await self._fuse_agent_responses(valid_responses, conv_context)
            self.metrics['successful_routings'] += 1
            
            return fused_response
            
        except Exception as e:
            self.logger.error(f"多Agent协作处理失败: {e}")
            self.metrics['failed_routings'] += 1
            return AgentResponse(
                content=f"多Agent协作处理时出现错误：{str(e)}",
                confidence=0.0,
                suggestions=["请尝试单一功能请求", "联系技术支持"]
            )
    
    async def _fuse_agent_responses(
        self,
        responses: List[Tuple[str, AgentResponse]],
        conv_context: ConversationContext
    ) -> AgentResponse:
        """融合多个Agent的响应"""
        if len(responses) == 1:
            return responses[0][1]
        
        # 选择置信度最高的主要响应
        primary_agent, primary_response = max(responses, key=lambda x: x[1].confidence)
        
        # 收集所有建议和后续行动
        all_suggestions = []
        all_next_actions = []
        
        for agent_id, response in responses:
            all_suggestions.extend(response.suggestions)
            all_next_actions.extend(response.next_actions)
        
        # 去重并限制数量
        unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]
        unique_next_actions = list(dict.fromkeys(all_next_actions))[:3]
        
        # 构建融合响应
        fused_content = primary_response.content
        
        # 如果有其他有价值的响应，添加补充信息
        other_responses = [resp for agent_id, resp in responses if agent_id != primary_agent]
        if other_responses and any(resp.confidence > 0.5 for resp in other_responses):
            fused_content += "\n\n补充信息："
            for agent_id, response in responses:
                if agent_id != primary_agent and response.confidence > 0.5:
                    fused_content += f"\n- {response.content[:100]}..."
        
        return AgentResponse(
            content=fused_content,
            confidence=primary_response.confidence,
            suggestions=unique_suggestions,
            next_actions=unique_next_actions,
            metadata={
                'primary_agent': primary_agent,
                'contributing_agents': [agent_id for agent_id, _ in responses],
                'fusion_method': 'confidence_based'
            }
        )
    
    def _update_metrics(self, start_time: datetime, success: bool) -> None:
        """更新性能指标"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 更新平均响应时间
        current_avg = self.metrics['avg_response_time']
        total_requests = self.metrics['successful_routings'] + self.metrics['failed_routings']
        
        if total_requests > 0:
            self.metrics['avg_response_time'] = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )
    
    async def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """获取对话上下文"""
        return self.conversation_contexts.get(conversation_id)
    
    async def update_conversation_mode(
        self,
        conversation_id: str,
        mode: ConversationMode,
        routing_strategy: Optional[AgentRoutingStrategy] = None
    ) -> bool:
        """更新对话模式"""
        if conversation_id in self.conversation_contexts:
            context = self.conversation_contexts[conversation_id]
            context.conversation_mode = mode
            if routing_strategy:
                context.routing_strategy = routing_strategy
            context.update()
            return True
        return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self.metrics,
            'active_conversations': len(self.conversation_contexts),
            'agent_status': self.agent_manager.get_running_agents()
        }
    
    async def cleanup_inactive_contexts(self, max_age_hours: int = 24) -> int:
        """清理不活跃的对话上下文"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        inactive_contexts = []
        
        for conv_id, context in self.conversation_contexts.items():
            if context.updated_at.timestamp() < cutoff_time:
                inactive_contexts.append(conv_id)
        
        for conv_id in inactive_contexts:
            del self.conversation_contexts[conv_id]
        
        self.logger.info(f"清理了 {len(inactive_contexts)} 个不活跃的对话上下文")
        return len(inactive_contexts)
    
    async def close(self) -> None:
        """关闭集成服务"""
        try:
            # 清理所有对话上下文
            self.conversation_contexts.clear()
            
            self.logger.info("Agent对话集成服务已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭Agent对话集成服务失败: {e}")


# 创建全局集成服务实例的工厂函数
async def create_agent_conversation_integration(
    agent_manager: AgentManager,
    nlu_service: NLUService,
    rag_service: RAGService
) -> AgentConversationIntegration:
    """创建Agent对话集成服务实例"""
    
    # 获取数据库会话
    async with get_db() as db:
        conversation_service = ConversationService(db)
        
        integration = AgentConversationIntegration(
            agent_manager=agent_manager,
            conversation_service=conversation_service,
            nlu_service=nlu_service,
            rag_service=rag_service
        )
        
        await integration.initialize()
        return integration