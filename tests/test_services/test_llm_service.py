"""
LLM服务单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List

from src.services.llm_service import (
    EnhancedLLMService,
    ModelType,
    FallbackStrategy,
    ModelConfig,
    ConversationContext,
    MCPTool,
    ChineseTokenOptimizer,
    LangChainLLMWrapper
)


class TestChineseTokenOptimizer:
    """中文Token优化器测试"""
    
    def test_optimize_prompt(self):
        """测试中文提示词优化"""
        optimizer = ChineseTokenOptimizer()
        
        # 测试中文标点符号优化
        input_text = "你好，世界！这是一个测试。"
        expected = "你好,世界!这是一个测试."
        result = optimizer.optimize_prompt(input_text)
        assert result == expected
        
        # 测试空格优化
        input_text = "这是   一个    测试"
        expected = "这是 一个 测试"
        result = optimizer.optimize_prompt(input_text)
        assert result == expected
    
    def test_estimate_chinese_tokens(self):
        """测试中文token估算"""
        optimizer = ChineseTokenOptimizer()
        
        # 纯中文文本
        chinese_text = "这是一个中文测试"
        tokens = optimizer.estimate_chinese_tokens(chinese_text)
        assert tokens > 0
        assert tokens == len(chinese_text) * 1.5  # 中文字符约1.5个token
        
        # 中英文混合
        mixed_text = "这是test文本"
        tokens = optimizer.estimate_chinese_tokens(mixed_text)
        chinese_chars = 4  # "这是文本"
        english_chars = 4  # "test"
        expected = int(chinese_chars * 1.5 + english_chars * 0.25)
        assert tokens == expected
    
    def test_truncate_context(self):
        """测试上下文截断"""
        optimizer = ChineseTokenOptimizer()
        
        messages = [
            {"role": "system", "content": "你是一个AI助手"},
            {"role": "user", "content": "第一个问题"},
            {"role": "assistant", "content": "第一个回答"},
            {"role": "user", "content": "第二个问题"},
            {"role": "assistant", "content": "第二个回答"},
        ]
        
        # 设置较小的token限制
        max_tokens = 20
        result = optimizer.truncate_context(messages, max_tokens)
        
        # 应该保留系统消息
        system_messages = [msg for msg in result if msg["role"] == "system"]
        assert len(system_messages) == 1
        
        # 总长度应该不超过限制
        total_tokens = sum(
            optimizer.estimate_chinese_tokens(msg["content"])
            for msg in result
        )
        assert total_tokens <= max_tokens


class TestModelConfig:
    """模型配置测试"""
    
    def test_model_config_creation(self):
        """测试模型配置创建"""
        config = ModelConfig(
            name="test-model",
            max_tokens=4096,
            context_window=8192,
            supports_function_calling=True,
            supports_chinese=True,
            chinese_optimized=True
        )
        
        assert config.name == "test-model"
        assert config.max_tokens == 4096
        assert config.context_window == 8192
        assert config.supports_function_calling is True
        assert config.supports_chinese is True
        assert config.chinese_optimized is True


class TestConversationContext:
    """对话上下文测试"""
    
    def test_context_creation(self):
        """测试上下文创建"""
        context = ConversationContext(
            conversation_id="test-conv-1",
            user_id="user-123"
        )
        
        assert context.conversation_id == "test-conv-1"
        assert context.user_id == "user-123"
        assert context.messages == []
        assert context.token_count == 0
        assert isinstance(context.created_at, datetime)


class TestMCPTool:
    """MCP工具测试"""
    
    def test_mcp_tool_creation(self):
        """测试MCP工具创建"""
        async def test_handler(**kwargs):
            return {"result": "success"}
        
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            parameters={"type": "object"},
            handler=test_handler
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "测试工具"
        assert tool.enabled is True
        assert callable(tool.handler)


@pytest.fixture
def mock_openai_client():
    """模拟OpenAI客户端"""
    client = AsyncMock()
    
    # 模拟聊天完成响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "这是一个测试响应"
    mock_response.model = "gpt-3.5-turbo"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    mock_response.usage.model_dump.return_value = {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
    mock_response.created = 1234567890
    
    client.chat.completions.create.return_value = mock_response
    
    # 模拟嵌入响应
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock()]
    mock_embedding_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536维向量
    
    client.embeddings.create.return_value = mock_embedding_response
    
    return client


@pytest.fixture
def llm_service(mock_openai_client):
    """LLM服务实例"""
    with patch('src.services.llm_service.openai.AsyncOpenAI') as mock_openai:
        mock_openai.return_value = mock_openai_client
        
        # 模拟配置
        with patch('src.services.llm_service.settings') as mock_settings:
            mock_settings.openai_configured = True
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"
            mock_settings.DEFAULT_MODEL = "gpt-3.5-turbo"
            
            service = EnhancedLLMService()
            return service


class TestEnhancedLLMService:
    """增强LLM服务测试"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, llm_service):
        """测试服务初始化"""
        assert llm_service.is_available()
        assert len(llm_service.model_configs) > 0
        assert len(llm_service.mcp_tools) > 0
        assert isinstance(llm_service.token_optimizer, ChineseTokenOptimizer)
        assert isinstance(llm_service.langchain_wrapper, LangChainLLMWrapper)
    
    @pytest.mark.asyncio
    async def test_create_context(self, llm_service):
        """测试创建对话上下文"""
        context = await llm_service.create_context(
            conversation_id="test-conv-1",
            user_id="user-123",
            metadata={"test": "data"}
        )
        
        assert context.conversation_id == "test-conv-1"
        assert context.user_id == "user-123"
        assert context.metadata["test"] == "data"
        assert "test-conv-1" in llm_service.contexts
    
    @pytest.mark.asyncio
    async def test_get_context(self, llm_service):
        """测试获取对话上下文"""
        # 创建上下文
        await llm_service.create_context("test-conv-1", "user-123")
        
        # 获取上下文
        context = await llm_service.get_context("test-conv-1")
        assert context is not None
        assert context.conversation_id == "test-conv-1"
        
        # 获取不存在的上下文
        context = await llm_service.get_context("non-existent")
        assert context is None
    
    @pytest.mark.asyncio
    async def test_update_context(self, llm_service):
        """测试更新对话上下文"""
        # 创建上下文
        await llm_service.create_context("test-conv-1", "user-123")
        
        # 更新上下文
        message = {"role": "user", "content": "测试消息"}
        await llm_service.update_context("test-conv-1", message)
        
        # 验证更新
        context = await llm_service.get_context("test-conv-1")
        assert len(context.messages) == 1
        assert context.messages[0] == message
        assert context.token_count > 0
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, llm_service):
        """测试聊天完成"""
        messages = [
            {"role": "user", "content": "你好，世界！"}
        ]
        
        response = await llm_service.chat_completion(messages)
        
        assert "content" in response
        assert "model" in response
        assert "usage" in response
        assert response["fallback_used"] is False
        
        # 验证客户端调用
        llm_service.clients["default"].chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_context(self, llm_service):
        """测试带上下文的聊天完成"""
        # 创建上下文
        conversation_id = "test-conv-1"
        await llm_service.create_context(conversation_id, "user-123")
        
        messages = [
            {"role": "user", "content": "你好"}
        ]
        
        response = await llm_service.chat_completion(
            messages,
            conversation_id=conversation_id
        )
        
        assert "content" in response
        
        # 验证上下文更新
        context = await llm_service.get_context(conversation_id)
        assert len(context.messages) == 1
        assert context.messages[0]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_chat_completion_stream(self, llm_service):
        """测试流式聊天完成"""
        # 模拟流式响应
        async def mock_stream():
            chunks = ["你", "好", "世", "界"]
            for chunk in chunks:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock()]
                mock_chunk.choices[0].delta.content = chunk
                yield mock_chunk
        
        llm_service.clients["default"].chat.completions.create.return_value = mock_stream()
        
        messages = [{"role": "user", "content": "你好"}]
        
        result = []
        async for chunk in llm_service.chat_completion_stream(messages):
            result.append(chunk)
        
        assert result == ["你", "好", "世", "界"]
    
    @pytest.mark.asyncio
    async def test_function_call(self, llm_service):
        """测试函数调用"""
        # 模拟函数调用响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "我将为您获取客户信息"
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].id = "call_123"
        mock_response.choices[0].message.tool_calls[0].function.name = "get_customer_info"
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"customer_id": "123"}'
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage.model_dump.return_value = {"total_tokens": 20}
        
        llm_service.clients["default"].chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "获取客户123的信息"}]
        
        response = await llm_service.function_call(messages)
        
        assert "content" in response
        assert "tool_calls" in response
        assert len(response["tool_calls"]) == 1
        assert response["tool_calls"][0]["function"]["name"] == "get_customer_info"
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, llm_service):
        """测试生成嵌入向量"""
        text = "这是一个测试文本"
        
        embedding = await llm_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # 标准嵌入维度
        assert all(isinstance(x, float) for x in embedding)
        
        # 验证客户端调用
        llm_service.clients["default"].embeddings.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_strategy(self, llm_service):
        """测试降级策略"""
        # 模拟主模型失败
        original_client = llm_service.clients["default"]
        original_client.chat.completions.create.side_effect = Exception("API Error")
        
        # 模拟降级模型成功
        fallback_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "降级响应"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage.model_dump.return_value = {"total_tokens": 10}
        mock_response.created = 1234567890
        
        fallback_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "测试"}]
        
        # 测试降级到下一个模型
        with patch.object(llm_service, '_get_fallback_models', return_value=["gpt-3.5-turbo"]):
            with patch.object(llm_service, '_get_client_for_model') as mock_get_client:
                # 第一次调用返回失败的客户端，第二次返回成功的客户端
                mock_get_client.side_effect = [original_client, fallback_client]
                
                response = await llm_service.chat_completion(
                    messages,
                    model="gpt-4",  # 指定一个会失败的模型
                    fallback_strategy=FallbackStrategy.NEXT_MODEL
                )
                
                assert response["fallback_used"] is True
                assert "fallback_model" in response
    
    @pytest.mark.asyncio
    async def test_simple_fallback_response(self, llm_service):
        """测试简单降级响应"""
        # 模拟所有模型都失败
        llm_service.clients["default"].chat.completions.create.side_effect = Exception("API Error")
        
        messages = [{"role": "user", "content": "测试"}]
        
        response = await llm_service.chat_completion(
            messages,
            fallback_strategy=FallbackStrategy.SIMPLE_RESPONSE
        )
        
        assert response["fallback_used"] is True
        assert response["fallback_type"] == "simple_response"
        assert "抱歉" in response["content"]
    
    def test_add_mcp_tool(self, llm_service):
        """测试添加MCP工具"""
        async def test_handler(**kwargs):
            return {"result": "test"}
        
        tool = MCPTool(
            name="test_new_tool",
            description="新测试工具",
            parameters={"type": "object"},
            handler=test_handler
        )
        
        initial_count = len(llm_service.mcp_tools)
        llm_service.add_mcp_tool(tool)
        
        assert len(llm_service.mcp_tools) == initial_count + 1
        assert "test_new_tool" in llm_service.mcp_tools
    
    def test_remove_mcp_tool(self, llm_service):
        """测试移除MCP工具"""
        # 添加一个工具
        async def test_handler(**kwargs):
            return {"result": "test"}
        
        tool = MCPTool(
            name="test_remove_tool",
            description="待移除工具",
            parameters={"type": "object"},
            handler=test_handler
        )
        
        llm_service.add_mcp_tool(tool)
        initial_count = len(llm_service.mcp_tools)
        
        # 移除工具
        llm_service.remove_mcp_tool("test_remove_tool")
        
        assert len(llm_service.mcp_tools) == initial_count - 1
        assert "test_remove_tool" not in llm_service.mcp_tools
    
    def test_get_model_info(self, llm_service):
        """测试获取模型信息"""
        info = llm_service.get_model_info()
        
        assert "default_model" in info
        assert "available_models" in info
        assert "model_configs" in info
        assert "available_clients" in info
        assert "mcp_tools" in info
        assert "configured" in info
        assert "timestamp" in info
        
        assert info["configured"] is True
        assert len(info["available_models"]) > 0
        assert len(info["mcp_tools"]) > 0


class TestLangChainIntegration:
    """LangChain集成测试"""
    
    @pytest.mark.asyncio
    async def test_langchain_wrapper(self, llm_service):
        """测试LangChain包装器"""
        wrapper = llm_service.get_langchain_llm()
        assert isinstance(wrapper, LangChainLLMWrapper)
        assert wrapper.llm_service == llm_service
    
    @pytest.mark.asyncio
    async def test_langchain_generate(self, llm_service):
        """测试LangChain生成"""
        from langchain.schema import HumanMessage
        
        wrapper = llm_service.get_langchain_llm()
        messages = [HumanMessage(content="你好")]
        
        # 由于LangChain的复杂性，这里主要测试接口是否正确
        assert hasattr(wrapper, '_agenerate')
        assert hasattr(wrapper, '_generate')
        assert wrapper._llm_type == "enhanced_llm_service"


@pytest.mark.integration
class TestLLMServiceIntegration:
    """LLM服务集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, llm_service):
        """测试完整对话流程"""
        conversation_id = "integration-test-conv"
        user_id = "test-user"
        
        # 创建上下文
        context = await llm_service.create_context(conversation_id, user_id)
        assert context is not None
        
        # 第一轮对话
        messages1 = [{"role": "user", "content": "你好，我是新用户"}]
        response1 = await llm_service.chat_completion(
            messages1,
            conversation_id=conversation_id
        )
        assert "content" in response1
        
        # 第二轮对话（带上下文）
        messages2 = [{"role": "user", "content": "请记住我刚才说的话"}]
        response2 = await llm_service.chat_completion(
            messages2,
            conversation_id=conversation_id
        )
        assert "content" in response2
        
        # 验证上下文保存
        final_context = await llm_service.get_context(conversation_id)
        assert len(final_context.messages) == 2  # 两个assistant响应
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution_flow(self, llm_service):
        """测试MCP工具执行流程"""
        # 模拟工具调用响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "我将为您创建线索"
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].id = "call_123"
        mock_response.choices[0].message.tool_calls[0].function.name = "create_lead"
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"name": "张三", "company": "测试公司"}'
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage.model_dump.return_value = {"total_tokens": 30}
        
        llm_service.clients["default"].chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "帮我创建一个线索，联系人张三，公司是测试公司"}]
        
        response = await llm_service.function_call(messages)
        
        assert "tool_calls" in response
        assert len(response["tool_calls"]) == 1
        
        tool_call = response["tool_calls"][0]
        assert tool_call["function"]["name"] == "create_lead"
        assert "result" in tool_call
        assert tool_call["result"]["status"] == "created"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])