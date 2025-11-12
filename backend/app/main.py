"""
FastAPI主应用入口

配置FastAPI应用、中间件、路由和生命周期事件
"""

# 标准库
from contextlib import asynccontextmanager
from pathlib import Path

# 第三方库
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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


# 静态文件目录路径
STATIC_DIR = Path(__file__).parent / "static"

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="CozyChat - AI对话应用后端服务",
    version=__version__,
    docs_url=None,  # 禁用默认的 Swagger UI，使用自定义的
    redoc_url=None,  # 禁用默认的 ReDoc，使用自定义的
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

# ===== 配置静态文件路由 =====
# 挂载静态文件目录，提供 Swagger UI 和 ReDoc 的 JS 文件
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


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


# ===== 自定义 Swagger UI 路由 =====
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义 Swagger UI，使用本地静态文件"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.app_name} - API Documentation",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_ui_parameters={
            "deepLinking": True,
            "showExtensions": True,
            "showCommonExtensions": True,
        }
    )


# ===== 自定义 ReDoc 路由 =====
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """自定义 ReDoc，使用本地静态文件，完全禁用字体加载"""
    return HTMLResponse(
        content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>{settings.app_name} - API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        /* 覆盖 ReDoc 的字体设置，使用系统字体 */
        * {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        }}
    </style>
    <script>
        // 在 ReDoc 加载之前拦截所有字体文件请求
        (function() {{
            const originalFetch = window.fetch;
            window.fetch = function(...args) {{
                const url = args[0];
                if (typeof url === 'string' && (url.includes('.woff') || url.includes('.woff2'))) {{
                    console.warn('Font file request blocked:', url);
                    return Promise.reject(new Error('Font loading disabled'));
                }}
                return originalFetch.apply(this, args);
            }};
            
            // 拦截动态创建的 link 标签
            const originalCreateElement = document.createElement;
            document.createElement = function(tagName) {{
                const element = originalCreateElement.call(document, tagName);
                if (tagName.toLowerCase() === 'link') {{
                    const originalSetAttribute = element.setAttribute;
                    element.setAttribute = function(name, value) {{
                        if (name === 'href' && (value.includes('.woff') || value.includes('.woff2'))) {{
                            console.warn('Font link blocked:', value);
                            return;
                        }}
                        return originalSetAttribute.call(this, name, value);
                    }};
                }}
                return element;
            }};
            
            // 拦截错误事件，忽略字体加载错误
            window.addEventListener('error', function(e) {{
                if (e.target && (
                    (e.target.tagName === 'LINK' && e.target.href && (e.target.href.includes('.woff') || e.target.href.includes('.woff2'))) ||
                    (e.target.tagName === 'STYLE' && e.target.textContent && (e.target.textContent.includes('.woff') || e.target.textContent.includes('.woff2')))
                )) {{
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    return false;
                }}
            }}, true);
        }})();
    </script>
</head>
<body>
    <redoc spec-url="/openapi.json"></redoc>
    <script src="/static/redoc/redoc.standalone.js"></script>
</body>
</html>
        """,
        status_code=200
    )


# ===== Favicon 路由 =====
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """提供 favicon 图标"""
    favicon_path = STATIC_DIR / "favicon" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    # 如果没有 favicon，返回 204 No Content
    return JSONResponse(content=None, status_code=204)


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
