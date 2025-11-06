"""
时间工具

提供时间查询和格式化功能
"""

# 标准库
from datetime import datetime, timezone, timedelta
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
            "查询当前时间、日期和时间信息。支持不同时区、时间格式化。"
            "适用于需要获取当前时间、日期、星期等信息的场景。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "timezone": {
                "type": "string",
                "description": "时区名称（可选），例如：'UTC'、'Asia/Shanghai'、'America/New_York'。默认为UTC",
                "required": False
            },
            "format": {
                "type": "string",
                "description": "时间格式（可选），例如：'iso'、'datetime'、'date'、'time'。默认为'iso'",
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
            timezone: 时区名称（可选）
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
                    # 如果时区解析失败，使用UTC
                    logger.warning(f"Invalid timezone '{timezone}', using UTC")
                    from datetime import timezone as tz_module
                    now = datetime.now(tz_module.utc)
            else:
                # 使用UTC时区
                from datetime import timezone as tz_module
                now = datetime.now(tz_module.utc)
            
            # 格式化输出
            format = format or "iso"
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
    
    def _parse_timezone(self, tz_str: str) -> Optional[timezone]:
        """解析时区字符串
        
        Args:
            tz_str: 时区字符串
            
        Returns:
            Optional[timezone]: 时区对象，如果解析失败返回None
        """
        # 常见时区映射
        timezone_map = {
            "utc": timezone.utc,
            "gmt": timezone.utc,
            "asia/shanghai": timezone(timedelta(hours=8)),
            "beijing": timezone(timedelta(hours=8)),
            "cst": timezone(timedelta(hours=8)),
            "america/new_york": timezone(timedelta(hours=-5)),
            "est": timezone(timedelta(hours=-5)),
            "america/los_angeles": timezone(timedelta(hours=-8)),
            "pst": timezone(timedelta(hours=-8)),
            "europe/london": timezone(timedelta(hours=0)),
            "jst": timezone(timedelta(hours=9)),
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
        if format == "iso":
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
            # 默认使用ISO格式
            return dt.isoformat()

