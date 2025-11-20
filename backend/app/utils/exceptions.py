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

