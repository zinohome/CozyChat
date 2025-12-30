"""全局异常处理器

集成Sentry监控，自动捕获和上报异常
统一处理所有业务异常
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.utils.exceptions import (
    CozyError,
    ChatServiceError,
    ContextServiceError,
    MessageServiceError,
    ToolServiceError,
    MemoryServiceError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ResourceNotFoundError,
)
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


# ============================================================================
# 业务异常处理器（新增）
# ============================================================================
# 创建时间：2025-01-XX
# 状态：✅ 统一业务异常处理
# ============================================================================

async def chat_service_error_handler(request: Request, exc: ChatServiceError):
    """处理聊天服务异常"""
    logger.error(
        f"ChatServiceError: {exc.code} - {exc.message}",
        exc_info=True,
        extra={"code": exc.code, "path": request.url.path}
    )
    
    # 发送到Sentry
    try:
        from app.utils.monitoring import capture_exception, set_context
        set_context("chat_service_error", {
            "error_code": exc.code,
            "error_message": exc.message,
            "request_path": str(request.url.path),
        })
        capture_exception(exc, level="error")
    except Exception:
        pass
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}}
    )


async def context_service_error_handler(request: Request, exc: ContextServiceError):
    """处理上下文服务异常"""
    logger.error(
        f"ContextServiceError: {exc.code} - {exc.message}",
        exc_info=True,
        extra={"code": exc.code, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}}
    )


async def message_service_error_handler(request: Request, exc: MessageServiceError):
    """处理消息服务异常"""
    logger.error(
        f"MessageServiceError: {exc.code} - {exc.message}",
        exc_info=True,
        extra={"code": exc.code, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}}
    )


async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """处理认证异常"""
    logger.warning(
        f"AuthenticationError: {exc.code} - {exc.message}",
        extra={"code": exc.code, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers={"WWW-Authenticate": "Bearer"}
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """处理授权异常"""
    logger.warning(
        f"AuthorizationError: {exc.code} - {exc.message}",
        extra={"code": exc.code, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error": {"code": exc.code, "message": exc.message}}
    )


async def validation_error_handler(request: Request, exc: ValidationError):
    """处理验证异常"""
    logger.warning(
        f"ValidationError: {exc.code} - {exc.message}",
        extra={"code": exc.code, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}}
    )


async def resource_not_found_error_handler(request: Request, exc: ResourceNotFoundError):
    """处理资源未找到异常"""
    logger.warning(
        f"ResourceNotFoundError: {exc.code} - {exc.message}",
        extra={"code": exc.code, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": {"code": exc.code, "message": exc.message}}
    )

