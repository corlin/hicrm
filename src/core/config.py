"""
应用程序配置管理
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os
import json
from pathlib import Path


class Settings(BaseSettings):
    """应用程序设置"""
    
    # 基础配置
    APP_NAME: str = "HiCRM"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: Union[List[str], str] = ["*"]
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/hicrm"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    
    # 中文模型配置
    QWEN_API_KEY: Optional[str] = None
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    GLM_API_KEY: Optional[str] = None
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    
    # LLM服务配置
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT: int = 60
    LLM_DEFAULT_TEMPERATURE: float = 0.7
    LLM_MAX_CONTEXT_LENGTH: int = 4000
    
    # Function Calling配置
    ENABLE_FUNCTION_CALLING: bool = True
    ENABLE_MCP_TOOLS: bool = True
    
    # 向量数据库配置
    # Qdrant端口说明:
    # - 6333: HTTP REST API
    # - 6334: gRPC API (高性能，当前使用)
    QDRANT_URL: str = "localhost:6334"  # gRPC连接使用host:port格式
    QDRANT_USE_GRPC: bool = True  # 启用gRPC连接
    # 开发环境建议留空，生产环境设置实际API key
    QDRANT_API_KEY: Optional[str] = None
    
    # Elasticsearch配置
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    ELASTICSEARCH_INDEX_PREFIX: str = "hicrm"
    
    # BGE模型配置
    BGE_MODEL_NAME: str = "BAAI/bge-m3"
    BGE_RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    BGE_DEVICE: str = "cpu"  # 可以设置为 "cuda" 如果有GPU
    
    # 消息队列配置
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 文件存储配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 缓存配置
    CACHE_TTL: int = 3600  # 1小时
    CACHE_PREFIX: str = "hicrm:"
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 处理ALLOWED_HOSTS字符串格式
        if isinstance(self.ALLOWED_HOSTS, str):
            try:
                self.ALLOWED_HOSTS = json.loads(self.ALLOWED_HOSTS)
            except json.JSONDecodeError:
                self.ALLOWED_HOSTS = [self.ALLOWED_HOSTS]
        
        # 确保上传目录存在
        upload_path = Path(self.UPLOAD_DIR)
        upload_path.mkdir(exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.DEBUG
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.DEBUG
    
    @property
    def database_url_sync(self) -> str:
        """同步数据库URL（用于Alembic等工具）"""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    @property
    def openai_configured(self) -> bool:
        """检查OpenAI是否已配置"""
        return bool(self.OPENAI_API_KEY)
    
    @property
    def qdrant_configured(self) -> bool:
        """检查Qdrant是否已配置"""
        return bool(self.QDRANT_URL)
    
    @property
    def elasticsearch_configured(self) -> bool:
        """检查Elasticsearch是否已配置"""
        return bool(self.ELASTICSEARCH_URL)
    
    def get_log_config(self) -> dict:
        """获取日志配置"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": self.LOG_FORMAT,
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "formatter": "detailed",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/hicrm.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
            },
            "loggers": {
                "": {
                    "level": self.LOG_LEVEL,
                    "handlers": ["default", "file"] if not self.is_development else ["default"],
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["default"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": "INFO" if self.DEBUG else "WARNING",
                    "handlers": ["default"],
                    "propagate": False,
                },
            },
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


# 全局设置实例
settings = Settings()