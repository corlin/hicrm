"""
LLM服务 - 处理大语言模型相关功能
支持OpenAI兼容API、Function Calling、MCP协议和中文模型优化
"""

import openai
from typing import List, Dict, Any, Optional, AsyncGenerator, Union, Callable
import logging
import json
import asyncio
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from langchain.llms.base import LLM
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema.output import ChatResult, ChatGeneration
from langchain.schema.messages import BaseMessage as LangChainBaseMessage

from src.core.config import settings

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """支持的模型类型"""
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    QWEN_72B = "qwen2.5-72b-instruct"
    GLM_4 = "glm-4"
    DEEPSEEK_CHAT = "deepseek-chat"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"


class FallbackStrategy(str, Enum):
    """降级策略"""
    NONE = "none"
    NEXT_MODEL = "next_model"
    SIMPLE_RESPONSE = "simple_response"
    CACHED_RESPONSE = "cached_response"


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    max_tokens: int
    context_window: int
    supports_function_calling: bool = True
    supports_chinese: bool = True
    cost_per_1k_tokens: float = 0.002
    priority: int = 1  # 优先级，数字越小优先级越高
    chinese_optimized: bool = False


@dataclass
class ConversationContext:
    """对话上下文"""
    conversation_id: str
    user_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    token_count: int = 0
    max_context_length: int = 4000


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    enabled: bool = True


class ChineseTokenOptimizer:
    """中文Token优化器"""
    
    @staticmethod
    def optimize_prompt(prompt: str) -> str:
        """优化中文提示词"""
        # 移除多余的空格和换行
        prompt = " ".join(prompt.split())
        
        # 中文标点符号优化
        replacements = {
            "，": ",",
            "。": ".",
            "？": "?",
            "！": "!",
            "：": ":",
            "；": ";",
        }
        
        for chinese, english in replacements.items():
            prompt = prompt.replace(chinese, english)
        
        return prompt
    
    @staticmethod
    def estimate_chinese_tokens(text: str) -> int:
        """估算中文文本的token数量"""
        # 中文字符通常占用更多token
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len(text) - chinese_chars
        
        # 粗略估算：中文字符约1.5个token，英文字符约0.25个token
        return int(chinese_chars * 1.5 + english_chars * 0.25)
    
    @staticmethod
    def truncate_context(messages: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """截断上下文以适应token限制"""
        if not messages:
            return messages
        
        # 保留系统消息和最后几条消息
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        other_messages = [msg for msg in messages if msg.get("role") != "system"]
        
        # 从最新消息开始计算token
        selected_messages = []
        current_tokens = 0
        
        # 为系统消息预留token
        for msg in system_messages:
            current_tokens += ChineseTokenOptimizer.estimate_chinese_tokens(msg.get("content", ""))
        
        # 从后往前添加消息
        for msg in reversed(other_messages):
            msg_tokens = ChineseTokenOptimizer.estimate_chinese_tokens(msg.get("content", ""))
            if current_tokens + msg_tokens <= max_tokens:
                selected_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        return system_messages + selected_messages


class LangChainLLMWrapper(BaseChatModel):
    """LangChain LLM包装器"""
    
    def __init__(self, llm_service: 'EnhancedLLMService'):
        super().__init__()
        self.llm_service = llm_service
    
    def _generate(
        self,
        messages: List[LangChainBaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成方法（LangChain要求）"""
        # 转换为异步调用
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._agenerate(messages, stop, run_manager, **kwargs))
    
    async def _agenerate(
        self,
        messages: List[LangChainBaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成方法"""
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": msg.content})
        
        # 调用LLM服务
        response = await self.llm_service.chat_completion(
            messages=formatted_messages,
            **kwargs
        )
        
        # 转换响应格式
        ai_message = AIMessage(content=response["content"])
        generation = ChatGeneration(message=ai_message)
        
        return ChatResult(generations=[generation])
    
    @property
    def _llm_type(self) -> str:
        return "enhanced_llm_service"


class EnhancedLLMService:
    """增强的LLM服务类"""
    
    def __init__(self):
        """初始化增强LLM服务"""
        self.clients: Dict[str, openai.AsyncOpenAI] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.contexts: Dict[str, ConversationContext] = {}
        self.mcp_tools: Dict[str, MCPTool] = {}
        self.token_optimizer = ChineseTokenOptimizer()
        self.langchain_wrapper = LangChainLLMWrapper(self)
        
        # 初始化模型配置
        self._init_model_configs()
        
        # 初始化客户端
        self._init_clients()
        
        # 初始化MCP工具
        self._init_mcp_tools()
        
        logger.info("增强LLM服务已初始化")
        logger.info(f"支持的模型: {list(self.model_configs.keys())}")
        logger.info(f"可用的MCP工具: {list(self.mcp_tools.keys())}")
    
    def _init_model_configs(self):
        """初始化模型配置"""
        self.model_configs = {
            ModelType.GPT_3_5_TURBO: ModelConfig(
                name="gpt-3.5-turbo",
                max_tokens=4096,
                context_window=16385,
                supports_function_calling=True,
                supports_chinese=True,
                cost_per_1k_tokens=0.002,
                priority=3
            ),
            ModelType.GPT_4: ModelConfig(
                name="gpt-4",
                max_tokens=8192,
                context_window=8192,
                supports_function_calling=True,
                supports_chinese=True,
                cost_per_1k_tokens=0.03,
                priority=2
            ),
            ModelType.GPT_4_TURBO: ModelConfig(
                name="gpt-4-turbo-preview",
                max_tokens=4096,
                context_window=128000,
                supports_function_calling=True,
                supports_chinese=True,
                cost_per_1k_tokens=0.01,
                priority=1
            ),
            ModelType.QWEN_72B: ModelConfig(
                name="qwen2.5-72b-instruct",
                max_tokens=8192,
                context_window=32768,
                supports_function_calling=True,
                supports_chinese=True,
                cost_per_1k_tokens=0.001,
                priority=1,
                chinese_optimized=True
            ),
            ModelType.GLM_4: ModelConfig(
                name="glm-4",
                max_tokens=4096,
                context_window=128000,
                supports_function_calling=True,
                supports_chinese=True,
                cost_per_1k_tokens=0.001,
                priority=1,
                chinese_optimized=True
            ),
            ModelType.DEEPSEEK_CHAT: ModelConfig(
                name="deepseek-chat",
                max_tokens=4096,
                context_window=32768,
                supports_function_calling=True,
                supports_chinese=True,
                cost_per_1k_tokens=0.0014,
                priority=2,
                chinese_optimized=True
            )
        }
    
    def _init_clients(self):
        """初始化OpenAI兼容客户端"""
        if not settings.openai_configured:
            logger.warning("OpenAI API未配置，LLM功能将不可用")
            return
        
        # 主客户端
        self.clients["default"] = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        
        # 可以配置多个API端点
        # 例如：不同的模型提供商
        if hasattr(settings, 'QWEN_API_KEY') and settings.QWEN_API_KEY:
            self.clients["qwen"] = openai.AsyncOpenAI(
                api_key=settings.QWEN_API_KEY,
                base_url=getattr(settings, 'QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
            )
        
        if hasattr(settings, 'GLM_API_KEY') and settings.GLM_API_KEY:
            self.clients["glm"] = openai.AsyncOpenAI(
                api_key=settings.GLM_API_KEY,
                base_url=getattr(settings, 'GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/')
            )
    
    def _init_mcp_tools(self):
        """初始化MCP工具"""
        # CRM相关工具
        self.mcp_tools["get_customer_info"] = MCPTool(
            name="get_customer_info",
            description="获取客户信息",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "客户ID"}
                },
                "required": ["customer_id"]
            },
            handler=self._handle_get_customer_info
        )
        
        self.mcp_tools["create_lead"] = MCPTool(
            name="create_lead",
            description="创建新线索",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "联系人姓名"},
                    "company": {"type": "string", "description": "公司名称"},
                    "email": {"type": "string", "description": "邮箱地址"},
                    "phone": {"type": "string", "description": "电话号码"},
                    "source": {"type": "string", "description": "线索来源"}
                },
                "required": ["name", "company"]
            },
            handler=self._handle_create_lead
        )
        
        self.mcp_tools["update_opportunity"] = MCPTool(
            name="update_opportunity",
            description="更新销售机会",
            parameters={
                "type": "object",
                "properties": {
                    "opportunity_id": {"type": "string", "description": "机会ID"},
                    "stage": {"type": "string", "description": "销售阶段"},
                    "value": {"type": "number", "description": "机会价值"},
                    "probability": {"type": "number", "description": "成交概率"}
                },
                "required": ["opportunity_id"]
            },
            handler=self._handle_update_opportunity
        )
    
    async def _handle_get_customer_info(self, **kwargs) -> Dict[str, Any]:
        """处理获取客户信息的MCP调用"""
        customer_id = kwargs.get("customer_id")
        # 这里应该调用实际的客户服务
        return {
            "customer_id": customer_id,
            "name": "示例客户",
            "company": "示例公司",
            "status": "active"
        }
    
    async def _handle_create_lead(self, **kwargs) -> Dict[str, Any]:
        """处理创建线索的MCP调用"""
        # 这里应该调用实际的线索服务
        return {
            "lead_id": f"lead_{int(time.time())}",
            "status": "created",
            "message": "线索创建成功"
        }
    
    async def _handle_update_opportunity(self, **kwargs) -> Dict[str, Any]:
        """处理更新销售机会的MCP调用"""
        # 这里应该调用实际的机会服务
        return {
            "opportunity_id": kwargs.get("opportunity_id"),
            "status": "updated",
            "message": "销售机会更新成功"
        }
    
    def get_langchain_llm(self) -> LangChainLLMWrapper:
        """获取LangChain包装器"""
        return self.langchain_wrapper
    
    def _get_client_for_model(self, model: str) -> openai.AsyncOpenAI:
        """根据模型获取对应的客户端"""
        if model.startswith("qwen") and "qwen" in self.clients:
            return self.clients["qwen"]
        elif model.startswith("glm") and "glm" in self.clients:
            return self.clients["glm"]
        else:
            return self.clients.get("default")
    
    def _get_fallback_models(self, current_model: str) -> List[str]:
        """获取降级模型列表"""
        # 按优先级排序，排除当前模型
        available_models = [
            config.name for config in sorted(
                self.model_configs.values(),
                key=lambda x: x.priority
            )
            if config.name != current_model
        ]
        return available_models[:3]  # 最多3个降级选项
    
    async def create_context(
        self,
        conversation_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """创建对话上下文"""
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        self.contexts[conversation_id] = context
        logger.debug(f"创建对话上下文: {conversation_id}")
        return context
    
    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """获取对话上下文"""
        return self.contexts.get(conversation_id)
    
    async def update_context(
        self,
        conversation_id: str,
        message: Dict[str, Any]
    ) -> None:
        """更新对话上下文"""
        context = self.contexts.get(conversation_id)
        if context:
            context.messages.append(message)
            context.updated_at = datetime.utcnow()
            context.token_count = self.token_optimizer.estimate_chinese_tokens(
                " ".join([msg.get("content", "") for msg in context.messages])
            )
            
            # 如果超过最大长度，截断上下文
            if context.token_count > context.max_context_length:
                context.messages = self.token_optimizer.truncate_context(
                    context.messages,
                    context.max_context_length
                )
                context.token_count = self.token_optimizer.estimate_chinese_tokens(
                    " ".join([msg.get("content", "") for msg in context.messages])
                )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        conversation_id: Optional[str] = None,
        fallback_strategy: FallbackStrategy = FallbackStrategy.NEXT_MODEL,
        **kwargs
    ) -> Dict[str, Any]:
        """
        增强的聊天完成接口
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            conversation_id: 对话ID
            fallback_strategy: 降级策略
            **kwargs: 其他参数
        
        Returns:
            响应结果
        """
        model = model or settings.DEFAULT_MODEL
        client = self._get_client_for_model(model)
        
        if not client:
            raise ValueError("LLM服务未正确配置")
        
        # 中文优化
        optimized_messages = []
        for msg in messages:
            optimized_content = self.token_optimizer.optimize_prompt(msg.get("content", ""))
            optimized_messages.append({
                **msg,
                "content": optimized_content
            })
        
        # 上下文管理
        if conversation_id:
            context = await self.get_context(conversation_id)
            if context:
                # 合并历史消息
                full_messages = context.messages + optimized_messages
                # 截断以适应token限制
                model_config = self.model_configs.get(model)
                if model_config:
                    max_context_tokens = min(
                        model_config.context_window - (max_tokens or 1000),
                        context.max_context_length
                    )
                    optimized_messages = self.token_optimizer.truncate_context(
                        full_messages,
                        max_context_tokens
                    )
        
        # 尝试主模型
        try:
            logger.debug(f"发送聊天请求到模型: {model}")
            logger.debug(f"消息数量: {len(optimized_messages)}")
            
            response = await client.chat.completions.create(
                model=model,
                messages=optimized_messages,
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
            
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": usage.model_dump() if usage else None,
                "created": response.created,
                "fallback_used": False
            }
            
            # 更新上下文
            if conversation_id:
                await self.update_context(conversation_id, {
                    "role": "assistant",
                    "content": result["content"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"主模型 {model} 请求失败: {e}")
            
            # 执行降级策略
            if fallback_strategy == FallbackStrategy.NEXT_MODEL:
                return await self._try_fallback_models(
                    optimized_messages, model, temperature, max_tokens, conversation_id, **kwargs
                )
            elif fallback_strategy == FallbackStrategy.SIMPLE_RESPONSE:
                return self._get_simple_response()
            elif fallback_strategy == FallbackStrategy.CACHED_RESPONSE:
                return await self._get_cached_response(optimized_messages)
            else:
                raise
    
    async def _try_fallback_models(
        self,
        messages: List[Dict[str, str]],
        failed_model: str,
        temperature: float,
        max_tokens: Optional[int],
        conversation_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """尝试降级模型"""
        fallback_models = self._get_fallback_models(failed_model)
        
        for fallback_model in fallback_models:
            try:
                logger.info(f"尝试降级模型: {fallback_model}")
                client = self._get_client_for_model(fallback_model)
                
                if not client:
                    continue
                
                response = await client.chat.completions.create(
                    model=fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                result = {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else None,
                    "created": response.created,
                    "fallback_used": True,
                    "original_model": failed_model,
                    "fallback_model": fallback_model
                }
                
                logger.info(f"降级模型 {fallback_model} 请求成功")
                
                # 更新上下文
                if conversation_id:
                    await self.update_context(conversation_id, {
                        "role": "assistant",
                        "content": result["content"]
                    })
                
                return result
                
            except Exception as e:
                logger.error(f"降级模型 {fallback_model} 也失败: {e}")
                continue
        
        # 所有模型都失败，返回简单响应
        return self._get_simple_response()
    
    def _get_simple_response(self) -> Dict[str, Any]:
        """获取简单响应（最后的降级策略）"""
        return {
            "content": "抱歉，我现在无法处理您的请求。请稍后再试。",
            "model": "fallback",
            "usage": None,
            "created": int(time.time()),
            "fallback_used": True,
            "fallback_type": "simple_response"
        }
    
    async def _get_cached_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """获取缓存响应"""
        # 这里可以实现基于消息内容的缓存查找
        # 暂时返回简单响应
        return self._get_simple_response()
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        增强的流式聊天完成
        """
        model = model or settings.DEFAULT_MODEL
        client = self._get_client_for_model(model)
        
        if not client:
            raise ValueError("LLM服务未正确配置")
        
        # 中文优化
        optimized_messages = []
        for msg in messages:
            optimized_content = self.token_optimizer.optimize_prompt(msg.get("content", ""))
            optimized_messages.append({
                **msg,
                "content": optimized_content
            })
        
        try:
            logger.debug(f"开始流式聊天请求到模型: {model}")
            
            stream = await client.chat.completions.create(
                model=model,
                messages=optimized_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            full_content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content
            
            # 更新上下文
            if conversation_id:
                await self.update_context(conversation_id, {
                    "role": "assistant",
                    "content": full_content
                })
                    
        except Exception as e:
            logger.error(f"流式LLM请求失败: {e}")
            raise
    
    async def function_call(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto",
        model: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        增强的函数调用接口（支持OpenAI新格式和MCP）
        
        Args:
            messages: 消息列表
            tools: 可用工具列表（新格式）
            tool_choice: 工具选择策略
            model: 模型名称
            conversation_id: 对话ID
            **kwargs: 其他参数
        
        Returns:
            响应结果
        """
        model = model or settings.DEFAULT_MODEL
        client = self._get_client_for_model(model)
        
        if not client:
            raise ValueError("LLM服务未正确配置")
        
        # 如果没有提供工具，使用MCP工具
        if not tools:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                }
                for tool in self.mcp_tools.values()
                if tool.enabled
            ]
        
        try:
            logger.debug(f"发送函数调用请求到模型: {model}")
            logger.debug(f"可用工具数量: {len(tools)}")
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                **kwargs
            )
            
            choice = response.choices[0]
            message = choice.message
            
            result = {
                "content": message.content,
                "tool_calls": [],
                "model": response.model,
                "usage": response.usage.model_dump() if response.usage else None
            }
            
            # 处理工具调用
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"模型调用工具: {function_name}")
                    
                    # 执行MCP工具
                    if function_name in self.mcp_tools:
                        mcp_tool = self.mcp_tools[function_name]
                        try:
                            tool_result = await mcp_tool.handler(**function_args)
                            result["tool_calls"].append({
                                "id": tool_call.id,
                                "function": {
                                    "name": function_name,
                                    "arguments": function_args
                                },
                                "result": tool_result
                            })
                        except Exception as e:
                            logger.error(f"MCP工具 {function_name} 执行失败: {e}")
                            result["tool_calls"].append({
                                "id": tool_call.id,
                                "function": {
                                    "name": function_name,
                                    "arguments": function_args
                                },
                                "error": str(e)
                            })
            
            # 更新上下文
            if conversation_id:
                await self.update_context(conversation_id, {
                    "role": "assistant",
                    "content": result["content"],
                    "tool_calls": result["tool_calls"]
                })
            
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
        """
        client = self._get_client_for_model(model)
        
        if not client:
            raise ValueError("LLM服务未正确配置")
        
        try:
            # 中文优化
            optimized_text = self.token_optimizer.optimize_prompt(text)
            logger.debug(f"生成文本嵌入，长度: {len(optimized_text)}")
            
            response = await client.embeddings.create(
                model=model,
                input=optimized_text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"生成嵌入向量，维度: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    def add_mcp_tool(self, tool: MCPTool) -> None:
        """添加MCP工具"""
        self.mcp_tools[tool.name] = tool
        logger.info(f"添加MCP工具: {tool.name}")
    
    def remove_mcp_tool(self, tool_name: str) -> None:
        """移除MCP工具"""
        if tool_name in self.mcp_tools:
            del self.mcp_tools[tool_name]
            logger.info(f"移除MCP工具: {tool_name}")
    
    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return len(self.clients) > 0
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "default_model": settings.DEFAULT_MODEL,
            "available_models": list(self.model_configs.keys()),
            "model_configs": {
                name: {
                    "max_tokens": config.max_tokens,
                    "context_window": config.context_window,
                    "supports_function_calling": config.supports_function_calling,
                    "supports_chinese": config.supports_chinese,
                    "chinese_optimized": config.chinese_optimized,
                    "priority": config.priority
                }
                for name, config in self.model_configs.items()
            },
            "available_clients": list(self.clients.keys()),
            "mcp_tools": list(self.mcp_tools.keys()),
            "configured": self.is_available(),
            "timestamp": datetime.utcnow().isoformat()
        }


# 全局增强LLM服务实例
enhanced_llm_service = EnhancedLLMService()

# 保持向后兼容
llm_service = enhanced_llm_service