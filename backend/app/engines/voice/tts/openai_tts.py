"""
OpenAI TTS引擎

使用OpenAI TTS API进行文本转语音
"""

# 标准库
from typing import Any, AsyncIterator, Dict, List, Optional

# 第三方库
from openai import AsyncOpenAI, APIError, OpenAIError

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import TTSEngineBase, TTSProvider


class OpenAITTSEngine(TTSEngineBase):
    """OpenAI TTS引擎
    
    使用OpenAI TTS API进行文本转语音
    """
    
    # OpenAI支持的语音列表
    AVAILABLE_VOICES = [
        "alloy", "echo", "fable", "onyx", "nova", "shimmer"
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化OpenAI TTS引擎
        
        Args:
            config: 配置字典（可选）
        """
        if config is None:
            config = {}
        
        super().__init__(config)
        
        # 创建OpenAI客户端
        self.client = AsyncOpenAI(
            api_key=config.get("api_key", settings.openai_api_key),
            base_url=config.get("base_url", settings.openai_base_url),
            timeout=config.get("timeout", 30.0)
        )
        
        # 验证语音名称
        if self.voice not in self.AVAILABLE_VOICES:
            logger.warning(
                f"Voice '{self.voice}' not in available voices, using 'shimmer'",
                extra={"voice": self.voice, "available_voices": self.AVAILABLE_VOICES}
            )
            self.voice = "shimmer"
        
        logger.info(
            f"OpenAI TTS engine initialized",
            extra={
                "provider": self.provider.value,
                "voice": self.voice,
                "speed": self.speed,
                "base_url": config.get("base_url", settings.openai_base_url)
            }
        )
    
    def _get_provider(self) -> TTSProvider:
        """返回提供商类型"""
        return TTSProvider.OPENAI
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> bytes:
        """使用OpenAI TTS进行文本转语音
        
        Args:
            text: 要转换的文本
            voice: 语音名称（可选）
            speed: 语速（可选，0.25-4.0）
            **kwargs: 其他参数
            
        Returns:
            bytes: 音频数据（MP3格式）
            
        Raises:
            ValueError: 如果文本为空或参数无效
            Exception: 如果转换失败
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        try:
            # 使用参数或默认值
            voice_name = voice or self.voice
            speed_value = speed or self.speed
            
            # 验证语速范围
            if not 0.25 <= speed_value <= 4.0:
                raise ValueError(f"Speed must be between 0.25 and 4.0, got {speed_value}")
            
            # 调用TTS API
            response = await self.client.audio.speech.create(
                model=kwargs.get("model", "tts-1"),
                voice=voice_name,
                input=text,
                speed=speed_value,
                **{k: v for k, v in kwargs.items() if k != "model"}
            )
            
            # 读取音频数据
            audio_data = b""
            async for chunk in response.iter_bytes():
                audio_data += chunk
            
            logger.info(
                f"OpenAI TTS synthesis completed",
                extra={
                    "voice": voice_name,
                    "speed": speed_value,
                    "text_length": len(text),
                    "audio_size": len(audio_data)
                }
            )
            
            return audio_data
            
        except APIError as e:
            logger.error(
                f"OpenAI TTS API error: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "status_code": getattr(e, "status_code", None)
                },
                exc_info=True
            )
            raise
        except OpenAIError as e:
            logger.error(f"OpenAI TTS error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI TTS: {e}", exc_info=True)
            raise
    
    async def stream_synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """流式文本转语音
        
        Args:
            text: 要转换的文本
            voice: 语音名称（可选）
            speed: 语速（可选）
            **kwargs: 其他参数
            
        Yields:
            bytes: 音频数据块
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        try:
            # 使用参数或默认值
            voice_name = voice or self.voice
            speed_value = speed or self.speed
            
            # 验证语速范围
            if not 0.25 <= speed_value <= 4.0:
                raise ValueError(f"Speed must be between 0.25 and 4.0, got {speed_value}")
            
            # 调用TTS API（流式）
            response = await self.client.audio.speech.create(
                model=kwargs.get("model", "tts-1"),
                voice=voice_name,
                input=text,
                speed=speed_value,
                **{k: v for k, v in kwargs.items() if k != "model"}
            )
            
            # 流式返回音频数据
            async for chunk in response.iter_bytes():
                yield chunk
            
            logger.info(
                f"OpenAI TTS stream synthesis completed",
                extra={
                    "voice": voice_name,
                    "speed": speed_value,
                    "text_length": len(text)
                }
            )
            
        except APIError as e:
            logger.error(
                f"OpenAI TTS stream API error: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "status_code": getattr(e, "status_code", None)
                },
                exc_info=True
            )
            raise
        except OpenAIError as e:
            logger.error(f"OpenAI TTS stream error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI TTS stream: {e}", exc_info=True)
            raise
    
    def get_available_voices(self) -> List[str]:
        """获取可用的语音列表
        
        Returns:
            List[str]: 语音名称列表
        """
        return self.AVAILABLE_VOICES.copy()
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        try:
            # 尝试列出模型来检查连接
            await self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI TTS health check failed: {e}")
            return False

