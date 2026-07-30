"""
Auth 认证中间件（Filter）

- 检查请求中的 API Key
- 验证通过后继续处理，否则返回 401
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from infra.utils.log_util import logger
from infra.settings import settings


class AuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        """
        初始化认证中间件
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求，重写 dispatch 方法
        
        Args:
            request: 请求对象
            call_next: 下一个中间件/路由处理函数
        
        Returns:
            响应对象
        """

        # 如果不是生产环境，跳过认证
        if not settings.is_production:
            response = await call_next(request)
            return response
        
        # 从请求头获取 API Key：Authorization 或 X-API-Key
        auth_header = request.headers.get("Authorization")
        x_api_key = request.headers.get("X-API-Key")
        
        # 提取实际的 API Key
        provided_key = None
        if auth_header and auth_header.startswith("Bearer "):
            provided_key = auth_header[7:]  # 去掉 "Bearer " 前缀
        elif x_api_key:
            provided_key = x_api_key
        
        # 验证 API Key
        if not provided_key or provided_key != settings.SECRET_KEY:
            logger.info(f"授权失败: {provided_key}")
            return JSONResponse(
                status_code=401,
                content={"error": "未授权", "message": "请提供有效的 API Key"}
            )
        
        # 认证通过，继续处理请求
        response = await call_next(request)
        return response