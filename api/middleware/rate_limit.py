"""
速率限制中间件（Filter）

- 限制每个 IP 的请求频率
- 使用滑动窗口算法
- 超过限制返回 429
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
from infra.utils.log_util import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        """
        初始化速率限制器
        
        Args:
            app: FastAPI 应用
            max_requests: 时间窗口内最大请求数（默认 60 次/分钟）
            window_seconds: 时间窗口大小（默认 60 秒）
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # 存储每个 IP 的请求时间戳
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求 重写 dispatch 方法
        
        Args:
            request: 请求对象
            call_next: 下一个中间件/路由处理函数
        
        Returns:
            响应对象
        """
        # 获取客户端 IP
        client_ip = request.client.host
        
        # 获取当前时间戳
        now = time.time()
        
        # 清理过期的请求记录（滑动窗口）
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if now - ts < self.window_seconds
        ]
        
        # 检查请求数是否超过限制
        if len(self.requests[client_ip]) >= self.max_requests:
            # 计算剩余时间（秒）
            reset_time = int(self.window_seconds - (now - self.requests[client_ip][0]))
            logger.info(f"IP {client_ip} 请求过于频繁")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "请求过于频繁",
                    "message": f"请 {reset_time} 秒后重试",
                    "retry_after": reset_time
                },
                headers={"Retry-After": str(reset_time)}
            )
        
        # 记录当前请求时间戳
        self.requests[client_ip].append(now)
        
        # 继续处理请求
        response = await call_next(request)
        
        # 在响应头中添加速率限制信息
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.max_requests - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))
        
        return response