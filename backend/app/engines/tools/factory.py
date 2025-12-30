"""
工具管理器工厂

提供工具实例的创建和缓存，避免重复初始化。
"""

# 标准库
from typing import Dict, List, Optional, Set
import threading

# 本地库
from app.engines.tools.manager import ToolManager
from app.engines.tools.base import Tool
from app.utils.logger import logger


class ToolManagerFactory:
    """工具管理器工厂
    
    根据人格配置提供对应的工具集合，
    对无状态工具使用单例缓存。
    """
    
    _instance: Optional['ToolManagerFactory'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """初始化工厂"""
        # 缓存已创建的工具实例（按工具名称）
        self._tool_cache: Dict[str, Tool] = {}
        # 缓存已创建的工具管理器（按工具ID集合的hash）
        self._manager_cache: Dict[str, ToolManager] = {}
        self._cache_lock = threading.Lock()
        
        logger.info("ToolManagerFactory initialized")
    
    @classmethod
    def get_instance(cls) -> 'ToolManagerFactory':
        """获取单例实例
        
        Returns:
            ToolManagerFactory: 单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_tool_manager(self, allowed_tools: Optional[List[str]] = None) -> ToolManager:
        """获取工具管理器
        
        Args:
            allowed_tools: 允许的工具名称列表，None表示允许所有工具
            
        Returns:
            ToolManager: 工具管理器实例
        """
        # 如果没有指定工具，创建包含所有工具的管理器
        if allowed_tools is None:
            cache_key = "__all__"
        else:
            # 使用排序后的工具列表作为缓存key
            cache_key = ",".join(sorted(allowed_tools))
        
        # 检查缓存
        with self._cache_lock:
            if cache_key in self._manager_cache:
                logger.debug(
                    f"Using cached ToolManager for: {cache_key}",
                    extra={"cache_key": cache_key}
                )
                return self._manager_cache[cache_key]
            
            # 创建新的管理器
            manager = ToolManager()
            
            # 如果指定了工具列表，只初始化这些工具
            if allowed_tools is not None:
                # 这里可以根据工具名称过滤或初始化特定工具
                # 当前ToolManager会自动扫描并注册所有工具
                # 如果需要更精细的控制，可以在这里实现
                pass
            
            # 缓存管理器
            self._manager_cache[cache_key] = manager
            
            logger.info(
                f"Created new ToolManager",
                extra={
                    "cache_key": cache_key,
                    "allowed_tools": allowed_tools,
                    "total_managers": len(self._manager_cache)
                }
            )
            
            return manager
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self._cache_lock:
            self._tool_cache.clear()
            self._manager_cache.clear()
            logger.info("ToolManagerFactory cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, int]: 缓存统计信息
        """
        with self._cache_lock:
            return {
                "tool_cache_size": len(self._tool_cache),
                "manager_cache_size": len(self._manager_cache),
            }


# 创建全局实例
_factory: Optional[ToolManagerFactory] = None


def get_tool_manager_factory() -> ToolManagerFactory:
    """获取全局工具管理器工厂
    
    Returns:
        ToolManagerFactory: 工具管理器工厂单例
    """
    global _factory
    if _factory is None:
        _factory = ToolManagerFactory.get_instance()
    return _factory


def init_tool_manager_factory() -> ToolManagerFactory:
    """初始化全局工具管理器工厂
    
    应在应用启动时调用一次。
    
    Returns:
        ToolManagerFactory: 工具管理器工厂实例
    """
    global _factory
    _factory = ToolManagerFactory.get_instance()
    return _factory

