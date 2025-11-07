"""
FastAPI主应用入口

配置FastAPI应用、中间件、路由和生命周期事件
"""

# 标准库
from contextlib import asynccontextmanager

# 第三方库
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 本地库
from app import __version__
from app.api.v1 import api_router
from app.config.config import settings
from app.models.base import close_db, init_db
from app.middleware.performance import PerformanceMiddleware
from app.utils.logger import logger
from app.utils.cache import cache_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    启动时初始化数据库，关闭时清理资源
    """
    # 启动时执行
    logger.info(f"Starting {settings.app_name} v{__version__}")
    logger.info(f"Environment: {settings.app_env}")
    
    # 初始化数据库（仅开发环境，生产环境使用Alembic迁移）
    # 注意：生产环境应该使用Alembic迁移，而不是自动创建表
    # 如果表已存在，init_db会跳过创建，不会报错
    if settings.is_development:
        try:
            await init_db()
        except Exception as e:
            # 数据库初始化失败不影响应用启动（表可能已存在）
            logger.warning(f"Database initialization skipped: {e}", exc_info=False)
    
    yield
    
    # 关闭时执行
    logger.info(f"Shutting down {settings.app_name}")
    cache_manager.close()
    await close_db()


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="CozyChat - AI对话应用后端服务",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ===== 配置CORS中间件 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 配置性能监控中间件 =====
app.add_middleware(PerformanceMiddleware)


# ===== 全局异常处理器 =====
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """全局异常处理器
    
    捕获所有未处理的异常并返回统一格式的错误响应
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.is_development else "An error occurred"
        }
    )


# ===== 注册路由 =====
app.include_router(api_router, prefix="/v1")


# ===== 根路由 =====
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": __version__,
        "docs": "/docs",
        "health": "/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
