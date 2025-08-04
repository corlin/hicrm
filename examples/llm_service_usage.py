"""
增强LLM服务使用示例
演示OpenAI兼容API、Function Calling、MCP协议和中文优化功能
"""

import asyncio
import json
from typing import Dict, Any

from src.services.llm_service import enhanced_llm_service, MCPTool, FallbackStrategy


async def basic_chat_example():
    """基础聊天示例"""
    print("=== 基础聊天示例 ===")
    
    messages = [
        {"role": "system", "content": "你是一个专业的CRM助手，帮助用户管理客户关系。"},
        {"role": "user", "content": "你好，我想了解如何提高客户满意度。"}
    ]
    
    response = await enhanced_llm_service.chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    
    print(f"模型: {response['model']}")
    print(f"响应: {response['content']}")
    print(f"Token使用: {response['usage']}")
    print()


async def chinese_optimization_example():
    """中文优化示例"""
    print("=== 中文优化示例 ===")
    
    # 包含中文标点符号的消息
    messages = [
        {"role": "user", "content": "你好，世界！这是一个测试，请回答：什么是CRM？"}
    ]
    
    response = await enhanced_llm_service.chat_completion(
        messages=messages,
        model="qwen2.5-72b-instruct"  # 使用中文优化模型
    )
    
    print(f"中文优化模型响应: {response['content']}")
    print()


async def context_management_example():
    """上下文管理示例"""
    print("=== 上下文管理示例 ===")
    
    conversation_id = "demo-conversation-1"
    user_id = "user-123"
    
    # 创建对话上下文
    context = await enhanced_llm_service.create_context(
        conversation_id=conversation_id,
        user_id=user_id,
        metadata={"department": "sales", "role": "manager"}
    )
    
    print(f"创建对话上下文: {context.conversation_id}")
    
    # 第一轮对话
    messages1 = [
        {"role": "user", "content": "我是销售经理张三，负责华东区域的客户管理。"}
    ]
    
    response1 = await enhanced_llm_service.chat_completion(
        messages=messages1,
        conversation_id=conversation_id
    )
    
    print(f"第一轮响应: {response1['content']}")
    
    # 第二轮对话（会包含上下文）
    messages2 = [
        {"role": "user", "content": "请根据我的角色，给我一些客户管理建议。"}
    ]
    
    response2 = await enhanced_llm_service.chat_completion(
        messages=messages2,
        conversation_id=conversation_id
    )
    
    print(f"第二轮响应（带上下文）: {response2['content']}")
    
    # 查看上下文状态
    final_context = await enhanced_llm_service.get_context(conversation_id)
    print(f"对话消息数量: {len(final_context.messages)}")
    print(f"Token计数: {final_context.token_count}")
    print()


async def function_calling_example():
    """Function Calling示例"""
    print("=== Function Calling示例 ===")
    
    messages = [
        {"role": "user", "content": "帮我获取客户ID为'cust-123'的客户信息"}
    ]
    
    response = await enhanced_llm_service.function_call(
        messages=messages,
        model="gpt-4-turbo-preview"
    )
    
    print(f"响应内容: {response['content']}")
    
    if response['tool_calls']:
        for tool_call in response['tool_calls']:
            print(f"调用工具: {tool_call['function']['name']}")
            print(f"参数: {tool_call['function']['arguments']}")
            print(f"结果: {tool_call['result']}")
    
    print()


async def mcp_tool_example():
    """MCP工具示例"""
    print("=== MCP工具示例 ===")
    
    # 添加自定义MCP工具
    async def custom_analysis_handler(**kwargs):
        """自定义分析工具"""
        analysis_type = kwargs.get("type", "general")
        data = kwargs.get("data", {})
        
        return {
            "analysis_type": analysis_type,
            "result": f"基于{analysis_type}分析，发现以下洞察...",
            "recommendations": [
                "建议1：优化客户沟通频率",
                "建议2：提升服务响应速度",
                "建议3：个性化客户体验"
            ],
            "confidence": 0.85
        }
    
    custom_tool = MCPTool(
        name="custom_analysis",
        description="执行自定义业务分析",
        parameters={
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "分析类型"},
                "data": {"type": "object", "description": "分析数据"}
            },
            "required": ["type"]
        },
        handler=custom_analysis_handler
    )
    
    enhanced_llm_service.add_mcp_tool(custom_tool)
    
    messages = [
        {"role": "user", "content": "请对我的销售数据进行客户满意度分析"}
    ]
    
    response = await enhanced_llm_service.function_call(messages)
    
    print(f"MCP工具响应: {response['content']}")
    
    if response['tool_calls']:
        for tool_call in response['tool_calls']:
            if tool_call['function']['name'] == 'custom_analysis':
                print(f"自定义分析结果: {json.dumps(tool_call['result'], ensure_ascii=False, indent=2)}")
    
    print()


async def fallback_strategy_example():
    """降级策略示例"""
    print("=== 降级策略示例 ===")
    
    messages = [
        {"role": "user", "content": "测试降级策略"}
    ]
    
    # 测试不同的降级策略
    strategies = [
        FallbackStrategy.NEXT_MODEL,
        FallbackStrategy.SIMPLE_RESPONSE,
        FallbackStrategy.CACHED_RESPONSE
    ]
    
    for strategy in strategies:
        try:
            response = await enhanced_llm_service.chat_completion(
                messages=messages,
                model="non-existent-model",  # 故意使用不存在的模型
                fallback_strategy=strategy
            )
            
            print(f"降级策略 {strategy.value}:")
            print(f"  降级使用: {response.get('fallback_used', False)}")
            print(f"  响应: {response['content'][:100]}...")
            
        except Exception as e:
            print(f"降级策略 {strategy.value} 失败: {e}")
    
    print()


async def streaming_example():
    """流式响应示例"""
    print("=== 流式响应示例 ===")
    
    messages = [
        {"role": "user", "content": "请详细介绍CRM系统的核心功能模块"}
    ]
    
    print("流式响应: ", end="", flush=True)
    
    async for chunk in enhanced_llm_service.chat_completion_stream(
        messages=messages,
        temperature=0.8
    ):
        print(chunk, end="", flush=True)
    
    print("\n")


async def langchain_integration_example():
    """LangChain集成示例"""
    print("=== LangChain集成示例 ===")
    
    # 获取LangChain包装器
    langchain_llm = enhanced_llm_service.get_langchain_llm()
    
    print(f"LangChain LLM类型: {langchain_llm._llm_type}")
    print("LangChain集成已就绪，可以与LangChain生态系统无缝集成")
    print()


async def model_info_example():
    """模型信息示例"""
    print("=== 模型信息示例 ===")
    
    info = enhanced_llm_service.get_model_info()
    
    print(f"默认模型: {info['default_model']}")
    print(f"可用模型: {', '.join(info['available_models'])}")
    print(f"可用客户端: {', '.join(info['available_clients'])}")
    print(f"MCP工具: {', '.join(info['mcp_tools'])}")
    print(f"服务状态: {'已配置' if info['configured'] else '未配置'}")
    
    print("\n模型配置详情:")
    for model_name, config in info['model_configs'].items():
        print(f"  {model_name}:")
        print(f"    最大Token: {config['max_tokens']}")
        print(f"    上下文窗口: {config['context_window']}")
        print(f"    支持函数调用: {config['supports_function_calling']}")
        print(f"    支持中文: {config['supports_chinese']}")
        print(f"    中文优化: {config['chinese_optimized']}")
        print(f"    优先级: {config['priority']}")
    
    print()


async def main():
    """主函数"""
    print("增强LLM服务功能演示")
    print("=" * 50)
    
    # 检查服务是否可用
    if not enhanced_llm_service.is_available():
        print("LLM服务未配置，请检查环境变量设置")
        return
    
    try:
        # 运行各种示例
        await model_info_example()
        await basic_chat_example()
        await chinese_optimization_example()
        await context_management_example()
        await function_calling_example()
        await mcp_tool_example()
        await fallback_strategy_example()
        await streaming_example()
        await langchain_integration_example()
        
    except Exception as e:
        print(f"示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())