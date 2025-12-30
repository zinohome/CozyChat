"""
AI引擎注册中心

管理所有可用的AI引擎
"""

# 标准库
from typing import Dict, List, Optional, Type

# 本地库
from app.utils.logger import logger
from .base import AIEngineBase


class AIEngineRegistry:
    """AI引擎注册中心
    
    单例模式，管理所有注册的AI引擎类
    
    Attributes:
        _engines: 引擎类字典，key为引擎名称，value为引擎类
    """
    
    _instance: Optional["AIEngineRegistry"] = None
    _engines: Dict[str, Type[AIEngineBase]] = {}
    
    def __new__(cls) -> "AIEngineRegistry":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name: str, engine_class: Type[AIEngineBase]) -> None:
        """注册AI引擎类
        
        Args:
            name: 引擎名称
            engine_class: 引擎类
            
        Raises:
            ValueError: 如果引擎名称已存在
        """
        if name in cls._engines:
            logger.warning(f"Engine '{name}' already registered, overwriting")
        
        if not issubclass(engine_class, AIEngineBase):
            raise ValueError(f"Engine class must be subclass of AIEngineBase")
        
        cls._engines[name] = engine_class
        logger.info(f"Registered AI engine: {name}")
    
    @classmethod
    def get_engine_class(cls, name: str) -> Optional[Type[AIEngineBase]]:
        """获取AI引擎类
        
        Args:
            name: 引擎名称
            
        Returns:
            Type[AIEngineBase]: 引擎类，如果不存在返回None
        """
        return cls._engines.get(name)
    
    @classmethod
    def list_engines(cls) -> List[str]:
        """列出所有注册的引擎名称
        
        Returns:
            List[str]: 引擎名称列表
        """
        return list(cls._engines.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """检查引擎是否已注册
        
        Args:
            name: 引擎名称
            
        Returns:
            bool: 是否已注册
        """
        return name in cls._engines
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """注销AI引擎
        
        Args:
            name: 引擎名称
        """
        if name in cls._engines:
            del cls._engines[name]
            logger.info(f"Unregistered AI engine: {name}")
        else:
            logger.warning(f"Engine '{name}' not found in registry")

