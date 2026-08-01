"""
自定义异常体系

类比 Java：
    - BusinessException 类似 RuntimeException（业务异常基类）
    - NotFoundException 类似 EntityNotFoundException
    - ValidationException 类似 MethodArgumentNotValidException
"""


class BusinessException(Exception):
    """
    业务异常基类
    
    所有业务相关的异常都应继承此类。
    包含 HTTP 状态码和错误信息，方便 Router 层统一处理。
    """
    def __init__(self, message: str, status_code: int = 500, error_code: str = "BUSINESS_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class NotFoundException(BusinessException):
    """资源不存在异常（404）"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND")


class ValidationException(BusinessException):
    """参数校验失败异常（400）"""
    def __init__(self, message: str = "参数校验失败"):
        super().__init__(message=message, status_code=400, error_code="VALIDATION_ERROR")


class AuthenticationException(BusinessException):
    """认证失败异常（401）"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, status_code=401, error_code="AUTH_ERROR")


class RateLimitException(BusinessException):
    """速率限制异常（429）"""
    def __init__(self, message: str = "请求过于频繁，请稍后重试"):
        super().__init__(message=message, status_code=429, error_code="RATE_LIMIT")


class LLMServiceException(BusinessException):
    """LLM 服务调用异常（502）"""
    def __init__(self, message: str = "LLM 服务调用失败"):
        super().__init__(message=message, status_code=502, error_code="LLM_SERVICE_ERROR")