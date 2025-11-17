"""
API限流中间件

使用slowapi实现API限流，防止恶意请求和系统过载
"""

# 标准库
from typing import Callable, Optional

# 第三方库
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status

# 本地库
from app.utils.logger import logger


# 创建限流器实例
limiter = Limiter(
    key_func=get_remote_address,  # 默认按IP限流
    default_limits=["1000/hour"],  # 默认限制：每小时1000次
    storage_uri="memory://",  # 使用内存存储（生产环境建议使用Redis）
    headers_enabled=True  # 在响应头中显示限流信息
)


def get_user_id_for_rate_limit(request: Request) -> str:
    """获取用户ID用于限流（如果已认证）
    
    优先使用用户ID，如果未认证则使用IP地址
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        str: 用户ID或IP地址
    """
    # 从请求状态中获取用户（如果已通过认证中间件设置）
    # 注意：这需要在认证中间件中设置 request.state.user
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.id}"
    
    # 使用IP地址作为fallback
    return get_remote_address(request)


# 自定义限流键函数（按用户ID限流）
def get_rate_limit_key(request: Request) -> str:
    """
    获取限流键
    
    根据用户认证状态选择限流键：
    - 已认证：使用用户ID
    - 未认证：使用IP地址
    """
    return get_user_id_for_rate_limit(request)


# 创建按用户限流的限流器
user_limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["1000/hour"],
    storage_uri="memory://",
    headers_enabled=True
)


def rate_limit(
    limit: str,
    per_user: bool = False,
    exempt_when: Optional[Callable[[Request], bool]] = None
):
    """限流装饰器
    
    简化版本：要求所有使用此装饰器的端点函数必须包含一个 `Request` 类型的参数。
    
    Args:
        limit: 限流规则，如 "10/minute", "100/hour"
        per_user: 是否按用户限流（True）还是按IP限流（False）
        exempt_when: 豁免条件函数（返回True时豁免限流）
        
    Returns:
        装饰器函数
        
    Example:
        @router.post("/chat/completions")
        @rate_limit("10/minute", per_user=True)
        async def chat_completions(request: Request, data: ChatRequest):
            pass
    
    Note:
        端点函数必须包含一个 `Request` 类型的参数（可以命名为 request 或 http_request）。
        如果没有，slowapi 会抛出错误。
    """
    def decorator(func):
        # 选择限流器
        limiter_instance = user_limiter if per_user else limiter
        
        # 应用限流
        if exempt_when:
            decorated = limiter_instance.limit(limit, exempt_when=exempt_when)(func)
        else:
            decorated = limiter_instance.limit(limit)(func)
        
        return decorated
    return decorator


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """限流异常处理器
    
    当请求超过限流阈值时，返回友好的错误信息
    
    Args:
        request: FastAPI请求对象
        exc: RateLimitExceeded异常
        
    Returns:
        HTTPException: 429状态码，包含限流信息
    """
    # 提取限流信息
    path = request.url.path
    method = request.method
    client_ip = get_remote_address(request)
    
    # 记录日志
    logger.warning(
        f"Rate limit exceeded for {method} {path}",
        extra={
            "ip": client_ip,
            "path": path,
            "method": method,
            "limit": str(exc.limit) if hasattr(exc, 'limit') else "unknown"
        }
    )
    
    # 计算重试时间
    retry_after = None
    if hasattr(exc, 'reset_time') and exc.reset_time:
        import time
        retry_after = max(0, int(exc.reset_time - time.time()))
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": "您的请求过于频繁，请稍后再试",
            "path": path,
            "retry_after": retry_after
        },
        headers={
            "Retry-After": str(retry_after) if retry_after else "60",
            "X-RateLimit-Limit": str(exc.limit) if hasattr(exc, 'limit') else "unknown",
            "X-RateLimit-Remaining": "0"
        }
    )


# 预定义的限流规则
RATE_LIMITS = {
    # 认证相关
    "auth": {
        "login": "5/minute",  # 登录：每分钟5次
        "register": "3/minute",  # 注册：每分钟3次
        "refresh": "10/minute",  # Token刷新：每分钟10次
    },
    # 聊天相关
    "chat": {
        "completions": "30/minute",  # 聊天完成：每分钟30次
        "stream": "10/minute",  # 流式聊天：每分钟10次
    },
    # 记忆相关
    "memory": {
        "search": "60/minute",  # 记忆搜索：每分钟60次
        "create": "20/minute",  # 创建记忆：每分钟20次
    },
    # 用户相关
    "user": {
        "profile": "30/minute",  # 用户画像：每分钟30次
        "preferences": "20/minute",  # 用户偏好：每分钟20次
    },
    # 工具相关
    "tools": {
        "execute": "50/minute",  # 工具执行：每分钟50次
    },
    # 音频相关
    "audio": {
        "transcription": "20/minute",  # 语音转文本：每分钟20次
        "speech": "30/minute",  # 文本转语音：每分钟30次
    },
    # 配置相关
    "config": {
        "realtime_token": "10/minute",  # Realtime Token：每分钟10次
    },
}


def get_rate_limit_for_endpoint(endpoint: str, category: str = "default") -> str:
    """获取端点的限流规则
    
    Args:
        endpoint: 端点名称（如 "login", "completions"）
        category: 类别（如 "auth", "chat"）
        
    Returns:
        str: 限流规则字符串
    
    Example:
        >>> get_rate_limit_for_endpoint("login", "auth")
        "5/minute"
    """
    if category in RATE_LIMITS and endpoint in RATE_LIMITS[category]:
        return RATE_LIMITS[category][endpoint]
    return "100/hour"  # 默认限流规则
