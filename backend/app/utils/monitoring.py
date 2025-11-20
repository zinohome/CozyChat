"""
应用监控模块

提供Sentry错误追踪和性能监控集成
"""

# 标准库
from typing import Any, Dict, Optional
import sys

# 本地库
from app.config.config import settings
from app.utils.logger import logger


def init_sentry() -> bool:
    """初始化Sentry监控
    
    根据配置决定是否启用Sentry，并进行初始化。
    
    Returns:
        bool: 是否成功初始化Sentry
        
    环境变量配置：
        SENTRY_DSN: Sentry项目的DSN
        SENTRY_ENABLE: 是否启用Sentry（默认False）
        SENTRY_ENVIRONMENT: 环境标识（development/staging/production）
        SENTRY_TRACES_SAMPLE_RATE: 性能追踪采样率（0.0-1.0）
        SENTRY_PROFILES_SAMPLE_RATE: 性能分析采样率（0.0-1.0）
        SENTRY_SEND_DEFAULT_PII: 是否发送个人身份信息
        SENTRY_ATTACH_STACKTRACE: 是否附加完整堆栈跟踪
        SENTRY_MAX_BREADCRUMBS: 最大面包屑数量
        SENTRY_DEBUG: 是否启用Sentry调试模式
    """
    # 检查是否启用Sentry
    if not settings.sentry_enable:
        logger.info("Sentry monitoring is disabled (SENTRY_ENABLE=false)")
        return False
    
    # 检查DSN是否配置
    if not settings.sentry_dsn:
        logger.warning(
            "Sentry is enabled but SENTRY_DSN is not configured. "
            "Skipping Sentry initialization."
        )
        return False
    
    try:
        # 导入Sentry SDK
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        logger.info("Initializing Sentry monitoring...")
        
        # 配置日志集成
        logging_integration = LoggingIntegration(
            level=None,  # 捕获所有级别的日志
            event_level=None  # 不自动将日志作为Sentry事件发送
        )
        
        # 初始化Sentry
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            
            # 环境和版本信息
            environment=settings.sentry_environment,
            release=_get_app_version(),
            
            # 采样率配置
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=settings.sentry_profiles_sample_rate,
            
            # 隐私和安全配置
            send_default_pii=settings.sentry_send_default_pii,
            attach_stacktrace=settings.sentry_attach_stacktrace,
            
            # 面包屑配置
            max_breadcrumbs=settings.sentry_max_breadcrumbs,
            
            # 调试模式
            debug=settings.sentry_debug,
            
            # 集成配置
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                logging_integration,
            ],
            
            # 性能监控配置
            enable_tracing=True,
            
            # 过滤敏感数据
            before_send=_before_send_event,
            before_send_transaction=_before_send_transaction,
        )
        
        logger.info(
            "Sentry monitoring initialized successfully",
            extra={
                "dsn": settings.sentry_dsn[:20] + "...",  # 只记录DSN前缀
                "environment": settings.sentry_environment,
                "traces_sample_rate": settings.sentry_traces_sample_rate,
                "profiles_sample_rate": settings.sentry_profiles_sample_rate,
            }
        )
        
        return True
        
    except ImportError:
        logger.error(
            "Failed to import sentry_sdk. "
            "Please install it: pip install sentry-sdk[fastapi]"
        )
        return False
    
    except Exception as e:
        logger.error(
            f"Failed to initialize Sentry: {e}",
            exc_info=True
        )
        return False


def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
) -> Optional[str]:
    """捕获并发送异常到Sentry
    
    Args:
        exception: 要捕获的异常
        context: 额外的上下文信息
        level: 日志级别（error/warning/info）
        
    Returns:
        Optional[str]: Sentry事件ID，如果未启用Sentry则返回None
    """
    if not settings.sentry_enable or not settings.sentry_dsn:
        return None
    
    try:
        import sentry_sdk
        
        # 设置上下文
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                scope.level = level
                event_id = sentry_sdk.capture_exception(exception)
        else:
            event_id = sentry_sdk.capture_exception(exception)
        
        return event_id
    
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")
        return None


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """发送消息到Sentry
    
    Args:
        message: 要发送的消息
        level: 日志级别（fatal/error/warning/info/debug）
        context: 额外的上下文信息
        
    Returns:
        Optional[str]: Sentry事件ID，如果未启用Sentry则返回None
    """
    if not settings.sentry_enable or not settings.sentry_dsn:
        return None
    
    try:
        import sentry_sdk
        
        # 设置上下文
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                scope.level = level
                event_id = sentry_sdk.capture_message(message, level=level)
        else:
            event_id = sentry_sdk.capture_message(message, level=level)
        
        return event_id
    
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")
        return None


def set_user_context(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
    **kwargs
) -> None:
    """设置用户上下文信息
    
    Args:
        user_id: 用户ID
        username: 用户名
        email: 邮箱（仅在SENTRY_SEND_DEFAULT_PII=true时发送）
        **kwargs: 其他用户相关信息
    """
    if not settings.sentry_enable or not settings.sentry_dsn:
        return
    
    try:
        import sentry_sdk
        
        user_data = {}
        if user_id:
            user_data["id"] = user_id
        if username:
            user_data["username"] = username
        if email and settings.sentry_send_default_pii:
            user_data["email"] = email
        
        # 添加其他用户数据
        user_data.update(kwargs)
        
        sentry_sdk.set_user(user_data)
    
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")


def set_tag(key: str, value: str) -> None:
    """设置Sentry标签
    
    Args:
        key: 标签键
        value: 标签值
    """
    if not settings.sentry_enable or not settings.sentry_dsn:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.set_tag(key, value)
    except Exception as e:
        logger.error(f"Failed to set tag in Sentry: {e}")


def set_context(key: str, value: Dict[str, Any]) -> None:
    """设置Sentry上下文
    
    Args:
        key: 上下文键
        value: 上下文数据（字典）
    """
    if not settings.sentry_enable or not settings.sentry_dsn:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.set_context(key, value)
    except Exception as e:
        logger.error(f"Failed to set context in Sentry: {e}")


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None
) -> None:
    """添加面包屑（用于追踪事件发生前的操作序列）
    
    Args:
        message: 面包屑消息
        category: 分类（如：http/db/navigation等）
        level: 级别（fatal/error/warning/info/debug）
        data: 额外数据
    """
    if not settings.sentry_enable or not settings.sentry_dsn:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    except Exception as e:
        logger.error(f"Failed to add breadcrumb in Sentry: {e}")


# ==================== 私有辅助函数 ====================

def _get_app_version() -> str:
    """获取应用版本号
    
    Returns:
        str: 版本号，格式如 "1.0.0" 或 "dev"
    """
    try:
        # 尝试从package读取版本
        from importlib.metadata import version
        return version("cozychat")
    except Exception:
        # 如果无法获取版本，返回默认值
        return "dev"


def _before_send_event(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """在发送事件到Sentry前的钩子函数
    
    用于过滤敏感数据、添加额外信息等。
    
    Args:
        event: Sentry事件数据
        hint: 额外的提示信息
        
    Returns:
        Optional[Dict]: 处理后的事件数据，返回None则不发送
    """
    # 过滤敏感信息
    if "request" in event:
        request = event["request"]
        
        # 过滤敏感header
        if "headers" in request:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in request["headers"]:
                    request["headers"][header] = "[Filtered]"
        
        # 过滤敏感查询参数
        if "query_string" in request:
            sensitive_params = ["password", "token", "api_key"]
            for param in sensitive_params:
                if param in str(request["query_string"]).lower():
                    request["query_string"] = "[Filtered]"
    
    # 添加Python版本信息
    if "contexts" in event:
        event["contexts"]["runtime"] = {
            "name": "python",
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    
    return event


def _before_send_transaction(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """在发送性能追踪事务到Sentry前的钩子函数
    
    Args:
        event: Sentry事件数据
        hint: 额外的提示信息
        
    Returns:
        Optional[Dict]: 处理后的事件数据，返回None则不发送
    """
    # 过滤健康检查端点的性能数据
    if "transaction" in event:
        transaction_name = event["transaction"]
        if transaction_name in ["/health", "/api/health", "/v1/health"]:
            return None  # 不发送健康检查的性能数据
    
    return event

