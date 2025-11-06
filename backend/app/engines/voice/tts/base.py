"""
TTS（文本转语音）引擎基类

定义所有TTS引擎的统一接口
"""

# 标准库
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

# 本地库
from app.utils.logger import logger


class TTSProvider(str, Enum):
    """TTS提供商枚举"""
    OPENAI = "openai"
    TENCENT = "tencent"
    CUSTOM = "custom"


class TTSEngineBase(ABC):
    """TTS引擎基类
    
    所有TTS引擎实现必须继承此类并实现抽象方法
    
    Attributes:
        provider: 提供商类型
        voice: 语音名称
        speed: 语速
        config: 配置字典
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化TTS引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.provider = self._get_provider()
        self.voice = config.get("voice", "shimmer")
        self.speed = config.get("speed", 1.0)
        
        logger.debug(
            f"Initializing TTS engine: {self.provider.value}",
            extra={"provider": self.provider.value, "voice": self.voice}
        )
    
    @abstractmethod
    def _get_provider(self) -> TTSProvider:
        """返回提供商类型
        
        Returns:
            TTSProvider: 提供商类型
        """
        raise NotImplementedError
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs: Any
    ) -> bytes:
        """文本转语音
        
        Args:
            text: 要转换的文本
            voice: 语音名称（可选，如果不提供则使用默认值）
            speed: 语速（可选，如果不提供则使用默认值）
            **kwargs: 其他参数
            
        Returns:
            bytes: 音频数据（bytes）
            
        Raises:
            ValueError: 如果文本为空
            Exception: 如果转换失败
        """
        raise NotImplementedError
    
    @abstractmethod
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
        raise NotImplementedError
    
    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """获取可用的语音列表
        
        Returns:
            List[str]: 语音名称列表
        """
        raise NotImplementedError
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        raise NotImplementedError
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的音频输出格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        return ["mp3", "opus", "aac", "flac"]

