"""
配置管理API

提供应用配置信息，供前端使用
"""

# 标准库
from typing import Dict, Optional

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

# 本地库
from app.api.deps import get_current_active_user
from app.config.config import settings
from app.models.user import User
from app.utils.logger import logger

router = APIRouter(prefix="/config", tags=["config"])


# ===== 请求/响应模型 =====

class OpenAIConfigResponse(BaseModel):
    """OpenAI配置响应"""
    api_key: str
    base_url: str


class RealtimeTokenResponse(BaseModel):
    """Realtime Token响应"""
    token: str
    url: str
    model: str


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
    用于前端直接连接 OpenAI Realtime API。
    
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
            # New API 方式：尝试获取临时秘钥，如果失败则返回 API key（前端使用 useInsecureApiKey）
            logger.info(
                "Attempting to generate ephemeral client key (New API)",
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
                    # New API 请求格式：使用 /v1/realtime/client_secrets 端点
                    response = await client.post(
                        client_secrets_url,
                        headers={
                            'Authorization': f'Bearer {settings.openai_api_key}',
                            'Content-Type': 'application/json',
                        },
                        json={
                            'model': 'gpt-4o-realtime-preview-2024-10-01',
                            'voice': 'shimmer'
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # New API 响应格式：可能包含 token、ephemeral_token 或 session.client_secret.value
                        client_secret = (
                            data.get('token', '') or
                            data.get('ephemeral_token', '') or
                            data.get('session', {}).get('client_secret', {}).get('value', '') or
                            data.get('client_secret', {}).get('value', '')
                        )
                        
                        if client_secret:
                            logger.info(
                                "Successfully generated ephemeral client key (New API)",
                                extra={"user_id": str(user.id)}
                            )
                        else:
                            logger.warning(
                                "New API response missing token, will use API key",
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
            
            # 如果无法获取临时秘钥，返回 API key（前端会使用 useInsecureApiKey）
            if not client_secret:
                logger.info(
                    "New API ephemeral token not available, using API key with useInsecureApiKey subprotocol",
                    extra={
                        "user_id": str(user.id),
                        "method": "useInsecureApiKey",
                        "note": "Frontend will use 'openai-insecure-api-key.{api_key}' subprotocol"
                    }
                )
                client_secret = settings.openai_api_key
        else:
            # OpenAI 官方方式：使用 /v1/realtime/client_secrets 端点
            logger.info(
                "Generating ephemeral client key (OpenAI)",
                extra={"user_id": str(user.id)}
            )
            
            client_secrets_url = "https://api.openai.com/v1/realtime/client_secrets"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # OpenAI 官方请求格式：使用 session 对象
                response = await client.post(
                    client_secrets_url,
                    headers={
                        'Authorization': f'Bearer {settings.openai_api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'session': {
                            'type': 'realtime',
                            'model': 'gpt-4o-realtime-preview-2024-10-01'
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
        
        # 构建 WebSocket URL（New API 和 OpenAI 官方共用）
        if is_new_api:
            # New API WebSocket URL
            if base_url.startswith('https://'):
                ws_base_url = base_url.replace('https://', 'wss://')
            elif base_url.startswith('http://'):
                ws_base_url = base_url.replace('http://', 'ws://')
            else:
                ws_base_url = base_url
            
            if ws_base_url.endswith('/v1'):
                ws_base_url = ws_base_url[:-3]
            elif ws_base_url.endswith('/v1/'):
                ws_base_url = ws_base_url[:-4]
            
            # New API WebSocket URL（浏览器使用子协议认证，不需要在 URL 中添加 token）
            ws_url = f"{ws_base_url.rstrip('/')}/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        else:
            # OpenAI 官方 WebSocket URL（浏览器使用子协议认证，不需要在 URL 中添加 token）
            ws_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        
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
            model='gpt-4o-realtime-preview-2024-10-01'
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

