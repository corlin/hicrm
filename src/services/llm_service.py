"""
LLM服务 - 处理大语言模型相关功能
"""

import openai
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import json
from datetime import datetime

from src.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """大语言模型服务类"""
    
    def __init__(self):
        """初始化LLM服务"""
        if not settings.openai_configured:
            logger.warning("OpenAI API未配置，LLM功能将不可用")
            self.client = None
            return
        
        # 配置OpenAI客户端（兼容OpenRouter等服务）
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        
        logger.info(f"LLM服务已初始化，使用模型: {settings.DEFAULT_MODEL}")
        logger.info(f"API端点: {settings.OPENAI_BASE_URL}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天完成接口
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            **kwargs: 其他参数
        
        Returns:
            响应结果
        """
        if not self.client:
            raise ValueError("LLM服务未正确配置")
        
        try:
            model = model or settings.DEFAULT_MODEL
            
            logger.debug(f"发送聊天请求到模型: {model}")
            logger.debug(f"消息数量: {len(messages)}")
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            
            if stream:
                return response
            
            # 记录使用情况
            usage = response.usage
            if usage:
                logger.info(f"Token使用情况 - 输入: {usage.prompt_tokens}, "
                          f"输出: {usage.completion_tokens}, "
                          f"总计: {usage.total_tokens}")
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": usage.model_dump() if usage else None,
                "created": response.created
            }
            
        except Exception as e:
            logger.error(f"LLM请求失败: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Yields:
            流式响应内容
        """
        if not self.client:
            raise ValueError("LLM服务未正确配置")
        
        try:
            model = model or settings.DEFAULT_MODEL
            
            logger.debug(f"开始流式聊天请求到模型: {model}")
            
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"流式LLM请求失败: {e}")
            raise
    
    async def function_call(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        function_call: Optional[str] = "auto",
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        函数调用接口
        
        Args:
            messages: 消息列表
            functions: 可用函数列表
            function_call: 函数调用策略
            model: 模型名称
            **kwargs: 其他参数
        
        Returns:
            响应结果
        """
        if not self.client:
            raise ValueError("LLM服务未正确配置")
        
        try:
            model = model or settings.DEFAULT_MODEL
            
            logger.debug(f"发送函数调用请求到模型: {model}")
            logger.debug(f"可用函数数量: {len(functions)}")
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                functions=functions,
                function_call=function_call,
                **kwargs
            )
            
            choice = response.choices[0]
            message = choice.message
            
            result = {
                "content": message.content,
                "function_call": None,
                "model": response.model,
                "usage": response.usage.model_dump() if response.usage else None
            }
            
            # 检查是否有函数调用
            if message.function_call:
                result["function_call"] = {
                    "name": message.function_call.name,
                    "arguments": json.loads(message.function_call.arguments)
                }
                logger.info(f"模型调用函数: {message.function_call.name}")
            
            return result
            
        except Exception as e:
            logger.error(f"函数调用请求失败: {e}")
            raise
    
    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002"
    ) -> List[float]:
        """
        生成文本嵌入向量
        
        Args:
            text: 输入文本
            model: 嵌入模型名称
        
        Returns:
            嵌入向量
        """
        if not self.client:
            raise ValueError("LLM服务未正确配置")
        
        try:
            logger.debug(f"生成文本嵌入，长度: {len(text)}")
            
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"生成嵌入向量，维度: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return self.client is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "default_model": settings.DEFAULT_MODEL,
            "api_base": settings.OPENAI_BASE_URL,
            "configured": self.is_available(),
            "timestamp": datetime.utcnow().isoformat()
        }


# 全局LLM服务实例
llm_service = LLMService()