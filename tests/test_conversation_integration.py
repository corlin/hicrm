"""
对话状态管理集成测试
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.conversation_service import ConversationService
from src.schemas.conversation import (
    ConversationCreate, MessageCreate, MessageRole, ConversationStateUpdate
)


class TestConversationIntegration:
    """对话状态管理集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self):
        """测试完整的对话流程"""
        # 这是一个集成测试示例，展示如何使用对话状态管理系统
        
        # 模拟数据库会话
        from unittest.mock import AsyncMock, MagicMock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        
        # 创建对话服务
        conversation_service = ConversationService(mock_db)
        
        # 模拟状态跟踪器方法
        conversation_service.state_tracker.initialize_conversation_state = AsyncMock()
        conversation_service.state_tracker.update_conversation_state = AsyncMock(return_value=True)
        conversation_service.state_tracker.add_to_context = AsyncMock(return_value=True)
        conversation_service.state_tracker.update_short_term_memory = AsyncMock(return_value=True)
        conversation_service.state_tracker.get_short_term_memory = AsyncMock(return_value="ABC Company")
        conversation_service.state_tracker.promote_to_long_term_memory = AsyncMock(return_value=True)
        conversation_service.state_tracker.update_flow_state = AsyncMock(return_value=True)
        
        # 1. 创建对话
        conversation_data = ConversationCreate(
            user_id="sales_user_001",
            title="客户咨询 - ABC公司",
            initial_context={
                "business_type": "sales",
                "priority": "high",
                "source": "website_form"
            }
        )
        
        # 模拟创建对话的返回
        now = datetime.utcnow()
        def mock_refresh_conversation(obj):
            obj.id = "conv-123"
            obj.created_at = now
            obj.updated_at = now
        
        mock_db.refresh.side_effect = mock_refresh_conversation
        
        conversation = await conversation_service.create_conversation(conversation_data)
        
        # 验证对话创建
        assert mock_db.add.called
        assert mock_db.commit.called
        assert conversation_service.state_tracker.initialize_conversation_state.called
        
        conversation_id = "conv-123"  # 模拟的对话ID
        
        # 2. 添加用户消息
        user_message = MessageCreate(
            role=MessageRole.USER,
            content="你好，我想了解一下你们的CRM系统",
            metadata={"source": "web_chat"}
        )
        
        def mock_refresh_message(obj):
            obj.id = "msg-001"
            obj.created_at = now
        
        mock_db.refresh.side_effect = mock_refresh_message
        
        await conversation_service.add_message(conversation_id, user_message)
        
        # 3. 更新对话状态 - 用户开始咨询
        await conversation_service.update_conversation_state(
            conversation_id,
            ConversationStateUpdate(
                current_task="product_inquiry",
                current_agent="sales_agent",
                flow_state="greeting"
            )
        )
        
        # 4. 添加上下文信息
        await conversation_service.add_context_variable(
            conversation_id, 
            "inquiry_type", 
            "crm_system"
        )
        
        # 5. 更新短期记忆 - 记住客户感兴趣的产品
        await conversation_service.update_short_term_memory(
            conversation_id,
            "interested_product",
            "CRM系统"
        )
        
        # 6. 添加助手回复
        assistant_message = MessageCreate(
            role=MessageRole.ASSISTANT,
            content="您好！很高兴为您介绍我们的CRM系统。请问您的公司规模大概是多少人？",
            agent_type="sales_agent",
            agent_id="agent_001",
            metadata={"confidence": 0.95}
        )
        
        await conversation_service.add_message(conversation_id, assistant_message)
        
        # 7. 更新流程状态
        await conversation_service.update_flow_state(conversation_id, "needs_assessment")
        
        # 8. 用户提供更多信息
        user_response = MessageCreate(
            role=MessageRole.USER,
            content="我们公司大概50人左右，主要做制造业",
            metadata={"source": "web_chat"}
        )
        
        await conversation_service.add_message(conversation_id, user_response)
        
        # 9. 更新上下文和记忆
        await conversation_service.add_context_variable(
            conversation_id,
            "company_size",
            "50人"
        )
        
        await conversation_service.add_context_variable(
            conversation_id,
            "industry",
            "制造业"
        )
        
        # 10. 将重要信息提升到长期记忆
        await conversation_service.promote_to_long_term_memory(
            conversation_id,
            "customer_profile",
            {
                "company_size": "50人",
                "industry": "制造业",
                "interest": "CRM系统"
            },
            importance_score=0.9
        )
        
        # 11. 更新对话状态
        await conversation_service.update_conversation_state(
            conversation_id,
            ConversationStateUpdate(
                current_task="solution_matching",
                flow_state="proposal_preparation",
                last_intent="provide_company_info",
                entities={
                    "company_size": "50人",
                    "industry": "制造业"
                }
            )
        )
        
        # 验证所有操作都被正确调用
        assert conversation_service.state_tracker.update_conversation_state.call_count >= 2
        assert conversation_service.state_tracker.add_to_context.call_count >= 3
        assert conversation_service.state_tracker.update_short_term_memory.called
        assert conversation_service.state_tracker.promote_to_long_term_memory.called
        assert conversation_service.state_tracker.update_flow_state.called
        
        # 验证消息添加
        assert mock_db.add.call_count >= 4  # 1个对话 + 3个消息
        
        print("✅ 完整对话流程测试通过")
    
    @pytest.mark.asyncio
    async def test_memory_management_flow(self):
        """测试记忆管理流程"""
        from unittest.mock import AsyncMock, MagicMock
        
        mock_db = AsyncMock(spec=AsyncSession)
        conversation_service = ConversationService(mock_db)
        
        # 模拟状态跟踪器方法
        conversation_service.state_tracker.update_short_term_memory = AsyncMock(return_value=True)
        conversation_service.state_tracker.get_short_term_memory = AsyncMock(return_value="test_value")
        conversation_service.state_tracker.promote_to_long_term_memory = AsyncMock(return_value=True)
        conversation_service.state_tracker.get_long_term_memory = AsyncMock(return_value="long_term_value")
        
        conversation_id = "test-conv-123"
        
        # 测试短期记忆操作
        result1 = await conversation_service.update_short_term_memory(
            conversation_id, "customer_name", "张总"
        )
        assert result1 is True
        
        result2 = await conversation_service.get_short_term_memory(
            conversation_id, "customer_name"
        )
        assert result2 == "test_value"
        
        # 测试长期记忆操作
        result3 = await conversation_service.promote_to_long_term_memory(
            conversation_id, 
            "customer_preference", 
            "喜欢详细的技术文档",
            0.8
        )
        assert result3 is True
        
        result4 = await conversation_service.get_long_term_memory(
            conversation_id, "customer_preference"
        )
        assert result4 == "long_term_value"
        
        print("✅ 记忆管理流程测试通过")
    
    @pytest.mark.asyncio
    async def test_context_management_flow(self):
        """测试上下文管理流程"""
        from unittest.mock import AsyncMock, MagicMock
        
        mock_db = AsyncMock(spec=AsyncSession)
        conversation_service = ConversationService(mock_db)
        
        # 模拟状态跟踪器方法
        conversation_service.state_tracker.add_to_context = AsyncMock(return_value=True)
        conversation_service.state_tracker.get_context_variable = AsyncMock(return_value="context_value")
        conversation_service.state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        conversation_id = "test-conv-123"
        
        # 测试上下文变量操作
        result1 = await conversation_service.add_context_variable(
            conversation_id, "current_topic", "产品演示"
        )
        assert result1 is True
        
        result2 = await conversation_service.get_context_variable(
            conversation_id, "current_topic"
        )
        assert result2 == "context_value"
        
        # 测试状态更新
        result3 = await conversation_service.update_conversation_state(
            conversation_id,
            ConversationStateUpdate(
                current_task="demo_preparation",
                current_agent="product_agent"
            )
        )
        assert result3 is True
        
        print("✅ 上下文管理流程测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])