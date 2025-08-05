"""
对话服务
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation, Message, ConversationStatus, MessageRole
from src.schemas.conversation import (
    ConversationCreate, ConversationResponse, ConversationUpdate,
    MessageCreate, MessageResponse, ConversationHistory,
    ConversationStateUpdate
)
from src.services.conversation_state_tracker import ConversationStateTracker

logger = logging.getLogger(__name__)


class ConversationService:
    """对话服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_tracker = ConversationStateTracker(db)
    
    async def get_conversations(
        self, 
        user_id: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConversationResponse]:
        """获取对话列表"""
        try:
            query = select(Conversation).order_by(Conversation.last_activity.desc())
            
            if user_id:
                query = query.where(Conversation.user_id == user_id)
            
            if status:
                query = query.where(Conversation.status == status)
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            conversations = result.scalars().all()
            
            return [
                ConversationResponse(
                    id=str(conv.id),
                    user_id=conv.user_id,
                    title=conv.title,
                    status=conv.status,
                    context=conv.context or {},
                    state=conv.state or {},
                    user_preferences=conv.user_preferences or {},
                    message_count=conv.message_count,
                    last_activity=conv.last_activity,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at
                )
                for conv in conversations
            ]
            
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """获取单个对话"""
        try:
            result = await self.db.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                return None
            
            return ConversationResponse(
                id=str(conversation.id),
                user_id=conversation.user_id,
                title=conversation.title,
                status=conversation.status,
                context=conversation.context or {},
                state=conversation.state or {},
                user_preferences=conversation.user_preferences or {},
                message_count=conversation.message_count,
                last_activity=conversation.last_activity,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            return None
    
    async def create_conversation(self, conversation_data: ConversationCreate) -> ConversationResponse:
        """创建对话"""
        try:
            # 创建对话记录
            conversation = Conversation(
                user_id=conversation_data.user_id,
                title=conversation_data.title,
                status=ConversationStatus.ACTIVE,
                context=conversation_data.initial_context or {},
                state={},
                user_preferences={},
                message_count=0,
                last_activity=datetime.utcnow()
            )
            
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
            
            # 初始化对话状态
            await self.state_tracker.initialize_conversation_state(
                str(conversation.id),
                conversation_data.user_id,
                conversation_data.initial_context
            )
            
            logger.info(f"Created conversation {conversation.id} for user {conversation_data.user_id}")
            
            return ConversationResponse(
                id=str(conversation.id),
                user_id=conversation.user_id,
                title=conversation.title,
                status=conversation.status,
                context=conversation.context or {},
                state=conversation.state or {},
                user_preferences=conversation.user_preferences or {},
                message_count=conversation.message_count,
                last_activity=conversation.last_activity,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            await self.db.rollback()
            raise
    
    async def update_conversation(
        self, 
        conversation_id: str, 
        update_data: ConversationUpdate
    ) -> Optional[ConversationResponse]:
        """更新对话"""
        try:
            # 构建更新字典
            update_values = {"updated_at": datetime.utcnow()}
            
            if update_data.title is not None:
                update_values["title"] = update_data.title
            
            if update_data.status is not None:
                update_values["status"] = update_data.status
            
            if update_data.context is not None:
                update_values["context"] = update_data.context
            
            if update_data.state is not None:
                update_values["state"] = update_data.state
            
            if update_data.user_preferences is not None:
                update_values["user_preferences"] = update_data.user_preferences
            
            # 执行更新
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(**update_values)
            )
            await self.db.commit()
            
            # 返回更新后的对话
            return await self.get_conversation(conversation_id)
            
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
            await self.db.rollback()
            return None
    
    async def add_message(self, conversation_id: str, message_data: MessageCreate) -> MessageResponse:
        """添加消息"""
        try:
            # 创建消息记录
            message = Message(
                conversation_id=conversation_id,
                role=message_data.role,
                content=message_data.content,
                agent_type=message_data.agent_type,
                agent_id=message_data.agent_id,
                meta_data=message_data.metadata,
                confidence={},
                processing_time=None,
                tokens_used=None
            )
            
            self.db.add(message)
            
            # 更新对话的消息计数和最后活动时间
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    message_count=Conversation.message_count + 1,
                    last_activity=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            await self.db.commit()
            await self.db.refresh(message)
            
            logger.info(f"Added message to conversation {conversation_id}")
            
            return MessageResponse(
                id=str(message.id),
                conversation_id=str(message.conversation_id),
                role=message.role,
                content=message.content,
                agent_type=message.agent_type,
                agent_id=message.agent_id,
                metadata=message.meta_data,
                confidence=message.confidence,
                processing_time=message.processing_time,
                tokens_used=message.tokens_used,
                created_at=message.created_at
            )
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_conversation_history(
        self, 
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Optional[ConversationHistory]:
        """获取对话历史"""
        try:
            # 获取对话信息
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # 获取消息列表
            result = await self.db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
            messages = result.scalars().all()
            
            # 获取总消息数
            count_result = await self.db.execute(
                select(func.count(Message.id))
                .where(Message.conversation_id == conversation_id)
            )
            total_messages = count_result.scalar()
            
            message_responses = [
                MessageResponse(
                    id=str(msg.id),
                    conversation_id=str(msg.conversation_id),
                    role=msg.role,
                    content=msg.content,
                    agent_type=msg.agent_type,
                    agent_id=msg.agent_id,
                    metadata=msg.meta_data,
                    confidence=msg.confidence,
                    processing_time=msg.processing_time,
                    tokens_used=msg.tokens_used,
                    created_at=msg.created_at
                )
                for msg in messages
            ]
            
            return ConversationHistory(
                conversation=conversation,
                messages=message_responses,
                total_messages=total_messages
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation history {conversation_id}: {str(e)}")
            return None
    
    async def update_conversation_state(
        self, 
        conversation_id: str, 
        state_update: ConversationStateUpdate
    ) -> bool:
        """更新对话状态"""
        return await self.state_tracker.update_conversation_state(conversation_id, state_update)
    
    async def add_context_variable(
        self, 
        conversation_id: str, 
        key: str, 
        value: Any
    ) -> bool:
        """添加上下文变量"""
        return await self.state_tracker.add_to_context(conversation_id, key, value)
    
    async def get_context_variable(
        self, 
        conversation_id: str, 
        key: str
    ) -> Optional[Any]:
        """获取上下文变量"""
        return await self.state_tracker.get_context_variable(conversation_id, key)
    
    async def update_short_term_memory(
        self, 
        conversation_id: str, 
        key: str, 
        value: Any
    ) -> bool:
        """更新短期记忆"""
        return await self.state_tracker.update_short_term_memory(conversation_id, key, value)
    
    async def get_short_term_memory(
        self, 
        conversation_id: str, 
        key: str
    ) -> Optional[Any]:
        """获取短期记忆"""
        return await self.state_tracker.get_short_term_memory(conversation_id, key)
    
    async def promote_to_long_term_memory(
        self, 
        conversation_id: str, 
        key: str, 
        value: Any,
        importance_score: float = 1.0
    ) -> bool:
        """提升到长期记忆"""
        return await self.state_tracker.promote_to_long_term_memory(
            conversation_id, key, value, importance_score
        )
    
    async def get_long_term_memory(
        self, 
        conversation_id: str, 
        key: str
    ) -> Optional[Any]:
        """获取长期记忆"""
        return await self.state_tracker.get_long_term_memory(conversation_id, key)
    
    async def update_flow_state(
        self, 
        conversation_id: str, 
        new_state: str
    ) -> bool:
        """更新流程状态"""
        return await self.state_tracker.update_flow_state(conversation_id, new_state)
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        return await self.state_tracker.get_conversation_history_summary(conversation_id)
    
    async def learn_user_preferences(
        self, 
        conversation_id: str,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """学习用户偏好"""
        return await self.state_tracker.learn_user_preferences(conversation_id, interaction_data)
    
    async def archive_conversation(self, conversation_id: str) -> bool:
        """归档对话"""
        try:
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    status=ConversationStatus.ARCHIVED,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            logger.info(f"Archived conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving conversation {conversation_id}: {str(e)}")
            await self.db.rollback()
            return False