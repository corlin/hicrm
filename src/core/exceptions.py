"""
自定义异常类
"""

from typing import Any, Dict, Optional


class BaseCustomException(Exception):
    """基础自定义异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseCustomException):
    """验证错误"""
    pass


class NotFoundError(BaseCustomException):
    """资源不存在错误"""
    pass


class BusinessLogicError(BaseCustomException):
    """业务逻辑错误"""
    pass


class AuthenticationError(BaseCustomException):
    """认证错误"""
    pass


class AuthorizationError(BaseCustomException):
    """授权错误"""
    pass


class ExternalServiceError(BaseCustomException):
    """外部服务错误"""
    pass


class DatabaseError(BaseCustomException):
    """数据库错误"""
    pass