"""
数据库核心功能测试
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from src.core.database import (
    get_db, get_redis, init_db, close_db, 
    engine, AsyncSessionLocal, redis_client, Base
)


class TestDatabaseCore:
    """数据库核心功能测试类"""
    
    @pytest.mark.asyncio
    async def test_get_db_session(self):
        """测试获取数据库会话"""
        async for session in get_db():
            assert isinstance(session, AsyncSession)
            assert session.is_active
            break
    
    @pytest.mark.asyncio
    async def test_get_db_session_rollback_on_error(self):
        """测试数据库会话在异常时回滚"""
        try:
            async for session in get_db():
                # 模拟数据库操作异常
                await session.execute(text("SELECT 1/0"))  # 除零错误
                await session.commit()
        except Exception:
            # 异常应该被正确处理
            pass
    
    @pytest.mark.asyncio
    async def test_get_redis_client(self):
        """测试获取Redis客户端"""
        client = await get_redis()
        assert isinstance(client, redis.Redis)
        assert client is redis_client
    
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """测试Redis连接"""
        client = await get_redis()
        
        # 测试基本操作
        await client.set("test_key", "test_value", ex=60)
        value = await client.get("test_key")
        assert value == "test_value"
        
        # 清理测试数据
        await client.delete("test_key")
    
    @pytest.mark.asyncio
    async def test_init_db_success(self):
        """测试数据库初始化成功"""
        with patch('src.core.database.engine') as mock_engine, \
             patch('src.core.database.redis_client') as mock_redis:
            
            # 模拟数据库连接
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            # 模拟Redis连接
            mock_redis.ping = AsyncMock()
            
            # 执行初始化
            await init_db()
            
            # 验证调用
            mock_engine.begin.assert_called_once()
            mock_conn.run_sync.assert_called_once()
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_init_db_failure(self):
        """测试数据库初始化失败"""
        with patch('src.core.database.engine') as mock_engine:
            # 模拟数据库连接失败
            mock_engine.begin.side_effect = Exception("连接失败")
            
            # 验证异常被抛出
            with pytest.raises(Exception, match="连接失败"):
                await init_db()
    
    @pytest.mark.asyncio
    async def test_close_db(self):
        """测试关闭数据库连接"""
        with patch('src.core.database.engine') as mock_engine, \
             patch('src.core.database.redis_client') as mock_redis:
            
            mock_engine.dispose = AsyncMock()
            mock_redis.close = AsyncMock()
            
            await close_db()
            
            mock_engine.dispose.assert_called_once()
            mock_redis.close.assert_called_once()
    
    def test_base_metadata_naming_convention(self):
        """测试数据库模型基类的命名约定"""
        naming_convention = Base.metadata.naming_convention
        
        assert "ix_%(column_0_label)s" == naming_convention["ix"]
        assert "uq_%(table_name)s_%(column_0_name)s" == naming_convention["uq"]
        assert "ck_%(table_name)s_%(constraint_name)s" == naming_convention["ck"]
        assert "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s" == naming_convention["fk"]
        assert "pk_%(table_name)s" == naming_convention["pk"]
    
    @pytest.mark.asyncio
    async def test_database_connection_pool(self):
        """测试数据库连接池配置"""
        # 验证引擎配置
        assert engine.pool.pre_ping is True
        assert engine.pool.recycle == 300
    
    @pytest.mark.asyncio
    async def test_session_factory_configuration(self):
        """测试会话工厂配置"""
        # 创建会话实例
        async with AsyncSessionLocal() as session:
            assert isinstance(session, AsyncSession)
            assert session.expire_on_commit is False
    
    @pytest.mark.asyncio
    async def test_concurrent_database_sessions(self):
        """测试并发数据库会话"""
        async def create_session():
            async for session in get_db():
                # 执行简单查询
                result = await session.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                assert row.test == 1
                return True
        
        # 创建多个并发会话
        tasks = [create_session() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert all(results)
        assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_redis_connection_pool(self):
        """测试Redis连接池"""
        client = await get_redis()
        
        # 测试连接池信息
        pool_info = client.connection_pool.connection_kwargs
        assert 'decode_responses' in pool_info
        assert pool_info['decode_responses'] is True
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self):
        """测试数据库事务回滚"""
        async with AsyncSessionLocal() as session:
            try:
                # 开始事务
                await session.begin()
                
                # 执行一些操作（这里只是示例）
                await session.execute(text("SELECT 1"))
                
                # 模拟异常
                raise Exception("测试异常")
                
            except Exception:
                # 回滚事务
                await session.rollback()
                
                # 验证会话状态
                assert not session.in_transaction()
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self):
        """测试Redis错误处理"""
        with patch('src.core.database.redis_client') as mock_redis:
            # 模拟Redis连接错误
            mock_redis.ping.side_effect = redis.ConnectionError("连接失败")
            
            client = await get_redis()
            
            # 验证错误被正确抛出
            with pytest.raises(redis.ConnectionError):
                await client.ping()