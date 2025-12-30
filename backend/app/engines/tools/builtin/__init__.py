"""
内置工具模块

提供常用的内置工具实现
"""

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

# 导入factory以自动注册工具
from . import factory  # noqa: F401

__all__ = [
    "CalculatorTool",
    "TimeTool",
    "WeatherTool",
    "UnitConverterTool",
    "TextSummarizerTool",
    "RandomGeneratorTool",
    "TavilySearchTool",
    "AmapRegeocodeTool",
    "AmapGeoTool",
    "AmapIPLocationTool",
    "AmapWeatherTool",
    "AmapBicyclingByAddressTool",
    "AmapBicyclingByCoordinatesTool",
    "AmapWalkingByAddressTool",
    "AmapWalkingByCoordinatesTool",
    "AmapDrivingByAddressTool",
    "AmapDrivingByCoordinatesTool",
    "AmapTransitByAddressTool",
    "AmapTransitByCoordinatesTool",
    "AmapDistanceTool",
    "AmapTextSearchTool",
    "AmapAroundSearchTool",
    "AmapSearchDetailTool",
]

