"""
日志配置模块

使用structlog提供结构化日志，同时输出到控制台和文件
"""

# 标准库
import logging
import logging.handlers
import re
import sys
from pathlib import Path
from typing import Any, Dict

# 第三方库
import structlog

# 本地库
from app.config.config import settings


def format_level_compact(logger, method_name, event_dict):
    """格式化日志级别为紧凑格式（去掉填充空格）
    
    从：[info     ]
    到：[info]
    """
    level = event_dict.get("level")
    if level:
        # 直接使用级别名，不填充空格
        event_dict["level"] = level.strip()
    
    return event_dict


def format_timestamp_local(logger, method_name, event_dict):
    """格式化时间戳为本地时区格式
    
    从：2025-11-18T07:06:55.699562Z
    到：2025-11-18 15:06:55.699
    """
    from datetime import datetime
    
    timestamp = event_dict.get("timestamp")
    if timestamp:
        # 如果是ISO格式字符串，先解析
        if isinstance(timestamp, str):
            try:
                # 移除Z后缀并解析
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                # 转换为本地时区
                dt_local = dt.astimezone()
                # 格式化为简洁格式
                event_dict["timestamp"] = dt_local.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            except:
                pass
    
    return event_dict


def format_callsite(logger, method_name, event_dict):
    """格式化调用位置信息为可点击的链接格式
    
    在 VSCode/Cursor 终端中，格式 "path/to/file.py:123" 会被识别为可点击链接
    必须使用相对于工作区根目录的路径才能点击跳转
    
    格式：[app/engines/tools/builtin/factory.py:43]（不含函数名，更简洁）
    """
    import os
    
    pathname = event_dict.pop("pathname", None)
    lineno = event_dict.pop("lineno", None)
    # 移除函数名（不需要显示）
    event_dict.pop("func_name", None)
    
    # 移除不需要的 logger_name
    event_dict.pop("logger", None)
    
    if pathname and lineno:
        # 将绝对路径转换为相对于当前工作目录的路径
        try:
            current_dir = os.getcwd()
            if pathname.startswith(current_dir):
                # 相对于当前工作目录（backend/）
                rel_path = os.path.relpath(pathname, current_dir)
                filepath = rel_path
            else:
                # 如果不在当前目录下，直接使用路径
                filepath = pathname
        except Exception:
            # 如果转换失败，尝试提取文件名
            filepath = os.path.basename(pathname)
        
        # 构建可点击的文件位置（VSCode/Cursor 格式）
        # 格式：path/to/file.py:123（不包含函数名）
        location = f"{filepath}:{lineno}"
        
        # 将位置信息添加到消息前面
        event = event_dict.get("event", "")
        event_dict["event"] = f"[{location}] {event}"
    
    return event_dict


class CompactConsoleRenderer:
    """紧凑的控制台渲染器
    
    特点：
    1. 时间格式：2025-11-18 15:06:55.699
    2. 日志级别：[info] 带背景色，使用对比色文字
    3. 代码位置：[app/file.py:123] 无函数名
    4. 保留颜色
    """
    
    # 日志级别样式（高强度背景色 + 白色文字 + 粗体）
    # 所有级别统一使用亮白色文字(\x1b[97m)
    LEVEL_STYLES = {
        "debug": "\x1b[106m\x1b[97m\x1b[1m",      # 亮青色背景 + 亮白色文字 + 粗体
        "info": "\x1b[102m\x1b[97m\x1b[1m",       # 亮绿色背景 + 亮白色文字 + 粗体
        "warning": "\x1b[103m\x1b[97m\x1b[1m",    # 亮黄色背景 + 亮白色文字 + 粗体
        "error": "\x1b[101m\x1b[97m\x1b[1m",      # 亮红色背景 + 亮白色文字 + 粗体
        "critical": "\x1b[105m\x1b[97m\x1b[1m",   # 亮紫色背景 + 亮白色文字 + 粗体
    }
    RESET = "\x1b[0m"
    DIM = "\x1b[2m"
    
    def __call__(self, logger, method_name, event_dict):
        """渲染日志为紧凑格式"""
        # 提取字段
        timestamp = event_dict.pop("timestamp", "")
        level = event_dict.pop("level", "info")
        event = event_dict.pop("event", "")
        
        # 去掉日志级别的空格填充（重要！）
        level = level.strip()
        
        # 构建日志行
        parts = []
        
        # 1. 时间戳（灰色）
        if timestamp:
            parts.append(f"{self.DIM}{timestamp}{self.RESET}")
        
        # 2. 日志级别（带背景色和对比色文字）
        level_style = self.LEVEL_STYLES.get(level.lower(), "")
        # 格式：背景色 + 文字 + 重置，两边加空格使其更醒目
        parts.append(f"{level_style} {level.upper()} {self.RESET}")
        
        # 3. 事件消息
        parts.append(event)
        
        # 4. 额外字段（如果有）
        if event_dict:
            # extra字段用紫色显示
            extra_str = " ".join(f"{self.DIM}\x1b[36m{k}\x1b[0m=\x1b[35m{v!r}\x1b[0m" 
                                 for k, v in event_dict.items())
            parts.append(extra_str)
        
        return " ".join(parts)


class PlainTextFormatter(logging.Formatter):
    """移除ANSI转义码的日志格式化器
    
    用于文件输出，确保日志文件是纯文本格式，不包含颜色代码
    """
    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，移除ANSI转义码"""
        # 先使用父类格式化
        formatted = super().format(record)
        # 移除ANSI转义码
        return self.ANSI_ESCAPE.sub('', formatted)


def setup_logging() -> structlog.BoundLogger:
    """配置结构化日志
    
    配置日志同时输出到控制台和文件
    
    Returns:
        structlog.BoundLogger: 日志记录器
    """
    import os
    
    # 强制启用颜色输出（即使在 TERM=dumb 环境下）
    os.environ['FORCE_COLOR'] = '1'
    os.environ['CLICOLOR_FORCE'] = '1'
    
    # 确保日志目录存在
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置标准库logging - 文件处理器（纯文本，无颜色）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 文件日志格式（纯文本，无ANSI转义码）
    file_formatter = PlainTextFormatter(
        "%(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    # 配置标准库logging - 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    
    # 配置根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.handlers.clear()  # 清除默认处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # ===== 禁用第三方库的详细日志 =====
    # httpcore和httpx的debug日志太详细，设置为WARNING级别
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # 其他可能过于详细的第三方库
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.getLogger("multipart").setLevel(logging.INFO)
    
    # 配置structlog
    # 文件输出：使用JSON格式（纯文本，无颜色）
    # 控制台输出：使用可读格式（开发环境带颜色，生产环境JSON）
    # 注意：文件输出会通过PlainTextFormatter自动移除ANSI转义码
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        format_level_compact,  # 格式化日志级别为紧凑格式（去掉空格）
        structlog.processors.CallsiteParameterAdder(  # 添加调用位置信息
            [
                structlog.processors.CallsiteParameter.PATHNAME,  # 使用完整路径而不是文件名
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.TimeStamper(fmt="iso", utc=False),  # 使用本地时区
        format_timestamp_local,  # 格式化为简洁的本地时间格式
        format_callsite,  # 格式化位置信息为简洁格式
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    # 根据环境选择渲染器
    if settings.is_development:
        # 开发环境：使用自定义的紧凑渲染器（强制启用颜色）
        # 注意：即使在 TERM=dumb 的环境下也强制启用颜色
        processors.append(CompactConsoleRenderer())
    else:
        # 生产环境：使用JSON格式（无颜色）
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 记录日志配置完成
    logger = structlog.get_logger()
    logger.info(
        "Logging configured",
        extra={
            "log_file": settings.log_file,
            "log_level": settings.log_level,
            "environment": settings.app_env
        }
    )
    
    return logger


# 创建全局logger实例
logger = setup_logging()


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """记录函数调用
    
    Args:
        func_name: 函数名称
        **kwargs: 函数参数
    """
    logger.debug(
        f"Function call: {func_name}",
        extra={"function": func_name, "params": kwargs}
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """记录错误
    
    Args:
        error: 异常对象
        context: 上下文信息
    """
    logger.error(
        f"Error occurred: {str(error)}",
        exc_info=True,
        extra={"context": context or {}}
    )


