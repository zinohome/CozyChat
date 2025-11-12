"""
OpenAI引擎实现

实现基于OpenAI API的AI引擎
"""

# 标准库
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

# 第三方库
from openai import AsyncOpenAI, APIError, OpenAIError

# 本地库
from app.config.config import settings
from app.utils.config_loader import get_config_loader
from app.utils.logger import logger
from .base import AIEngineBase, ChatMessage, ChatResponse, StreamChunk


class OpenAIEngine(AIEngineBase):
    """OpenAI引擎实现
    
    支持OpenAI GPT系列模型，包括GPT-4、GPT-3.5等
    
    Attributes:
        client: OpenAI异步客户端
    """
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """初始化OpenAI引擎
        
        Args:
            model: 模型名称
            api_key: OpenAI API密钥
            base_url: API基础URL（用于兼容其他OpenAI格式的API）
            **kwargs: 其他参数
        """
        super().__init__(
            engine_name="openai",
            model=model,
            api_key=api_key or settings.openai_api_key,
            base_url=base_url or settings.openai_base_url,
            **kwargs
        )
        
        # 创建异步客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 加载配置以获取支持的模型列表
        self._supported_models: Optional[List[str]] = None
        try:
            config_loader = get_config_loader()
            engine_config = config_loader.load_engine_config("openai")
            models_config = engine_config.get("models", [])
            if models_config:
                # 从配置中提取模型名称列表
                self._supported_models = [
                    model_item.get("name") 
                    for model_item in models_config 
                    if isinstance(model_item, dict) and "name" in model_item
                ]
        except Exception as e:
            logger.warning(f"Failed to load model list from config: {e}")
            self._supported_models = None
        
        logger.info(
            f"OpenAI engine initialized with model {model}",
            extra={"model": model, "base_url": self.base_url}
        )
    
    def list_models(self) -> List[str]:
        """获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型名称列表
        """
        if self._supported_models:
            return self._supported_models
        # 如果没有配置，返回当前模型
        return [self.model] if self.model else []
    
    async def chat(
        self,
        messages: List[ChatMessage],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ChatResponse:
        """生成聊天响应（非流式）
        
        Args:
            messages: 消息列表
            stream: 是否流式输出（此方法忽略）
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 工具列表
            **kwargs: 其他参数
            
        Returns:
            ChatResponse: 聊天响应
            
        Raises:
            OpenAIError: OpenAI API错误
        """
        try:
            # 转换消息格式
            formatted_messages = [msg.to_dict() for msg in messages]
            
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
                "stream": False,
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            if tools:
                request_params["tools"] = tools
                # 设置 tool_choice 为 "auto" 以允许模型选择是否使用工具
                request_params["tool_choice"] = "auto"
            
            # 合并额外参数
            request_params.update(kwargs)
            
            logger.debug(
                "Calling OpenAI API",
                extra={
                    "model": self.model,
                    "message_count": len(messages),
                    "temperature": temperature,
                    "has_tools": bool(tools),
                    "tools_count": len(tools) if tools else 0
                }
            )
            
            # 调用OpenAI API
            response = await self.client.chat.completions.create(**request_params)
            
            # 转换响应格式
            choice = response.choices[0]
            assistant_message = ChatMessage(
                role=choice.message.role,
                content=choice.message.content,
                function_call=choice.message.function_call.to_dict() 
                    if choice.message.function_call else None,
                tool_calls=[tc.to_dict() for tc in choice.message.tool_calls] 
                    if choice.message.tool_calls else None
            )
            
            chat_response = ChatResponse(
                id=response.id,
                message=assistant_message,
                model=response.model,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                created=response.created
            )
            
            logger.info(
                "OpenAI API call completed",
                extra={
                    "response_id": response.id,
                    "finish_reason": choice.finish_reason,
                    "tokens": response.usage.total_tokens if response.usage else 0
                }
            )
            
            return chat_response
            
        except APIError as e:
            # OpenAI 2.x 推荐使用 APIError（更具体的异常）
            logger.error(
                f"OpenAI API error: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "status_code": getattr(e, "status_code", None),
                    "response": getattr(e, "response", None)
                },
                exc_info=True
            )
            raise
        except OpenAIError as e:
            # 保留 OpenAIError 作为后备
            logger.error(f"OpenAI error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI chat: {e}", exc_info=True)
            raise
    
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """生成聊天响应（流式）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 工具列表
            **kwargs: 其他参数
            
        Yields:
            StreamChunk: 流式响应数据块
            
        Raises:
            OpenAIError: OpenAI API错误
        """
        try:
            # 转换消息格式
            formatted_messages = [msg.to_dict() for msg in messages]
            
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
                "stream": True,
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            if tools:
                request_params["tools"] = tools
                # 设置 tool_choice 为 "auto" 以允许模型选择是否使用工具
                request_params["tool_choice"] = "auto"
            
            # 合并额外参数
            request_params.update(kwargs)
            
            logger.info(
                "Calling OpenAI streaming API",
                extra={
                    "model": self.model,
                    "message_count": len(messages),
                    "has_tools": bool(tools),
                    "tools_count": len(tools) if tools else 0,
                    "first_message_role": messages[0].role if messages else None,
                    "system_prompt_length": len(messages[0].content) if messages and messages[0].role == "system" else 0,
                    "tool_choice": "auto" if tools else None
                }
            )
            
            # 调试：打印工具列表
            if tools:
                logger.info(
                    "Tools passed to OpenAI API",
                    extra={
                        "tools": [t.get("function", {}).get("name") for t in tools]
                }
            )
            
            # 调用OpenAI流式API
            stream = await self.client.chat.completions.create(**request_params)
            
            async for chunk in stream:
                if chunk.choices:
                    choice = chunk.choices[0]
                    
                    # 构建delta字典
                    delta = {}
                    if choice.delta.role:
                        delta["role"] = choice.delta.role
                    if choice.delta.content:
                        delta["content"] = choice.delta.content
                    if choice.delta.function_call:
                        delta["function_call"] = choice.delta.function_call.to_dict()
                    if choice.delta.tool_calls:
                        delta["tool_calls"] = [
                            tc.to_dict() for tc in choice.delta.tool_calls
                        ]
                    
                    yield StreamChunk(
                        id=chunk.id,
                        delta=delta,
                        model=chunk.model,
                        finish_reason=choice.finish_reason,
                        created=chunk.created
                    )
            
            logger.info("OpenAI streaming completed")
            
        except OpenAIError as e:
            logger.error(f"OpenAI streaming error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI streaming: {e}", exc_info=True)
            raise

