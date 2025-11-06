"""
OpenAI STT引擎

使用OpenAI Whisper API进行语音转文本
"""

# 标准库
import io
from typing import Any, Dict, Optional

# 第三方库
from openai import AsyncOpenAI, APIError, OpenAIError

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import STTEngineBase, STTProvider


class OpenAISTTEngine(STTEngineBase):
    """OpenAI Whisper STT引擎
    
    使用OpenAI Whisper API进行语音转文本
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化OpenAI STT引擎
        
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
        
        logger.info(
            f"OpenAI STT engine initialized",
            extra={
                "provider": self.provider.value,
                "model": self.model,
                "base_url": config.get("base_url", settings.openai_base_url)
            }
        )
    
    def _get_provider(self) -> STTProvider:
        """返回提供商类型"""
        return STTProvider.OPENAI
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """使用OpenAI Whisper进行语音识别
        
        Args:
            audio_data: 音频数据（bytes）
            language: 语言代码（可选）
            **kwargs: 其他参数
            
        Returns:
            str: 识别的文本
            
        Raises:
            ValueError: 如果音频数据无效
            Exception: 如果识别失败
        """
        try:
            # 验证音频格式
            if not self.validate_audio_format(audio_data):
                raise ValueError("Unsupported audio format")
            
            # 将bytes转为file-like对象
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # 调用Whisper API
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language or self.language,
                response_format="text",
                **kwargs
            )
            
            # OpenAI API返回的是字符串（当response_format="text"时）
            text = response if isinstance(response, str) else str(response)
            
            logger.info(
                f"OpenAI STT transcription completed",
                extra={
                    "model": self.model,
                    "language": language or self.language,
                    "text_length": len(text)
                }
            )
            
            return text
            
        except APIError as e:
            logger.error(
                f"OpenAI STT API error: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "status_code": getattr(e, "status_code", None)
                },
                exc_info=True
            )
            raise
        except OpenAIError as e:
            logger.error(f"OpenAI STT error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI STT: {e}", exc_info=True)
            raise
    
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
            logger.warning(f"OpenAI STT health check failed: {e}")
            return False

