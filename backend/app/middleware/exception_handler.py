"""全局异常处理器

集成Sentry监控，自动捕获和上报异常
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.utils.exceptions import CozyError
from app.utils.logger import logger


async def cozy_exception_handler(request: Request, exc: CozyError):
    """处理CozyError异常
    
    CozyError是业务逻辑异常，记录为warning级别，
    并发送到Sentry（如果启用）用于监控业务异常频率
    """
    logger.warning(
        f"CozyError: {exc.code} - {exc.message}",
        extra={"code": exc.code, "path": request.url.path}
    )
    
    # 发送到Sentry（作为warning级别）
    try:
        from app.utils.monitoring import capture_exception, set_context
        set_context("business_error", {
            "error_code": exc.code,
            "error_message": exc.message,
            "request_path": str(request.url.path),
            "request_method": request.method
        })
        capture_exception(exc, level="warning")
    except Exception:
        pass  # Sentry错误不影响响应
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常
    
    未捕获的异常会被记录为error级别，并发送到Sentry（如果启用）
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path}
    )
    
    # 发送到Sentry
    try:
        from app.utils.monitoring import capture_exception, set_context, add_breadcrumb
        
        # 添加请求信息为面包屑
        add_breadcrumb(
            message=f"{request.method} {request.url.path}",
            category="http.request",
            level="info",
            data={
                "method": request.method,
                "path": str(request.url.path),
                "query_params": str(request.query_params) if request.query_params else None
            }
        )
        
        # 设置上下文
        set_context("request", {
            "method": request.method,
            "path": str(request.url.path),
            "client_host": request.client.host if request.client else None
        })
        
        # 捕获异常
        capture_exception(exc, level="error")
    except Exception:
        pass  # Sentry错误不影响响应
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
    )

