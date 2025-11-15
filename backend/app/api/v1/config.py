"""
配置管理API

提供应用配置信息，供前端使用
"""

# 标准库
from typing import Dict, Optional, Any

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

# 本地库
from app.api.deps import get_current_active_user
from app.config.config import settings
from app.models.user import User
from app.utils.logger import logger
from app.utils.config_loader import get_config_loader

router = APIRouter(prefix="/config", tags=["config"])


# ===== 请求/响应模型 =====

class OpenAIConfigResponse(BaseModel):
    """OpenAI配置响应"""
    api_key: str
    base_url: str


class RealtimeTokenResponse(BaseModel):
    """Realtime Token响应"""
    token: str
    """Ephemeral client key (token)"""
    url: str
    """WebSocket URL（用于 WebSocket 传输层）"""
    model: str
    """Model name"""


class RealtimeConfigResponse(BaseModel):
    """Realtime 全局配置响应"""
    voice: str
    """默认语音"""
    model: str
    """默认模型"""
    temperature: float
    """温度"""
    max_response_output_tokens: int
    """最大输出token数"""
    input_audio_transcription: Optional[Dict[str, str]] = None
    """音频转录配置"""
    transport: Optional[Dict[str, Any]] = None
    """传输层配置（例如：{"type": "webrtc"} 或 {"type": "websocket"}）"""
    websocket: Optional[Dict[str, Any]] = None
    """WebSocket配置（包括音频缓冲区等）"""


# ===== API路由 =====

@router.get("/openai-config", response_model=OpenAIConfigResponse)
async def get_openai_config(
    user: User = Depends(get_current_active_user)
) -> OpenAIConfigResponse:
    """
    获取 OpenAI 配置（供前端使用）
    
    返回 OpenAI API key 和 base URL，供前端直接连接 OpenAI Realtime API。
    
    Args:
        user: 当前用户（需要认证）
        
    Returns:
        OpenAIConfigResponse: OpenAI配置信息
        
    Raises:
        HTTPException: 如果用户未认证
    """
    try:
        # 检查 OpenAI API key 是否存在
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured"
            )
        
        logger.info(
            "Retrieved OpenAI config",
            extra={"user_id": str(user.id)}
        )
        
        return OpenAIConfigResponse(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get OpenAI config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get OpenAI config"
        )


@router.post("/realtime-token", response_model=RealtimeTokenResponse)
async def get_realtime_token(
    user: User = Depends(get_current_active_user)
) -> RealtimeTokenResponse:
    """
    获取 OpenAI Realtime API 的 ephemeral client key (token)
    
    这个端点会调用 OpenAI 的 /v1/realtime/client_secrets 端点生成临时客户端密钥，
    用于前端连接 OpenAI Realtime API。
    
    Args:
        user: 当前用户（需要认证）
        
    Returns:
        RealtimeTokenResponse: 包含 token、WebSocket URL 和 model
        
    Raises:
        HTTPException: 如果生成失败
    """
    try:
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured"
            )
        
        base_url = settings.openai_base_url
        is_new_api = base_url and base_url != 'https://api.openai.com/v1'
        
        if is_new_api:
            # New API 方式：使用 /v1/realtime/client_secrets 端点
            logger.info(
                "Generating ephemeral client key (New API)",
                extra={
                    "user_id": str(user.id),
                    "base_url": base_url
                }
            )
            
            # 构建 New API 的 client_secrets 端点
            if base_url.endswith('/v1'):
                client_secrets_url = base_url.replace('/v1', '/v1/realtime/client_secrets')
            elif base_url.endswith('/v1/'):
                client_secrets_url = base_url.replace('/v1/', '/v1/realtime/client_secrets')
            else:
                client_secrets_url = f"{base_url.rstrip('/')}/v1/realtime/client_secrets"
            
            client_secret = None
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # New API 请求格式：使用 session 对象（与 OpenAI 官方格式相同）
                    # 关键：必须在创建 ephemeral token 时配置转录功能
                    # 参考 curl 成功的响应格式，正确的结构是：session.audio.input.transcription
                    response = await client.post(
                        client_secrets_url,
                        headers={
                            'Authorization': f'Bearer {settings.openai_api_key}',
                            'Content-Type': 'application/json',
                        },
                        json={
                            'session': {
                                'type': 'realtime',
                                'model': settings.openai_realtime_model,  # 使用配置文件中的模型名称
                                # ✅ 关键：使用正确的嵌套结构配置转录功能
                                'audio': {
                                    'input': {
                                        'transcription': {
                                            'model': 'whisper-1'
                                        }
                                    }
                                }
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # New API 响应格式：可能包含 value（顶层）、token、ephemeral_token 或 client_secret.value
                        # 根据日志，响应格式是：{'value': 'ek_...', 'expires_at': ..., 'session': {...}}
                        client_secret = (
                            data.get('value', '') or  # 顶层 value（New API 格式）
                            data.get('token', '') or
                            data.get('ephemeral_token', '') or
                            data.get('client_secret', {}).get('value', '') or
                            data.get('session', {}).get('client_secret', {}).get('value', '')
                        )
                        
                        if client_secret:
                            logger.info(
                                "Successfully generated ephemeral client key (New API)",
                                extra={"user_id": str(user.id)}
                            )
                        else:
                            logger.warning(
                                "New API response missing token",
                                extra={
                                    "user_id": str(user.id),
                                    "response": data
                                }
                            )
                    else:
                        logger.warning(
                            f"Failed to generate ephemeral client key (New API): {response.status_code}",
                            extra={
                                "user_id": str(user.id),
                                "client_secrets_url": client_secrets_url,
                                "error": response.text[:200]
                            }
                        )
            except Exception as e:
                logger.warning(
                    f"Exception while generating ephemeral client key (New API): {e}",
                    extra={"user_id": str(user.id)}
                )
            
            if not client_secret:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to generate ephemeral client key from New API"
                )
        else:
            # OpenAI 官方方式：使用 /v1/realtime/client_secrets 端点
            logger.info(
                "Generating ephemeral client key (OpenAI)",
                extra={"user_id": str(user.id)}
            )
            
            client_secrets_url = "https://api.openai.com/v1/realtime/client_secrets"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    client_secrets_url,
                    headers={
                        'Authorization': f'Bearer {settings.openai_api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'session': {
                            'type': 'realtime',
                            'model': settings.openai_realtime_model
                        }
                    }
                )
                
                if response.status_code != 200:
                    error_text = response.text[:500]
                    logger.error(
                        f"Failed to generate ephemeral client key: {response.status_code} - {error_text}",
                        extra={"user_id": str(user.id)}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Failed to generate ephemeral client key: {response.status_code} - {error_text}"
                    )
                
                data = response.json()
                client_secret = data.get('client_secret', {}).get('value', '')
                
                if not client_secret:
                    logger.error(
                        "Ephemeral client key response missing 'client_secret.value'",
                        extra={"user_id": str(user.id), "response": data}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Invalid response from OpenAI API: missing client_secret.value"
                    )
        
        # 构建 WebSocket URL（用于 WebSocket 传输层，WebRTC 不需要）
        if is_new_api:
            ws_base_url = base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            if ws_base_url.endswith('/v1'):
                ws_base_url = ws_base_url[:-3]
            elif ws_base_url.endswith('/v1/'):
                ws_base_url = ws_base_url[:-4]
            ws_url = f"{ws_base_url.rstrip('/')}/v1/realtime?model={settings.openai_realtime_model}"
        else:
            ws_url = f"wss://api.openai.com/v1/realtime?model={settings.openai_realtime_model}"
        
        logger.info(
            "Generated realtime token successfully",
            extra={
                "user_id": str(user.id),
                "is_new_api": is_new_api
            }
        )
        
        return RealtimeTokenResponse(
            token=client_secret,
            url=ws_url,
            model=settings.openai_realtime_model
        )
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error generating ephemeral client key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to OpenAI API: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate ephemeral client key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ephemeral client key: {str(e)}"
        )


@router.get("/realtime-config", response_model=RealtimeConfigResponse)
async def get_realtime_config(
    user: User = Depends(get_current_active_user)
) -> RealtimeConfigResponse:
    """
    获取 Realtime 全局默认配置
    
    从 realtime.yaml 加载全局默认配置，personality 可以覆盖这些配置。
    
    Args:
        user: 当前用户（需要认证）
        
    Returns:
        RealtimeConfigResponse: Realtime全局配置信息
        
    Raises:
        HTTPException: 如果配置加载失败
    """
    try:
        # 加载 realtime.yaml 配置
        config_loader = get_config_loader()
        realtime_config = config_loader.load_voice_config('realtime')
        
        # 获取 OpenAI 引擎配置
        openai_config = realtime_config.get('openai', {})
        
        logger.info(
            "Retrieved realtime global config",
            extra={"user_id": str(user.id)}
        )
        
        # 获取传输层配置
        transport_config = openai_config.get('transport', {})
        
        # 获取音频转录配置
        input_audio_transcription = openai_config.get('input_audio_transcription')
        
        # 获取 WebSocket 配置
        websocket_config = openai_config.get('websocket', {})
        
        return RealtimeConfigResponse(
            voice=openai_config.get('voice', 'shimmer'),
            model=openai_config.get('model', settings.openai_realtime_model),
            temperature=openai_config.get('temperature', 0.8),
            max_response_output_tokens=openai_config.get('max_response_output_tokens', 4096),
            input_audio_transcription=input_audio_transcription,
            transport=transport_config if transport_config else None,
            websocket=websocket_config if websocket_config else None
        )
    except Exception as e:
        logger.error(f"Failed to get realtime config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get realtime config"
        )


