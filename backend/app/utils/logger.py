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
    
    # 配置structlog
    # 文件输出：使用JSON格式（纯文本，无颜色）
    # 控制台输出：使用可读格式（开发环境带颜色，生产环境JSON）
    # 注意：文件输出会通过PlainTextFormatter自动移除ANSI转义码
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    # 根据环境选择渲染器
    if settings.is_development:
        # 开发环境：控制台使用可读格式（带颜色）
        # 文件输出会通过PlainTextFormatter自动移除颜色代码
        processors.append(structlog.dev.ConsoleRenderer())
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


