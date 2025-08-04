"""
销售机会API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.core.database import get_db
from src.schemas.opportunity import OpportunityCreate, OpportunityUpdate, OpportunityResponse
from src.services.opportunity_service import OpportunityService

router = APIRouter()


@router.get("/", response_model=List[OpportunityResponse])
async def get_opportunities(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取销售机会列表"""
    service = OpportunityService(db)
    opportunities = await service.get_opportunities(skip=skip, limit=limit)
    return opportunities


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个销售机会信息"""
    service = OpportunityService(db)
    opportunity = await service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售机会不存在"
        )
    return opportunity


@router.post("/", response_model=OpportunityResponse)
async def create_opportunity(
    opportunity_data: OpportunityCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新销售机会"""
    service = OpportunityService(db)
    opportunity = await service.create_opportunity(opportunity_data)
    return opportunity


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    opportunity_data: OpportunityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新销售机会信息"""
    service = OpportunityService(db)
    opportunity = await service.update_opportunity(opportunity_id, opportunity_data)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售机会不存在"
        )
    return opportunity


@router.post("/{opportunity_id}/advance-stage")
async def advance_opportunity_stage(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db)
):
    """推进销售机会到下一阶段"""
    service = OpportunityService(db)
    success = await service.advance_stage(opportunity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售机会不存在或无法推进"
        )
    return {"message": "销售机会阶段推进成功"}