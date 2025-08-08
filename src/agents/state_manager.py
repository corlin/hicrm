"""
Agent状态管理器

使用Redis实现Agent状态的持久化存储和管理。
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

import redis.asyncio as redis
from pydantic import BaseModel

from .base import AgentState, AgentStatus
from ..core.config import settings


logger = logging.getLogger(__name__)


class StateManagerConfig(BaseModel):
    """状态管理器配置"""
    redis_url: str = settings.REDIS_URL
    key_prefix: str = "agent:state:"
    ttl: int = 86400  # 24小时
    cleanup_interval: int = 3600  # 1小时清理一次过期状态


class AgentStateManager:
    """
    Agent状态管理器
    
    负责Agent状态的持久化存储、检索和管理，使用Redis作为存储后端。
    """
    
    def __init__(self, config: Optional[StateManagerConfig] = None):
        self.config = config or StateManagerConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """初始化状态管理器"""
        try:
            # 创建Redis连接
            self.redis_client = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # 测试连接
            await self.redis_client.ping()
            self.logger.info("Agent state manager initialized successfully")
            
            # 启动清理任务
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_states())
            
        except Exception as e:
            self.logger.error(f"Failed to initialize state manager: {e}")
            raise
    
    async def close(self) -> None:
        """关闭状态管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Agent state manager closed")
    
    def _get_state_key(self, agent_id: str) -> str:
        """获取状态存储键"""
        return f"{self.config.key_prefix}{agent_id}"
    
    def _get_index_key(self) -> str:
        """获取索引键"""
        return f"{self.config.key_prefix}index"
    
    async def save_state(self, agent_id: str, state: AgentState) -> None:
        """
        保存Agent状态
        
        Args:
            agent_id: Agent ID
            state: Agent状态
        """
        if not self.redis_client:
            raise RuntimeError("State manager not initialized")
        
        try:
            state_key = self._get_state_key(agent_id)
            index_key = self._get_index_key()
            
            # 序列化状态
            state_data = state.dict()
            state_data["last_active"] = state.last_active.isoformat()
            
            # 使用管道操作确保原子性
            pipe = self.redis_client.pipeline()
            
            # 保存状态数据
            pipe.hset(state_key, mapping={
                "data": json.dumps(state_data),
                "updated_at": datetime.now().isoformat()
            })
            
            # 设置TTL
            pipe.expire(state_key, self.config.ttl)
            
            # 更新索引
            pipe.sadd(index_key, agent_id)
            
            await pipe.execute()
            
            self.logger.debug(f"Saved state for agent {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save state for agent {agent_id}: {e}")
            raise
    
    async def load_state(self, agent_id: str) -> Optional[AgentState]:
        """
        加载Agent状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent状态，如果不存在则返回None
        """
        if not self.redis_client:
            raise RuntimeError("State manager not initialized")
        
        try:
            state_key = self._get_state_key(agent_id)
            
            # 获取状态数据
            state_hash = await self.redis_client.hgetall(state_key)
            
            if not state_hash or "data" not in state_hash:
                return None
            
            # 反序列化状态
            state_data = json.loads(state_hash["data"])
            
            # 转换时间字段
            if "last_active" in state_data:
                state_data["last_active"] = datetime.fromisoformat(state_data["last_active"])
            
            state = AgentState(**state_data)
            
            self.logger.debug(f"Loaded state for agent {agent_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to load state for agent {agent_id}: {e}")
            return None
    
    async def delete_state(self, agent_id: str) -> bool:
        """
        删除Agent状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功删除
        """
        if not self.redis_client:
            raise RuntimeError("State manager not initialized")
        
        try:
            state_key = self._get_state_key(agent_id)
            index_key = self._get_index_key()
            
            # 使用管道操作
            pipe = self.redis_client.pipeline()
            pipe.delete(state_key)
            pipe.srem(index_key, agent_id)
            
            results = await pipe.execute()
            deleted = results[0] > 0
            
            if deleted:
                self.logger.debug(f"Deleted state for agent {agent_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete state for agent {agent_id}: {e}")
            return False
    
    async def list_agents(self) -> List[str]:
        """
        列出所有有状态的Agent
        
        Returns:
            Agent ID列表
        """
        if not self.redis_client:
            raise RuntimeError("State manager not initialized")
        
        try:
            index_key = self._get_index_key()
            agent_ids = await self.redis_client.smembers(index_key)
            return list(agent_ids)
            
        except Exception as e:
            self.logger.error(f"Failed to list agents: {e}")
            return []
    
    async def get_agents_by_status(self, status: AgentStatus) -> List[str]:
        """
        根据状态获取Agent列表
        
        Args:
            status: Agent状态
            
        Returns:
            符合条件的Agent ID列表
        """
        agent_ids = await self.list_agents()
        matching_agents = []
        
        for agent_id in agent_ids:
            state = await self.load_state(agent_id)
            if state and state.status == status:
                matching_agents.append(agent_id)
        
        return matching_agents
    
    async def get_active_agents(self, since: Optional[datetime] = None) -> List[str]:
        """
        获取活跃的Agent列表
        
        Args:
            since: 活跃时间阈值，默认为1小时前
            
        Returns:
            活跃的Agent ID列表
        """
        if since is None:
            since = datetime.now() - timedelta(hours=1)
        
        agent_ids = await self.list_agents()
        active_agents = []
        
        for agent_id in agent_ids:
            state = await self.load_state(agent_id)
            if state and state.last_active >= since:
                active_agents.append(agent_id)
        
        return active_agents
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """
        更新Agent状态
        
        Args:
            agent_id: Agent ID
            status: 新状态
            
        Returns:
            是否成功更新
        """
        state = await self.load_state(agent_id)
        if not state:
            return False
        
        state.status = status
        state.last_active = datetime.now()
        
        await self.save_state(agent_id, state)
        return True
    
    async def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取Agent性能指标
        
        Args:
            agent_id: Agent ID
            
        Returns:
            性能指标字典
        """
        state = await self.load_state(agent_id)
        if not state:
            return None
        
        return {
            "agent_id": agent_id,
            "status": state.status,
            "error_count": state.error_count,
            "last_active": state.last_active,
            "performance_metrics": state.performance_metrics,
            "uptime": (datetime.now() - state.last_active).total_seconds()
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        获取系统级别的Agent指标
        
        Returns:
            系统指标字典
        """
        agent_ids = await self.list_agents()
        
        status_counts = {status: 0 for status in AgentStatus}
        total_errors = 0
        active_count = 0
        
        for agent_id in agent_ids:
            state = await self.load_state(agent_id)
            if state:
                status_counts[state.status] += 1
                total_errors += state.error_count
                
                # 检查是否在最近1小时内活跃
                if (datetime.now() - state.last_active).total_seconds() < 3600:
                    active_count += 1
        
        return {
            "total_agents": len(agent_ids),
            "active_agents": active_count,
            "status_distribution": status_counts,
            "total_errors": total_errors,
            "average_errors": total_errors / len(agent_ids) if agent_ids else 0
        }
    
    async def _cleanup_expired_states(self) -> None:
        """清理过期的Agent状态"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                
                agent_ids = await self.list_agents()
                expired_agents = []
                
                for agent_id in agent_ids:
                    state_key = self._get_state_key(agent_id)
                    ttl = await self.redis_client.ttl(state_key)
                    
                    # 如果TTL为-1（永不过期）或-2（不存在），则需要清理
                    if ttl == -2:
                        expired_agents.append(agent_id)
                
                # 清理过期的Agent
                if expired_agents:
                    index_key = self._get_index_key()
                    await self.redis_client.srem(index_key, *expired_agents)
                    self.logger.info(f"Cleaned up {len(expired_agents)} expired agent states")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error during state cleanup: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        try:
            if not self.redis_client:
                return {"status": "error", "message": "Not initialized"}
            
            # 测试Redis连接
            await self.redis_client.ping()
            
            # 获取基本统计信息
            agent_count = len(await self.list_agents())
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "agent_count": agent_count,
                "cleanup_task_running": self._cleanup_task and not self._cleanup_task.done()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "redis_connected": False
            }