"""
工具基类

定义所有工具的统一接口
"""

# 标准库
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

# 本地库
from app.utils.logger import logger


class ToolType(str, Enum):
    """工具类型枚举"""
    BUILTIN = "builtin"  # 内置工具
    MCP = "mcp"          # MCP工具


class Tool(ABC):
    """工具基类
    
    所有工具实现必须继承此类并实现抽象方法
    
    Attributes:
        tool_type: 工具类型（内置或MCP）
        name: 工具名称
        description: 工具描述
        parameters: 工具参数schema
    """
    
    def __init__(self, tool_type: ToolType = ToolType.BUILTIN):
        """初始化工具
        
        Args:
            tool_type: 工具类型
        """
        self.tool_type = tool_type
        logger.debug(
            f"Initializing tool: {self.name}",
            extra={"tool_name": self.name, "tool_type": tool_type.value}
        )
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称
        
        Returns:
            str: 工具名称（唯一标识）
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述
        
        Returns:
            str: 工具描述（用于AI理解工具用途）
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema
        
        返回符合JSON Schema格式的参数定义
        
        Returns:
            Dict[str, Any]: 参数schema，格式如下：
            {
                "param_name": {
                    "type": "string",
                    "description": "参数描述",
                    "required": True/False,
                    "default": 默认值（可选）
                }
            }
        """
        raise NotImplementedError
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 工具执行结果
            
        Raises:
            ValueError: 如果参数无效
            Exception: 工具执行失败时抛出
        """
        raise NotImplementedError
    
    def to_openai_function(self) -> Dict[str, Any]:
        """转换为OpenAI function calling格式
        
        Returns:
            Dict[str, Any]: OpenAI function格式的工具定义
        """
        # 提取必需参数
        required_params = self._get_required_params()
        
        # 构建参数schema
        properties = {}
        for param_name, param_schema in self.parameters.items():
            # 复制schema，移除required字段（OpenAI格式中required是顶级字段）
            prop = {k: v for k, v in param_schema.items() if k != "required"}
            properties[param_name] = prop
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_params
                }
            }
        }
    
    def _get_required_params(self) -> List[str]:
        """获取必需参数列表
        
        Returns:
            List[str]: 必需参数名称列表
        """
        return [
            name for name, schema in self.parameters.items()
            if schema.get("required", False)
        ]
    
    def validate_parameters(self, **kwargs: Any) -> None:
        """验证工具参数
        
        Args:
            **kwargs: 待验证的参数
            
        Raises:
            ValueError: 如果参数验证失败
        """
        # 检查必需参数
        required_params = self._get_required_params()
        missing_params = [p for p in required_params if p not in kwargs]
        if missing_params:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )
        
        # 检查参数类型（简单验证）
        for param_name, param_value in kwargs.items():
            if param_name not in self.parameters:
                logger.warning(
                    f"Unknown parameter '{param_name}' for tool '{self.name}'"
                )
                continue
            
            param_schema = self.parameters[param_name]
            expected_type = param_schema.get("type")
            
            if expected_type:
                # 简单的类型检查
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict
                }
                
                expected_python_type = type_map.get(expected_type)
                if expected_python_type and not isinstance(param_value, expected_python_type):
                    raise ValueError(
                        f"Parameter '{param_name}' must be of type {expected_type}, "
                        f"got {type(param_value).__name__}"
                    )

