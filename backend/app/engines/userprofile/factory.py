"""
用户画像引擎工厂
"""

# 标准库
from typing import Dict, Any

# 本地库
from app.engines.userprofile.base import UserProfileEngineBase
from app.engines.userprofile.memobase_engine import MemobaseUserProfileEngine
from app.utils.logger import logger


class UserProfileEngineFactory:
    """用户画像引擎工厂"""
    
    @staticmethod
    def create_engine(provider: str, config: Dict[str, Any]) -> UserProfileEngineBase:
        """创建用户画像引擎实例
        
        Args:
            provider: 引擎提供商（如 "memobase"）
            config: 引擎配置
        
        Returns:
            UserProfileEngineBase: 用户画像引擎实例
        
        Raises:
            ValueError: 未知的provider
        """
        provider = provider.lower().strip()
        
        if provider == "memobase":
            logger.info(f"Creating Memobase userprofile engine with config: {config}")
            return MemobaseUserProfileEngine(config=config)
        
        # 未来可扩展其他用户画像引擎
        else:
            raise ValueError(
                f"Unknown userprofile engine provider: {provider}. "
                f"Supported providers: memobase"
            )

