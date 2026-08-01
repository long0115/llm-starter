"""
FastAPI 应用入口

使用分层架构：
    - 依赖注入管理服务实例
    - 配置管理使用 Pydantic Settings

功能：
    - 创建应用实例
    - 注册中间件（CORS、认证、速率限制）
    - 注册路由（对话、RAG、Agent）
    - 全局异常处理
    - 健康检查接口
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
# 导入中间件
from api.middleware.auth import AuthMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
# 导入路由
from api.routers import chat, rag, agent, session
# 导入配置
from infra.settings import settings
# 导入日志工具
from infra.utils.log_util import logger
from infra.exceptions import BusinessException

# 加载 .env 文件到环境变量
load_dotenv()


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESC,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 注册 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ALLOW_ORIGINS.split(","),
    allow_methods=settings.CORS_ALLOW_METHODS.split(","),
    allow_headers=settings.CORS_ALLOW_HEADERS.split(",")
)

# 注册自定义中间件（认证、速率限制）
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# 注册路由
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(session.router)

# 健康检查接口
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }


# 业务异常处理（根据异常类型返回对应状态码）
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    logger.warning(f"业务异常 [{exc.error_code}]: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message
        }
    )

# 参数校验异常处理（保留原有的）
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"参数校验失败: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "VALIDATION_ERROR",
            "message": "请检查请求参数",
            "details": exc.errors()
        }
    )

# HTTP 异常处理（保留原有的）
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP 异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": str(exc.detail)
        }
    )

# 全局异常处理（兜底，只处理未预期的异常）
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"服务器内部错误: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "服务暂时不可用，请稍后重试"
        }
    )