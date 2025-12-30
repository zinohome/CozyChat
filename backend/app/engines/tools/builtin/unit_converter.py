"""
单位转换工具

提供各种单位之间的转换功能
"""

# 标准库
from typing import Any, Dict, Optional

# 本地库
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class UnitConverterTool(Tool):
    """单位转换工具
    
    支持长度、重量、温度、体积、面积、速度、时间、数据存储等单位的转换
    """
    
    def __init__(self):
        """初始化单位转换工具"""
        super().__init__(tool_type=ToolType.BUILTIN)
        
        # 定义各种单位的转换因子（相对于基准单位）
        self.conversion_factors = {
            # 长度单位（基准：米）
            "length": {
                "meter": 1.0,
                "m": 1.0,
                "kilometer": 1000.0,
                "km": 1000.0,
                "centimeter": 0.01,
                "cm": 0.01,
                "millimeter": 0.001,
                "mm": 0.001,
                "inch": 0.0254,
                "in": 0.0254,
                "foot": 0.3048,
                "ft": 0.3048,
                "yard": 0.9144,
                "yd": 0.9144,
                "mile": 1609.344,
                "mi": 1609.344,
                "nautical_mile": 1852.0,
                "nmi": 1852.0,
            },
            # 重量单位（基准：千克）
            "weight": {
                "kilogram": 1.0,
                "kg": 1.0,
                "gram": 0.001,
                "g": 0.001,
                "milligram": 0.000001,
                "mg": 0.000001,
                "pound": 0.453592,
                "lb": 0.453592,
                "ounce": 0.0283495,
                "oz": 0.0283495,
                "ton": 1000.0,
                "metric_ton": 1000.0,
                "tonne": 1000.0,
            },
            # 体积单位（基准：升）
            "volume": {
                "liter": 1.0,
                "l": 1.0,
                "milliliter": 0.001,
                "ml": 0.001,
                "gallon": 3.78541,
                "gal": 3.78541,
                "quart": 0.946353,
                "qt": 0.946353,
                "pint": 0.473176,
                "pt": 0.473176,
                "cup": 0.236588,
                "fluid_ounce": 0.0295735,
                "fl_oz": 0.0295735,
                "cubic_meter": 1000.0,
                "m3": 1000.0,
                "cubic_centimeter": 0.001,
                "cm3": 0.001,
                "cc": 0.001,
            },
            # 面积单位（基准：平方米）
            "area": {
                "square_meter": 1.0,
                "m2": 1.0,
                "square_kilometer": 1000000.0,
                "km2": 1000000.0,
                "square_centimeter": 0.0001,
                "cm2": 0.0001,
                "square_millimeter": 0.000001,
                "mm2": 0.000001,
                "square_inch": 0.00064516,
                "in2": 0.00064516,
                "square_foot": 0.092903,
                "ft2": 0.092903,
                "square_yard": 0.836127,
                "yd2": 0.836127,
                "acre": 4046.86,
                "hectare": 10000.0,
                "ha": 10000.0,
            },
            # 速度单位（基准：米/秒）
            "speed": {
                "meter_per_second": 1.0,
                "m/s": 1.0,
                "kilometer_per_hour": 0.277778,
                "km/h": 0.277778,
                "mile_per_hour": 0.44704,
                "mph": 0.44704,
                "foot_per_second": 0.3048,
                "ft/s": 0.3048,
                "knot": 0.514444,
                "kt": 0.514444,
            },
            # 时间单位（基准：秒）
            "time": {
                "second": 1.0,
                "s": 1.0,
                "minute": 60.0,
                "min": 60.0,
                "hour": 3600.0,
                "h": 3600.0,
                "day": 86400.0,
                "d": 86400.0,
                "week": 604800.0,
                "wk": 604800.0,
                "month": 2592000.0,  # 30天
                "year": 31536000.0,  # 365天
                "yr": 31536000.0,
            },
            # 数据存储单位（基准：字节）
            "data": {
                "byte": 1.0,
                "b": 1.0,
                "kilobyte": 1024.0,
                "kb": 1024.0,
                "megabyte": 1048576.0,
                "mb": 1048576.0,
                "gigabyte": 1073741824.0,
                "gb": 1073741824.0,
                "terabyte": 1099511627776.0,
                "tb": 1099511627776.0,
                "petabyte": 1125899906842624.0,
                "pb": 1125899906842624.0,
            },
        }
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "unit_converter"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "执行各种单位之间的转换。支持以下类型的单位转换："
            "长度（米、千米、厘米、英寸、英尺、码、英里等）、"
            "重量（千克、克、磅、盎司等）、"
            "体积（升、毫升、加仑、夸脱、品脱等）、"
            "面积（平方米、平方千米、平方英尺、英亩等）、"
            "速度（米/秒、千米/小时、英里/小时、节等）、"
            "时间（秒、分钟、小时、天、周、月、年等）、"
            "数据存储（字节、KB、MB、GB、TB、PB等）。"
            "适用于需要将数值从一种单位转换为另一种单位的场景。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "value": {
                "type": "number",
                "description": "要转换的数值",
                "required": True
            },
            "from_unit": {
                "type": "string",
                "description": "源单位名称，例如：'km'、'mile'、'kg'、'pound'、'celsius'、'fahrenheit'等",
                "required": True
            },
            "to_unit": {
                "type": "string",
                "description": "目标单位名称，例如：'m'、'inch'、'g'、'ounce'、'fahrenheit'、'celsius'等",
                "required": True
            },
            "category": {
                "type": "string",
                "description": "单位类别（可选），用于明确单位类型。可选值：'length'、'weight'、'volume'、'area'、'speed'、'time'、'data'、'temperature'。如果不提供，工具会自动识别。",
                "required": False
            }
        }
    
    async def execute(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        category: Optional[str] = None
    ) -> str:
        """执行单位转换
        
        Args:
            value: 要转换的数值
            from_unit: 源单位
            to_unit: 目标单位
            category: 单位类别（可选）
            
        Returns:
            str: 转换结果或错误信息
        """
        try:
            # 标准化单位名称（转小写，去除空格）
            from_unit = from_unit.lower().strip()
            to_unit = to_unit.lower().strip()
            
            # 温度转换需要特殊处理
            if self._is_temperature_unit(from_unit) or self._is_temperature_unit(to_unit):
                result = self._convert_temperature(value, from_unit, to_unit)
                logger.info(
                    f"Temperature conversion: {value} {from_unit} = {result} {to_unit}",
                    extra={"value": value, "from_unit": from_unit, "to_unit": to_unit, "result": result}
                )
                return f"{result} {to_unit}"
            
            # 确定单位类别
            if category:
                category = category.lower().strip()
            else:
                category = self._detect_category(from_unit, to_unit)
            
            if not category:
                return "错误：无法识别单位类型，请指定category参数"
            
            if category not in self.conversion_factors:
                return f"错误：不支持的单位类别 '{category}'"
            
            # 获取转换因子
            factors = self.conversion_factors[category]
            
            if from_unit not in factors:
                return f"错误：不支持的源单位 '{from_unit}'（类别：{category}）"
            
            if to_unit not in factors:
                return f"错误：不支持的目标单位 '{to_unit}'（类别：{category}）"
            
            # 执行转换：先转换为基准单位，再转换为目标单位
            base_value = value * factors[from_unit]
            result_value = base_value / factors[to_unit]
            
            # 格式化结果（保留合理的小数位数）
            if result_value >= 1000:
                result_str = f"{result_value:.2f}"
            elif result_value >= 1:
                result_str = f"{result_value:.4f}"
            else:
                result_str = f"{result_value:.6f}"
            
            # 去除末尾的零
            result_str = result_str.rstrip('0').rstrip('.')
            
            logger.info(
                f"Unit conversion: {value} {from_unit} = {result_str} {to_unit}",
                extra={
                    "value": value,
                    "from_unit": from_unit,
                    "to_unit": to_unit,
                    "category": category,
                    "result": result_str
                }
            )
            
            return f"{result_str} {to_unit}"
            
        except Exception as e:
            error_msg = f"错误：单位转换失败 - {str(e)}"
            logger.error(f"Unit converter error: {error_msg}", exc_info=True)
            return error_msg
    
    def _is_temperature_unit(self, unit: str) -> bool:
        """检查是否为温度单位
        
        Args:
            unit: 单位名称
            
        Returns:
            bool: 是否为温度单位
        """
        temp_units = ["celsius", "c", "fahrenheit", "f", "kelvin", "k"]
        return unit.lower() in temp_units
    
    def _convert_temperature(
        self,
        value: float,
        from_unit: str,
        to_unit: str
    ) -> str:
        """转换温度
        
        Args:
            value: 温度值
            from_unit: 源单位
            to_unit: 目标单位
            
        Returns:
            str: 转换后的温度值（字符串）
        """
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        # 先转换为摄氏度（基准）
        if from_unit in ["celsius", "c"]:
            celsius = value
        elif from_unit in ["fahrenheit", "f"]:
            celsius = (value - 32) * 5 / 9
        elif from_unit in ["kelvin", "k"]:
            celsius = value - 273.15
        else:
            return f"错误：不支持的源温度单位 '{from_unit}'"
        
        # 从摄氏度转换为目标单位
        if to_unit in ["celsius", "c"]:
            result = celsius
        elif to_unit in ["fahrenheit", "f"]:
            result = celsius * 9 / 5 + 32
        elif to_unit in ["kelvin", "k"]:
            result = celsius + 273.15
        else:
            return f"错误：不支持的目标温度单位 '{to_unit}'"
        
        # 格式化结果
        if abs(result) >= 100:
            result_str = f"{result:.2f}"
        else:
            result_str = f"{result:.4f}"
        
        return result_str.rstrip('0').rstrip('.')
    
    def _detect_category(self, from_unit: str, to_unit: str) -> Optional[str]:
        """自动检测单位类别
        
        Args:
            from_unit: 源单位
            to_unit: 目标单位
            
        Returns:
            Optional[str]: 单位类别，如果无法识别返回None
        """
        # 检查所有类别
        for category, factors in self.conversion_factors.items():
            if from_unit in factors and to_unit in factors:
                return category
        
        return None

