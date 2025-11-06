"""
聊天API接口

提供OpenAI兼容的Chat Completions API
"""

# 标准库
import json
from typing import AsyncIterator

# 第三方库
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

# 本地库
from app.engines.ai import AIEngineFactory, ChatMessage as EngineChatMessage
from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    EngineListResponse,
    ModelInfo,
    ModelListResponse,
)
from app.utils.logger import logger

router = APIRouter()


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """创建聊天补全（OpenAI兼容接口）
    
    支持流式和非流式两种模式
    
    Args:
        request: 聊天请求
        
    Returns:
        ChatCompletionResponse: 聊天响应（非流式）
        StreamingResponse: SSE流（流式）
        
    Raises:
        HTTPException: 引擎创建失败或API调用失败
    """
    try:
        # 创建AI引擎
        engine = AIEngineFactory.create_engine(
            engine_type=request.engine_type,
            model=request.model
        )
        
        # 转换消息格式
        messages = [
            EngineChatMessage(
                role=msg.role,
                content=msg.content,
                name=msg.name,
                function_call=msg.function_call,
                tool_calls=msg.tool_calls
            )
            for msg in request.messages
        ]
        
        # 流式输出
        if request.stream:
            async def generate_stream() -> AsyncIterator[str]:
                """生成SSE流"""
                try:
                    async for chunk in engine.chat_stream(
                        messages=messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        tools=request.tools
                    ):
                        # 转换为SSE格式
                        chunk_dict = chunk.to_dict()
                        yield f"data: {json.dumps(chunk_dict, ensure_ascii=False)}\n\n"
                    
                    # 发送结束标记
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"Stream generation error: {e}", exc_info=True)
                    error_data = {
                        "error": {
                            "message": str(e),
                            "type": "stream_error"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # 非流式输出
        else:
            response = await engine.chat(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=request.tools
            )
            
            # 转换为API响应格式
            return ChatCompletionResponse(
                id=response.id,
                created=response.created,
                model=response.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=response.message,
                        finish_reason=response.finish_reason
                    )
                ],
                usage=ChatCompletionUsage(**response.usage) if response.usage else ChatCompletionUsage(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
            )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat completion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        )


@router.get("/engines", response_model=EngineListResponse)
async def list_engines() -> EngineListResponse:
    """列出所有可用的AI引擎
    
    Returns:
        EngineListResponse: 引擎列表
    """
    try:
        available_engines = AIEngineFactory.list_available_engines()
        
        return EngineListResponse(
            engines=list(available_engines.keys()),
            default_engine="openai",
            descriptions=available_engines
        )
    except Exception as e:
        logger.error(f"Failed to list engines: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list engines"
        )


@router.get("/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """列出所有可用模型（OpenAI兼容接口）
    
    Returns:
        ModelListResponse: 模型列表
    """
    # 定义可用模型
    models = [
        ModelInfo(
            id="gpt-4",
            engine_type="openai",
            description="GPT-4模型，最强大的语言模型",
            context_window=8192,
            supports_tools=True,
            supports_vision=True
        ),
        ModelInfo(
            id="gpt-3.5-turbo",
            engine_type="openai",
            description="GPT-3.5 Turbo模型，快速且经济",
            context_window=4096,
            supports_tools=True,
            supports_vision=False
        ),
        ModelInfo(
            id="llama2",
            engine_type="ollama",
            description="Llama2本地模型",
            context_window=4096,
            supports_tools=False,
            supports_vision=False
        ),
        ModelInfo(
            id="mistral",
            engine_type="ollama",
            description="Mistral本地模型",
            context_window=8192,
            supports_tools=False,
            supports_vision=False
        ),
    ]
    
    return ModelListResponse(data=models)

