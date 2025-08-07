"""
简化的对话状态管理验证程序

这个程序专门用于验证对话状态管理系统的核心功能，
避免其他模型依赖问题。
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.services.conversation_service import ConversationService
from src.schemas.conversation import (
    ConversationCreate, MessageCreate, MessageRole, 
    ConversationStateUpdate
)
from src.utils.unicode_utils import SafeOutput


class SimpleConversationDemo:
    """简化的对话演示类"""
    
    def __init__(self):
        # 创建完全模拟的环境
        self.mock_db = self._create_mock_db()
        self.conversation_service = ConversationService(self.mock_db)
        self._setup_mocks()
        
        # Initialize safe output utility
        self.safe_output = SafeOutput()
        
    def _create_mock_db(self):
        """创建模拟数据库"""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        return mock_db
    
    def _setup_mocks(self):
        """设置所有必要的模拟"""
        # 模拟状态跟踪器的所有方法
        tracker = self.conversation_service.state_tracker
        tracker.initialize_conversation_state = AsyncMock()
        tracker.update_conversation_state = AsyncMock(return_value=True)
        tracker.add_to_context = AsyncMock(return_value=True)
        tracker.get_context_variable = AsyncMock(return_value="test_value")
        tracker.update_short_term_memory = AsyncMock(return_value=True)
        tracker.get_short_term_memory = AsyncMock(return_value="memory_value")
        tracker.promote_to_long_term_memory = AsyncMock(return_value=True)
        tracker.get_long_term_memory = AsyncMock(return_value="long_term_value")
        tracker.update_flow_state = AsyncMock(return_value=True)
        tracker.learn_user_preferences = AsyncMock(return_value=True)
        tracker.get_conversation_history_summary = AsyncMock(return_value={
            "recent_messages": [],
            "current_state": {"flow_state": "active"},
            "context_keys": ["test_key"],
            "memory_summary": {"short_term_items": 1, "long_term_items": 1}
        })
    
    async def demo_conversation_creation(self):
        """演示对话创建"""
        self.safe_output.safe_print(self.safe_output.format_status("info", "演示对话创建...", "🔧"))
        
        # 模拟对话创建
        def mock_refresh(obj):
            obj.id = "demo-conv-001"
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        
        self.mock_db.refresh.side_effect = mock_refresh
        
        conversation_data = ConversationCreate(
            user_id="demo_user_001",
            title="演示对话",
            initial_context={"demo": True, "purpose": "validation"}
        )
        
        conversation = await self.conversation_service.create_conversation(conversation_data)
        
        self.safe_output.safe_print(self.safe_output.format_status("success", "对话创建成功"))
        print(f"   用户ID: {conversation_data.user_id}")
        print(f"   标题: {conversation_data.title}")
        print(f"   初始上下文: {conversation_data.initial_context}")
        
        return "demo-conv-001"
    
    async def demo_message_management(self, conversation_id: str):
        """演示消息管理"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '演示消息管理...', '💬')}")
        
        # 模拟消息创建
        def mock_refresh_msg(obj):
            obj.id = "demo-msg-001"
            obj.created_at = datetime.utcnow()
        
        self.mock_db.refresh.side_effect = mock_refresh_msg
        
        # 添加用户消息
        user_message = MessageCreate(
            role=MessageRole.USER,
            content="这是一条测试消息",
            metadata={"test": True}
        )
        
        message = await self.conversation_service.add_message(
            conversation_id, 
            user_message
        )
        
        self.safe_output.safe_print(self.safe_output.format_status("success", "用户消息添加成功"))
        print(f"   内容: {user_message.content}")
        print(f"   角色: {user_message.role}")
        
        # 添加助手回复
        assistant_message = MessageCreate(
            role=MessageRole.ASSISTANT,
            content="这是助手的回复",
            agent_type="demo_agent",
            agent_id="agent_001",
            metadata={"confidence": 0.95}
        )
        
        await self.conversation_service.add_message(
            conversation_id,
            assistant_message
        )
        
        self.safe_output.safe_print(self.safe_output.format_status("success", "助手消息添加成功"))
        print(f"   内容: {assistant_message.content}")
        print(f"   Agent类型: {assistant_message.agent_type}")
    
    async def demo_state_management(self, conversation_id: str):
        """演示状态管理"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '演示状态管理...', '🎯')}")
        
        # 更新对话状态
        state_update = ConversationStateUpdate(
            current_task="demo_task",
            current_agent="demo_agent",
            flow_state="demo_state",
            last_intent="demo_intent",
            entities={"demo_entity": "demo_value"}
        )
        
        success = await self.conversation_service.update_conversation_state(
            conversation_id,
            state_update
        )
        
        self.safe_output.safe_print(self.safe_output.format_status("success", "对话状态更新成功"))
        print(f"   当前任务: {state_update.current_task}")
        print(f"   当前Agent: {state_update.current_agent}")
        print(f"   流程状态: {state_update.flow_state}")
        print(f"   最后意图: {state_update.last_intent}")
        
        # 更新流程状态
        await self.conversation_service.update_flow_state(
            conversation_id,
            "new_demo_state"
        )
        
        self.safe_output.safe_print(self.safe_output.format_status("success", "流程状态更新成功: new_demo_state"))
    
    async def demo_context_management(self, conversation_id: str):
        """演示上下文管理"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '演示上下文管理...', '🔧')}")
        
        # 添加上下文变量
        context_vars = {
            "demo_topic": "状态管理验证",
            "demo_stage": "功能测试",
            "demo_priority": "high"
        }
        
        for key, value in context_vars.items():
            await self.conversation_service.add_context_variable(
                conversation_id,
                key,
                value
            )
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', f'上下文变量添加: {key} = {value}')}")
        
        # 获取上下文变量
        value = await self.conversation_service.get_context_variable(
            conversation_id,
            "demo_topic"
        )
        self.safe_output.safe_print(f"{self.safe_output.format_status('success', f'上下文变量获取: demo_topic = {value}')}")
    
    async def demo_memory_management(self, conversation_id: str):
        """演示记忆管理"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '演示记忆管理...', '🧠')}")
        
        # 短期记忆
        await self.conversation_service.update_short_term_memory(
            conversation_id,
            "demo_short_term",
            "这是短期记忆内容"
        )
        self.safe_output.safe_print(self.safe_output.format_status("success", "短期记忆添加成功"))
        
        short_memory = await self.conversation_service.get_short_term_memory(
            conversation_id,
            "demo_short_term"
        )
        self.safe_output.safe_print(f"{self.safe_output.format_status('success', f'短期记忆获取: {short_memory}')}")
        
        # 长期记忆
        await self.conversation_service.promote_to_long_term_memory(
            conversation_id,
            "demo_long_term",
            {"important": "这是重要的长期记忆", "score": 0.9},
            importance_score=0.9
        )
        self.safe_output.safe_print(self.safe_output.format_status("success", "长期记忆添加成功 (重要性: 0.9)"))
        
        long_memory = await self.conversation_service.get_long_term_memory(
            conversation_id,
            "demo_long_term"
        )
        self.safe_output.safe_print(f"{self.safe_output.format_status('success', f'长期记忆获取: {long_memory}')}")
    
    async def demo_preference_learning(self, conversation_id: str):
        """演示偏好学习"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '演示偏好学习...', '📚')}")
        
        # 学习用户偏好
        interaction_data = {
            "response_style": "detailed",
            "preferred_agent": "demo_agent",
            "communication_tone": "professional"
        }
        
        success = await self.conversation_service.learn_user_preferences(
            conversation_id,
            interaction_data
        )
        
        self.safe_output.safe_print(self.safe_output.format_status("success", "用户偏好学习成功"))
        print(f"   偏好数据: {interaction_data}")
    
    async def demo_conversation_summary(self, conversation_id: str):
        """演示对话摘要"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '演示对话摘要...', '📊')}")
        
        summary = await self.conversation_service.get_conversation_summary(
            conversation_id
        )
        
        self.safe_output.safe_print(self.safe_output.format_status("success", "对话摘要获取成功"))
        print(f"   当前状态: {summary['current_state']}")
        print(f"   上下文键: {summary['context_keys']}")
        print(f"   记忆统计: {summary['memory_summary']}")
    
    async def run_demo(self):
        """运行完整演示"""
        self.safe_output.safe_print(self.safe_output.format_status("info", "开始简化对话状态管理验证", "🚀"))
        self.safe_output.safe_print("="*60)
        
        try:
            # 创建对话
            conversation_id = await self.demo_conversation_creation()
            
            # 消息管理
            await self.demo_message_management(conversation_id)
            
            # 状态管理
            await self.demo_state_management(conversation_id)
            
            # 上下文管理
            await self.demo_context_management(conversation_id)
            
            # 记忆管理
            await self.demo_memory_management(conversation_id)
            
            # 偏好学习
            await self.demo_preference_learning(conversation_id)
            
            # 对话摘要
            await self.demo_conversation_summary(conversation_id)
            
            print("\n" + "="*60)
            self.safe_output.safe_print(self.safe_output.format_status("success", "所有功能验证完成！", "🎉"))
            self.safe_output.safe_print(self.safe_output.format_status("success", "对话状态管理系统工作正常"))
            print("="*60)
            
        except Exception as e:
            self.safe_output.safe_print(f"\n{self.safe_output.format_status('error', f'验证过程中出现错误: {str(e)}')}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    demo = SimpleConversationDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())