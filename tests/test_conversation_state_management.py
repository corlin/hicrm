"""
对话状态管理单元测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from src.services.conversation_service import ConversationService
from src.services.conversation_state_tracker import ConversationStateTracker
from src.models.conversation import Conversation, Message, ConversationState, ConversationStatus, MessageRole
from src.schemas.conversation import (
    ConversationCreate, MessageCreate, ConversationStateUpdate
)


class TestConversationStateTracker:
    """对话状态跟踪器测试"""
    
    @pytest.fixture
    async def mock_db(self):
        """模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db
    
    @pytest.fixture
    async def state_tracker(self, mock_db):
        """创建状态跟踪器实例"""
        return ConversationStateTracker(mock_db)
    
    @pytest.fixture
    def sample_conversation_id(self):
        """示例对话ID"""
        return "test-conversation-123"
    
    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return "test-user-456"
    
    async def test_initialize_conversation_state(self, state_tracker, sample_conversation_id, sample_user_id):
        """测试初始化对话状态"""
        initial_context = {"business_type": "sales", "priority": "high"}
        
        # 模拟数据库操作
        state_tracker.db.commit = AsyncMock()
        state_tracker.db.refresh = AsyncMock()
        
        # 执行初始化
        result = await state_tracker.initialize_conversation_state(
            sample_conversation_id, 
            sample_user_id, 
            initial_context
        )
        
        # 验证结果
        assert state_tracker.db.add.called
        assert state_tracker.db.commit.called
        
        # 验证添加的对象类型
        added_obj = state_tracker.db.add.call_args[0][0]
        assert isinstance(added_obj, ConversationState)
        assert added_obj.conversation_id == sample_conversation_id
        assert added_obj.flow_state == "initialized"
        assert "start" in added_obj.step_history
    
    async def test_get_conversation_state(self, state_tracker, sample_conversation_id):
        """测试获取对话状态"""
        # 模拟数据库查询结果
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            flow_state="active",
            current_agent="sales_agent"
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_state
        state_tracker.db.execute.return_value = mock_result
        
        # 执行查询
        result = await state_tracker.get_conversation_state(sample_conversation_id)
        
        # 验证结果
        assert result == mock_state
        assert state_tracker.db.execute.called
    
    async def test_update_conversation_state(self, state_tracker, sample_conversation_id):
        """测试更新对话状态"""
        state_update = ConversationStateUpdate(
            current_task="customer_analysis",
            current_agent="sales_agent",
            flow_state="processing"
        )
        
        # 模拟数据库操作
        state_tracker.db.execute = AsyncMock()
        state_tracker.db.commit = AsyncMock()
        
        # 执行更新
        result = await state_tracker.update_conversation_state(sample_conversation_id, state_update)
        
        # 验证结果
        assert result is True
        assert state_tracker.db.execute.called
        assert state_tracker.db.commit.called
    
    async def test_add_to_context(self, state_tracker, sample_conversation_id):
        """测试添加上下文变量"""
        # 模拟现有状态
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            context_variables={"existing_key": "existing_value"}
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        # 执行添加
        result = await state_tracker.add_to_context(sample_conversation_id, "new_key", "new_value")
        
        # 验证结果
        assert result is True
        assert state_tracker.update_conversation_state.called
        
        # 验证更新的上下文包含新键值
        call_args = state_tracker.update_conversation_state.call_args
        updated_context = call_args[0][1].context_variables
        assert "new_key" in updated_context
        assert updated_context["new_key"] == "new_value"
        assert "existing_key" in updated_context
    
    async def test_context_memory_limit(self, state_tracker, sample_conversation_id):
        """测试上下文记忆限制"""
        # 创建超过限制的上下文
        large_context = {f"key_{i}": f"value_{i}" for i in range(60)}
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            context_variables=large_context
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        # 执行添加
        await state_tracker.add_to_context(sample_conversation_id, "new_key", "new_value")
        
        # 验证上下文被限制
        call_args = state_tracker.update_conversation_state.call_args
        updated_context = call_args[0][1].context_variables
        assert len(updated_context) <= state_tracker.context_memory_limit
    
    async def test_update_short_term_memory(self, state_tracker, sample_conversation_id):
        """测试更新短期记忆"""
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            short_term_memory={}
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        # 执行更新
        result = await state_tracker.update_short_term_memory(
            sample_conversation_id, 
            "customer_name", 
            "ABC Company"
        )
        
        # 验证结果
        assert result is True
        
        # 验证记忆项包含时间戳和TTL
        call_args = state_tracker.update_conversation_state.call_args
        memory = call_args[0][1].short_term_memory
        assert "customer_name" in memory
        
        memory_item = memory["customer_name"]
        assert memory_item["value"] == "ABC Company"
        assert "timestamp" in memory_item
        assert "ttl" in memory_item
    
    async def test_get_short_term_memory_valid(self, state_tracker, sample_conversation_id):
        """测试获取有效的短期记忆"""
        # 创建未过期的记忆项
        current_time = datetime.utcnow()
        memory_item = {
            "value": "ABC Company",
            "timestamp": current_time.isoformat(),
            "ttl": 7200  # 2小时
        }
        
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            short_term_memory={"customer_name": memory_item}
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        
        # 执行获取
        result = await state_tracker.get_short_term_memory(sample_conversation_id, "customer_name")
        
        # 验证结果
        assert result == "ABC Company"
    
    async def test_get_short_term_memory_expired(self, state_tracker, sample_conversation_id):
        """测试获取过期的短期记忆"""
        # 创建过期的记忆项
        expired_time = datetime.utcnow() - timedelta(hours=3)
        memory_item = {
            "value": "ABC Company",
            "timestamp": expired_time.isoformat(),
            "ttl": 7200  # 2小时
        }
        
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            short_term_memory={"customer_name": memory_item}
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        state_tracker._remove_short_term_memory = AsyncMock(return_value=True)
        
        # 执行获取
        result = await state_tracker.get_short_term_memory(sample_conversation_id, "customer_name")
        
        # 验证结果
        assert result is None
        assert state_tracker._remove_short_term_memory.called
    
    async def test_promote_to_long_term_memory(self, state_tracker, sample_conversation_id):
        """测试提升到长期记忆"""
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            long_term_memory={}
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        # 执行提升
        result = await state_tracker.promote_to_long_term_memory(
            sample_conversation_id,
            "customer_preference",
            "prefers_email_communication",
            importance_score=0.8
        )
        
        # 验证结果
        assert result is True
        
        # 验证长期记忆项包含必要字段
        call_args = state_tracker.update_conversation_state.call_args
        memory = call_args[0][1].long_term_memory
        assert "customer_preference" in memory
        
        memory_item = memory["customer_preference"]
        assert memory_item["value"] == "prefers_email_communication"
        assert memory_item["importance_score"] == 0.8
        assert memory_item["access_count"] == 1
        assert "created_at" in memory_item
        assert "last_accessed" in memory_item
    
    async def test_get_long_term_memory_updates_access(self, state_tracker, sample_conversation_id):
        """测试获取长期记忆时更新访问信息"""
        # 创建长期记忆项
        memory_item = {
            "value": "prefers_email_communication",
            "importance_score": 0.8,
            "access_count": 1,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat()
        }
        
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            long_term_memory={"customer_preference": memory_item}
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        # 执行获取
        result = await state_tracker.get_long_term_memory(sample_conversation_id, "customer_preference")
        
        # 验证结果
        assert result == "prefers_email_communication"
        
        # 验证访问计数被更新
        call_args = state_tracker.update_conversation_state.call_args
        updated_memory = call_args[0][1].long_term_memory
        updated_item = updated_memory["customer_preference"]
        assert updated_item["access_count"] == 2
    
    async def test_update_flow_state(self, state_tracker, sample_conversation_id):
        """测试更新流程状态"""
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            flow_state="initialized",
            step_history=["start", "initialized"]
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        # 执行更新
        result = await state_tracker.update_flow_state(sample_conversation_id, "processing")
        
        # 验证结果
        assert result is True
        
        # 验证历史被更新
        call_args = state_tracker.update_conversation_state.call_args
        update_data = call_args[0][1]
        assert update_data.flow_state == "processing"
        assert "processing" in update_data.step_history
    
    async def test_clean_expired_memory(self, state_tracker):
        """测试清理过期记忆"""
        current_time = datetime.utcnow()
        expired_time = current_time - timedelta(hours=3)
        
        memory_dict = {
            "valid_item": {
                "value": "valid",
                "timestamp": current_time.isoformat(),
                "ttl": 7200
            },
            "expired_item": {
                "value": "expired",
                "timestamp": expired_time.isoformat(),
                "ttl": 7200
            }
        }
        
        # 执行清理
        cleaned = state_tracker._clean_expired_memory(memory_dict)
        
        # 验证结果
        assert "valid_item" in cleaned
        assert "expired_item" not in cleaned
    
    async def test_get_conversation_history_summary(self, state_tracker, sample_conversation_id):
        """测试获取对话历史摘要"""
        # 模拟消息查询结果
        mock_messages = [
            Message(
                id="msg1",
                conversation_id=sample_conversation_id,
                role=MessageRole.USER,
                content="Hello",
                agent_type=None,
                created_at=datetime.utcnow()
            ),
            Message(
                id="msg2",
                conversation_id=sample_conversation_id,
                role=MessageRole.ASSISTANT,
                content="Hi there!",
                agent_type="sales_agent",
                created_at=datetime.utcnow()
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        state_tracker.db.execute.return_value = mock_result
        
        # 模拟状态查询结果
        mock_state = ConversationState(
            conversation_id=sample_conversation_id,
            flow_state="active",
            current_agent="sales_agent",
            current_task="greeting",
            last_intent="greeting",
            context_variables={"user_name": "John"},
            short_term_memory={"recent_topic": "introduction"},
            long_term_memory={"preference": "formal_tone"}
        )
        
        state_tracker.get_conversation_state = AsyncMock(return_value=mock_state)
        
        # 执行获取摘要
        summary = await state_tracker.get_conversation_history_summary(sample_conversation_id)
        
        # 验证结果
        assert "recent_messages" in summary
        assert "current_state" in summary
        assert "context_keys" in summary
        assert "memory_summary" in summary
        
        assert len(summary["recent_messages"]) == 2
        assert summary["current_state"]["flow_state"] == "active"
        assert summary["current_state"]["current_agent"] == "sales_agent"
        assert "user_name" in summary["context_keys"]
        assert summary["memory_summary"]["short_term_items"] == 1
        assert summary["memory_summary"]["long_term_items"] == 1


class TestConversationService:
    """对话服务测试"""
    
    @pytest.fixture
    async def mock_db(self):
        """模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db
    
    @pytest.fixture
    async def conversation_service(self, mock_db):
        """创建对话服务实例"""
        return ConversationService(mock_db)
    
    @pytest.fixture
    def sample_conversation_create(self):
        """示例创建对话数据"""
        return ConversationCreate(
            user_id="test-user-123",
            title="Test Conversation",
            initial_context={"business_type": "sales"}
        )
    
    async def test_create_conversation(self, conversation_service, sample_conversation_create):
        """测试创建对话"""
        # 模拟数据库操作
        now = datetime.utcnow()
        mock_conversation = Conversation(
            id="test-conv-123",
            user_id=sample_conversation_create.user_id,
            title=sample_conversation_create.title,
            status=ConversationStatus.ACTIVE,
            context=sample_conversation_create.initial_context,
            state={},
            user_preferences={},
            message_count=0,
            last_activity=now,
            created_at=now,
            updated_at=now
        )
        
        conversation_service.db.commit = AsyncMock()
        conversation_service.db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, 'id', "test-conv-123") or setattr(obj, 'created_at', now) or setattr(obj, 'updated_at', now))
        conversation_service.state_tracker.initialize_conversation_state = AsyncMock()
        
        # 执行创建
        result = await conversation_service.create_conversation(sample_conversation_create)
        
        # 验证结果
        assert conversation_service.db.add.called
        assert conversation_service.db.commit.called
        assert conversation_service.state_tracker.initialize_conversation_state.called
        
        # 验证添加的对象
        added_obj = conversation_service.db.add.call_args[0][0]
        assert isinstance(added_obj, Conversation)
        assert added_obj.user_id == sample_conversation_create.user_id
        assert added_obj.title == sample_conversation_create.title
    
    async def test_add_message(self, conversation_service):
        """测试添加消息"""
        conversation_id = "test-conv-123"
        message_data = MessageCreate(
            role=MessageRole.USER,
            content="Hello, I need help with sales",
            agent_type=None,
            agent_id=None,
            metadata={"source": "web"}
        )
        
        # 模拟数据库操作
        now = datetime.utcnow()
        mock_message = Message(
            id="test-msg-123",
            conversation_id=conversation_id,
            role=message_data.role,
            content=message_data.content,
            meta_data=message_data.metadata,
            confidence={},
            created_at=now
        )
        
        conversation_service.db.commit = AsyncMock()
        conversation_service.db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, 'id', "test-msg-123") or setattr(obj, 'created_at', now))
        
        # 执行添加消息
        result = await conversation_service.add_message(conversation_id, message_data)
        
        # 验证结果
        assert conversation_service.db.add.called
        assert conversation_service.db.commit.called
        
        # 验证添加的消息
        added_obj = conversation_service.db.add.call_args[0][0]
        assert isinstance(added_obj, Message)
        assert added_obj.conversation_id == conversation_id
        assert added_obj.role == message_data.role
        assert added_obj.content == message_data.content
    
    async def test_get_conversation(self, conversation_service):
        """测试获取对话"""
        conversation_id = "test-conv-123"
        
        # 模拟数据库查询结果
        mock_conversation = Conversation(
            id=conversation_id,
            user_id="test-user-123",
            title="Test Conversation",
            status=ConversationStatus.ACTIVE,
            context={"business_type": "sales"},
            state={},
            user_preferences={},
            message_count=5,
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conversation
        conversation_service.db.execute.return_value = mock_result
        
        # 执行获取
        result = await conversation_service.get_conversation(conversation_id)
        
        # 验证结果
        assert result is not None
        assert result.id == conversation_id
        assert result.user_id == "test-user-123"
        assert result.title == "Test Conversation"
        assert result.status == ConversationStatus.ACTIVE
    
    async def test_update_conversation_state_integration(self, conversation_service):
        """测试对话状态更新集成"""
        conversation_id = "test-conv-123"
        state_update = ConversationStateUpdate(
            current_task="customer_analysis",
            current_agent="sales_agent"
        )
        
        # 模拟状态跟踪器
        conversation_service.state_tracker.update_conversation_state = AsyncMock(return_value=True)
        
        # 执行更新
        result = await conversation_service.update_conversation_state(conversation_id, state_update)
        
        # 验证结果
        assert result is True
        assert conversation_service.state_tracker.update_conversation_state.called
        
        # 验证调用参数
        call_args = conversation_service.state_tracker.update_conversation_state.call_args
        assert call_args[0][0] == conversation_id
        assert call_args[0][1] == state_update
    
    async def test_memory_operations_integration(self, conversation_service):
        """测试记忆操作集成"""
        conversation_id = "test-conv-123"
        
        # 模拟状态跟踪器方法
        conversation_service.state_tracker.update_short_term_memory = AsyncMock(return_value=True)
        conversation_service.state_tracker.get_short_term_memory = AsyncMock(return_value="test_value")
        conversation_service.state_tracker.promote_to_long_term_memory = AsyncMock(return_value=True)
        conversation_service.state_tracker.get_long_term_memory = AsyncMock(return_value="long_term_value")
        
        # 测试短期记忆操作
        result1 = await conversation_service.update_short_term_memory(
            conversation_id, "test_key", "test_value"
        )
        assert result1 is True
        
        result2 = await conversation_service.get_short_term_memory(conversation_id, "test_key")
        assert result2 == "test_value"
        
        # 测试长期记忆操作
        result3 = await conversation_service.promote_to_long_term_memory(
            conversation_id, "important_key", "important_value", 0.9
        )
        assert result3 is True
        
        result4 = await conversation_service.get_long_term_memory(conversation_id, "important_key")
        assert result4 == "long_term_value"
        
        # 验证所有方法都被调用
        assert conversation_service.state_tracker.update_short_term_memory.called
        assert conversation_service.state_tracker.get_short_term_memory.called
        assert conversation_service.state_tracker.promote_to_long_term_memory.called
        assert conversation_service.state_tracker.get_long_term_memory.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])