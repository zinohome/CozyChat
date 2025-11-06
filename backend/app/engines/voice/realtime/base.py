"""
RealTime（实时语音对话）引擎基类

定义所有RealTime引擎的统一接口
"""

# 标准库
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Dict, Optional

# 本地库
from app.utils.logger import logger


class RealtimeProvider(str, Enum):
    """RealTime提供商枚举"""
    OPENAI = "openai"
    CUSTOM = "custom"


class RealtimeEngineBase(ABC):
    """RealTime引擎基类
    
    所有RealTime引擎实现必须继承此类并实现抽象方法
    
    Attributes:
        provider: 提供商类型
        voice: 语音名称
        config: 配置字典
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化RealTime引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.provider = self._get_provider()
        self.voice = config.get("voice", "shimmer")
        
        logger.debug(
            f"Initializing RealTime engine: {self.provider.value}",
            extra={"provider": self.provider.value, "voice": self.voice}
        )
    
    @abstractmethod
    def _get_provider(self) -> RealtimeProvider:
        """返回提供商类型
        
        Returns:
            RealtimeProvider: 提供商类型
        """
        raise NotImplementedError
    
    @abstractmethod
    async def connect(self) -> str:
        """建立WebSocket连接
        
        Returns:
            str: WebSocket连接URL或会话ID
        """
        raise NotImplementedError
    
    @abstractmethod
    async def send_audio(self, audio_data: bytes) -> None:
        """发送音频数据
        
        Args:
            audio_data: 音频数据（bytes）
        """
        raise NotImplementedError
    
    @abstractmethod
    async def receive_audio(self) -> AsyncIterator[bytes]:
        """接收音频数据
        
        Yields:
            bytes: 音频数据块
        """
        raise NotImplementedError
    
    @abstractmethod
    async def send_text(self, text: str) -> None:
        """发送文本消息
        
        Args:
            text: 文本内容
        """
        raise NotImplementedError
    
    @abstractmethod
    async def receive_text(self) -> AsyncIterator[str]:
        """接收文本消息
        
        Yields:
            str: 文本内容
        """
        raise NotImplementedError
    
    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        raise NotImplementedError
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 引擎是否健康
        """
        raise NotImplementedError

