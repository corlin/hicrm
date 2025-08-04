"""
配置测试
"""

import pytest
import os
from unittest.mock import patch

from src.core.config import Settings


class TestSettings:
    """配置测试类"""
    
    def test_default_settings(self):
        """测试默认设置"""
        settings = Settings()
        
        assert settings.APP_NAME == "HiCRM"
        assert settings.VERSION == "0.1.0"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.DEBUG is False
    
    def test_environment_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {
            'DEBUG': 'true',
            'PORT': '9000',
            'APP_NAME': 'TestCRM'
        }):
            settings = Settings()
            
            assert settings.DEBUG is True
            assert settings.PORT == 9000
            assert settings.APP_NAME == "TestCRM"
    
    def test_allowed_hosts_parsing(self):
        """测试ALLOWED_HOSTS解析"""
        # 测试JSON字符串格式
        with patch.dict(os.environ, {
            'ALLOWED_HOSTS': '["localhost", "127.0.0.1"]'
        }):
            settings = Settings()
            assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
        
        # 测试单个字符串格式
        with patch.dict(os.environ, {
            'ALLOWED_HOSTS': 'localhost'
        }):
            settings = Settings()
            assert settings.ALLOWED_HOSTS == ["localhost"]
    
    def test_properties(self):
        """测试属性方法"""
        # 测试开发环境
        settings = Settings(DEBUG=True)
        assert settings.is_development is True
        assert settings.is_production is False
        
        # 测试生产环境
        settings = Settings(DEBUG=False)
        assert settings.is_development is False
        assert settings.is_production is True
    
    def test_database_url_sync(self):
        """测试同步数据库URL"""
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
        )
        assert settings.database_url_sync == "postgresql://user:pass@localhost/db"
    
    def test_openai_configured(self):
        """测试OpenAI配置检查"""
        # 未配置
        settings = Settings(OPENAI_API_KEY=None)
        assert settings.openai_configured is False
        
        # 已配置
        settings = Settings(OPENAI_API_KEY="sk-test")
        assert settings.openai_configured is True
    
    def test_qdrant_configured(self):
        """测试Qdrant配置检查"""
        # 未配置
        settings = Settings(QDRANT_URL="")
        assert settings.qdrant_configured is False
        
        # 已配置
        settings = Settings(QDRANT_URL="http://localhost:6333")
        assert settings.qdrant_configured is True
    
    def test_log_config(self):
        """测试日志配置"""
        settings = Settings(DEBUG=True, LOG_LEVEL="DEBUG")
        log_config = settings.get_log_config()
        
        assert log_config["version"] == 1
        assert "formatters" in log_config
        assert "handlers" in log_config
        assert "loggers" in log_config
        
        # 开发环境只有控制台输出
        assert len(log_config["loggers"][""]["handlers"]) == 1
        
        # 生产环境有文件输出
        settings = Settings(DEBUG=False)
        log_config = settings.get_log_config()
        assert len(log_config["loggers"][""]["handlers"]) == 2