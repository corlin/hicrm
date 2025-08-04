"""
系统管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import asyncio
import logging

from src.core.config import settings
from src.core.database import get_redis
from src.services.llm_service import llm_service
import redis.asyncio as redis

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """系统健康检查"""
    health_status = {
        "status": "healthy",
        "service": "hicrm-api",
        "version": settings.VERSION,
        "environment": "development" if settings.is_development else "production",
        "timestamp": None
    }
    
    try:
        # 检查各个组件的健康状态
        checks = {}
        
        # 检查Redis连接
        try:
            redis_client = await get_redis()
            await redis_client.ping()
            checks["redis"] = {"status": "healthy", "url": settings.REDIS_URL}
        except Exception as e:
            checks["redis"] = {"status": "unhealthy", "error": str(e)}
        
        # 检查LLM服务
        checks["llm"] = {
            "status": "healthy" if llm_service.is_available() else "not_configured",
            "model": settings.DEFAULT_MODEL,
            "api_base": settings.OPENAI_BASE_URL
        }
        
        # 检查Qdrant
        checks["qdrant"] = {
            "status": "configured" if settings.qdrant_configured else "not_configured",
            "url": settings.QDRANT_URL
        }
        
        health_status["checks"] = checks
        health_status["timestamp"] = "2024-01-01T00:00:00Z"  # 实际应用中使用真实时间戳
        
        # 如果有任何组件不健康，返回503状态
        if any(check.get("status") == "unhealthy" for check in checks.values()):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status
            )
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": str(e)}
        )


@router.get("/config")
async def get_config():
    """获取系统配置信息（脱敏）"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "environment": "development" if settings.is_development else "production",
        "api_prefix": settings.API_V1_PREFIX,
        "features": {
            "llm_enabled": llm_service.is_available(),
            "qdrant_enabled": settings.qdrant_configured,
            "metrics_enabled": settings.ENABLE_METRICS,
        },
        "limits": {
            "default_page_size": settings.DEFAULT_PAGE_SIZE,
            "max_page_size": settings.MAX_PAGE_SIZE,
            "max_file_size": settings.MAX_FILE_SIZE,
            "cache_ttl": settings.CACHE_TTL
        }
    }


@router.get("/models")
async def get_model_info():
    """获取模型信息"""
    if not llm_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM服务未配置"
        )
    
    return llm_service.get_model_info()


@router.post("/test-llm")
async def test_llm_connection():
    """测试LLM连接"""
    if not llm_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM服务未配置"
        )
    
    try:
        # 发送一个简单的测试请求
        messages = [
            {"role": "user", "content": "请回复'连接测试成功'"}
        ]
        
        response = await llm_service.chat_completion(
            messages=messages,
            max_tokens=50,
            temperature=0.1
        )
        
        return {
            "status": "success",
            "model": response.get("model"),
            "response": response.get("content"),
            "usage": response.get("usage")
        }
        
    except Exception as e:
        logger.error(f"LLM连接测试失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM连接测试失败: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics():
    """获取系统指标"""
    if not settings.ENABLE_METRICS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指标收集未启用"
        )
    
    # 这里可以集成Prometheus指标或其他监控数据
    return {
        "status": "metrics_enabled",
        "port": settings.METRICS_PORT,
        "message": "指标收集已启用，请访问指标端点获取详细数据"
    }