"""
RealTime引擎工厂

创建RealTime引擎实例的工厂类
"""

# 标准库
from typing import Any, Dict, Optional

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import RealtimeEngineBase, RealtimeProvider
from .openai_realtime import OpenAIRealtimeEngine


class RealtimeEngineFactory:
    """RealTime引擎工厂类
    
    使用工厂模式创建RealTime引擎实例
    """
    
    @staticmethod
    def create_engine(
        provider: str,
        config: Optional[Dict[str, Any]] = None
    ) -> RealtimeEngineBase:
        """创建RealTime引擎实例
        
        Args:
            provider: 提供商类型（openai等）
            config: 配置字典（可选）
            
        Returns:
            RealtimeEngineBase: RealTime引擎实例
            
        Raises:
            ValueError: 如果提供商类型不支持
        """
        if config is None:
            config = {}
        
        provider_lower = provider.lower()
        
        if provider_lower == RealtimeProvider.OPENAI.value:
            # 设置默认配置
            if "api_key" not in config:
                config["api_key"] = settings.openai_api_key
            if "base_url" not in config:
                config["base_url"] = settings.openai_base_url
            
            engine = OpenAIRealtimeEngine(config)
            
        else:
            available_providers = [p.value for p in RealtimeProvider]
            raise ValueError(
                f"Unsupported RealTime provider: {provider}. "
                f"Available providers: {', '.join(available_providers)}"
            )
        
        logger.info(
            f"Created RealTime engine: {provider}",
            extra={"provider": provider, "class": engine.__class__.__name__}
        )
        
        return engine
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> RealtimeEngineBase:
        """从配置字典创建RealTime引擎
        
        Args:
            config: 配置字典，必须包含'provider'字段
            
        Returns:
            RealtimeEngineBase: RealTime引擎实例
            
        Raises:
            ValueError: 如果配置格式不正确
        """
        if "provider" not in config:
            raise ValueError("Config must contain 'provider' field")
        
        provider = config["provider"]
        
        # 提取其他参数
        other_params = {k: v for k, v in config.items() if k != "provider"}
        
        return RealtimeEngineFactory.create_engine(
            provider=provider,
            config=other_params
        )
    
    @staticmethod
    def list_available_providers() -> Dict[str, str]:
        """列出所有可用的提供商
        
        Returns:
            Dict[str, str]: 提供商名称到描述的映射
        """
        return {
            RealtimeProvider.OPENAI.value: "OpenAI Realtime API",
            RealtimeProvider.CUSTOM.value: "Custom RealTime Engine"
        }

