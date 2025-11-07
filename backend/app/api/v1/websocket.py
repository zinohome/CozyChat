"""
WebSocket API路由

提供实时语音对话（RealTime Audio）的WebSocket接口

RealTime语音对话功能：
- WebSocket连接：/v1/ws/realtime
- 支持实时双向语音对话
- 使用OpenAI Realtime API
- 支持音频流传输和文本消息

使用示例：
1. 建立WebSocket连接：wss://api.cozychat.ai/v1/ws/realtime?token=<jwt_token>&personality_id=<personality_id>
2. 发送音频数据：通过WebSocket发送二进制音频数据或JSON消息
3. 接收AI响应：通过WebSocket接收音频数据和文本转录

注意：RealTime语音对话仅支持WebSocket协议，不支持REST API
"""

# 标准库
import json
from typing import Optional

# 第三方库
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

# 本地库
from app.api.deps import get_current_user_from_token
from app.core.personality import PersonalityManager
from app.engines.voice.realtime.factory import RealtimeEngineFactory
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


@router.websocket("/realtime")
async def websocket_realtime(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token"),
    personality_id: Optional[str] = Query(None, description="人格ID"),
    session_id: Optional[str] = Query(None, description="会话ID")
):
    """
    RealTime语音对话WebSocket接口
    
    支持实时双向语音对话，使用OpenAI Realtime API
    
    Args:
        websocket: WebSocket连接
        token: JWT token（用于认证）
        personality_id: 人格ID
        session_id: 会话ID
    """
    await websocket.accept()
    
    user: Optional[User] = None
    realtime_engine = None
    
    try:
        # 认证用户
        if token:
            try:
                user = await get_current_user_from_token(token)
                logger.info(
                    "WebSocket connection authenticated",
                    extra={"user_id": str(user.id)}
                )
            except Exception as e:
                logger.warning(f"WebSocket authentication failed: {e}")
                await websocket.close(code=1008, reason="Authentication failed")
                return
        else:
            logger.warning("WebSocket connection without token")
            await websocket.close(code=1008, reason="Token required")
            return
        
        # 获取人格配置
        realtime_config = {}
        if personality_id:
            personality_manager = PersonalityManager()
            personality = personality_manager.get_personality(personality_id)
            if personality:
                voice_config = personality.voice
                if voice_config and voice_config.get("realtime"):
                    realtime_config = voice_config["realtime"]
                    provider = realtime_config.get("provider", "openai")
                else:
                    provider = "openai"
            else:
                provider = "openai"
        else:
            provider = "openai"
        
        # 创建RealTime引擎
        realtime_engine = RealtimeEngineFactory.create_engine(provider, realtime_config)
        
        logger.info(
            "RealTime WebSocket connection established",
            extra={
                "user_id": str(user.id),
                "personality_id": personality_id,
                "session_id": session_id
            }
        )
        
        # 启动RealTime引擎（连接WebSocket）
        await realtime_engine.connect()
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "realtime_started",
            "session_id": session_id or "realtime_session",
            "status": "ready"
        })
        
        # 消息处理循环
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive()
                
                if "text" in data:
                    # 文本消息（控制消息）
                    message = json.loads(data["text"])
                    message_type = message.get("type")
                    
                    if message_type == "stop_realtime":
                        # 停止实时对话
                        await realtime_engine.close()
                        await websocket.send_json({
                            "type": "realtime_stopped",
                            "status": "stopped"
                        })
                        break
                    
                    elif message_type == "audio_chunk":
                        # 音频数据（base64编码或bytes）
                        audio_data = message.get("audio_data")
                        if audio_data:
                            # 发送音频数据到RealTime引擎
                            import base64
                            if isinstance(audio_data, str):
                                # base64编码的字符串
                                audio_bytes = base64.b64decode(audio_data)
                            else:
                                audio_bytes = audio_data
                            
                            await realtime_engine.send_audio(audio_bytes)
                
                elif "bytes" in data:
                    # 二进制音频数据
                    audio_data = data["bytes"]
                    if audio_data:
                        # 发送音频数据到RealTime引擎
                        await realtime_engine.send_audio(audio_data)
                
            except WebSocketDisconnect:
                logger.info(
                    "WebSocket disconnected",
                    extra={"user_id": str(user.id) if user else None}
                )
                break
            except Exception as e:
                logger.error(
                    f"WebSocket message processing error: {e}",
                    exc_info=True,
                    extra={"user_id": str(user.id) if user else None}
                )
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
        
    except Exception as e:
        logger.error(
            f"WebSocket RealTime error: {e}",
            exc_info=True,
            extra={"user_id": str(user.id) if user else None}
        )
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            await websocket.close(code=1011, reason="Internal error")
    finally:
        # 清理资源
        if realtime_engine:
            try:
                await realtime_engine.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect RealTime engine: {e}", exc_info=True)
        
        logger.info(
            "WebSocket RealTime connection closed",
            extra={"user_id": str(user.id) if user else None}
        )

