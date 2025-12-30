"""
高德地图工具

提供高德地图API的各种功能，包括地理编码、路线规划、POI搜索等
"""

# 标准库
import json
from typing import Any, Dict, Optional

# 第三方库
import httpx

# 本地库
from app.config.config import settings
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class AmapBaseTool(Tool):
    """高德地图工具基类
    
    提供通用的API调用和错误处理
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化高德地图工具
        
        Args:
            api_key: 高德地图API密钥（可选，如果不提供则从配置读取）
        """
        super().__init__(tool_type=ToolType.BUILTIN)
        self.api_key = api_key or getattr(settings, "amap_maps_api_key", None)
        if not self.api_key:
            logger.warning("AMAP_MAPS_API_KEY not configured")
    
    def _make_request(
        self,
        url: str,
        params: Dict[str, Any],
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """发送HTTP请求
        
        Args:
            url: 请求URL
            params: 请求参数
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: API响应数据
        """
        if not self.api_key:
            raise ValueError("AMAP_MAPS_API_KEY not configured")
        
        params["key"] = self.api_key
        
        try:
            response = httpx.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Amap API HTTP error: {e}")
            raise
        except httpx.TimeoutException:
            logger.error("Amap API request timeout")
            raise
        except Exception as e:
            logger.error(f"Amap API request failed: {e}")
            raise
    
    def _format_error(self, data: Dict[str, Any]) -> str:
        """格式化错误信息
        
        Args:
            data: API响应数据
            
        Returns:
            str: 错误信息
        """
        error_msg = data.get("info") or data.get("infocode") or "Unknown error"
        return f"错误：{error_msg}"
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """格式化结果
        
        Args:
            result: 结果字典
            
        Returns:
            str: 格式化后的结果字符串
        """
        return json.dumps(result, ensure_ascii=False, indent=2)


class AmapRegeocodeTool(AmapBaseTool):
    """逆地理编码工具
    
    将高德经纬度坐标转换为行政区划地址信息
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_regeocode"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "将一个高德经纬度坐标转换为行政区划地址信息。"
            "输入格式：经度,纬度（例如：116.434307,39.90909）。"
            "返回省、市、区信息。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "location": {
                "type": "string",
                "description": "经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            }
        }
    
    async def execute(self, location: str) -> str:
        """执行逆地理编码
        
        Args:
            location: 经纬度坐标
            
        Returns:
            str: 地址信息或错误信息
        """
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/geocode/regeo",
                {"location": location}
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            result = {
                "province": data["regeocode"]["addressComponent"]["province"],
                "city": data["regeocode"]["addressComponent"]["city"],
                "district": data["regeocode"]["addressComponent"]["district"]
            }
            
            logger.info(f"Amap regeocode executed: {location}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：逆地理编码失败 - {str(e)}"
            logger.error(f"Amap regeocode error: {error_msg}", exc_info=True)
            return error_msg


class AmapGeoTool(AmapBaseTool):
    """地理编码工具
    
    将详细的结构化地址转换为经纬度坐标
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_geo"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "将详细的结构化地址转换为经纬度坐标。"
            "支持对地标性名胜景区、建筑物名称解析为经纬度坐标。"
            "可以指定城市名称以提高准确性。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "address": {
                "type": "string",
                "description": "结构化地址，例如：'北京市朝阳区阜通东大街6号'",
                "required": True
            },
            "city": {
                "type": "string",
                "description": "城市名称（可选），用于提高地理编码准确性",
                "required": False
            }
        }
    
    async def execute(self, address: str, city: Optional[str] = None) -> str:
        """执行地理编码
        
        Args:
            address: 结构化地址
            city: 城市名称（可选）
            
        Returns:
            str: 坐标信息或错误信息
        """
        try:
            params = {"address": address}
            if city:
                params["city"] = city
            
            data = self._make_request(
                "https://restapi.amap.com/v3/geocode/geo",
                params
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            geocodes = data.get("geocodes", [])
            results = []
            for geo in geocodes:
                results.append({
                    "country": geo.get("country"),
                    "province": geo.get("province"),
                    "city": geo.get("city"),
                    "citycode": geo.get("citycode"),
                    "district": geo.get("district"),
                    "street": geo.get("street"),
                    "number": geo.get("number"),
                    "adcode": geo.get("adcode"),
                    "location": geo.get("location"),
                    "level": geo.get("level")
                })
            
            logger.info(f"Amap geo executed: {address}")
            return self._format_result({"return": results})
            
        except Exception as e:
            error_msg = f"错误：地理编码失败 - {str(e)}"
            logger.error(f"Amap geo error: {error_msg}", exc_info=True)
            return error_msg


class AmapIPLocationTool(AmapBaseTool):
    """IP定位工具
    
    根据IP地址定位所在位置
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_ip_location"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "IP定位根据用户输入的IP地址，定位IP的所在位置。"
            "返回省份、城市、行政区划代码等信息。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "ip": {
                "type": "string",
                "description": "IP地址",
                "required": True
            }
        }
    
    async def execute(self, ip: str) -> str:
        """执行IP定位
        
        Args:
            ip: IP地址
            
        Returns:
            str: 位置信息或错误信息
        """
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/ip",
                {"ip": ip}
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            result = {
                "province": data.get("province"),
                "city": data.get("city"),
                "adcode": data.get("adcode"),
                "rectangle": data.get("rectangle")
            }
            
            logger.info(f"Amap IP location executed: {ip}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：IP定位失败 - {str(e)}"
            logger.error(f"Amap IP location error: {error_msg}", exc_info=True)
            return error_msg


class AmapWeatherTool(AmapBaseTool):
    """高德天气工具
    
    根据城市名称或adcode查询天气
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_weather"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "根据城市名称或者标准adcode查询指定城市的天气。"
            "返回城市天气信息和预报数据。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "city": {
                "type": "string",
                "description": "城市名称或者adcode",
                "required": True
            }
        }
    
    async def execute(self, city: str) -> str:
        """执行天气查询
        
        Args:
            city: 城市名称或adcode
            
        Returns:
            str: 天气信息或错误信息
        """
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/weather/weatherInfo",
                {
                    "city": city,
                    "extensions": "all"
                }
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            forecasts = data.get("forecasts", [])
            if not forecasts:
                return "错误：没有可用的预报数据"
            
            result = {
                "city": forecasts[0]["city"],
                "forecasts": forecasts[0]["casts"]
            }
            
            logger.info(f"Amap weather executed: {city}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：获取天气失败 - {str(e)}"
            logger.error(f"Amap weather error: {error_msg}", exc_info=True)
            return error_msg


class AmapBicyclingByAddressTool(AmapBaseTool):
    """骑行路线规划工具（地址版）
    
    使用地址进行骑行路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_bicycling_by_address"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "骑行路径规划（地址版），使用地址进行骑行路线规划，推荐优先使用此工具。"
            "规划时会考虑天桥、单行线、封路等情况。最大支持500km的骑行路线规划。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin_address": {
                "type": "string",
                "description": "起点地址，例如：'北京市朝阳区阜通东大街6号'",
                "required": True
            },
            "destination_address": {
                "type": "string",
                "description": "终点地址，例如：'北京市海淀区上地十街10号'",
                "required": True
            },
            "origin_city": {
                "type": "string",
                "description": "起点所在城市（可选），用于提高地理编码准确性",
                "required": False
            },
            "destination_city": {
                "type": "string",
                "description": "终点所在城市（可选），用于提高地理编码准确性",
                "required": False
            }
        }
    
    async def execute(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None
    ) -> str:
        """执行骑行路线规划
        
        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点所在城市（可选）
            destination_city: 终点所在城市（可选）
            
        Returns:
            str: 路线信息或错误信息
        """
        try:
            # 先进行地理编码获取坐标
            geo_tool = AmapGeoTool(self.api_key)
            
            # 获取起点坐标
            origin_result = await geo_tool.execute(origin_address, origin_city)
            origin_data = json.loads(origin_result)
            if "错误" in origin_result or "error" in origin_data:
                return f"错误：起点地址地理编码失败 - {origin_result}"
            
            origin_location = origin_data.get("return", [{}])[0].get("location")
            if not origin_location:
                return "错误：无法从起点地址获取坐标"
            
            # 获取终点坐标
            destination_result = await geo_tool.execute(destination_address, destination_city)
            destination_data = json.loads(destination_result)
            if "错误" in destination_result or "error" in destination_data:
                return f"错误：终点地址地理编码失败 - {destination_result}"
            
            destination_location = destination_data.get("return", [{}])[0].get("location")
            if not destination_location:
                return "错误：无法从终点地址获取坐标"
            
            # 使用坐标进行路线规划
            bicycling_tool = AmapBicyclingByCoordinatesTool(self.api_key)
            route_result = await bicycling_tool.execute(origin_location, destination_location)
            
            # 添加地址信息
            route_data = json.loads(route_result)
            if "错误" not in route_result and "error" not in route_data:
                route_data["addresses"] = {
                    "origin": {
                        "address": origin_address,
                        "coordinates": origin_location
                    },
                    "destination": {
                        "address": destination_address,
                        "coordinates": destination_location
                    }
                }
                return self._format_result(route_data)
            
            return route_result
            
        except Exception as e:
            error_msg = f"错误：骑行路线规划失败 - {str(e)}"
            logger.error(f"Amap bicycling by address error: {error_msg}", exc_info=True)
            return error_msg


class AmapBicyclingByCoordinatesTool(AmapBaseTool):
    """骑行路线规划工具（坐标版）
    
    使用坐标进行骑行路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_bicycling_by_coordinates"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "骑行路径规划，根据起点终点经纬度坐标规划骑行通勤方案。"
            "规划时会考虑天桥、单行线、封路等情况。最大支持500km的骑行路线规划。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin": {
                "type": "string",
                "description": "起点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "destination": {
                "type": "string",
                "description": "终点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            }
        }
    
    async def execute(self, origin: str, destination: str) -> str:
        """执行骑行路线规划
        
        Args:
            origin: 起点坐标
            destination: 终点坐标
            
        Returns:
            str: 路线信息或错误信息
        """
        try:
            data = self._make_request(
                "https://restapi.amap.com/v4/direction/bicycling",
                {
                    "origin": origin,
                    "destination": destination
                }
            )
            
            if data.get("errcode") != 0:
                return self._format_error(data)
            
            paths = []
            for path in data["data"]["paths"]:
                steps = []
                for step in path["steps"]:
                    steps.append({
                        "instruction": step.get("instruction"),
                        "road": step.get("road"),
                        "distance": step.get("distance"),
                        "orientation": step.get("orientation"),
                        "duration": step.get("duration")
                    })
                paths.append({
                    "distance": path.get("distance"),
                    "duration": path.get("duration"),
                    "steps": steps
                })
            
            result = {
                "data": {
                    "origin": data["data"]["origin"],
                    "destination": data["data"]["destination"],
                    "paths": paths
                }
            }
            
            logger.info(f"Amap bicycling by coordinates executed: {origin} -> {destination}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：骑行路线规划失败 - {str(e)}"
            logger.error(f"Amap bicycling by coordinates error: {error_msg}", exc_info=True)
            return error_msg


class AmapWalkingByAddressTool(AmapBaseTool):
    """步行路线规划工具（地址版）
    
    使用地址进行步行路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_walking_by_address"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "步行路径规划（地址版），使用地址进行步行路线规划，推荐优先使用此工具。"
            "支持100km以内的步行通勤方案规划。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin_address": {
                "type": "string",
                "description": "起点地址，例如：'北京市朝阳区阜通东大街6号'",
                "required": True
            },
            "destination_address": {
                "type": "string",
                "description": "终点地址，例如：'北京市海淀区上地十街10号'",
                "required": True
            },
            "origin_city": {
                "type": "string",
                "description": "起点所在城市（可选），用于提高地理编码准确性",
                "required": False
            },
            "destination_city": {
                "type": "string",
                "description": "终点所在城市（可选），用于提高地理编码准确性",
                "required": False
            }
        }
    
    async def execute(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None
    ) -> str:
        """执行步行路线规划"""
        try:
            geo_tool = AmapGeoTool(self.api_key)
            
            # 获取起点坐标
            origin_result = await geo_tool.execute(origin_address, origin_city)
            origin_data = json.loads(origin_result)
            if "错误" in origin_result or "error" in origin_data:
                return f"错误：起点地址地理编码失败 - {origin_result}"
            
            origin_location = origin_data.get("return", [{}])[0].get("location")
            if not origin_location:
                return "错误：无法从起点地址获取坐标"
            
            # 获取终点坐标
            destination_result = await geo_tool.execute(destination_address, destination_city)
            destination_data = json.loads(destination_result)
            if "错误" in destination_result or "error" in destination_data:
                return f"错误：终点地址地理编码失败 - {destination_result}"
            
            destination_location = destination_data.get("return", [{}])[0].get("location")
            if not destination_location:
                return "错误：无法从终点地址获取坐标"
            
            # 使用坐标进行路线规划
            walking_tool = AmapWalkingByCoordinatesTool(self.api_key)
            route_result = await walking_tool.execute(origin_location, destination_location)
            
            # 添加地址信息
            route_data = json.loads(route_result)
            if "错误" not in route_result and "error" not in route_data:
                route_data["addresses"] = {
                    "origin": {
                        "address": origin_address,
                        "coordinates": origin_location
                    },
                    "destination": {
                        "address": destination_address,
                        "coordinates": destination_location
                    }
                }
                return self._format_result(route_data)
            
            return route_result
            
        except Exception as e:
            error_msg = f"错误：步行路线规划失败 - {str(e)}"
            logger.error(f"Amap walking by address error: {error_msg}", exc_info=True)
            return error_msg


class AmapWalkingByCoordinatesTool(AmapBaseTool):
    """步行路线规划工具（坐标版）
    
    使用坐标进行步行路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_walking_by_coordinates"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "步行路径规划，根据起点终点经纬度坐标规划100km以内的步行通勤方案。"
            "返回包含距离、时长和详细导航信息的路线数据。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin": {
                "type": "string",
                "description": "起点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "destination": {
                "type": "string",
                "description": "终点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            }
        }
    
    async def execute(self, origin: str, destination: str) -> str:
        """执行步行路线规划"""
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/direction/walking",
                {
                    "origin": origin,
                    "destination": destination
                }
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            paths = []
            for path in data["route"]["paths"]:
                steps = []
                for step in path["steps"]:
                    steps.append({
                        "instruction": step.get("instruction"),
                        "road": step.get("road"),
                        "distance": step.get("distance"),
                        "orientation": step.get("orientation"),
                        "duration": step.get("duration")
                    })
                paths.append({
                    "distance": path.get("distance"),
                    "duration": path.get("duration"),
                    "steps": steps
                })
            
            result = {
                "route": {
                    "origin": data["route"]["origin"],
                    "destination": data["route"]["destination"],
                    "paths": paths
                }
            }
            
            logger.info(f"Amap walking by coordinates executed: {origin} -> {destination}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：步行路线规划失败 - {str(e)}"
            logger.error(f"Amap walking by coordinates error: {error_msg}", exc_info=True)
            return error_msg


class AmapDrivingByAddressTool(AmapBaseTool):
    """驾车路线规划工具（地址版）
    
    使用地址进行驾车路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_driving_by_address"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "驾车路径规划（地址版），使用地址进行驾车路线规划，推荐优先使用此工具。"
            "规划时会考虑交通状况和道路限制。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin_address": {
                "type": "string",
                "description": "起点地址，例如：'北京市朝阳区阜通东大街6号'",
                "required": True
            },
            "destination_address": {
                "type": "string",
                "description": "终点地址，例如：'北京市海淀区上地十街10号'",
                "required": True
            },
            "origin_city": {
                "type": "string",
                "description": "起点所在城市（可选），用于提高地理编码准确性",
                "required": False
            },
            "destination_city": {
                "type": "string",
                "description": "终点所在城市（可选），用于提高地理编码准确性",
                "required": False
            }
        }
    
    async def execute(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None
    ) -> str:
        """执行驾车路线规划"""
        try:
            geo_tool = AmapGeoTool(self.api_key)
            
            # 获取起点坐标
            origin_result = await geo_tool.execute(origin_address, origin_city)
            origin_data = json.loads(origin_result)
            if "错误" in origin_result or "error" in origin_data:
                return f"错误：起点地址地理编码失败 - {origin_result}"
            
            origin_location = origin_data.get("return", [{}])[0].get("location")
            if not origin_location:
                return "错误：无法从起点地址获取坐标"
            
            # 获取终点坐标
            destination_result = await geo_tool.execute(destination_address, destination_city)
            destination_data = json.loads(destination_result)
            if "错误" in destination_result or "error" in destination_data:
                return f"错误：终点地址地理编码失败 - {destination_result}"
            
            destination_location = destination_data.get("return", [{}])[0].get("location")
            if not destination_location:
                return "错误：无法从终点地址获取坐标"
            
            # 使用坐标进行路线规划
            driving_tool = AmapDrivingByCoordinatesTool(self.api_key)
            route_result = await driving_tool.execute(origin_location, destination_location)
            
            # 添加地址信息
            route_data = json.loads(route_result)
            if "错误" not in route_result and "error" not in route_data:
                route_data["addresses"] = {
                    "origin": {
                        "address": origin_address,
                        "coordinates": origin_location
                    },
                    "destination": {
                        "address": destination_address,
                        "coordinates": destination_location
                    }
                }
                return self._format_result(route_data)
            
            return route_result
            
        except Exception as e:
            error_msg = f"错误：驾车路线规划失败 - {str(e)}"
            logger.error(f"Amap driving by address error: {error_msg}", exc_info=True)
            return error_msg


class AmapDrivingByCoordinatesTool(AmapBaseTool):
    """驾车路线规划工具（坐标版）
    
    使用坐标进行驾车路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_driving_by_coordinates"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "驾车路径规划，根据起点终点经纬度坐标规划以小客车、轿车通勤出行的方案。"
            "返回包含距离、时长和详细导航信息的路线数据。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin": {
                "type": "string",
                "description": "起点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "destination": {
                "type": "string",
                "description": "终点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            }
        }
    
    async def execute(self, origin: str, destination: str) -> str:
        """执行驾车路线规划"""
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/direction/driving",
                {
                    "origin": origin,
                    "destination": destination
                }
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            paths = []
            for path in data["route"]["paths"]:
                steps = []
                for step in path["steps"]:
                    steps.append({
                        "instruction": step.get("instruction"),
                        "road": step.get("road"),
                        "distance": step.get("distance"),
                        "orientation": step.get("orientation"),
                        "duration": step.get("duration")
                    })
                paths.append({
                    "path": path.get("path"),
                    "distance": path.get("distance"),
                    "duration": path.get("duration"),
                    "steps": steps
                })
            
            result = {
                "route": {
                    "origin": data["route"]["origin"],
                    "destination": data["route"]["destination"],
                    "paths": paths
                }
            }
            
            logger.info(f"Amap driving by coordinates executed: {origin} -> {destination}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：驾车路线规划失败 - {str(e)}"
            logger.error(f"Amap driving by coordinates error: {error_msg}", exc_info=True)
            return error_msg


class AmapTransitByAddressTool(AmapBaseTool):
    """公共交通路线规划工具（地址版）
    
    使用地址进行公共交通路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_transit_by_address"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "公共交通路径规划（地址版），使用地址进行公共交通路线规划，推荐优先使用此工具。"
            "支持综合各类公共（火车、公交、地铁）交通方式的通勤方案。"
            "跨城场景下必须提供起点和终点城市。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin_address": {
                "type": "string",
                "description": "起点地址，例如：'北京市朝阳区阜通东大街6号'",
                "required": True
            },
            "destination_address": {
                "type": "string",
                "description": "终点地址，例如：'北京市海淀区上地十街10号'",
                "required": True
            },
            "origin_city": {
                "type": "string",
                "description": "起点所在城市（跨城交通必需）",
                "required": True
            },
            "destination_city": {
                "type": "string",
                "description": "终点所在城市（跨城交通必需）",
                "required": True
            }
        }
    
    async def execute(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: str,
        destination_city: str
    ) -> str:
        """执行公共交通路线规划"""
        try:
            geo_tool = AmapGeoTool(self.api_key)
            
            # 获取起点坐标
            origin_result = await geo_tool.execute(origin_address, origin_city)
            origin_data = json.loads(origin_result)
            if "错误" in origin_result or "error" in origin_data:
                return f"错误：起点地址地理编码失败 - {origin_result}"
            
            origin_location = origin_data.get("return", [{}])[0].get("location")
            if not origin_location:
                return "错误：无法从起点地址获取坐标"
            
            # 获取终点坐标
            destination_result = await geo_tool.execute(destination_address, destination_city)
            destination_data = json.loads(destination_result)
            if "错误" in destination_result or "error" in destination_data:
                return f"错误：终点地址地理编码失败 - {destination_result}"
            
            destination_location = destination_data.get("return", [{}])[0].get("location")
            if not destination_location:
                return "错误：无法从终点地址获取坐标"
            
            # 使用坐标进行路线规划
            transit_tool = AmapTransitByCoordinatesTool(self.api_key)
            route_result = await transit_tool.execute(
                origin_location,
                destination_location,
                origin_city,
                destination_city
            )
            
            # 添加地址信息
            route_data = json.loads(route_result)
            if "错误" not in route_result and "error" not in route_data:
                route_data["addresses"] = {
                    "origin": {
                        "address": origin_address,
                        "coordinates": origin_location
                    },
                    "destination": {
                        "address": destination_address,
                        "coordinates": destination_location
                    }
                }
                return self._format_result(route_data)
            
            return route_result
            
        except Exception as e:
            error_msg = f"错误：公共交通路线规划失败 - {str(e)}"
            logger.error(f"Amap transit by address error: {error_msg}", exc_info=True)
            return error_msg


class AmapTransitByCoordinatesTool(AmapBaseTool):
    """公共交通路线规划工具（坐标版）
    
    使用坐标进行公共交通路线规划
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_transit_by_coordinates"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "根据起点终点经纬度坐标规划综合各类公共（火车、公交、地铁）交通方式的通勤方案。"
            "跨城场景下必须传起点城市与终点城市。"
            "返回包含距离、时长和详细公共交通信息的路线数据。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origin": {
                "type": "string",
                "description": "起点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "destination": {
                "type": "string",
                "description": "终点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "city": {
                "type": "string",
                "description": "起点城市名称",
                "required": True
            },
            "cityd": {
                "type": "string",
                "description": "终点城市名称",
                "required": True
            }
        }
    
    async def execute(
        self,
        origin: str,
        destination: str,
        city: str,
        cityd: str
    ) -> str:
        """执行公共交通路线规划"""
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/direction/transit/integrated",
                {
                    "origin": origin,
                    "destination": destination,
                    "city": city,
                    "cityd": cityd
                }
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            transits = []
            if data["route"].get("transits"):
                for transit in data["route"]["transits"]:
                    segments = []
                    if transit.get("segments"):
                        for segment in transit["segments"]:
                            walking_steps = []
                            if segment.get("walking", {}).get("steps"):
                                for step in segment["walking"]["steps"]:
                                    walking_steps.append({
                                        "instruction": step.get("instruction"),
                                        "road": step.get("road"),
                                        "distance": step.get("distance"),
                                        "action": step.get("action"),
                                        "assistant_action": step.get("assistant_action")
                                    })
                            
                            buslines = []
                            if segment.get("bus", {}).get("buslines"):
                                for busline in segment["bus"]["buslines"]:
                                    via_stops = []
                                    if busline.get("via_stops"):
                                        for stop in busline["via_stops"]:
                                            via_stops.append({"name": stop.get("name")})
                                    
                                    buslines.append({
                                        "name": busline.get("name"),
                                        "departure_stop": {"name": busline.get("departure_stop", {}).get("name")},
                                        "arrival_stop": {"name": busline.get("arrival_stop", {}).get("name")},
                                        "distance": busline.get("distance"),
                                        "duration": busline.get("duration"),
                                        "via_stops": via_stops
                                    })
                            
                            segments.append({
                                "walking": {
                                    "origin": segment.get("walking", {}).get("origin"),
                                    "destination": segment.get("walking", {}).get("destination"),
                                    "distance": segment.get("walking", {}).get("distance"),
                                    "duration": segment.get("walking", {}).get("duration"),
                                    "steps": walking_steps
                                },
                                "bus": {"buslines": buslines},
                                "entrance": {"name": segment.get("entrance", {}).get("name")},
                                "exit": {"name": segment.get("exit", {}).get("name")},
                                "railway": {
                                    "name": segment.get("railway", {}).get("name"),
                                    "trip": segment.get("railway", {}).get("trip")
                                }
                            })
                    
                    transits.append({
                        "duration": transit.get("duration"),
                        "walking_distance": transit.get("walking_distance"),
                        "segments": segments
                    })
            
            result = {
                "route": {
                    "origin": data["route"]["origin"],
                    "destination": data["route"]["destination"],
                    "distance": data["route"].get("distance"),
                    "transits": transits
                }
            }
            
            logger.info(f"Amap transit by coordinates executed: {origin} -> {destination}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：公共交通路线规划失败 - {str(e)}"
            logger.error(f"Amap transit by coordinates error: {error_msg}", exc_info=True)
            return error_msg


class AmapDistanceTool(AmapBaseTool):
    """距离测量工具
    
    测量两个经纬度坐标之间的距离
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_distance"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "测量两个经纬度坐标之间的距离，支持驾车、步行以及球面距离测量。"
            "type参数：1=直线距离，2=驾车距离，3=步行距离。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "origins": {
                "type": "string",
                "description": "起点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "destination": {
                "type": "string",
                "description": "终点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "type": {
                "type": "string",
                "description": "测量类型，可选值：'1'（直线距离，默认）、'2'（驾车距离）、'3'（步行距离）",
                "required": False
            }
        }
    
    async def execute(
        self,
        origins: str,
        destination: str,
        type: str = "1"
    ) -> str:
        """执行距离测量"""
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/distance",
                {
                    "origins": origins,
                    "destination": destination,
                    "type": type
                }
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            results = []
            for result in data["results"]:
                results.append({
                    "origin_id": result.get("origin_id"),
                    "dest_id": result.get("dest_id"),
                    "distance": result.get("distance"),
                    "duration": result.get("duration")
                })
            
            logger.info(f"Amap distance executed: {origins} -> {destination}, type={type}")
            return self._format_result({"results": results})
            
        except Exception as e:
            error_msg = f"错误：距离测量失败 - {str(e)}"
            logger.error(f"Amap distance error: {error_msg}", exc_info=True)
            return error_msg


class AmapTextSearchTool(AmapBaseTool):
    """POI关键词搜索工具
    
    根据关键词搜索POI
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_text_search"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "关键词搜索API，根据用户输入的关键字进行POI搜索，并返回相关的信息。"
            "可以指定城市和是否限制城市范围内搜索。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "keywords": {
                "type": "string",
                "description": "搜索关键词",
                "required": True
            },
            "city": {
                "type": "string",
                "description": "查询城市（可选）",
                "required": False
            },
            "citylimit": {
                "type": "string",
                "description": "是否限制城市范围内搜索，可选值：'true'（限制）、'false'（不限制，默认）",
                "required": False
            }
        }
    
    async def execute(
        self,
        keywords: str,
        city: str = "",
        citylimit: str = "false"
    ) -> str:
        """执行POI关键词搜索"""
        try:
            params = {
                "keywords": keywords,
                "citylimit": citylimit
            }
            if city:
                params["city"] = city
            
            data = self._make_request(
                "https://restapi.amap.com/v3/place/text",
                params
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            suggestion_cities = []
            if data.get("suggestion", {}).get("cities"):
                for city_item in data["suggestion"]["cities"]:
                    suggestion_cities.append({"name": city_item.get("name")})
            
            pois = []
            for poi in data.get("pois", []):
                pois.append({
                    "id": poi.get("id"),
                    "name": poi.get("name"),
                    "address": poi.get("address"),
                    "typecode": poi.get("typecode")
                })
            
            result = {
                "suggestion": {
                    "keywords": data.get("suggestion", {}).get("keywords"),
                    "cities": suggestion_cities
                },
                "pois": pois
            }
            
            logger.info(f"Amap text search executed: keywords={keywords}, city={city}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：POI关键词搜索失败 - {str(e)}"
            logger.error(f"Amap text search error: {error_msg}", exc_info=True)
            return error_msg


class AmapAroundSearchTool(AmapBaseTool):
    """POI周边搜索工具
    
    根据坐标和半径搜索周边POI
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_around_search"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "周边搜索，根据用户传入关键词以及坐标location，搜索出radius半径范围的POI。"
            "可以指定搜索关键词和搜索半径（单位：米）。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "location": {
                "type": "string",
                "description": "中心点经纬度坐标，格式为'经度,纬度'（例如：'116.434307,39.90909'）",
                "required": True
            },
            "radius": {
                "type": "string",
                "description": "搜索半径（单位：米），默认1000",
                "required": False
            },
            "keywords": {
                "type": "string",
                "description": "搜索关键词（可选）",
                "required": False
            }
        }
    
    async def execute(
        self,
        location: str,
        radius: str = "1000",
        keywords: str = ""
    ) -> str:
        """执行POI周边搜索"""
        try:
            params = {
                "location": location,
                "radius": radius
            }
            if keywords:
                params["keywords"] = keywords
            
            data = self._make_request(
                "https://restapi.amap.com/v3/place/around",
                params
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            pois = []
            for poi in data.get("pois", []):
                pois.append({
                    "id": poi.get("id"),
                    "name": poi.get("name"),
                    "address": poi.get("address"),
                    "typecode": poi.get("typecode")
                })
            
            logger.info(f"Amap around search executed: location={location}, radius={radius}, keywords={keywords}")
            return self._format_result({"pois": pois})
            
        except Exception as e:
            error_msg = f"错误：POI周边搜索失败 - {str(e)}"
            logger.error(f"Amap around search error: {error_msg}", exc_info=True)
            return error_msg


class AmapSearchDetailTool(AmapBaseTool):
    """POI详情查询工具
    
    查询POI的详细信息
    """
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "amap_search_detail"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "查询关键词搜索或周边搜索获取到的POI ID的详细信息。"
            "返回POI的完整信息，包括位置、地址、营业信息等。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "id": {
                "type": "string",
                "description": "POI ID（从关键词搜索或周边搜索获取）",
                "required": True
            }
        }
    
    async def execute(self, id: str) -> str:
        """执行POI详情查询"""
        try:
            data = self._make_request(
                "https://restapi.amap.com/v3/place/detail",
                {"id": id}
            )
            
            if data.get("status") != "1":
                return self._format_error(data)
            
            if not data.get("pois"):
                return "错误：未找到POI"
            
            poi = data["pois"][0]
            result = {
                "id": poi.get("id"),
                "name": poi.get("name"),
                "location": poi.get("location"),
                "address": poi.get("address"),
                "business_area": poi.get("business_area"),
                "city": poi.get("cityname"),
                "type": poi.get("type"),
                "alias": poi.get("alias")
            }
            
            # 添加营业信息（如果存在）
            if poi.get("biz_ext"):
                result.update(poi["biz_ext"])
            
            logger.info(f"Amap search detail executed: id={id}")
            return self._format_result(result)
            
        except Exception as e:
            error_msg = f"错误：POI详情查询失败 - {str(e)}"
            logger.error(f"Amap search detail error: {error_msg}", exc_info=True)
            return error_msg

