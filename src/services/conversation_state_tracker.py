"""
对话状态跟踪器
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation, Message, ConversationState, ConversationStatus, MessageRole
from src.schemas.conversation import (
    ConversationContext, ConversationState as ConversationStateSchema,
    UserPreferences, ConversationStateUpdate
)

logger = logging.getLogger(__name__)


class ConversationStateTracker:
    """对话状态跟踪器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.context_memory_limit = 50  # 上下文记忆限制
        self.short_term_memory_ttl = timedelta(hours=2)  # 短期记忆TTL
        self.long_term_memory_threshold = 5  # 长期记忆阈值
    
    async def initialize_conversation_state(
        self, 
        conversation_id: str, 
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """初始化对话状态"""
        try:
            # 创建初始上下文
            context = ConversationContext(
                user_id=user_id,
                business_context=initial_context or {},
                variables={}
            )
            
            # 创建初始状态
            state = ConversationStateSchema(
                flow_state="initialized",
                step_history=["start"],
                short_term_memory={},
                long_term_memory={}
            )
            
            # 创建对话状态记录
            conversation_state = ConversationState(
                conversation_id=conversation_id,
                context_variables=context.dict(),
                flow_state=state.flow_state,
                step_history=state.step_history,
                short_term_memory=state.short_term_memory,
                long_term_memory=state.long_term_memory
            )
            
            self.db.add(conversation_state)
            await self.db.commit()
            await self.db.refresh(conversation_state)
            
            logger.info(f"Initialized conversation state for conversation {conversation_id}")
            return conversation_state
            
        except Exception as e:
            logger.error(f"Error initializing conversation state: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_conversation_state(self, conversation_id: str) -> Optional[ConversationState]:
        """获取对话状态"""
        try:
            result = await self.db.execute(
                select(ConversationState)
                .where(ConversationState.conversation_id == conversation_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting conversation state: {str(e)}")
            return None
    
    async def update_conversation_state(
        self, 
        conversation_id: str, 
        state_update: ConversationStateUpdate
    ) -> bool:
        """更新对话状态"""
        try:
            # 构建更新字典
            update_data = {}
            
            if state_update.current_task is not None:
                update_data["current_task"] = state_update.current_task
            
            if state_update.current_agent is not None:
                update_data["current_agent"] = state_update.current_agent
            
            if state_update.context_variables is not None:
                update_data["context_variables"] = state_update.context_variables
            
            if state_update.flow_state is not None:
                update_data["flow_state"] = state_update.flow_state
            
            if state_update.last_intent is not None:
                update_data["last_intent"] = state_update.last_intent
            
            if state_update.entities is not None:
                update_data["entities"] = state_update.entities
            
            if state_update.short_term_memory is not None:
                update_data["short_term_memory"] = state_update.short_term_memory
            
            if state_update.long_term_memory is not None:
                update_data["long_term_memory"] = state_update.long_term_memory
            
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                
                await self.db.execute(
                    update(ConversationState)
                    .where(ConversationState.conversation_id == conversation_id)
                    .values(**update_data)
                )
                await self.db.commit()
                
                logger.info(f"Updated conversation state for conversation {conversation_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating conversation state: {str(e)}")
            await self.db.rollback()
            return False
    
    async def add_to_context(
        self, 
        conversation_id: str, 
        key: str, 
        value: Any
    ) -> bool:
        """添加上下文变量"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state:
                return False
            
            context_vars = state.context_variables or {}
            context_vars[key] = value
            
            # 限制上下文大小
            if len(context_vars) > self.context_memory_limit:
                # 移除最旧的条目
                sorted_items = sorted(context_vars.items())
                context_vars = dict(sorted_items[-self.context_memory_limit:])
            
            return await self.update_conversation_state(
                conversation_id,
                ConversationStateUpdate(context_variables=context_vars)
            )
            
        except Exception as e:
            logger.error(f"Error adding to context: {str(e)}")
            return False
    
    async def get_context_variable(
        self, 
        conversation_id: str, 
        key: str
    ) -> Optional[Any]:
        """获取上下文变量"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state or not state.context_variables:
                return None
            
            return state.context_variables.get(key)
            
        except Exception as e:
            logger.error(f"Error getting context variable: {str(e)}")
            return None
    
    async def update_short_term_memory(
        self, 
        conversation_id: str, 
        key: str, 
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """更新短期记忆"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state:
                return False
            
            short_term = state.short_term_memory or {}
            
            # 添加时间戳
            memory_item = {
                "value": value,
                "timestamp": datetime.utcnow().isoformat(),
                "ttl": (ttl or self.short_term_memory_ttl).total_seconds()
            }
            
            short_term[key] = memory_item
            
            # 清理过期的短期记忆
            short_term = self._clean_expired_memory(short_term)
            
            return await self.update_conversation_state(
                conversation_id,
                ConversationStateUpdate(short_term_memory=short_term)
            )
            
        except Exception as e:
            logger.error(f"Error updating short term memory: {str(e)}")
            return False
    
    async def get_short_term_memory(
        self, 
        conversation_id: str, 
        key: str
    ) -> Optional[Any]:
        """获取短期记忆"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state or not state.short_term_memory:
                return None
            
            memory_item = state.short_term_memory.get(key)
            if not memory_item:
                return None
            
            # 检查是否过期
            timestamp = datetime.fromisoformat(memory_item["timestamp"])
            ttl = timedelta(seconds=memory_item["ttl"])
            
            if datetime.utcnow() - timestamp > ttl:
                # 记忆已过期，移除它
                await self._remove_short_term_memory(conversation_id, key)
                return None
            
            return memory_item["value"]
            
        except Exception as e:
            logger.error(f"Error getting short term memory: {str(e)}")
            return None
    
    async def promote_to_long_term_memory(
        self, 
        conversation_id: str, 
        key: str, 
        value: Any,
        importance_score: float = 1.0
    ) -> bool:
        """提升到长期记忆"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state:
                return False
            
            long_term = state.long_term_memory or {}
            
            # 创建长期记忆项
            memory_item = {
                "value": value,
                "created_at": datetime.utcnow().isoformat(),
                "importance_score": importance_score,
                "access_count": 1,
                "last_accessed": datetime.utcnow().isoformat()
            }
            
            # 如果已存在，更新访问计数和重要性
            if key in long_term:
                existing = long_term[key]
                memory_item["access_count"] = existing.get("access_count", 0) + 1
                memory_item["importance_score"] = max(
                    importance_score, 
                    existing.get("importance_score", 0)
                )
                memory_item["created_at"] = existing.get("created_at", memory_item["created_at"])
            
            long_term[key] = memory_item
            
            return await self.update_conversation_state(
                conversation_id,
                ConversationStateUpdate(long_term_memory=long_term)
            )
            
        except Exception as e:
            logger.error(f"Error promoting to long term memory: {str(e)}")
            return False
    
    async def get_long_term_memory(
        self, 
        conversation_id: str, 
        key: str
    ) -> Optional[Any]:
        """获取长期记忆"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state or not state.long_term_memory:
                return None
            
            memory_item = state.long_term_memory.get(key)
            if not memory_item:
                return None
            
            # 更新访问信息
            memory_item["access_count"] = memory_item.get("access_count", 0) + 1
            memory_item["last_accessed"] = datetime.utcnow().isoformat()
            
            # 更新数据库
            long_term = state.long_term_memory
            long_term[key] = memory_item
            
            await self.update_conversation_state(
                conversation_id,
                ConversationStateUpdate(long_term_memory=long_term)
            )
            
            return memory_item["value"]
            
        except Exception as e:
            logger.error(f"Error getting long term memory: {str(e)}")
            return None
    
    async def update_flow_state(
        self, 
        conversation_id: str, 
        new_state: str,
        add_to_history: bool = True
    ) -> bool:
        """更新流程状态"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state:
                return False
            
            update_data = {"flow_state": new_state}
            
            if add_to_history:
                step_history = state.step_history or []
                step_history.append(new_state)
                
                # 限制历史长度
                if len(step_history) > 100:
                    step_history = step_history[-100:]
                
                update_data["step_history"] = step_history
            
            return await self.update_conversation_state(
                conversation_id,
                ConversationStateUpdate(**update_data)
            )
            
        except Exception as e:
            logger.error(f"Error updating flow state: {str(e)}")
            return False
    
    async def get_conversation_history_summary(
        self, 
        conversation_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取对话历史摘要"""
        try:
            # 获取最近的消息
            result = await self.db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            
            # 获取对话状态
            state = await self.get_conversation_state(conversation_id)
            
            # 构建摘要
            summary = {
                "recent_messages": [
                    {
                        "role": msg.role,
                        "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                        "agent_type": msg.agent_type,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in reversed(messages)
                ],
                "current_state": {
                    "flow_state": state.flow_state if state else None,
                    "current_agent": state.current_agent if state else None,
                    "current_task": state.current_task if state else None,
                    "last_intent": state.last_intent if state else None
                },
                "context_keys": list(state.context_variables.keys()) if state and state.context_variables else [],
                "memory_summary": {
                    "short_term_items": len(state.short_term_memory) if state and state.short_term_memory else 0,
                    "long_term_items": len(state.long_term_memory) if state and state.long_term_memory else 0
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting conversation history summary: {str(e)}")
            return {}
    
    async def learn_user_preferences(
        self, 
        conversation_id: str,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """学习用户偏好"""
        try:
            # 获取对话记录
            result = await self.db.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                return False
            
            # 分析交互数据并更新偏好
            preferences = conversation.user_preferences or {}
            learned_patterns = conversation.learned_patterns or {}
            
            # 学习通信风格
            if "response_length" in interaction_data:
                preferences["preferred_response_length"] = interaction_data["response_length"]
            
            # 学习Agent偏好
            if "preferred_agent" in interaction_data:
                preferred_agents = preferences.get("preferred_agents", [])
                agent = interaction_data["preferred_agent"]
                if agent not in preferred_agents:
                    preferred_agents.append(agent)
                preferences["preferred_agents"] = preferred_agents
            
            # 学习任务模式
            if "task_pattern" in interaction_data:
                task_patterns = learned_patterns.get("task_patterns", {})
                pattern = interaction_data["task_pattern"]
                task_patterns[pattern] = task_patterns.get(pattern, 0) + 1
                learned_patterns["task_patterns"] = task_patterns
            
            # 更新数据库
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    user_preferences=preferences,
                    learned_patterns=learned_patterns,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            logger.info(f"Updated user preferences for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error learning user preferences: {str(e)}")
            await self.db.rollback()
            return False
    
    def _clean_expired_memory(self, memory_dict: Dict[str, Any]) -> Dict[str, Any]:
        """清理过期的记忆"""
        cleaned = {}
        current_time = datetime.utcnow()
        
        for key, item in memory_dict.items():
            try:
                timestamp = datetime.fromisoformat(item["timestamp"])
                ttl = timedelta(seconds=item["ttl"])
                
                if current_time - timestamp <= ttl:
                    cleaned[key] = item
            except (KeyError, ValueError):
                # 如果格式不正确，跳过这个项目
                continue
        
        return cleaned
    
    async def _remove_short_term_memory(self, conversation_id: str, key: str) -> bool:
        """移除短期记忆项"""
        try:
            state = await self.get_conversation_state(conversation_id)
            if not state or not state.short_term_memory:
                return False
            
            short_term = state.short_term_memory.copy()
            if key in short_term:
                del short_term[key]
                
                return await self.update_conversation_state(
                    conversation_id,
                    ConversationStateUpdate(short_term_memory=short_term)
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing short term memory: {str(e)}")
            return False