"""
STT引擎工厂

创建STT引擎实例的工厂类
"""

# 标准库
from typing import Any, Dict, Optional

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import STTEngineBase, STTProvider
from .openai_stt import OpenAISTTEngine


class STTEngineFactory:
    """STT引擎工厂类
    
    使用工厂模式创建STT引擎实例
    """
    
    @staticmethod
    def create_engine(
        provider: str,
        config: Optional[Dict[str, Any]] = None
    ) -> STTEngineBase:
        """创建STT引擎实例
        
        Args:
            provider: 提供商类型（openai, tencent等）
            config: 配置字典（可选）
            
        Returns:
            STTEngineBase: STT引擎实例
            
        Raises:
            ValueError: 如果提供商类型不支持
        """
        if config is None:
            config = {}
        
        provider_lower = provider.lower()
        
        if provider_lower == STTProvider.OPENAI.value:
            # 设置默认配置
            if "api_key" not in config:
                config["api_key"] = settings.openai_api_key
            if "base_url" not in config:
                config["base_url"] = settings.openai_base_url
            
            engine = OpenAISTTEngine(config)
            
        elif provider_lower == STTProvider.TENCENT.value:
            # 腾讯ASR实现（待实现）
            raise NotImplementedError("Tencent ASR engine not implemented yet")
            
        else:
            available_providers = [p.value for p in STTProvider]
            raise ValueError(
                f"Unsupported STT provider: {provider}. "
                f"Available providers: {', '.join(available_providers)}"
            )
        
        logger.info(
            f"Created STT engine: {provider}",
            extra={"provider": provider, "class": engine.__class__.__name__}
        )
        
        return engine
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> STTEngineBase:
        """从配置字典创建STT引擎
        
        Args:
            config: 配置字典，必须包含'provider'字段
            
        Returns:
            STTEngineBase: STT引擎实例
            
        Raises:
            ValueError: 如果配置格式不正确
        """
        if "provider" not in config:
            raise ValueError("Config must contain 'provider' field")
        
        provider = config["provider"]
        
        # 提取其他参数
        other_params = {k: v for k, v in config.items() if k != "provider"}
        
        return STTEngineFactory.create_engine(
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
            STTProvider.OPENAI.value: "OpenAI Whisper",
            STTProvider.TENCENT.value: "Tencent ASR (待实现)",
            STTProvider.CUSTOM.value: "Custom STT Engine"
        }

