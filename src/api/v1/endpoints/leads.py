"""
线索管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.core.database import get_db
from src.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from src.services.lead_service import LeadService

router = APIRouter()


@router.get("/", response_model=List[LeadResponse])
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取线索列表"""
    service = LeadService(db)
    leads = await service.get_leads(skip=skip, limit=limit)
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个线索信息"""
    service = LeadService(db)
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线索不存在"
        )
    return lead


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新线索"""
    service = LeadService(db)
    lead = await service.create_lead(lead_data)
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新线索信息"""
    service = LeadService(db)
    lead = await service.update_lead(lead_id, lead_data)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线索不存在"
        )
    return lead


@router.post("/{lead_id}/score")
async def calculate_lead_score(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """计算线索评分"""
    service = LeadService(db)
    score = await service.calculate_score(lead_id)
    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线索不存在"
        )
    return {"lead_id": lead_id, "score": score}