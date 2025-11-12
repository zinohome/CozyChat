"""
音频API路由

提供STT（语音转文本）、TTS（文本转语音）接口

注意：RealTime语音对话接口通过WebSocket实现，请参考：
- WebSocket路由：/v1/ws/realtime
- 详见：app/api/v1/websocket.py
"""

# 标准库
from typing import Optional

# 第三方库
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# 本地库
from app.api.deps import get_current_active_user
from app.core.personality import PersonalityManager
from app.engines.voice.stt.factory import STTEngineFactory
from app.engines.voice.tts.factory import TTSEngineFactory
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


# ==================== 请求/响应模型 ====================

class TranscriptionRequest(BaseModel):
    """STT转录请求（JSON参数）"""
    model: Optional[str] = Field(default="whisper-1", description="模型名称")
    language: Optional[str] = Field(default=None, description="语言代码（如zh-CN）")
    personality_id: Optional[str] = Field(default=None, description="人格ID")


class TranscriptionResponse(BaseModel):
    """STT转录响应"""
    text: str = Field(..., description="转录的文本")


class SpeechRequest(BaseModel):
    """TTS语音合成请求"""
    model: Optional[str] = Field(default="tts-1", description="模型名称")
    input: str = Field(..., description="要合成的文本")
    voice: Optional[str] = Field(default="alloy", description="语音类型")
    speed: Optional[float] = Field(default=1.0, description="语速（0.25-4.0）")
    personality_id: Optional[str] = Field(default=None, description="人格ID")


# ==================== STT API ====================

@router.post("/transcriptions", response_model=TranscriptionResponse)
async def create_transcription(
    file: UploadFile = File(..., description="音频文件"),
    model: str = Form(default="whisper-1"),
    language: Optional[str] = Form(default=None),
    personality_id: Optional[str] = Form(default=None),
    user: User = Depends(get_current_active_user)
):
    """
    语音转文本（STT）
    
    支持多种音频格式：mp3, mp4, mpeg, mpga, m4a, wav, webm
    
    Args:
        file: 音频文件
        model: 模型名称（默认whisper-1）
        language: 语言代码（可选）
        personality_id: 人格ID（可选，如果提供则使用人格配置的STT设置）
        user: 当前用户
    
    Returns:
        TranscriptionResponse: 转录结果
    """
    try:
        # 读取音频文件
        audio_data = await file.read()
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="音频文件为空")
        
        # 获取STT配置
        stt_config = {}
        if personality_id:
            personality_manager = PersonalityManager()
            personality = personality_manager.get_personality(personality_id)
            if personality:
                voice_config = personality.voice
                if voice_config and voice_config.get("stt"):
                    stt_config = voice_config["stt"]
                    # 使用人格配置的provider和model
                    provider = stt_config.get("provider", "openai")
                    if "model" not in stt_config:
                        stt_config["model"] = model
                    if "language" not in stt_config and language:
                        stt_config["language"] = language
                else:
                    provider = "openai"
                    stt_config = {"model": model, "language": language}
            else:
                provider = "openai"
                stt_config = {"model": model, "language": language}
        else:
            provider = "openai"
            stt_config = {"model": model, "language": language}
        
        # 创建STT引擎
        stt_engine = STTEngineFactory.create_engine(provider, stt_config)
        
        # 执行转录
        text = await stt_engine.transcribe(audio_data, **stt_config)
        
        logger.info(
            "STT transcription completed",
            extra={
                "user_id": str(user.id),
                "personality_id": personality_id,
                "model": model,
                "text_length": len(text)
            }
        )
        
        return TranscriptionResponse(text=text)
        
    except Exception as e:
        logger.error(
            f"STT transcription failed: {e}",
            exc_info=True,
            extra={"user_id": str(user.id), "personality_id": personality_id}
        )
        raise HTTPException(status_code=500, detail=f"转录失败: {str(e)}")


# ==================== TTS API ====================

@router.post("/speech")
async def create_speech(
    request: SpeechRequest,
    user: User = Depends(get_current_active_user)
):
    """
    文本转语音（TTS）
    
    返回音频流（audio/mpeg格式）
    
    Args:
        request: TTS请求
        user: 当前用户
    
    Returns:
        StreamingResponse: 音频流
    """
    try:
        # 获取TTS配置
        tts_config = {}
        if request.personality_id:
            personality_manager = PersonalityManager()
            personality = personality_manager.get_personality(request.personality_id)
            if personality and personality.voice and personality.voice.tts:
                # VoiceConfig 是 dataclass，使用属性访问
                tts_config = personality.voice.tts.copy()  # 复制字典避免修改原配置
                provider = tts_config.get("provider", "openai")
                # 使用人格配置的voice和speed，但允许请求参数覆盖
                if request.voice:
                    tts_config["voice"] = request.voice
                elif "voice" not in tts_config:
                    tts_config["voice"] = "alloy"
                if request.speed:
                    tts_config["speed"] = request.speed
                elif "speed" not in tts_config:
                    tts_config["speed"] = 1.0
                if request.model:
                    tts_config["model"] = request.model
                elif "model" not in tts_config:
                    tts_config["model"] = "tts-1"
            else:
                provider = "openai"
                tts_config = {
                    "model": request.model,
                    "voice": request.voice,
                    "speed": request.speed
                }
        else:
            provider = "openai"
            tts_config = {
                "model": request.model,
                "voice": request.voice,
                "speed": request.speed
            }
        
        # 创建TTS引擎
        tts_engine = TTSEngineFactory.create_engine(provider, tts_config)
        
        # 执行语音合成
        audio_data = await tts_engine.synthesize(
            request.input,
            voice=tts_config.get("voice", request.voice),
            speed=tts_config.get("speed", request.speed)
        )
        
        logger.info(
            "TTS synthesis completed",
            extra={
                "user_id": str(user.id),
                "personality_id": request.personality_id,
                "model": request.model,
                "text_length": len(request.input),
                "audio_size": len(audio_data)
            }
        )
        
        # 返回音频流
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
        
    except Exception as e:
        logger.error(
            f"TTS synthesis failed: {e}",
            exc_info=True,
            extra={"user_id": str(user.id), "personality_id": request.personality_id}
        )
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.post("/speech/stream")
async def create_speech_stream(
    request: SpeechRequest,
    user: User = Depends(get_current_active_user)
):
    """
    流式文本转语音（TTS Stream）
    
    返回流式音频数据
    
    Args:
        request: TTS请求
        user: 当前用户
    
    Returns:
        StreamingResponse: 流式音频数据
    """
    try:
        # 获取TTS配置
        tts_config = {}
        if request.personality_id:
            personality_manager = PersonalityManager()
            personality = personality_manager.get_personality(request.personality_id)
            if personality and personality.voice and personality.voice.tts:
                # VoiceConfig 是 dataclass，使用属性访问
                tts_config = personality.voice.tts.copy()  # 复制字典避免修改原配置
                provider = tts_config.get("provider", "openai")
                # 使用人格配置的voice和speed，但允许请求参数覆盖
                if request.voice:
                    tts_config["voice"] = request.voice
                elif "voice" not in tts_config:
                    tts_config["voice"] = "alloy"
                if request.speed:
                    tts_config["speed"] = request.speed
                elif "speed" not in tts_config:
                    tts_config["speed"] = 1.0
                if request.model:
                    tts_config["model"] = request.model
                elif "model" not in tts_config:
                    tts_config["model"] = "tts-1"
            else:
                provider = "openai"
                tts_config = {
                    "model": request.model,
                    "voice": request.voice,
                    "speed": request.speed
                }
        else:
            provider = "openai"
            tts_config = {
                "model": request.model,
                "voice": request.voice,
                "speed": request.speed
            }
        
        # 创建TTS引擎
        tts_engine = TTSEngineFactory.create_engine(provider, tts_config)
        
        # 执行流式语音合成
        async def generate_audio_stream():
            async for chunk in tts_engine.stream_synthesize(
                request.input,
                voice=tts_config.get("voice", request.voice),
                speed=tts_config.get("speed", request.speed)
            ):
                yield chunk
        
        logger.info(
            "TTS stream synthesis started",
            extra={
                "user_id": str(user.id),
                "personality_id": request.personality_id,
                "model": request.model,
                "text_length": len(request.input)
            }
        )
        
        # 返回流式音频
        return StreamingResponse(
            generate_audio_stream(),
            media_type="audio/mpeg"
        )
        
    except Exception as e:
        logger.error(
            f"TTS stream synthesis failed: {e}",
            exc_info=True,
            extra={"user_id": str(user.id), "personality_id": request.personality_id}
        )
        raise HTTPException(status_code=500, detail=f"流式语音合成失败: {str(e)}")

