"""
内置工具工厂

创建和注册内置工具
"""

# 本地库
from app.config.config import settings
from app.engines.tools.registry import ToolRegistry
from .calculator import CalculatorTool
from .time_tool import TimeTool
from .weather_tool import WeatherTool


# 注册内置工具
ToolRegistry.register("calculator", CalculatorTool)
ToolRegistry.register("time", TimeTool)
ToolRegistry.register("weather", WeatherTool)


def create_builtin_tool(tool_name: str, **kwargs):
    """创建内置工具实例
    
    Args:
        tool_name: 工具名称
        **kwargs: 工具初始化参数
        
    Returns:
        Tool: 工具实例，如果不存在返回None
    """
    tool_class = ToolRegistry.get_tool_class(tool_name)
    if tool_class is None:
        return None
    
    # 根据工具类型设置默认参数
    if tool_name == "weather":
        # WeatherTool需要API密钥
        if "api_key" not in kwargs:
            kwargs["api_key"] = settings.openweather_api_key
    
    try:
        return tool_class(**kwargs)
    except Exception:
        return None

