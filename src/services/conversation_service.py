"""
对话服务 - 占位符
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.conversation import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse


class ConversationService:
    """对话服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_conversations(self) -> List[ConversationResponse]:
        """获取对话列表"""
        return []
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """获取单个对话"""
        return None
    
    async def create_conversation(self, conversation_data: ConversationCreate) -> ConversationResponse:
        """创建对话"""
        raise NotImplementedError("待实现")
    
    async def add_message(self, conversation_id: str, message_data: MessageCreate) -> MessageResponse:
        """添加消息"""
        raise NotImplementedError("待实现")