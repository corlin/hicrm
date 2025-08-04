"""
LLM服务测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.llm_service import LLMService


class TestLLMService:
    """LLM服务测试类"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """模拟OpenAI客户端"""
        mock_client = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def llm_service_configured(self, mock_openai_client):
        """配置好的LLM服务"""
        with patch('src.services.llm_service.settings') as mock_settings:
            mock_settings.openai_configured = True
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_BASE_URL = "https://api.test.com/v1"
            mock_settings.DEFAULT_MODEL = "test-model"
            
            with patch('src.services.llm_service.openai.AsyncOpenAI') as mock_openai:
                mock_openai.return_value = mock_openai_client
                service = LLMService()
                return service, mock_openai_client
    
    @pytest.fixture
    def llm_service_unconfigured(self):
        """未配置的LLM服务"""
        with patch('src.services.llm_service.settings') as mock_settings:
            mock_settings.openai_configured = False
            service = LLMService()
            return service
    
    def test_init_configured(self, llm_service_configured):
        """测试已配置的服务初始化"""
        service, mock_client = llm_service_configured
        assert service.client is not None
        assert service.is_available() is True
    
    def test_init_unconfigured(self, llm_service_unconfigured):
        """测试未配置的服务初始化"""
        service = llm_service_unconfigured
        assert service.client is None
        assert service.is_available() is False
    
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, llm_service_configured):
        """测试聊天完成成功"""
        service, mock_client = llm_service_configured
        
        # 模拟响应
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "测试响应"
        mock_response.model = "test-model"
        mock_response.created = 1234567890
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
        
        mock_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "测试消息"}]
        result = await service.chat_completion(messages)
        
        assert result["content"] == "测试响应"
        assert result["model"] == "test-model"
        assert result["usage"]["total_tokens"] == 15
        
        # 验证调用参数
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["messages"] == messages
        assert call_args[1]["model"] == "test-model"
    
    @pytest.mark.asyncio
    async def test_chat_completion_unconfigured(self, llm_service_unconfigured):
        """测试未配置服务的聊天完成"""
        service = llm_service_unconfigured
        
        messages = [{"role": "user", "content": "测试消息"}]
        
        with pytest.raises(ValueError, match="LLM服务未正确配置"):
            await service.chat_completion(messages)
    
    @pytest.mark.asyncio
    async def test_chat_completion_stream(self, llm_service_configured):
        """测试流式聊天完成"""
        service, mock_client = llm_service_configured
        
        # 模拟流式响应
        mock_chunk1 = MagicMock()
        mock_chunk1.choices[0].delta.content = "测试"
        mock_chunk2 = MagicMock()
        mock_chunk2.choices[0].delta.content = "响应"
        mock_chunk3 = MagicMock()
        mock_chunk3.choices[0].delta.content = None  # 结束标志
        
        async def mock_stream():
            yield mock_chunk1
            yield mock_chunk2
            yield mock_chunk3
        
        mock_client.chat.completions.create.return_value = mock_stream()
        
        messages = [{"role": "user", "content": "测试消息"}]
        result_chunks = []
        
        async for chunk in service.chat_completion_stream(messages):
            result_chunks.append(chunk)
        
        assert result_chunks == ["测试", "响应"]
    
    @pytest.mark.asyncio
    async def test_function_call(self, llm_service_configured):
        """测试函数调用"""
        service, mock_client = llm_service_configured
        
        # 模拟函数调用响应
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.function_call.name = "test_function"
        mock_response.choices[0].message.function_call.arguments = '{"param": "value"}'
        mock_response.model = "test-model"
        mock_response.usage.model_dump.return_value = {"total_tokens": 20}
        
        mock_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "调用函数"}]
        functions = [{"name": "test_function", "description": "测试函数"}]
        
        result = await service.function_call(messages, functions)
        
        assert result["function_call"]["name"] == "test_function"
        assert result["function_call"]["arguments"] == {"param": "value"}
        assert result["model"] == "test-model"
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, llm_service_configured):
        """测试生成嵌入向量"""
        service, mock_client = llm_service_configured
        
        # 模拟嵌入响应
        mock_response = MagicMock()
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        
        mock_client.embeddings.create.return_value = mock_response
        
        result = await service.generate_embedding("测试文本")
        
        assert result == [0.1, 0.2, 0.3]
        
        # 验证调用参数
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-ada-002",
            input="测试文本"
        )
    
    def test_get_model_info(self, llm_service_configured):
        """测试获取模型信息"""
        service, _ = llm_service_configured
        
        with patch('src.services.llm_service.settings') as mock_settings:
            mock_settings.DEFAULT_MODEL = "test-model"
            mock_settings.OPENAI_BASE_URL = "https://api.test.com/v1"
            
            info = service.get_model_info()
            
            assert info["default_model"] == "test-model"
            assert info["api_base"] == "https://api.test.com/v1"
            assert info["configured"] is True
            assert "timestamp" in info