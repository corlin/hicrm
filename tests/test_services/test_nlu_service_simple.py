"""
NLU服务简单测试
"""

import pytest
import asyncio
from datetime import datetime

from src.services.nlu_service import (
    DialogueStateTracker,
    ChineseNLUProcessor,
    IntentType,
    EntityType,
    Intent,
    Entity,
    DialogueState
)


class TestChineseNLUProcessor:
    """中文NLU处理器测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.processor = ChineseNLUProcessor()
    
    def test_extract_intent_customer_inquiry(self):
        """测试客户查询意图识别"""
        text = "查询客户ABC公司的信息"
        intent = self.processor.extract_intent(text)
        
        assert intent.type == IntentType.CUSTOMER_INQUIRY
        assert intent.confidence > 0.5
        assert intent.metadata["method"] == "rule_based"
    
    def test_extract_intent_lead_create(self):
        """测试创建线索意图识别"""
        text = "新增一个线索，联系人张三"
        intent = self.processor.extract_intent(text)
        
        assert intent.type == IntentType.LEAD_CREATE
        assert intent.confidence > 0.5
    
    def test_extract_intent_greeting(self):
        """测试问候意图识别"""
        text = "你好，我想咨询一下"
        intent = self.processor.extract_intent(text)
        
        assert intent.type == IntentType.GREETING
        assert intent.confidence > 0.5
    
    def test_extract_intent_unknown(self):
        """测试未知意图识别"""
        text = "这是一个完全无关的句子"
        intent = self.processor.extract_intent(text)
        
        assert intent.type == IntentType.UNKNOWN
        assert intent.confidence == 0.0
    
    def test_extract_entities_person_name(self):
        """测试人名实体识别"""
        text = "联系人张三，电话123456789"
        entities = self.processor.extract_entities(text)
        
        person_entities = [e for e in entities if e.type == EntityType.PERSON_NAME]
        assert len(person_entities) > 0
        assert person_entities[0].value == "张三"
    
    def test_extract_entities_company_name(self):
        """测试公司名实体识别"""
        text = "ABC科技有限公司需要CRM系统"
        entities = self.processor.extract_entities(text)
        
        company_entities = [e for e in entities if e.type == EntityType.COMPANY_NAME]
        assert len(company_entities) > 0
        assert "ABC科技有限公司" in company_entities[0].value
    
    def test_extract_entities_amount(self):
        """测试金额实体识别"""
        text = "预算50万元，项目周期6个月"
        entities = self.processor.extract_entities(text)
        
        amount_entities = [e for e in entities if e.type == EntityType.AMOUNT]
        assert len(amount_entities) > 0
        assert "50万" in amount_entities[0].value


class TestDialogueStateTracker:
    """对话状态跟踪器测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.tracker = DialogueStateTracker()
    
    def test_get_or_create_dialogue_state(self):
        """测试获取或创建对话状态"""
        conversation_id = "test-conv-1"
        user_id = "user-123"
        
        # 第一次调用应该创建新状态
        state1 = self.tracker.get_or_create_dialogue_state(conversation_id, user_id)
        assert state1.conversation_id == conversation_id
        assert state1.user_id == user_id
        
        # 第二次调用应该返回相同状态
        state2 = self.tracker.get_or_create_dialogue_state(conversation_id, user_id)
        assert state1 is state2
    
    @pytest.mark.asyncio
    async def test_process_utterance_customer_inquiry(self):
        """测试处理客户查询话语"""
        conversation_id = "test-conv-1"
        user_id = "user-123"
        text = "查询ABC公司的客户信息"
        
        intent, entities, dialogue_state = await self.tracker.process_utterance(
            conversation_id, user_id, text
        )
        
        # 验证意图识别
        assert intent.type == IntentType.CUSTOMER_INQUIRY
        assert intent.confidence > 0.5
        
        # 验证实体识别
        company_entities = [e for e in entities if e.type == EntityType.COMPANY_NAME]
        assert len(company_entities) > 0
        
        # 验证对话状态更新
        assert dialogue_state.current_intent.type == IntentType.CUSTOMER_INQUIRY
        assert len(dialogue_state.dialogue_history) == 1
        assert len(dialogue_state.context_entities) > 0
    
    @pytest.mark.asyncio
    async def test_process_utterance_lead_create(self):
        """测试处理创建线索话语"""
        conversation_id = "test-conv-2"
        user_id = "user-456"
        text = "新增线索，联系人张三，公司是德芙科技"
        
        intent, entities, dialogue_state = await self.tracker.process_utterance(
            conversation_id, user_id, text
        )
        
        # 验证意图识别
        assert intent.type == IntentType.LEAD_CREATE
        
        # 验证实体识别
        person_entities = [e for e in entities if e.type == EntityType.PERSON_NAME]
        company_entities = [e for e in entities if e.type == EntityType.COMPANY_NAME]
        
        assert len(person_entities) > 0
        assert len(company_entities) > 0
        
        # 验证槽位填充
        assert "person_name" in dialogue_state.active_slots
        assert "company_name" in dialogue_state.active_slots
    
    def test_get_context_summary(self):
        """测试获取上下文摘要"""
        conversation_id = "test-conv-1"
        user_id = "user-123"
        
        # 创建并更新对话状态
        dialogue_state = self.tracker.get_or_create_dialogue_state(conversation_id, user_id)
        
        intent = Intent(IntentType.CUSTOMER_INQUIRY, 0.8)
        entities = [Entity(EntityType.COMPANY_NAME, "ABC公司", 0.9, 0, 5)]
        
        self.tracker.update_dialogue_state(dialogue_state, intent, entities, "查询ABC公司")
        
        # 获取上下文摘要
        summary = self.tracker.get_context_summary(conversation_id)
        
        assert summary["current_intent"] == IntentType.CUSTOMER_INQUIRY.value
        assert len(summary["context_entities"]) > 0
        assert summary["dialogue_turns"] == 1
        assert "last_updated" in summary
    
    def test_clear_dialogue_state(self):
        """测试清除对话状态"""
        conversation_id = "test-conv-1"
        user_id = "user-123"
        
        # 创建对话状态
        self.tracker.get_or_create_dialogue_state(conversation_id, user_id)
        assert conversation_id in self.tracker.dialogue_states
        
        # 清除对话状态
        self.tracker.clear_dialogue_state(conversation_id)
        assert conversation_id not in self.tracker.dialogue_states


if __name__ == "__main__":
    pytest.main([__file__, "-v"])