"""
对话Pydantic模式
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ConversationStatus(str, Enum):
    """对话状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class ConversationContext(BaseModel):
    """对话上下文模式"""
    user_id: str
    user_role: Optional[str] = None
    current_task: Optional[str] = None
    business_context: Dict[str, Any] = Field(default_factory=dict)
    active_agents: List[str] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """对话状态模式"""
    current_agent: Optional[str] = None
    flow_state: Optional[str] = None
    last_intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    step_history: List[str] = Field(default_factory=list)
    short_term_memory: Dict[str, Any] = Field(default_factory=dict)
    long_term_memory: Dict[str, Any] = Field(default_factory=dict)


class UserPreferences(BaseModel):
    """用户偏好模式"""
    communication_style: Optional[str] = None
    preferred_agents: List[str] = Field(default_factory=list)
    response_format: Optional[str] = None
    language: str = "zh-CN"
    timezone: Optional[str] = None


class ConversationBase(BaseModel):
    """对话基础模式"""
    title: Optional[str] = None
    user_id: str
    context: ConversationContext = Field(default_factory=ConversationContext)
    state: ConversationState = Field(default_factory=ConversationState)
    user_preferences: UserPreferences = Field(default_factory=UserPreferences)


class ConversationCreate(BaseModel):
    """创建对话模式"""
    user_id: str
    title: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """更新对话模式"""
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None
    context: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """对话响应模式"""
    id: str
    user_id: str
    title: Optional[str] = None
    status: ConversationStatus
    context: Dict[str, Any]
    state: Dict[str, Any]
    user_preferences: Dict[str, Any]
    message_count: int
    last_activity: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """消息基础模式"""
    content: str
    role: MessageRole
    agent_type: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    """创建消息模式"""
    pass


class MessageResponse(MessageBase):
    """消息响应模式"""
    id: str
    conversation_id: str
    confidence: Dict[str, Any]
    processing_time: Optional[int] = None
    tokens_used: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationStateUpdate(BaseModel):
    """对话状态更新模式"""
    current_task: Optional[str] = None
    current_agent: Optional[str] = None
    context_variables: Optional[Dict[str, Any]] = None
    flow_state: Optional[str] = None
    step_history: Optional[List[str]] = None
    last_intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    short_term_memory: Optional[Dict[str, Any]] = None
    long_term_memory: Optional[Dict[str, Any]] = None


class ConversationHistory(BaseModel):
    """对话历史模式"""
    conversation: ConversationResponse
    messages: List[MessageResponse]
    total_messages: int