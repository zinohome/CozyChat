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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# 本地库
from app import __version__
from app.api.v1 import api_router
from app.config.config import settings
from app.models.base import close_db, init_db
from app.middleware.performance import PerformanceMiddleware
from app.middleware.rate_limit import limiter, rate_limit_handler
from app.utils.logger import logger
from app.utils.cache import cache_manager
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    启动时初始化数据库和全局组件，关闭时清理资源
    """
    # 启动时执行
    logger.info(f"Starting {settings.app_name} v{__version__}")
    logger.info(f"Environment: {settings.app_env}")
    
    # 初始化Sentry监控（Phase 3: Monitoring Integration）
    try:
        from app.utils.monitoring import init_sentry
        sentry_initialized = init_sentry()
        if sentry_initialized:
            logger.info("Sentry monitoring enabled and initialized")
        else:
            logger.info("Sentry monitoring is disabled or not configured")
    except Exception as e:
        # Sentry初始化失败不影响应用启动
        logger.warning(f"Failed to initialize Sentry: {e}", exc_info=False)
    
    # 初始化数据库（仅开发环境，生产环境使用Alembic迁移）
    # 注意：生产环境应该使用Alembic迁移，而不是自动创建表
    # 如果表已存在，init_db会跳过创建，不会报错
    if settings.is_development:
        try:
            await init_db()
        except Exception as e:
            # 数据库初始化失败不影响应用启动（表可能已存在）
            logger.warning(f"Database initialization skipped: {e}", exc_info=False)
    
    # 初始化全局组件（Phase 2: Lifecycle Optimization）
    logger.info("Initializing global components...")
    
    # 1. 初始化人格注册表
    try:
        from app.core.personality import init_personality_registry
        personality_registry = init_personality_registry()
        logger.info(f"PersonalityRegistry initialized with {len(personality_registry.list_personality_ids())} personalities")
    except Exception as e:
        logger.error(f"Failed to initialize PersonalityRegistry: {e}", exc_info=True)
    
    # 2. 初始化工具管理器工厂
    try:
        from app.engines.tools.factory import init_tool_manager_factory
        tool_factory = init_tool_manager_factory()
        logger.info("ToolManagerFactory initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ToolManagerFactory: {e}", exc_info=True)
    
    # 2.1. 发现并注册MCP工具
    mcp_discovery = None
    try:
        from app.engines.tools.mcp.discovery import MCPDiscovery
        mcp_discovery = MCPDiscovery()
        mcp_results = await mcp_discovery.discover_from_config()
        if mcp_results:
            total_tools = sum(len(tools) for tools in mcp_results.values())
            logger.info(
                f"MCP discovery completed: {len(mcp_results)} servers, {total_tools} tools",
                extra={"servers": list(mcp_results.keys())}
            )
        else:
            logger.info("No MCP tools discovered")
    except Exception as e:
        logger.warning(f"Failed to discover MCP tools: {e}", exc_info=False)
    
    # 3. 初始化LLM引擎池
    try:
        from app.engines.ai.engine_pool import init_llm_engine_pool
        engine_pool = init_llm_engine_pool()
        logger.info("LLMEnginePool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LLMEnginePool: {e}", exc_info=True)
    
    # 4. 初始化Qdrant客户端
    try:
        from app.engines.memory.qdrant_client_manager import init_qdrant_client
        qdrant_client = init_qdrant_client()
        # 注意：init_qdrant_client() 内部已经记录了 "Qdrant client initialized" 日志
        # 这里不需要重复记录
    except Exception as e:
        logger.warning(f"Failed to initialize Qdrant client: {e}", exc_info=False)
    
    # 5. 初始化并启动记忆写入Worker（Phase 3.2: Async Memory Queue）
    memory_worker = None
    if settings.memory_async_write:
        try:
            from app.engines.memory import get_memory_manager
            from app.engines.memory.worker import MemoryWorker
            
            # 使用全局单例，避免重复初始化
            memory_manager = get_memory_manager()
            
            # 从memory_manager获取queue和engine，避免重复创建
            if memory_manager.queue and memory_manager.engine:
                # 类型检查：MemoryWorker 需要 QdrantMemoryEngine
                from app.engines.memory.qdrant_engine import QdrantMemoryEngine
                if not isinstance(memory_manager.engine, QdrantMemoryEngine):
                    logger.warning(
                        "Memory engine is not QdrantMemoryEngine, "
                        "memory worker requires Qdrant engine"
                    )
                else:
                    # 创建并启动Worker，复用已有的queue和engine
                    memory_worker = MemoryWorker(
                        queue=memory_manager.queue,
                        engine=memory_manager.engine,  # type: ignore[arg-type]
                        deduplicator=memory_manager.deduplicator,  # 复用deduplicator
                        batch_size=settings.memory_batch_size
                    )
                    await memory_worker.start()
                    logger.info("Memory worker started")
            else:
                logger.warning(
                    "Memory manager queue or engine not available, "
                    "memory worker not started"
                )
        except Exception as e:
            logger.error(f"Failed to start memory worker: {e}", exc_info=True)
    
    logger.info("All global components initialized successfully")
    
    # 6. Demo模式：自动创建DemoUser（如果启用）
    if settings.demo_mode:
        try:
            from app.models.base import get_sync_db
            from app.models.user import User
            from app.models.user_profile import UserProfile
            from app.utils.security import hash_password
            from sqlalchemy import or_
            
            # 使用同步数据库会话
            db = next(get_sync_db())
            try:
                # 检查DemoUser是否已存在
                existing_user = db.query(User).filter(
                    or_(
                        User.username == settings.demo_username,
                        User.email == settings.demo_email
                    )
                ).first()
                
                if not existing_user:
                    # 创建DemoUser
                    password_hash = hash_password(settings.demo_password)
                    demo_user = User(
                        username=settings.demo_username,
                        email=settings.demo_email,
                        password_hash=password_hash,
                        role="user",
                        display_name="Demo用户",
                        status="active"
                    )
                    db.add(demo_user)
                    db.commit()
                    db.refresh(demo_user)
                    
                    # 创建用户画像
                    profile = UserProfile(user_id=demo_user.id)
                    db.add(profile)
                    db.commit()
                    
                    logger.info(
                        f"Demo user created: {settings.demo_username}",
                        extra={"user_id": str(demo_user.id)}
                    )
                else:
                    logger.debug(
                        f"Demo user already exists: {settings.demo_username}",
                        extra={"user_id": str(existing_user.id)}
                    )
            finally:
                db.close()
        except Exception as e:
            logger.warning(
                f"Failed to create demo user: {e}",
                exc_info=False
            )
    
    yield
    
    # 关闭时执行
    logger.info(f"Shutting down {settings.app_name}")
    
    # 关闭MCP客户端连接
    if mcp_discovery:
        try:
            await mcp_discovery.close_all()
        except Exception as e:
            logger.error(f"Error closing MCP clients: {e}", exc_info=True)
    
    # 停止记忆写入Worker
    if memory_worker:
        try:
            await memory_worker.stop(wait_for_completion=True)
            logger.info("Memory worker stopped gracefully")
        except Exception as e:
            logger.error(f"Error stopping memory worker: {e}", exc_info=True)
    
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
# 开发环境下允许所有来源，生产环境使用配置的 origins
# 注意：使用 ["*"] 时，allow_credentials 必须为 False
# 微信浏览器需要特殊处理
if settings.is_development:
    cors_origins = ["*"]
    cors_allow_credentials = False
    logger.info(
        "CORS configured for development: allow all origins",
        extra={"cors_origins": ["*"], "allow_credentials": False}
    )
else:
    # 生产环境：使用配置的 origins
    cors_origins = settings.cors_origins
    
    # 微信浏览器特殊处理：如果配置为空或未包含微信域名，添加警告
    if not cors_origins or len(cors_origins) == 0:
        logger.warning(
            "CORS_ORIGINS 未配置或为空，微信浏览器可能无法访问。"
            "建议在 .env 中配置 CORS_ORIGINS，包含前端域名。"
        )
        # 如果未配置，使用通配符（不推荐，但可以临时解决）
        cors_origins = ["*"]
        cors_allow_credentials = False
    else:
        cors_allow_credentials = True
        logger.info(
            f"CORS origins configured: {cors_origins}",
            extra={"cors_origins": cors_origins, "allow_credentials": cors_allow_credentials}
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRFToken",
        "X-OpenAI-Agents-SDK",  # WebRTC 需要
    ],
    expose_headers=["*"],
    max_age=3600,  # 预检请求缓存时间
)

# ===== 添加CORS诊断和修复中间件（用于调试微信浏览器问题） =====
class CORSDiagnosticMiddleware(BaseHTTPMiddleware):
    """CORS诊断和修复中间件，用于调试和修复微信浏览器问题
    
    微信浏览器有时不发送 Origin 头，但会发送 Referer 头。
    当 Origin 为 None 时，从 Referer 中提取 origin 并添加到请求头中。
    """
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否是微信浏览器
        user_agent = request.headers.get("user-agent", "")
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        is_wechat = "MicroMessenger" in user_agent
        
        # 微信浏览器特殊处理：如果 origin 为 None 但有 referer，从 referer 提取 origin
        if is_wechat and not origin and referer:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                # 提取 scheme://host:port
                extracted_origin = f"{parsed.scheme}://{parsed.netloc}"
                # 将提取的 origin 添加到请求头中（FastAPI 的 Request 是只读的，但我们可以创建一个新的请求）
                # 注意：这里我们修改请求的 scope，但更好的方法是在响应时处理
                logger.info(
                    "WeChat browser: extracted origin from referer",
                    extra={
                        "referer": referer,
                        "extracted_origin": extracted_origin
                    }
                )
                # 由于 Request 是只读的，我们在响应时处理
                origin = extracted_origin
            except Exception as e:
                logger.warning(f"Failed to extract origin from referer: {e}")
        
        # 记录微信浏览器的请求
        if is_wechat:
            logger.info(
                "WeChat browser request detected",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "origin": origin,
                    "referer": referer,
                    "user_agent": user_agent[:100],  # 只记录前100个字符
                }
            )
        
        # 记录OPTIONS预检请求
        if request.method == "OPTIONS":
            logger.debug(
                "CORS preflight request",
                extra={
                    "origin": origin,
                    "access_control_request_method": request.headers.get("access-control-request-method"),
                    "access_control_request_headers": request.headers.get("access-control-request-headers"),
                    "is_wechat": is_wechat
                }
            )
        
        response = await call_next(request)
        
        # 微信浏览器特殊处理：如果 origin 为 None 但响应中没有 CORS 头，手动添加
        if is_wechat:
            # 检查响应中是否有 CORS 头
            has_cors_origin = "access-control-allow-origin" in response.headers
            
            # 如果没有 CORS 头，手动添加（开发环境允许所有来源）
            if not has_cors_origin:
                if settings.is_development:
                    response.headers["access-control-allow-origin"] = "*"
                    response.headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                    response.headers["access-control-allow-headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-CSRFToken, X-OpenAI-Agents-SDK"
                    logger.debug(
                        "WeChat browser: manually added CORS headers (development mode)",
                        extra={
                            "path": request.url.path,
                            "method": request.method
                        }
                    )
                elif origin:
                    # 生产环境：如果从 referer 提取了 origin，使用它
                    response.headers["access-control-allow-origin"] = origin
                    response.headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                    response.headers["access-control-allow-headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-CSRFToken, X-OpenAI-Agents-SDK"
                    logger.debug(
                        "WeChat browser: manually added CORS headers (production mode)",
                        extra={
                            "origin": origin,
                            "path": request.url.path,
                            "method": request.method
                        }
                    )
        
        # 记录CORS响应头
        if is_wechat:
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-credentials": response.headers.get("access-control-allow-credentials"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                "access-control-allow-headers": response.headers.get("access-control-allow-headers"),
            }
            logger.debug(
                "CORS response headers for WeChat browser",
                extra={
                    "origin": origin or "None (extracted from referer)",
                    "cors_headers": cors_headers,
                    "status_code": response.status_code,
                    "path": request.url.path
                }
            )
        
        return response

# 在CORS中间件之后添加诊断中间件
app.add_middleware(CORSDiagnosticMiddleware)

# ===== 配置性能监控中间件 =====
app.add_middleware(PerformanceMiddleware)

# ===== 配置限流中间件 =====
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]

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
    # openapi_url 可能为 None，需要提供默认值
    openapi_url = app.openapi_url or "/openapi.json"
    return get_swagger_ui_html(
        openapi_url=openapi_url,
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
