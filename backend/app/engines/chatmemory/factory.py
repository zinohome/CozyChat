"""
会话记忆引擎工厂
"""

# 标准库
from typing import Dict, Any

# 本地库
from app.engines.chatmemory.base import ChatMemoryEngineBase
from app.engines.chatmemory.mem0_engine import Mem0ChatMemoryEngine
from app.utils.logger import logger


class ChatMemoryEngineFactory:
    """会话记忆引擎工厂"""
    
    @staticmethod
    def create_engine(provider: str, config: Dict[str, Any]) -> ChatMemoryEngineBase:
        """创建会话记忆引擎实例
        
        Args:
            provider: 引擎提供商（如 "mem0"）
            config: 引擎配置
        
        Returns:
            ChatMemoryEngineBase: 会话记忆引擎实例
        
        Raises:
            ValueError: 未知的provider
        """
        provider = provider.lower().strip()
        
        if provider == "mem0":
            logger.info(f"Creating Mem0 chatmemory engine with config: {config}")
            return Mem0ChatMemoryEngine(config=config)
        
        # 未来可扩展其他会话记忆引擎
        else:
            raise ValueError(
                f"Unknown chatmemory engine provider: {provider}. "
                f"Supported providers: mem0"
            )

