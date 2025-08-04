"""
LLM服务集成测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from src.services.llm_service import LLMService


class TestLLMServiceIntegration:
    """LLM服务集成测试类"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """模拟OpenAI响应"""
        def create_response(content: str, model: str = "test-model"):
            response = MagicMock()
            response.choices[0].message.content = content
            response.choices[0].message.function_call = None
            response.model = model
            response.created = 1234567890
            response.usage.prompt_tokens = 10
            response.usage.completion_tokens = len(content.split())
            response.usage.total_tokens = 10 + len(content.split())
            response.usage.model_dump.return_value = {
                "prompt_tokens": 10,
                "completion_tokens": len(content.split()),
                "total_tokens": 10 + len(content.split())
            }
            return response
        return create_response
    
    @pytest.fixture
    def configured_llm_service(self):
        """配置好的LLM服务"""
        with patch('src.services.llm_service.settings') as mock_settings:
            mock_settings.openai_configured = True
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_BASE_URL = "https://api.test.com/v1"
            mock_settings.DEFAULT_MODEL = "test-model"
            
            with patch('src.services.llm_service.openai.AsyncOpenAI') as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client
                service = LLMService()
                return service, mock_client
    
    @pytest.mark.asyncio
    async def test_customer_analysis_workflow(self, configured_llm_service, mock_openai_response):
        """测试客户分析工作流"""
        service, mock_client = configured_llm_service
        
        # 模拟客户分析响应
        analysis_response = mock_openai_response(
            "基于提供的客户信息，这是一个高价值的潜在客户。建议重点跟进。"
        )
        mock_client.chat.completions.create.return_value = analysis_response
        
        # 客户分析消息
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的销售顾问，请分析客户信息并提供建议。"
            },
            {
                "role": "user",
                "content": "客户：ABC科技，行业：软件开发，规模：中型企业，预算：50万，需求：CRM系统"
            }
        ]
        
        result = await service.chat_completion(messages)
        
        assert result["content"] is not None
        assert "客户" in result["content"]
        assert result["model"] == "test-model"
        assert result["usage"]["total_tokens"] > 0
        
        # 验证调用参数
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert len(call_args[1]["messages"]) == 2
        assert call_args[1]["model"] == "test-model"
    
    @pytest.mark.asyncio
    async def test_sales_script_generation(self, configured_llm_service, mock_openai_response):
        """测试销售话术生成"""
        service, mock_client = configured_llm_service
        
        # 模拟话术生成响应
        script_response = mock_openai_response(
            "您好张总，我是来自HiCRM的销售顾问。了解到贵公司在客户管理方面有需求，我们的解决方案可以帮助您提升30%的销售效率。"
        )
        mock_client.chat.completions.create.return_value = script_response
        
        messages = [
            {
                "role": "system",
                "content": "你是一个销售专家，请为以下客户生成个性化的销售话术。"
            },
            {
                "role": "user",
                "content": "客户：张总，公司：制造企业，痛点：客户管理混乱，决策风格：数据驱动"
            }
        ]
        
        result = await service.chat_completion(messages, temperature=0.7)
        
        assert result["content"] is not None
        assert "张总" in result["content"]
        assert len(result["content"]) > 50  # 话术应该有一定长度
        
        # 验证温度参数
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_function_calling_integration(self, configured_llm_service):
        """测试函数调用集成"""
        service, mock_client = configured_llm_service
        
        # 模拟函数调用响应
        function_response = MagicMock()
        function_response.choices[0].message.content = None
        function_response.choices[0].message.function_call.name = "search_customers"
        function_response.choices[0].message.function_call.arguments = json.dumps({
            "industry": "软件开发",
            "size": "medium",
            "status": "prospect"
        })
        function_response.model = "test-model"
        function_response.usage.model_dump.return_value = {"total_tokens": 25}
        
        mock_client.chat.completions.create.return_value = function_response
        
        messages = [
            {
                "role": "user",
                "content": "帮我找一些软件开发行业的中型企业潜在客户"
            }
        ]
        
        functions = [
            {
                "name": "search_customers",
                "description": "搜索客户",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string"},
                        "size": {"type": "string"},
                        "status": {"type": "string"}
                    }
                }
            }
        ]
        
        result = await service.function_call(messages, functions)
        
        assert result["function_call"]["name"] == "search_customers"
        assert result["function_call"]["arguments"]["industry"] == "软件开发"
        assert result["function_call"]["arguments"]["size"] == "medium"
        assert result["function_call"]["arguments"]["status"] == "prospect"
    
    @pytest.mark.asyncio
    async def test_streaming_response_integration(self, configured_llm_service):
        """测试流式响应集成"""
        service, mock_client = configured_llm_service
        
        # 模拟流式响应
        chunks = [
            "根据",
            "您的",
            "客户",
            "信息，",
            "我建议",
            "采用",
            "以下",
            "策略："
        ]
        
        async def mock_stream():
            for chunk_content in chunks:
                chunk = MagicMock()
                chunk.choices[0].delta.content = chunk_content
                yield chunk
            
            # 结束标志
            end_chunk = MagicMock()
            end_chunk.choices[0].delta.content = None
            yield end_chunk
        
        mock_client.chat.completions.create.return_value = mock_stream()
        
        messages = [
            {
                "role": "user",
                "content": "请为这个客户制定销售策略"
            }
        ]
        
        collected_chunks = []
        async for chunk in service.chat_completion_stream(messages):
            collected_chunks.append(chunk)
        
        assert collected_chunks == chunks
        assert len(collected_chunks) == 8
    
    @pytest.mark.asyncio
    async def test_embedding_generation_integration(self, configured_llm_service):
        """测试嵌入向量生成集成"""
        service, mock_client = configured_llm_service
        
        # 模拟嵌入响应
        embedding_response = MagicMock()
        test_embedding = [0.1, 0.2, 0.3, -0.1, -0.2] * 307 + [0.1, 0.2]  # 1537维向量
        embedding_response.data[0].embedding = test_embedding
        
        mock_client.embeddings.create.return_value = embedding_response
        
        text = "这是一个测试客户的描述信息"
        result = await service.generate_embedding(text)
        
        assert result == test_embedding
        assert len(result) == 1537
        
        # 验证调用参数
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-ada-002",
            input=text
        )
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, configured_llm_service):
        """测试错误处理集成"""
        service, mock_client = configured_llm_service
        
        # 模拟API错误
        import openai
        mock_client.chat.completions.create.side_effect = openai.APIError("API调用失败")
        
        messages = [{"role": "user", "content": "测试消息"}]
        
        with pytest.raises(openai.APIError):
            await service.chat_completion(messages)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, configured_llm_service):
        """测试速率限制集成"""
        service, mock_client = configured_llm_service
        
        # 模拟速率限制错误
        import openai
        mock_client.chat.completions.create.side_effect = openai.RateLimitError("速率限制")
        
        messages = [{"role": "user", "content": "测试消息"}]
        
        with pytest.raises(openai.RateLimitError):
            await service.chat_completion(messages)
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_integration(self, configured_llm_service, mock_openai_response):
        """测试多轮对话集成"""
        service, mock_client = configured_llm_service
        
        # 模拟多轮对话
        responses = [
            "您好！我是您的AI销售助手，请问有什么可以帮助您的？",
            "好的，我来帮您分析这个客户的情况。",
            "根据分析，建议您采用顾问式销售方法。"
        ]
        
        conversation_messages = [
            {"role": "system", "content": "你是一个专业的销售助手"},
            {"role": "user", "content": "你好"},
        ]
        
        for i, expected_response in enumerate(responses):
            mock_client.chat.completions.create.return_value = mock_openai_response(expected_response)
            
            result = await service.chat_completion(conversation_messages)
            assert result["content"] == expected_response
            
            # 添加助手回复到对话历史
            conversation_messages.append({"role": "assistant", "content": expected_response})
            
            # 添加下一个用户消息（除了最后一轮）
            if i < len(responses) - 1:
                next_user_messages = [
                    "我想分析一个客户",
                    "具体应该怎么做？"
                ]
                conversation_messages.append({"role": "user", "content": next_user_messages[i]})
        
        # 验证对话历史长度
        assert len(conversation_messages) == 7  # system + 3轮对话 (user + assistant) + 最后一个user
    
    @pytest.mark.asyncio
    async def test_model_switching_integration(self, configured_llm_service, mock_openai_response):
        """测试模型切换集成"""
        service, mock_client = configured_llm_service
        
        # 测试不同模型
        models = ["gpt-3.5-turbo", "gpt-4", "custom-model"]
        
        for model in models:
            mock_client.chat.completions.create.return_value = mock_openai_response(
                f"来自{model}的响应", model
            )
            
            messages = [{"role": "user", "content": "测试消息"}]
            result = await service.chat_completion(messages, model=model)
            
            assert result["model"] == model
            assert f"来自{model}的响应" in result["content"]
            
            # 验证模型参数
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == model