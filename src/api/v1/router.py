"""
API v1 路由配置
"""

from fastapi import APIRouter
from src.api.v1.endpoints import customers, leads, opportunities, conversations, system

api_router = APIRouter()

# 注册系统管理路由
api_router.include_router(
    system.router,
    prefix="/system",
    tags=["system"]
)

# 注册各模块路由
api_router.include_router(
    customers.router,
    prefix="/customers",
    tags=["customers"]
)

api_router.include_router(
    leads.router,
    prefix="/leads", 
    tags=["leads"]
)

api_router.include_router(
    opportunities.router,
    prefix="/opportunities",
    tags=["opportunities"]
)

api_router.include_router(
    conversations.router,
    prefix="/conversations",
    tags=["conversations"]
)