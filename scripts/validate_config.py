#!/usr/bin/env python3
"""
配置验证脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def validate_database_connection():
    """验证数据库连接"""
    try:
        from src.core.database import engine, redis_client
        
        # 测试PostgreSQL连接
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            assert result.scalar() == 1
        logger.info("✅ PostgreSQL连接正常")
        
        # 测试Redis连接
        await redis_client.ping()
        logger.info("✅ Redis连接正常")
        
        return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False


async def validate_llm_service():
    """验证LLM服务"""
    try:
        from src.services.llm_service import llm_service
        
        if not llm_service.is_available():
            logger.warning("⚠️ LLM服务未配置")
            return False
        
        # 测试简单的LLM调用
        messages = [{"role": "user", "content": "Hello"}]
        response = await llm_service.chat_completion(messages, max_tokens=10)
        
        if response.get("content"):
            logger.info("✅ LLM服务正常")
            return True
        else:
            logger.error("❌ LLM服务响应异常")
            return False
            
    except Exception as e:
        logger.error(f"❌ LLM服务验证失败: {e}")
        return False


def validate_configuration():
    """验证配置"""
    logger.info("开始验证配置...")
    
    # 检查必要的配置项
    config_checks = [
        ("APP_NAME", settings.APP_NAME),
        ("VERSION", settings.VERSION),
        ("SECRET_KEY", settings.SECRET_KEY != "your-secret-key-change-in-production"),
        ("DATABASE_URL", settings.DATABASE_URL),
        ("REDIS_URL", settings.REDIS_URL),
    ]
    
    all_good = True
    
    for name, value in config_checks:
        if value:
            logger.info(f"✅ {name}: 已配置")
        else:
            logger.error(f"❌ {name}: 未正确配置")
            all_good = False
    
    # 检查可选配置
    optional_checks = [
        ("OPENAI_API_KEY", settings.openai_configured, "LLM功能"),
        ("QDRANT_URL", settings.qdrant_configured, "向量数据库"),
    ]
    
    for name, configured, description in optional_checks:
        if configured:
            logger.info(f"✅ {name}: 已配置 ({description})")
        else:
            logger.warning(f"⚠️ {name}: 未配置 ({description}功能将不可用)")
    
    # 检查环境设置
    if settings.is_development:
        logger.info("🔧 运行环境: 开发模式")
    else:
        logger.info("🚀 运行环境: 生产模式")
        if settings.SECRET_KEY == "your-secret-key-change-in-production":
            logger.error("❌ 生产环境必须更改默认SECRET_KEY")
            all_good = False
    
    return all_good


async def main():
    """主函数"""
    logger.info("HiCRM配置验证工具")
    logger.info("=" * 50)
    
    # 验证基础配置
    config_ok = validate_configuration()
    
    # 验证数据库连接
    db_ok = await validate_database_connection()
    
    # 验证LLM服务
    llm_ok = await validate_llm_service()
    
    logger.info("=" * 50)
    
    if config_ok and db_ok:
        logger.info("🎉 配置验证通过！系统可以正常启动")
        if llm_ok:
            logger.info("🤖 LLM功能已就绪")
        else:
            logger.info("⚠️ LLM功能不可用，但系统仍可正常运行")
        return 0
    else:
        logger.error("💥 配置验证失败！请检查配置后重试")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)