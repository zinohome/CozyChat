"""
工具注册中心

管理所有可用的工具
"""

# 标准库
from typing import Any, Dict, List, Optional, Type

# 本地库
from app.utils.logger import logger
from .base import Tool


class ToolRegistry:
    """工具注册中心
    
    单例模式，管理所有注册的工具类
    
    Attributes:
        _tools: 工具类字典，key为工具名称，value为工具类
    """
    
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, Type[Tool]] = {}
    
    def __new__(cls) -> "ToolRegistry":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name: str, tool_class: Type[Tool]) -> None:
        """注册工具类
        
        Args:
            name: 工具名称
            tool_class: 工具类
            
        Raises:
            ValueError: 如果工具类不是Tool的子类
        """
        if name in cls._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")
        
        if not issubclass(tool_class, Tool):
            raise ValueError(f"Tool class must be subclass of Tool")
        
        cls._tools[name] = tool_class
        logger.info(f"Registered tool: {name}")
    
    @classmethod
    def get_tool_class(cls, name: str) -> Optional[Type[Tool]]:
        """获取工具类
        
        Args:
            name: 工具名称
            
        Returns:
            Type[Tool]: 工具类，如果不存在返回None
        """
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> List[str]:
        """列出所有注册的工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(cls._tools.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """检查工具是否已注册
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 是否已注册
        """
        return name in cls._tools
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """注销工具
        
        Args:
            name: 工具名称
        """
        if name in cls._tools:
            del cls._tools[name]
            logger.info(f"Unregistered tool: {name}")
        else:
            logger.warning(f"Tool '{name}' not found in registry")
    
    @classmethod
    def get_all_tools_info(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有工具的信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 工具名称到工具信息的映射
        """
        tools_info = {}
        for name, tool_class in cls._tools.items():
            # 创建临时实例以获取工具信息
            try:
                tool_instance = tool_class()
                tools_info[name] = {
                    "name": tool_instance.name,
                    "description": tool_instance.description,
                    "type": tool_instance.tool_type.value,
                    "parameters": tool_instance.parameters
                }
            except Exception as e:
                logger.warning(f"Failed to get info for tool '{name}': {e}")
                tools_info[name] = {
                    "name": name,
                    "description": "Unknown",
                    "type": "unknown",
                    "parameters": {}
                }
        return tools_info

