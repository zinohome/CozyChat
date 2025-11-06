"""
天气工具

提供天气查询功能（需要外部API）
"""

# 标准库
from typing import Any, Dict, Optional

# 第三方库
import httpx

# 本地库
from app.config.config import settings
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class WeatherTool(Tool):
    """天气工具
    
    提供天气查询功能，支持通过OpenWeatherMap API查询天气
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化天气工具
        
        Args:
            api_key: OpenWeatherMap API密钥（可选，如果不提供则从配置读取）
        """
        super().__init__(tool_type=ToolType.BUILTIN)
        self.api_key = api_key or getattr(settings, "openweather_api_key", None)
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "weather"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "查询指定城市的天气信息。包括温度、湿度、风速、天气状况等。"
            "适用于需要获取实时天气信息的场景。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "city": {
                "type": "string",
                "description": "城市名称，例如：'Beijing'、'Shanghai'、'New York'",
                "required": True
            },
            "units": {
                "type": "string",
                "description": "温度单位，可选值：'metric'（摄氏度）、'imperial'（华氏度）、'kelvin'（开尔文）。默认为'metric'",
                "required": False
            }
        }
    
    async def execute(
        self,
        city: str,
        units: Optional[str] = None
    ) -> str:
        """执行天气查询
        
        Args:
            city: 城市名称
            units: 温度单位（可选）
            
        Returns:
            str: 天气信息或错误信息
        """
        if not self.api_key:
            error_msg = "错误：未配置OpenWeatherMap API密钥。请在环境变量中设置OPENWEATHER_API_KEY"
            logger.warning(error_msg)
            return error_msg
        
        try:
            units = units or "metric"
            
            # 构建请求参数
            params = {
                "q": city,
                "appid": self.api_key,
                "units": units,
                "lang": "zh_cn"  # 中文描述
            }
            
            # 发送请求
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # 解析响应
            result = self._format_weather_data(data, units)
            
            logger.info(
                f"Weather query executed: {city}",
                extra={"city": city, "units": units}
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                error_msg = f"错误：未找到城市 '{city}' 的天气信息"
            elif e.response.status_code == 401:
                error_msg = "错误：OpenWeatherMap API密钥无效"
            else:
                error_msg = f"错误：天气API请求失败 - HTTP {e.response.status_code}"
            logger.warning(f"Weather tool error: {error_msg}")
            return error_msg
        except httpx.TimeoutException:
            error_msg = "错误：天气API请求超时"
            logger.warning(f"Weather tool error: {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"错误：获取天气信息失败 - {str(e)}"
            logger.error(f"Weather tool error: {error_msg}", exc_info=True)
            return error_msg
    
    def _format_weather_data(self, data: Dict[str, Any], units: str) -> str:
        """格式化天气数据
        
        Args:
            data: API返回的天气数据
            units: 温度单位
            
        Returns:
            str: 格式化后的天气信息
        """
        city_name = data.get("name", "未知城市")
        country = data.get("sys", {}).get("country", "")
        
        # 温度单位符号
        temp_symbol = {
            "metric": "°C",
            "imperial": "°F",
            "kelvin": "K"
        }.get(units, "°C")
        
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        
        # 构建结果字符串
        result_parts = [
            f"📍 {city_name}, {country}",
            f"🌡️ 温度: {main.get('temp', 'N/A')}{temp_symbol}",
            f"🌡️ 体感温度: {main.get('feels_like', 'N/A')}{temp_symbol}",
            f"🌡️ 最高温度: {main.get('temp_max', 'N/A')}{temp_symbol}",
            f"🌡️ 最低温度: {main.get('temp_min', 'N/A')}{temp_symbol}",
            f"💧 湿度: {main.get('humidity', 'N/A')}%",
            f"🌬️ 风速: {wind.get('speed', 'N/A')} m/s",
            f"☁️ 天气: {weather.get('description', 'N/A')}",
        ]
        
        # 添加气压（如果存在）
        if "pressure" in main:
            result_parts.append(f"📊 气压: {main['pressure']} hPa")
        
        return "\n".join(result_parts)

