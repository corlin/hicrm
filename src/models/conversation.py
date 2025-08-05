"""
对话数据模型
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.core.database import Base


class ConversationStatus(str, enum.Enum):
    """对话状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class Conversation(Base):
    """对话模型"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    title = Column(String(500))
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE)
    
    # 对话上下文和状态
    context = Column(JSON, default=dict)  # 对话上下文信息
    state = Column(JSON, default=dict)    # 对话状态信息
    meta_data = Column(JSON, default=dict) # 元数据
    
    # 用户偏好和学习数据
    user_preferences = Column(JSON, default=dict)
    learned_patterns = Column(JSON, default=dict)
    
    # 统计信息
    message_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """消息模型"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Agent相关信息
    agent_type = Column(String(100))  # 处理消息的Agent类型
    agent_id = Column(String(255))    # Agent实例ID
    
    # 消息元数据
    meta_data = Column(JSON, default=dict)
    confidence = Column(JSON, default=dict)  # 置信度信息
    
    # 处理信息
    processing_time = Column(Integer)  # 处理时间(毫秒)
    tokens_used = Column(Integer)      # 使用的token数量
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")


class ConversationState(Base):
    """对话状态跟踪模型"""
    __tablename__ = "conversation_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    # 状态信息
    current_task = Column(String(255))
    current_agent = Column(String(100))
    context_variables = Column(JSON, default=dict)
    
    # 对话流程状态
    flow_state = Column(String(100))
    step_history = Column(JSON, default=list)
    
    # 用户意图和实体
    last_intent = Column(String(100))
    entities = Column(JSON, default=dict)
    
    # 会话记忆
    short_term_memory = Column(JSON, default=dict)
    long_term_memory = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    conversation = relationship("Conversation")