"""
时间工具

提供时间查询和格式化功能
"""

# 标准库
from datetime import datetime, timezone as tz_class, timedelta
from typing import Any, Dict, Optional

# 本地库
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class TimeTool(Tool):
    """时间工具
    
    提供当前时间查询、时区转换、时间格式化等功能
    """
    
    def __init__(self):
        """初始化时间工具"""
        super().__init__(tool_type=ToolType.BUILTIN)
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "time"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "获取当前时间、日期和时间信息。"
            "当用户询问以下任何问题时，你必须使用此工具，不要猜测或编造时间："
            "'现在几点钟'、'现在几点了'、'当前时间'、'现在是什么时间'、'几点'、"
            "'今天是几号'、'今天几号'、'现在是什么日期'、'今天是星期几'、'今天星期几'、'日期'。"
            "此工具返回的是真实的当前时间和日期信息。支持不同时区、时间格式化。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "timezone": {
                "type": "string",
                "description": "时区名称（可选），例如：'UTC'、'Asia/Shanghai'、'America/New_York'。默认为Asia/Shanghai（上海时区，UTC+8）",
                "required": False
            },
            "format": {
                "type": "string",
                "description": "时间格式（可选）。当用户问'几点钟'、'几点了'时使用'time_chinese'（默认，返回几点几分）。当用户问'今天几号'、'日期'时使用'date_chinese'（返回年月日和星期）。其他格式：'iso'、'datetime'、'date'、'time'、'full'。",
                "required": False
            }
        }
    
    async def execute(
        self,
        timezone: Optional[str] = None,
        format: Optional[str] = None
    ) -> str:
        """执行时间查询
        
        Args:
            timezone: 时区名称（可选，默认为Asia/Shanghai）
            format: 时间格式（可选）
            
        Returns:
            str: 时间信息
        """
        try:
            # 获取当前时间
            if timezone:
                # 尝试解析时区
                tz = self._parse_timezone(timezone)
                if tz:
                    now = datetime.now(tz)
                else:
                    # 如果时区解析失败，使用上海时区
                    logger.warning(f"Invalid timezone '{timezone}', using Asia/Shanghai")
                    shanghai_tz = tz_class(timedelta(hours=8))
                    now = datetime.now(shanghai_tz)
            else:
                # 默认使用上海时区（UTC+8）
                shanghai_tz = tz_class(timedelta(hours=8))
                now = datetime.now(shanghai_tz)
            
            # 格式化输出（默认使用"几点几分"格式）
            format = format or "time_chinese"
            result = self._format_time(now, format)
            
            logger.info(
                f"Time query executed: {result}",
                extra={"timezone": timezone, "format": format}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"错误：获取时间失败 - {str(e)}"
            logger.error(f"Time tool error: {error_msg}", exc_info=True)
            return error_msg
    
    def _parse_timezone(self, tz_str: str) -> Optional[tz_class]:
        """解析时区字符串
        
        Args:
            tz_str: 时区字符串
            
        Returns:
            Optional[timezone]: 时区对象，如果解析失败返回None
        """
        # 常见时区映射
        timezone_map = {
            "utc": tz_class.utc,
            "gmt": tz_class.utc,
            "asia/shanghai": tz_class(timedelta(hours=8)),
            "beijing": tz_class(timedelta(hours=8)),
            "cst": tz_class(timedelta(hours=8)),
            "america/new_york": tz_class(timedelta(hours=-5)),
            "est": tz_class(timedelta(hours=-5)),
            "america/los_angeles": tz_class(timedelta(hours=-8)),
            "pst": tz_class(timedelta(hours=-8)),
            "europe/london": tz_class(timedelta(hours=0)),
            "jst": tz_class(timedelta(hours=9)),
        }
        
        tz_lower = tz_str.lower().replace(" ", "_")
        return timezone_map.get(tz_lower)
    
    def _format_time(self, dt: datetime, format: str) -> str:
        """格式化时间
        
        Args:
            dt: 日期时间对象
            format: 格式类型
            
        Returns:
            str: 格式化后的时间字符串
        """
        if format == "time_chinese":
            # 几点几分格式（中文）
            hour = dt.hour
            minute = dt.minute
            return f"{hour}点{minute:02d}分"
        elif format == "date_chinese":
            # 日期格式（中文）：今天几号
            weekday_map = {
                0: "星期一",
                1: "星期二",
                2: "星期三",
                3: "星期四",
                4: "星期五",
                5: "星期六",
                6: "星期日",
            }
            weekday = weekday_map[dt.weekday()]
            return f"{dt.strftime('%Y年%m月%d日')} {weekday}"
        elif format == "iso":
            return dt.isoformat()
        elif format == "datetime":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format == "date":
            return dt.strftime("%Y-%m-%d")
        elif format == "time":
            return dt.strftime("%H:%M:%S")
        elif format == "full":
            weekday_map = {
                0: "星期一",
                1: "星期二",
                2: "星期三",
                3: "星期四",
                4: "星期五",
                5: "星期六",
                6: "星期日",
            }
            weekday = weekday_map[dt.weekday()]
            return f"{dt.strftime('%Y年%m月%d日')} {weekday} {dt.strftime('%H:%M:%S')}"
        else:
            # 默认使用"几点几分"格式
            hour = dt.hour
            minute = dt.minute
            return f"{hour}点{minute:02d}分"

