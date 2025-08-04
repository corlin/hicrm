"""
对话管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.core.database import get_db
from src.schemas.conversation import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from src.services.conversation_service import ConversationService

router = APIRouter()


@router.post("/", response_model=ConversationResponse)
async def start_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """开始新对话"""
    service = ConversationService(db)
    conversation = await service.start_conversation(conversation_data)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取对话信息"""
    service = ConversationService(db)
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    return conversation


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """发送消息"""
    service = ConversationService(db)
    message = await service.send_message(conversation_id, message_data)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    return message


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取对话消息历史"""
    service = ConversationService(db)
    messages = await service.get_messages(conversation_id, skip=skip, limit=limit)
    return messages


@router.delete("/{conversation_id}")
async def end_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """结束对话"""
    service = ConversationService(db)
    success = await service.end_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    return {"message": "对话已结束"}