"""
内置工具工厂

创建和注册内置工具（从YAML配置加载）
"""

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from app.utils.config_loader import get_config_loader
from app.engines.tools.registry import ToolRegistry
from .calculator import CalculatorTool
from .time_tool import TimeTool
from .weather_tool import WeatherTool


# 注册内置工具（工具类从代码注册，但配置从YAML加载）
ToolRegistry.register("calculator", CalculatorTool)
ToolRegistry.register("time", TimeTool)
ToolRegistry.register("weather", WeatherTool)


def register_builtin_tools():
    """从YAML配置注册内置工具
    
    从config/tools/builtin.yaml加载工具配置
    """
    try:
        config_loader = get_config_loader()
        tool_config = config_loader.load_tool_config()
        builtin_tools = tool_config.get("builtin", [])
        
        # 工具已经在代码中注册，这里只是验证配置
        registered_tools = ToolRegistry.list_tools()
        for tool_def in builtin_tools:
            tool_name = tool_def.get("name")
            if tool_name and tool_name not in registered_tools:
                logger.warning(
                    f"Tool '{tool_name}' defined in YAML but not registered in code",
                    extra={"tool_name": tool_name}
                )
        
        logger.info(
            f"Loaded {len(builtin_tools)} builtin tools from YAML config",
            extra={"tools": [t.get("name") for t in builtin_tools]}
        )
        
    except Exception as e:
        logger.warning(
            f"Failed to load builtin tools config from YAML: {e}",
            exc_info=False
        )


# 自动注册（导入时执行）
register_builtin_tools()


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

