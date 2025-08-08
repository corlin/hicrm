"""
Agent系统模块

基于LangGraph框架的多专业Agent协作系统，提供智能化的CRM业务处理能力。
"""

from .base import BaseAgent, AgentState, AgentMessage, AgentResponse
from .manager import AgentManager
from .communication import MessageBroker, AgentCommunicator
from .state_manager import AgentStateManager

__all__ = [
    "BaseAgent",
    "AgentState", 
    "AgentMessage",
    "AgentResponse",
    "AgentManager",
    "MessageBroker",
    "AgentCommunicator", 
    "AgentStateManager",
]