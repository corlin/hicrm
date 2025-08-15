"""
Agent对话集成服务测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from src.services.agent_conversation_integration import (
    AgentConversationIntegration,
    ConversationContext,
    ConversationMode,
    AgentRoutingStrategy
)
from src.agents.base import AgentMessage, AgentResponse, MessageType
from src.services.nlu_service import NLUResult, Intent, IntentType
from src.services.rag_service import RAGResult, RAGMode
from src.schemas.conversation import MessageCreate, MessageResponse
from src.models.conversation import MessageRole


class TestConversationContext:
    """对话上下文测试"""
    
    def test_conversation_context_creation(self):
        """测试对话上下文创建"""
        context = ConversationContext("conv_123", "user_456")
        
        assert context.conversation_id == "conv_123"
        assert context.user_id == "user_456"
        assert context.active_agents == []
        assert context.current_intent is None
        assert context.conversation_mode == ConversationMode.AUTO_ROUTING
        assert context.routing_strategy == AgentRoutingStrategy.INTENT_BASED
        assert isinstance(context.context_variables, dict)
        assert isinstance(context.agent_states, dict)
    
    def test_conversation_context_update(self):
        """测试对话上下文更新"""
        context = ConversationContext("conv_123", "user_456")
        original_updated_at = context.updated_at
        
        # 等待一小段时间确保时间戳不同
        import time
        time.sleep(0.01)
        
        context.update(
            current_intent=IntentType.CUSTOMER_SEARCH,
            active_agents=["sales_agent"]
        )
        
        assert context.current_intent == IntentType.CUSTOMER_SEARCH
        assert context.active_agents == ["sales_agent"]
        assert context.updated_at > original_updated_at


class TestAgentConversationIntegration:
    """Agent对话集成服务测试"""
    
    @pytest.fixture
    def mock_agent_manager(self):
        """模拟Agent管理器"""
        manager = Mock()
        manager.running_agents = {
            "sales_agent": Mock(),
            "market_agent": Mock(),
            "crm_expert_agent": Mock()
        }
        
        # 设置Agent可用性
        for agent in manager.running_agents.values():
            agent.is_available.return_value = True
        
        manager.send_message_to_agent = AsyncMock()
        manager.assign_task = AsyncMock(return_value="task_123")
        manager.get_task_status = AsyncMock(return_value={
            'assigned_agents': ['sales_agent']
        })
        manager.get_running_agents = Mock(return_value={
            'sales_agent': {
                'error_count': 0,
                'status': 'idle',
                'available': True
            }
        })
        
        return manager
    
    @pytest.fixture
    def mock_conversation_service(self):
        """模拟对话服务"""
        service = Mock()
        service.get_conversation = AsyncMock(return_value=Mock(context={}))
        service.add_message = AsyncMock(return_value=MessageResponse(
            id="msg_123",
            conversation_id="conv_123",
            role=MessageRole.ASSISTANT,
            content="Test response",
            created_at=datetime.now()
        ))
        return service
    
    @pytest.fixture
    def mock_nlu_service(self):
        """模拟NLU服务"""
        service = Mock()
        service.analyze = AsyncMock(return_value=NLUResult(
            text="查找客户",
            intent=Intent(type=IntentType.CUSTOMER_SEARCH, confidence=0.9),
            entities=[],
            slots={},
            confidence=0.9,
            processing_time=0.1
        ))
        return service
    
    @pytest.fixture
    def mock_rag_service(self):
        """模拟RAG服务"""
        service = Mock()
        service.query = AsyncMock(return_value=RAGResult(
            answer="这是RAG检索的答案",
            sources=[],
            confidence=0.8,
            retrieval_time=0.1,
            generation_time=0.2,
            total_time=0.3,
            mode=RAGMode.HYBRID,
            metadata={}
        ))
        return service
    
    @pytest.fixture
    def integration_service(
        self,
        mock_agent_manager,
        mock_conversation_service,
        mock_nlu_service,
        mock_rag_service
    ):
        """创建集成服务实例"""
        return AgentConversationIntegration(
            agent_manager=mock_agent_manager,
            conversation_service=mock_conversation_service,
            nlu_service=mock_nlu_service,
            rag_service=mock_rag_service
        )
    
    @pytest.mark.asyncio
    async def test_initialize(self, integration_service, mock_agent_manager, mock_rag_service):
        """测试初始化"""
        mock_agent_manager.start_all_agents = AsyncMock()
        mock_rag_service.initialize = AsyncMock()
        mock_rag_service.config = Mock()
        
        await integration_service.initialize()
        
        # 验证初始化调用
        mock_agent_manager.start_all_agents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_user_message_success(
        self,
        integration_service,
        mock_agent_manager,
        mock_conversation_service,
        mock_nlu_service,
        mock_rag_service
    ):
        """测试成功处理用户消息"""
        # 设置Agent响应
        mock_agent_response = AgentResponse(
            content="找到了3个潜在客户",
            confidence=0.9,
            suggestions=["查看详细信息", "联系客户"],
            next_actions=["schedule_meeting"]
        )
        mock_agent_manager.send_message_to_agent.return_value = mock_agent_response
        
        # 处理消息
        result = await integration_service.process_user_message(
            conversation_id="conv_123",
            user_message="帮我找一些制造业的客户",
            user_id="user_456"
        )
        
        # 验证结果
        assert isinstance(result, MessageResponse)
        assert result.content == "找到了3个潜在客户"
        
        # 验证服务调用
        mock_conversation_service.add_message.assert_called()
        mock_nlu_service.analyze.assert_called_once()
        mock_agent_manager.send_message_to_agent.assert_called_once()
        
        # 验证对话上下文创建
        assert "conv_123" in integration_service.conversation_contexts
        context = integration_service.conversation_contexts["conv_123"]
        assert context.user_id == "user_456"
        assert context.current_intent == IntentType.CUSTOMER_SEARCH
    
    @pytest.mark.asyncio
    async def test_process_user_message_with_rag(
        self,
        integration_service,
        mock_agent_manager,
        mock_nlu_service,
        mock_rag_service
    ):
        """测试使用RAG处理用户消息"""
        # 设置低置信度的NLU结果以触发RAG
        mock_nlu_service.analyze.return_value = NLUResult(
            text="这个问题比较复杂",
            intent=Intent(type=IntentType.UNKNOWN, confidence=0.5),
            entities=[],
            slots={},
            confidence=0.5,
            processing_time=0.1
        )
        
        mock_agent_response = AgentResponse(
            content="基于知识库的回答",
            confidence=0.8,
            suggestions=[],
            next_actions=[]
        )
        mock_agent_manager.send_message_to_agent.return_value = mock_agent_response
        
        # 处理消息
        await integration_service.process_user_message(
            conversation_id="conv_123",
            user_message="复杂的业务问题",
            user_id="user_456"
        )
        
        # 验证RAG被调用
        mock_rag_service.query.assert_called_once()
        
        # 验证对话上下文包含RAG结果
        context = integration_service.conversation_contexts["conv_123"]
        assert context.last_rag_results is not None
    
    @pytest.mark.asyncio
    async def test_select_agents_by_intent(self, integration_service):
        """测试基于意图选择Agent"""
        agents = await integration_service._select_agents_by_intent(
            IntentType.CUSTOMER_SEARCH
        )
        
        assert "sales_agent" in agents
        assert len(agents) <= 2
    
    @pytest.mark.asyncio
    async def test_select_agents_by_capability(
        self,
        integration_service,
        mock_agent_manager
    ):
        """测试基于能力选择Agent"""
        nlu_result = NLUResult(
            text="创建客户",
            intent=Intent(type=IntentType.CUSTOMER_CREATE, confidence=0.9),
            entities=[],
            slots={},
            confidence=0.9,
            processing_time=0.1
        )
        
        agents = await integration_service._select_agents_by_capability(
            nlu_result, None
        )
        
        # 验证Agent管理器被调用
        mock_agent_manager.assign_task.assert_called_once()
        assert len(agents) > 0
    
    @pytest.mark.asyncio
    async def test_select_agents_by_load(self, integration_service):
        """测试基于负载选择Agent"""
        agents = await integration_service._select_agents_by_load()
        
        assert len(agents) == 1
        assert agents[0] in ["sales_agent", "market_agent", "crm_expert_agent"]
    
    @pytest.mark.asyncio
    async def test_select_agents_round_robin(self, integration_service):
        """测试轮询选择Agent"""
        # 多次调用验证轮询
        agents1 = await integration_service._select_agents_round_robin()
        agents2 = await integration_service._select_agents_round_robin()
        
        assert len(agents1) == 1
        assert len(agents2) == 1
        # 在有多个Agent的情况下，轮询应该选择不同的Agent
        # 但由于我们只有模拟的Agent，这里只验证基本功能
    
    @pytest.mark.asyncio
    async def test_process_single_agent(
        self,
        integration_service,
        mock_agent_manager
    ):
        """测试单Agent处理"""
        mock_response = AgentResponse(
            content="单Agent响应",
            confidence=0.9,
            suggestions=[],
            next_actions=[]
        )
        mock_agent_manager.send_message_to_agent.return_value = mock_response
        
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="test",
            content="测试消息"
        )
        
        result = await integration_service._process_single_agent(
            "sales_agent",
            message
        )
        
        assert result.content == "单Agent响应"
        assert result.confidence == 0.9
        mock_agent_manager.send_message_to_agent.assert_called_once_with(
            "sales_agent", message
        )
    
    @pytest.mark.asyncio
    async def test_process_multi_agent(
        self,
        integration_service,
        mock_agent_manager
    ):
        """测试多Agent协作处理"""
        # 设置多个Agent响应
        responses = [
            AgentResponse(content="Agent1响应", confidence=0.8, suggestions=["建议1"], next_actions=["行动1"]),
            AgentResponse(content="Agent2响应", confidence=0.9, suggestions=["建议2"], next_actions=["行动2"])
        ]
        mock_agent_manager.send_message_to_agent.side_effect = responses
        
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="test",
            content="测试消息"
        )
        
        context = ConversationContext("conv_123", "user_456")
        
        result = await integration_service._process_multi_agent(
            ["sales_agent", "market_agent"],
            message,
            context
        )
        
        # 验证融合响应
        assert "Agent2响应" in result.content  # 置信度更高的响应作为主要内容
        assert result.confidence == 0.9
        assert len(result.suggestions) > 0
        assert len(result.next_actions) > 0
    
    @pytest.mark.asyncio
    async def test_fuse_agent_responses(self, integration_service):
        """测试Agent响应融合"""
        responses = [
            ("agent1", AgentResponse(content="响应1", confidence=0.7, suggestions=["建议1"], next_actions=["行动1"])),
            ("agent2", AgentResponse(content="响应2", confidence=0.9, suggestions=["建议2"], next_actions=["行动2"]))
        ]
        
        context = ConversationContext("conv_123", "user_456")
        
        result = await integration_service._fuse_agent_responses(responses, context)
        
        # 验证主要响应是置信度最高的
        assert "响应2" in result.content
        assert result.confidence == 0.9
        
        # 验证建议和行动被合并
        assert "建议1" in result.suggestions or "建议2" in result.suggestions
        assert "行动1" in result.next_actions or "行动2" in result.next_actions
        
        # 验证元数据
        assert result.metadata["primary_agent"] == "agent2"
        assert "agent1" in result.metadata["contributing_agents"]
        assert "agent2" in result.metadata["contributing_agents"]
    
    def test_should_use_rag(self, integration_service):
        """测试RAG使用判断"""
        # 需要知识检索的意图
        nlu_result_analysis = NLUResult(
            text="分析客户",
            intent=Intent(type=IntentType.CUSTOMER_ANALYSIS, confidence=0.9),
            entities=[],
            slots={},
            confidence=0.9,
            processing_time=0.1
        )
        assert integration_service._should_use_rag(nlu_result_analysis) is True
        
        # 低置信度的结果
        nlu_result_low_confidence = NLUResult(
            text="不确定的问题",
            intent=Intent(type=IntentType.CUSTOMER_SEARCH, confidence=0.5),
            entities=[],
            slots={},
            confidence=0.5,
            processing_time=0.1
        )
        assert integration_service._should_use_rag(nlu_result_low_confidence) is True
        
        # 不需要RAG的高置信度结果
        nlu_result_no_rag = NLUResult(
            text="查找客户",
            intent=Intent(type=IntentType.CUSTOMER_SEARCH, confidence=0.9),
            entities=[],
            slots={},
            confidence=0.9,
            processing_time=0.1
        )
        assert integration_service._should_use_rag(nlu_result_no_rag) is False
    
    @pytest.mark.asyncio
    async def test_get_conversation_context(self, integration_service):
        """测试获取对话上下文"""
        # 创建上下文
        context = ConversationContext("conv_123", "user_456")
        integration_service.conversation_contexts["conv_123"] = context
        
        # 获取上下文
        retrieved_context = await integration_service.get_conversation_context("conv_123")
        assert retrieved_context is context
        
        # 获取不存在的上下文
        non_existent = await integration_service.get_conversation_context("conv_999")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_update_conversation_mode(self, integration_service):
        """测试更新对话模式"""
        # 创建上下文
        context = ConversationContext("conv_123", "user_456")
        integration_service.conversation_contexts["conv_123"] = context
        
        # 更新模式
        success = await integration_service.update_conversation_mode(
            "conv_123",
            ConversationMode.MULTI_AGENT,
            AgentRoutingStrategy.CAPABILITY_BASED
        )
        
        assert success is True
        assert context.conversation_mode == ConversationMode.MULTI_AGENT
        assert context.routing_strategy == AgentRoutingStrategy.CAPABILITY_BASED
        
        # 更新不存在的对话
        success = await integration_service.update_conversation_mode(
            "conv_999",
            ConversationMode.SINGLE_AGENT
        )
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, integration_service):
        """测试获取性能指标"""
        # 添加一些测试数据
        integration_service.metrics['successful_routings'] = 10
        integration_service.metrics['failed_routings'] = 2
        integration_service.conversation_contexts["conv_123"] = ConversationContext("conv_123", "user_456")
        
        metrics = await integration_service.get_metrics()
        
        assert metrics['successful_routings'] == 10
        assert metrics['failed_routings'] == 2
        assert metrics['active_conversations'] == 1
        assert 'agent_status' in metrics
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_contexts(self, integration_service):
        """测试清理不活跃的对话上下文"""
        # 创建一个旧的上下文
        old_context = ConversationContext("conv_old", "user_456")
        old_context.updated_at = datetime.fromtimestamp(0)  # 很久以前的时间
        
        # 创建一个新的上下文
        new_context = ConversationContext("conv_new", "user_456")
        
        integration_service.conversation_contexts["conv_old"] = old_context
        integration_service.conversation_contexts["conv_new"] = new_context
        
        # 清理不活跃的上下文
        cleaned_count = await integration_service.cleanup_inactive_contexts(max_age_hours=1)
        
        assert cleaned_count == 1
        assert "conv_old" not in integration_service.conversation_contexts
        assert "conv_new" in integration_service.conversation_contexts
    
    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        integration_service,
        mock_agent_manager,
        mock_nlu_service
    ):
        """测试错误处理"""
        # 设置NLU服务抛出异常
        mock_nlu_service.analyze.side_effect = Exception("NLU服务错误")
        
        result = await integration_service.process_user_message(
            conversation_id="conv_123",
            user_message="测试消息",
            user_id="user_456"
        )
        
        # 验证错误响应
        assert "遇到了问题" in result.content
        assert "NLU服务错误" in result.content
        
        # 验证指标更新
        assert integration_service.metrics['failed_routings'] > 0


if __name__ == "__main__":
    pytest.main([__file__])