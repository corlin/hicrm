"""
简单的认证模块

为WebSocket路由器提供基础的用户认证功能。
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# 简单的用户模型
class User:
    def __init__(self, user_id: str, username: str, is_admin: bool = False):
        self.user_id = user_id
        self.username = username
        self.is_admin = is_admin

# 模拟用户数据库
MOCK_USERS = {
    "user-123": User("user-123", "test_user", False),
    "admin-456": User("admin-456", "admin_user", True)
}

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[User]:
    """
    获取当前用户（可选）
    
    这是一个简化的实现，实际项目中应该使用JWT或其他认证机制
    """
    if not credentials:
        return None
    
    try:
        # 简单的token验证（实际应该验证JWT）
        token = credentials.credentials
        
        # 模拟token解析
        if token.startswith("user-"):
            user_id = token
            return MOCK_USERS.get(user_id)
        
        return None
        
    except Exception as e:
        logger.error(f"用户认证失败: {e}")
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials
) -> User:
    """
    获取当前用户（必需）
    """
    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user