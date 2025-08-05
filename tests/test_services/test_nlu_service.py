"""
NLU服务单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.nlu_service import (
    NLUService, 
    ChineseNLUProcessor,
    IntentType, 
    EntityType, 
    Entity, 
    Intent, 
    Slot, 
    NLUResult
)
from src.services.llm_service import EnhancedLLMService


class TestChineseNLUProcessor:
    """中文NLU处理器测试"""
    
    def setup_method(self):
        self.processor = ChineseNLUProcessor()
    
    def test_extract_company_entities(self):
        """测试公司实体提取"""
        text = "我想找一些华为科技和阿里巴巴集团的客户信息"
        entities = self.processor.extract_entities_by_pattern(text)
        
        company_entities = [e for e in entities if e.type == EntityType.COMPANY]
        assert len(company_entities) >= 1
        
        company_names = [e.value for e in company_entities]
        assert any("华为科技" in name for name in company_names)
    
    def test_extract_person_entities(self):
        """测试人名实体提取"""
        text = "请联系张总和李经理安排会议"
        entities = self.processor.extract_entities_by_pattern(text)
        
        person_entities = [e for e in entities if e.type == EntityType.PERSON]
        assert len(person_entities) >= 1
        
        person_names = [e.value for e in person_entities]
        assert any("张总" in name for name in person_names)
    
    def test_extract_budget_entities(self):
        """测试预算实体提取"""
        text = "客户预算是50万元，另一个项目需要100万"
        entities = self.processor.extract_entities_by_pattern(text)
        
        budget_entities = [e for e in entities if e.type == EntityType.BUDGET]
        assert len(budget_entities) >= 1
        
        # 测试标准化值
        for entity in budget_entities:
            if "50万" in entity.value:
                assert entity.normalized_value == 500000
    
    def test_extract_date_entities(self):
        """测试日期实体提取"""
        text = "明天和客户开会，下周三提交方案"
        entities = self.processor.extract_entities_by_pattern(text)
        
        date_entities = [e for e in entities if e.type == EntityType.DATE]
        assert len(date_entities) >= 1
        
        date_values = [e.value for e in date_entities]
        assert any("明天" in value for value in date_values)
    
    def test_classify_customer_search_intent(self):
        """测试客户搜索意图分类"""
        text = "帮我找一些制造业的潜在客户"
        intent, confidence = self.processor.classify_intent_by_keywords(text)
        
        assert intent == IntentType.CUSTOMER_SEARCH
        assert confidence > 0.0
    
    def test_classify_lead_create_intent(self):
        """测试线索创建意图分类"""
        text = "新建一个线索，公司是德芙科技"
        intent, confidence = self.processor.classify_intent_by_keywords(text)
        
        assert intent == IntentType.LEAD_CREATE
        assert confidence > 0.0
    
    def test_classify_meeting_intent(self):
        """测试会议安排意图分类"""
        text = "安排明天和ABC公司的会议"
        intent, confidence = self.processor.classify_intent_by_keywords(text)
        
        assert intent == IntentType.SCHEDULE_MEETING
        assert confidence > 0.0
    
    def test_classify_unknown_intent(self):
        """测试未知意图分类"""
        text = "今天天气真好啊"
        intent, confidence = self.processor.classify_intent_by_keywords(text)
        
        assert intent == IntentType.UNKNOWN
        assert confidence == 0.0
    
    def test_normalize_budget_values(self):
        """测试预算值标准化"""
        test_cases = [
            ("50万", 500000),
            ("100万元", 1000000),
            ("2千", 2000),
            ("5百万", 5000000),
            ("1亿", 100000000),
        ]
        
        for input_value, expected in test_cases:
            normalized = self.processor._normalize_entity_value('budget', input_value)
            assert normalized == expected
    
    def test_normalize_number_values(self):
        """测试数字值标准化"""
        test_cases = [
            ("123", 123.0),
            ("45.67", 45.67),
            ("invalid", "invalid"),
        ]
        
        for input_value, expected in test_cases:
            normalized = self.processor._normalize_entity_value('number', input_value)
            assert normalized == expected


class TestNLUService:
    """NLU服务测试"""
    
    def setup_method(self):
        # 创建模拟的LLM服务
        self.mock_llm_service = Mock(spec=EnhancedLLMService)
        self.nlu_service = NLUService(llm_service=self.mock_llm_service)
    
    @pytest.mark.asyncio
    async def test_analyze_customer_search(self):
        """测试客户搜索分析"""
        text = "帮我找一些制造业的潜在客户，预算在100万以上"
        
        # 设置LLM mock响应
        mock_response = {
            "content": '''```json
{
  "intent": "customer_search",
  "confidence": 0.9,
  "entities": [
    {
      "type": "industry",
      "value": "制造业",
      "confidence": 0.8
    }
  ]
}
```''',
            "model": "test-model",
            "usage": None,
            "created": 1234567890,
            "fallback_used": False
        }
        self.mock_llm_service.chat_completion = AsyncMock(return_value=mock_response)
        
        result = await self.nlu_service.analyze(text)
        
        assert isinstance(result, NLUResult)
        assert result.intent.type == IntentType.CUSTOMER_SEARCH
        assert result.confidence > 0.0
        
        # 检查实体提取
        industry_entities = [e for e in result.entities if e.type == EntityType.INDUSTRY]
        budget_entities = [e for e in result.entities if e.type == EntityType.BUDGET]
        
        assert len(industry_entities) >= 1 or len(budget_entities) >= 1
    
    @pytest.mark.asyncio
    async def test_analyze_lead_creation(self):
        """测试线索创建分析"""
        text = "新建线索：德芙科技，联系人李经理，需要财务软件，预算50万"
        
        result = await self.nlu_service.analyze(text)
        
        assert result.intent.type == IntentType.LEAD_CREATE
        
        # 检查槽位填充
        assert 'company_name' in result.slots
        assert 'contact_name' in result.slots
        assert 'budget' in result.slots
        
        # 检查必需槽位是否填充
        company_slot = result.slots['company_name']
        contact_slot = result.slots['contact_name']
        
        # 至少应该识别出一些实体
        assert len(result.entities) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_meeting_scheduling(self):
        """测试会议安排分析"""
        text = "安排明天下午和ABC公司张总的会议"
        
        result = await self.nlu_service.analyze(text)
        
        assert result.intent.type == IntentType.SCHEDULE_MEETING
        
        # 检查槽位
        assert 'customer' in result.slots
        assert 'contact' in result.slots
        assert 'date' in result.slots
    
    @pytest.mark.asyncio
    async def test_analyze_with_llm_fallback(self):
        """测试LLM回退分析"""
        # 模拟LLM响应
        mock_response = {
            "content": '''```json
{
  "intent": "customer_search",
  "confidence": 0.9,
  "entities": [
    {
      "type": "industry",
      "value": "科技行业",
      "confidence": 0.8
    }
  ]
}
```''',
            "model": "test-model",
            "usage": None,
            "created": 1234567890,
            "fallback_used": False
        }
        
        self.mock_llm_service.chat_completion = AsyncMock(return_value=mock_response)
        
        # 使用一个规则置信度较低的文本
        text = "我需要一些科技行业的信息"
        
        result = await self.nlu_service.analyze(text)
        
        assert isinstance(result, NLUResult)
        # 应该调用了LLM服务
        self.mock_llm_service.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_entities_only(self):
        """测试单独实体提取"""
        text = "联系华为科技的张总，预算100万"
        
        entities = await self.nlu_service.extract_entities(text)
        
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        entity_types = [e.type for e in entities]
        assert EntityType.COMPANY in entity_types or EntityType.PERSON in entity_types
    
    @pytest.mark.asyncio
    async def test_classify_intent_only(self):
        """测试单独意图分类"""
        text = "查找今天的线索"
        
        # 设置LLM mock响应
        mock_response = {
            "content": '''```json
{
  "intent": "lead_search",
  "confidence": 0.9,
  "entities": []
}
```''',
            "model": "test-model",
            "usage": None,
            "created": 1234567890,
            "fallback_used": False
        }
        self.mock_llm_service.chat_completion = AsyncMock(return_value=mock_response)
        
        intent = await self.nlu_service.classify_intent(text)
        
        assert isinstance(intent, Intent)
        assert intent.type == IntentType.LEAD_SEARCH
        assert intent.confidence > 0.0
    
    def test_slot_filling(self):
        """测试槽位填充"""
        # 创建测试实体
        entities = [
            Entity(
                type=EntityType.COMPANY,
                value="德芙科技",
                confidence=0.9,
                start_pos=0,
                end_pos=4
            ),
            Entity(
                type=EntityType.CONTACT_NAME,
                value="李经理",
                confidence=0.8,
                start_pos=5,
                end_pos=8
            ),
            Entity(
                type=EntityType.BUDGET,
                value="50万",
                confidence=0.9,
                start_pos=9,
                end_pos=12,
                normalized_value=500000
            )
        ]
        
        slots = self.nlu_service._fill_slots(IntentType.LEAD_CREATE, entities)
        
        assert 'company_name' in slots
        assert 'contact_name' in slots
        assert 'budget' in slots
        
        # 检查槽位值
        assert slots['company_name'].filled
        assert slots['company_name'].value == "德芙科技"
        assert slots['contact_name'].filled
        assert slots['contact_name'].value == "李经理"
        assert slots['budget'].filled
        assert slots['budget'].value == 500000
    
    def test_missing_slots_detection(self):
        """测试缺失槽位检测"""
        # 创建部分填充的槽位
        slots = {
            'company_name': Slot(
                name='company_name',
                value="德芙科技",
                entity_type=EntityType.COMPANY,
                confidence=0.9,
                required=True,
                filled=True
            ),
            'contact_name': Slot(
                name='contact_name',
                value=None,
                entity_type=EntityType.CONTACT_NAME,
                confidence=0.0,
                required=True,
                filled=False
            ),
            'budget': Slot(
                name='budget',
                value=None,
                entity_type=EntityType.BUDGET,
                confidence=0.0,
                required=False,
                filled=False
            )
        }
        
        missing = self.nlu_service.get_missing_slots(slots)
        assert 'contact_name' in missing
        assert 'budget' not in missing  # 非必需
        
        is_complete = self.nlu_service.is_slots_complete(slots)
        assert not is_complete
    
    @pytest.mark.asyncio
    async def test_slot_filling_prompt_generation(self):
        """测试槽位填充提示生成"""
        missing_slots = ['company_name', 'contact_name']
        
        prompt = await self.nlu_service.get_slot_filling_prompt(
            IntentType.LEAD_CREATE, 
            missing_slots
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "公司名称" in prompt
        assert "联系人姓名" in prompt
    
    def test_entity_deduplication(self):
        """测试实体去重"""
        entities = [
            Entity(
                type=EntityType.COMPANY,
                value="华为科技",
                confidence=0.9,
                start_pos=0,
                end_pos=4
            ),
            Entity(
                type=EntityType.COMPANY,
                value="华为科技",  # 重复
                confidence=0.8,
                start_pos=10,
                end_pos=14
            ),
            Entity(
                type=EntityType.PERSON,
                value="张总",
                confidence=0.9,
                start_pos=5,
                end_pos=7
            )
        ]
        
        unique_entities = self.nlu_service._deduplicate_entities(entities)
        
        assert len(unique_entities) == 2
        company_entities = [e for e in unique_entities if e.type == EntityType.COMPANY]
        assert len(company_entities) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        # 模拟LLM服务异常
        self.mock_llm_service.chat_completion = AsyncMock(side_effect=Exception("LLM服务异常"))
        
        text = "测试错误处理"
        result = await self.nlu_service.analyze(text)
        
        # 应该返回默认结果而不是抛出异常
        assert isinstance(result, NLUResult)
        assert result.confidence >= 0.0
    
    @pytest.mark.asyncio
    async def test_context_usage(self):
        """测试上下文使用"""
        context = {
            "user_id": "user123",
            "current_task": "customer_management",
            "previous_intent": "customer_search"
        }
        
        text = "创建一个新的"
        result = await self.nlu_service.analyze(text, context)
        
        assert isinstance(result, NLUResult)
        assert result.metadata["context"] == context
    
    def test_slot_definitions_initialization(self):
        """测试槽位定义初始化"""
        slot_defs = self.nlu_service.slot_definitions
        
        # 检查关键意图的槽位定义
        assert IntentType.CUSTOMER_SEARCH in slot_defs
        assert IntentType.LEAD_CREATE in slot_defs
        assert IntentType.OPPORTUNITY_CREATE in slot_defs
        
        # 检查槽位结构
        customer_search_slots = slot_defs[IntentType.CUSTOMER_SEARCH]
        assert isinstance(customer_search_slots, list)
        assert len(customer_search_slots) > 0
        
        for slot_def in customer_search_slots:
            assert 'name' in slot_def
            assert 'entity_type' in slot_def
            assert 'required' in slot_def


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_nlu_pipeline(self):
        """测试完整NLU流水线"""
        # 使用真实的NLU服务（但模拟LLM）
        mock_llm_service = Mock(spec=EnhancedLLMService)
        nlu_service = NLUService(llm_service=mock_llm_service)
        
        # 测试复杂的用户输入
        text = "帮我创建一个线索，公司是北京德芙科技有限公司，联系人李经理，他们需要财务管理软件，预算大概在80万左右，希望下个月能开始实施"
        
        result = await nlu_service.analyze(text)
        
        # 验证结果完整性
        assert isinstance(result, NLUResult)
        assert result.intent.type in [IntentType.LEAD_CREATE, IntentType.CUSTOMER_CREATE]
        assert len(result.entities) > 0
        assert len(result.slots) > 0
        assert result.processing_time > 0
        
        # 验证实体类型多样性
        entity_types = [e.type for e in result.entities]
        assert len(set(entity_types)) > 1  # 应该有多种类型的实体
        
        # 验证槽位填充
        filled_slots = [name for name, slot in result.slots.items() if slot.filled]
        assert len(filled_slots) > 0
    
    @pytest.mark.asyncio
    async def test_chinese_text_processing(self):
        """测试中文文本处理"""
        mock_llm_service = Mock(spec=EnhancedLLMService)
        nlu_service = NLUService(llm_service=mock_llm_service)
        
        # 测试各种中文表达
        test_cases = [
            "找一下制造业的客户",
            "新增线索：阿里巴巴，马总",
            "安排明天上午十点的会议",
            "生成本月的销售报告",
            "这个客户的预算是五十万人民币"
        ]
        
        for text in test_cases:
            result = await nlu_service.analyze(text)
            
            assert isinstance(result, NLUResult)
            assert result.intent.type != IntentType.UNKNOWN or result.confidence == 0.0
            # 至少应该能提取到一些信息
            assert len(result.entities) > 0 or result.intent.confidence > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])