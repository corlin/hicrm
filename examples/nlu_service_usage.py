"""
NLU服务使用示例
演示如何使用正式的NLU服务进行意图识别和实体抽取
"""

import asyncio
import sys
import os
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.nlu_service import NLUService, IntentType, EntityType


async def test_intent_recognition():
    """测试意图识别"""
    print("=== 意图识别测试 ===")
    
    nlu_service = NLUService()
    
    test_cases = [
        "查询ABC公司的客户信息",
        "新增一个线索，联系人张三",
        "你好，我想咨询一下",
        "再见，谢谢帮助",
        "这是一个无关的句子"
    ]
    
    for text in test_cases:
        result = await nlu_service.analyze(text)
        
        print(f"输入: {text}")
        print(f"意图: {result.intent.type.value} (置信度: {result.intent.confidence:.2f})")
        print(f"实体: {[(e.type.value, e.value) for e in result.entities]}")
        print(f"处理时间: {result.processing_time:.3f}秒")
        print()


async def test_entity_extraction():
    """测试实体抽取"""
    print("=== 实体抽取测试 ===")
    
    nlu_service = NLUService()
    
    test_cases = [
        "联系人张三，公司是ABC科技有限公司",
        "预算50万元，项目在北京",
        "制造业客户，需要CRM系统",
        "金融行业的客户，预算100万",
        "教育行业客户，联系人李经理"
    ]
    
    for text in test_cases:
        result = await nlu_service.analyze(text)
        
        print(f"输入: {text}")
        print(f"意图: {result.intent.type.value} (置信度: {result.intent.confidence:.2f})")
        print(f"实体:")
        for entity in result.entities:
            normalized = f" -> {entity.normalized_value}" if entity.normalized_value != entity.value else ""
            print(f"  - {entity.type.value}: {entity.value}{normalized} (置信度: {entity.confidence:.2f})")
        print()


async def test_slot_filling():
    """测试槽位填充"""
    print("=== 槽位填充测试 ===")
    
    nlu_service = NLUService()
    
    test_cases = [
        "我想创建一个新客户，公司是ABC科技",
        "新增线索，联系人张三，预算50万",
        "安排会议，客户是德芙科技，时间是明天下午"
    ]
    
    for text in test_cases:
        result = await nlu_service.analyze(text)
        
        print(f"输入: {text}")
        print(f"意图: {result.intent.type.value}")
        print(f"槽位:")
        for slot_name, slot in result.slots.items():
            status = "✓" if slot.filled else "✗"
            print(f"  {status} {slot_name}: {slot.value} (必需: {slot.required})")
        
        missing_slots = nlu_service.get_missing_slots(result.slots)
        if missing_slots:
            prompt = await nlu_service.get_slot_filling_prompt(result.intent.type, missing_slots)
            print(f"缺失槽位: {missing_slots}")
            print(f"提示: {prompt}")
        else:
            print("所有必需槽位已填充完成")
        print()


async def test_advanced_analysis():
    """测试高级分析功能"""
    print("=== 高级分析测试 ===")
    
    nlu_service = NLUService()
    
    # 测试复杂句子
    complex_text = "我想为制造业的ABC公司创建一个新客户，联系人是张经理，预算大概50万左右，希望下周安排一次会议"
    
    result = await nlu_service.analyze(complex_text)
    
    print(f"复杂输入: {complex_text}")
    print(f"意图: {result.intent.type.value} (置信度: {result.intent.confidence:.2f})")
    print(f"实体数量: {len(result.entities)}")
    print("实体详情:")
    for entity in result.entities:
        print(f"  - {entity.type.value}: '{entity.value}' (位置: {entity.start_pos}-{entity.end_pos})")
    
    print(f"槽位填充情况:")
    for slot_name, slot in result.slots.items():
        status = "✓" if slot.filled else "✗"
        print(f"  {status} {slot_name}: {slot.value}")
    
    print(f"处理时间: {result.processing_time:.3f}秒")
    print(f"总体置信度: {result.confidence:.2f}")
    print()


async def main():
    """主函数"""
    print("NLU服务功能演示")
    print("=" * 50)
    print("使用正式的NLU服务进行自然语言理解测试")
    print()
    
    try:
        await test_intent_recognition()
        await test_entity_extraction()
        await test_slot_filling()
        await test_advanced_analysis()
        
        print("=" * 50)
        print("所有测试完成！")
        
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())