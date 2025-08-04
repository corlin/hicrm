"""
对话Pydantic模式 - 占位符
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConversationBase(BaseModel):
    """对话基础模式"""
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """创建对话模式"""
    pass


class ConversationResponse(ConversationBase):
    """对话响应模式"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """消息基础模式"""
    content: str


class MessageCreate(MessageBase):
    """创建消息模式"""
    pass


class MessageResponse(MessageBase):
    """消息响应模式"""
    id: str
    conversation_id: str
    created_at: datetime

    class Config:
        from_attributes = True