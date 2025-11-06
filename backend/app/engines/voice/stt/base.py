"""
STT（语音转文本）引擎基类

定义所有STT引擎的统一接口
"""

# 标准库
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

# 本地库
from app.utils.logger import logger


class STTProvider(str, Enum):
    """STT提供商枚举"""
    OPENAI = "openai"
    TENCENT = "tencent"
    CUSTOM = "custom"


class STTEngineBase(ABC):
    """STT引擎基类
    
    所有STT引擎实现必须继承此类并实现抽象方法
    
    Attributes:
        provider: 提供商类型
        model: 模型名称
        language: 语言代码
        config: 配置字典
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化STT引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.provider = self._get_provider()
        self.model = config.get("model", "whisper-1")
        self.language = config.get("language", "zh-CN")
        
        logger.debug(
            f"Initializing STT engine: {self.provider.value}",
            extra={"provider": self.provider.value, "model": self.model}
        )
    
    @abstractmethod
    def _get_provider(self) -> STTProvider:
        """返回提供商类型
        
        Returns:
            STTProvider: 提供商类型
        """
        raise NotImplementedError
    
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """语音转文本
        
        Args:
            audio_data: 音频数据（bytes）
            language: 语言代码（可选，如果不提供则使用默认值）
            **kwargs: 其他参数
            
        Returns:
            str: 识别的文本
            
        Raises:
            ValueError: 如果音频数据无效
            Exception: 如果识别失败
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
        """获取支持的音频格式
        
        Returns:
            List[str]: 支持的音频格式列表
        """
        return ["wav", "mp3", "m4a", "webm", "ogg", "flac"]
    
    def validate_audio_format(self, audio_data: bytes, format: Optional[str] = None) -> bool:
        """验证音频格式
        
        Args:
            audio_data: 音频数据
            format: 音频格式（可选）
            
        Returns:
            bool: 格式是否支持
        """
        supported_formats = self.get_supported_formats()
        
        if format:
            return format.lower() in [f.lower() for f in supported_formats]
        
        # 尝试从文件头判断格式
        if len(audio_data) < 12:
            return False
        
        # 检查常见音频格式的魔数
        magic_numbers = {
            b"RIFF": "wav",
            b"ID3": "mp3",
            b"\xff\xfb": "mp3",
            b"fLaC": "flac",
            b"OggS": "ogg",
            b"ftyp": "m4a",
        }
        
        for magic, fmt in magic_numbers.items():
            if audio_data.startswith(magic):
                return fmt in supported_formats
        
        return True

