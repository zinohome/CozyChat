"""
AI引擎工厂

创建AI引擎实例的工厂类
"""

# 标准库
from typing import Any, Dict, Optional

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from .base import AIEngineBase
from .ollama_engine import OllamaEngine
from .openai_engine import OpenAIEngine
from .registry import AIEngineRegistry


# 注册内置引擎
AIEngineRegistry.register("openai", OpenAIEngine)
AIEngineRegistry.register("ollama", OllamaEngine)


class AIEngineFactory:
    """AI引擎工厂类
    
    使用工厂模式创建AI引擎实例
    """
    
    @staticmethod
    def create_engine(
        engine_type: str,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> AIEngineBase:
        """创建AI引擎实例
        
        Args:
            engine_type: 引擎类型（openai, ollama等）
            model: 模型名称（可选，如果不提供则使用默认值）
            **kwargs: 其他参数
            
        Returns:
            AIEngineBase: AI引擎实例
            
        Raises:
            ValueError: 如果引擎类型不支持
        """
        # 获取引擎类
        engine_class = AIEngineRegistry.get_engine_class(engine_type)
        
        if engine_class is None:
            available_engines = AIEngineRegistry.list_engines()
            raise ValueError(
                f"Unsupported engine type: {engine_type}. "
                f"Available engines: {', '.join(available_engines)}"
            )
        
        # 从YAML配置加载引擎配置
        try:
            config_loader = get_config_loader()
            engine_config = config_loader.load_engine_config(engine_type)
            
            # 合并YAML配置和传入参数（传入参数优先级更高）
            default_config = engine_config.get("default", {})
            if model is None:
                model = default_config.get("model") or kwargs.get("model")
            
            # 构建引擎参数
            engine_params: Dict[str, Any] = {}
            
            # 从YAML默认配置获取参数
            if engine_type == "openai":
                engine_params.update({
                    "model": model or default_config.get("model", "gpt-3.5-turbo"),
                    "api_key": kwargs.get("api_key", settings.openai_api_key),
                    "base_url": kwargs.get("base_url", default_config.get("base_url") or settings.openai_base_url),
                })
            elif engine_type == "ollama":
                engine_params.update({
                    "model": model or default_config.get("model", "llama2"),
                    "base_url": kwargs.get("base_url", default_config.get("base_url", settings.ollama_base_url)),
                })
            else:
                # 通用创建方式
                engine_params.update({
                    "model": model or default_config.get("model", "default"),
                })
                engine_params.update(default_config)
            
            # 传入的kwargs覆盖YAML配置
            engine_params.update(kwargs)
            
            engine = engine_class(**engine_params)
            
        except Exception as e:
            # 如果YAML配置加载失败，回退到硬编码配置
            logger.warning(
                f"Failed to load engine config from YAML, using defaults: {e}",
                exc_info=False
            )
            
            # 回退到硬编码配置
            if engine_type == "openai":
                if model is None:
                    model = "gpt-3.5-turbo"
                engine = engine_class(
                    model=model,
                    api_key=kwargs.get("api_key", settings.openai_api_key),
                    base_url=kwargs.get("base_url", settings.openai_base_url),
                    **{k: v for k, v in kwargs.items() if k not in ["api_key", "base_url"]}
                )
            elif engine_type == "ollama":
                if model is None:
                    model = "llama2"
                engine = engine_class(
                    model=model,
                    base_url=kwargs.get("base_url", settings.ollama_base_url),
                    **{k: v for k, v in kwargs.items() if k != "base_url"}
                )
            else:
                engine = engine_class(model=model or "default", **kwargs)
        
        logger.info(
            f"Created AI engine: {engine_type}",
            extra={
                "engine_type": engine_type,
                "model": model,
                "class": engine_class.__name__
            }
        )
        
        return engine
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> AIEngineBase:
        """从配置字典创建AI引擎
        
        Args:
            config: 配置字典，必须包含'type'和'model'字段
            
        Returns:
            AIEngineBase: AI引擎实例
            
        Raises:
            ValueError: 如果配置格式不正确
        """
        if "type" not in config:
            raise ValueError("Config must contain 'type' field")
        
        engine_type = config["type"]
        model = config.get("model")
        
        # 提取其他参数
        other_params = {k: v for k, v in config.items() if k not in ["type", "model"]}
        
        return AIEngineFactory.create_engine(
            engine_type=engine_type,
            model=model,
            **other_params
        )
    
    @staticmethod
    def list_available_engines() -> Dict[str, str]:
        """列出所有可用的引擎
        
        Returns:
            Dict[str, str]: 引擎名称到描述的映射
        """
        engines = AIEngineRegistry.list_engines()
        return {
            engine: f"{engine.capitalize()} Engine"
            for engine in engines
        }

