"""
Ollama引擎实现

实现基于Ollama API的本地AI引擎
"""

# 标准库
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

# 第三方库
import httpx

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import AIEngineBase, ChatMessage, ChatResponse, StreamChunk


class OllamaEngine(AIEngineBase):
    """Ollama引擎实现
    
    支持本地运行的Ollama模型
    
    Attributes:
        client: HTTP客户端
    """
    
    def __init__(
        self,
        model: str = "llama2",
        base_url: Optional[str] = None,
        **kwargs
    ):
        """初始化Ollama引擎
        
        Args:
            model: 模型名称（如llama2, mistral等）
            base_url: Ollama服务URL
            **kwargs: 其他参数
        """
        super().__init__(
            engine_name="ollama",
            model=model,
            api_key=None,  # Ollama不需要API Key
            base_url=base_url or settings.ollama_base_url,
            **kwargs
        )
        
        self.client = httpx.AsyncClient(timeout=120.0)  # Ollama可能较慢
        
        logger.info(
            f"Ollama engine initialized with model {model}",
            extra={"model": model, "base_url": self.base_url}
        )
    
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
            tools: 工具列表（Ollama暂不支持）
            **kwargs: 其他参数
            
        Returns:
            ChatResponse: 聊天响应
            
        Raises:
            httpx.HTTPError: HTTP请求错误
        """
        try:
            # 转换消息格式
            formatted_messages = [msg.to_dict() for msg in messages]
            
            # 构建请求参数
            request_data = {
                "model": self.model,
                "messages": formatted_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                request_data["options"]["num_predict"] = max_tokens
            
            logger.debug(
                "Calling Ollama API",
                extra={
                    "model": self.model,
                    "message_count": len(messages)
                }
            )
            
            # 调用Ollama API
            url = f"{self.base_url}/api/chat"
            response = await self.client.post(url, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            
            # 转换响应格式
            assistant_message = ChatMessage(
                role="assistant",
                content=result["message"]["content"]
            )
            
            # Ollama响应格式转换为OpenAI格式
            response_id = f"chatcmpl-ollama-{uuid.uuid4().hex[:8]}"
            chat_response = ChatResponse(
                id=response_id,
                message=assistant_message,
                model=self.model,
                finish_reason="stop",
                usage={
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                }
            )
            
            logger.info(
                "Ollama API call completed",
                extra={
                    "response_id": response_id,
                    "tokens": chat_response.usage["total_tokens"]
                }
            )
            
            return chat_response
            
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Ollama chat: {e}", exc_info=True)
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
            tools: 工具列表（Ollama暂不支持）
            **kwargs: 其他参数
            
        Yields:
            StreamChunk: 流式响应数据块
            
        Raises:
            httpx.HTTPError: HTTP请求错误
        """
        try:
            # 转换消息格式
            formatted_messages = [msg.to_dict() for msg in messages]
            
            # 构建请求参数
            request_data = {
                "model": self.model,
                "messages": formatted_messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                request_data["options"]["num_predict"] = max_tokens
            
            logger.debug(
                "Calling Ollama streaming API",
                extra={
                    "model": self.model,
                    "message_count": len(messages)
                }
            )
            
            # 调用Ollama流式API
            url = f"{self.base_url}/api/chat"
            response_id = f"chatcmpl-ollama-{uuid.uuid4().hex[:8]}"
            
            async with self.client.stream("POST", url, json=request_data) as response:
                response.raise_for_status()
                
                # 首先发送role
                yield StreamChunk(
                    id=response_id,
                    delta={"role": "assistant"},
                    model=self.model,
                    finish_reason=None
                )
                
                # 逐行读取响应
                async for line in response.aiter_lines():
                    if line.strip():
                        import json
                        try:
                            chunk_data = json.loads(line)
                            
                            if "message" in chunk_data:
                                content = chunk_data["message"].get("content", "")
                                if content:
                                    yield StreamChunk(
                                        id=response_id,
                                        delta={"content": content},
                                        model=self.model,
                                        finish_reason=None
                                    )
                            
                            # 检查是否完成
                            if chunk_data.get("done", False):
                                yield StreamChunk(
                                    id=response_id,
                                    delta={},
                                    model=self.model,
                                    finish_reason="stop"
                                )
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON line: {line}")
                            continue
            
            logger.info("Ollama streaming completed")
            
        except httpx.HTTPError as e:
            logger.error(f"Ollama streaming error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Ollama streaming: {e}", exc_info=True)
            raise
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.aclose()

