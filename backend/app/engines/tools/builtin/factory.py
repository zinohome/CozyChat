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
from .unit_converter import UnitConverterTool
from .text_summarizer import TextSummarizerTool
from .random_generator import RandomGeneratorTool
from .tavily_search import TavilySearchTool
from .amap_tools import (
    AmapRegeocodeTool,
    AmapGeoTool,
    AmapIPLocationTool,
    AmapWeatherTool,
    AmapBicyclingByAddressTool,
    AmapBicyclingByCoordinatesTool,
    AmapWalkingByAddressTool,
    AmapWalkingByCoordinatesTool,
    AmapDrivingByAddressTool,
    AmapDrivingByCoordinatesTool,
    AmapTransitByAddressTool,
    AmapTransitByCoordinatesTool,
    AmapDistanceTool,
    AmapTextSearchTool,
    AmapAroundSearchTool,
    AmapSearchDetailTool,
)


# 注册内置工具（工具类从代码注册，但配置从YAML加载）
ToolRegistry.register("calculator", CalculatorTool)
ToolRegistry.register("time", TimeTool)
ToolRegistry.register("weather", WeatherTool)
ToolRegistry.register("unit_converter", UnitConverterTool)
ToolRegistry.register("text_summarizer", TextSummarizerTool)
ToolRegistry.register("random_generator", RandomGeneratorTool)
ToolRegistry.register("tavily_search", TavilySearchTool)

# 注册高德地图工具
ToolRegistry.register("amap_regeocode", AmapRegeocodeTool)
ToolRegistry.register("amap_geo", AmapGeoTool)
ToolRegistry.register("amap_ip_location", AmapIPLocationTool)
ToolRegistry.register("amap_weather", AmapWeatherTool)
ToolRegistry.register("amap_bicycling_by_address", AmapBicyclingByAddressTool)
ToolRegistry.register("amap_bicycling_by_coordinates", AmapBicyclingByCoordinatesTool)
ToolRegistry.register("amap_walking_by_address", AmapWalkingByAddressTool)
ToolRegistry.register("amap_walking_by_coordinates", AmapWalkingByCoordinatesTool)
ToolRegistry.register("amap_driving_by_address", AmapDrivingByAddressTool)
ToolRegistry.register("amap_driving_by_coordinates", AmapDrivingByCoordinatesTool)
ToolRegistry.register("amap_transit_by_address", AmapTransitByAddressTool)
ToolRegistry.register("amap_transit_by_coordinates", AmapTransitByCoordinatesTool)
ToolRegistry.register("amap_distance", AmapDistanceTool)
ToolRegistry.register("amap_text_search", AmapTextSearchTool)
ToolRegistry.register("amap_around_search", AmapAroundSearchTool)
ToolRegistry.register("amap_search_detail", AmapSearchDetailTool)


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
    elif tool_name == "tavily_search":
        # Tavily搜索工具需要API密钥
        if "api_key" not in kwargs:
            kwargs["api_key"] = settings.tavily_api_key
    elif tool_name.startswith("amap_"):
        # 高德地图工具需要API密钥
        if "api_key" not in kwargs:
            kwargs["api_key"] = settings.amap_maps_api_key
    
    try:
        return tool_class(**kwargs)
    except Exception:
        return None

