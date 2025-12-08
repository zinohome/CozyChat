"""自定义异常类层次结构"""


class CozyError(Exception):
    """CozyChat基础异常类"""
    
    def __init__(self, message: str, code: str = "COZY_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(CozyError):
    """认证错误"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class ValidationError(CozyError):
    """验证错误"""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class ResourceNotFoundError(CozyError):
    """资源未找到"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND")


class BusinessLogicError(CozyError):
    """业务逻辑错误"""
    
    def __init__(self, message: str = "Business logic error"):
        super().__init__(message, "BUSINESS_ERROR")


class ExternalServiceError(CozyError):
    """外部服务错误"""
    
    def __init__(self, message: str = "External service error"):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")


# ============================================================================
# 业务异常类（新增）
# ============================================================================
# 创建时间：2025-01-XX
# 状态：✅ 统一异常类型
# ============================================================================

class ChatServiceError(CozyError):
    """聊天服务异常"""
    
    def __init__(self, message: str = "Chat service error"):
        super().__init__(message, "CHAT_SERVICE_ERROR")


class ContextServiceError(CozyError):
    """上下文服务异常"""
    
    def __init__(self, message: str = "Context service error"):
        super().__init__(message, "CONTEXT_SERVICE_ERROR")


class MessageServiceError(CozyError):
    """消息服务异常"""
    
    def __init__(self, message: str = "Message service error"):
        super().__init__(message, "MESSAGE_SERVICE_ERROR")


class ToolServiceError(CozyError):
    """工具服务异常"""
    
    def __init__(self, message: str = "Tool service error"):
        super().__init__(message, "TOOL_SERVICE_ERROR")


class MemoryServiceError(CozyError):
    """记忆服务异常"""
    
    def __init__(self, message: str = "Memory service error"):
        super().__init__(message, "MEMORY_SERVICE_ERROR")


class AuthorizationError(CozyError):
    """授权错误"""
    
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, "AUTHORIZATION_ERROR")

