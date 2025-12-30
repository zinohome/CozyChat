"""
健康检查接口

提供应用健康状态检查
"""

# 标准库
from datetime import datetime
from typing import Dict, Any

# 第三方库
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app import __version__
from app.api.deps import get_db
from app.config.config import settings
from app.utils.logger import logger

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """健康检查接口
    
    检查应用和数据库连接状态
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict: 健康状态信息
    """
    try:
        # 检查数据库连接
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    health_status = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "version": __version__,
        "environment": settings.app_env,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
    }
    
    logger.info("Health check completed", extra=health_status)
    return health_status


@router.get("/")
async def root() -> Dict[str, str]:
    """根路径
    
    Returns:
        Dict: 欢迎信息
    """
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": __version__,
        "docs": "/docs",
        "health": "/v1/health"
    }


@router.get("/health/engines", response_model=Dict[str, Any])
async def check_engines_health() -> Dict[str, Any]:
    """检查三大人格化引擎健康状态
    
    Returns:
        Dict: 三大引擎健康状态
    """
    try:
        from app.services.context.context_service_new import ContextServiceNew
        
        # 获取ContextService实例
        context_service = ContextServiceNew.get_instance()
        
        # 执行健康检查
        health_status = await context_service.health_check()
        
        # 添加时间戳
        health_status["timestamp"] = datetime.utcnow().isoformat()
        health_status["status"] = "healthy" if health_status.get("overall") else "degraded"
        
        logger.info("Engines health check completed", extra=health_status)
        return health_status
        
    except Exception as e:
        logger.error(f"Engines health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "knowledge": False,
            "userprofile": False,
            "chatmemory": False,
            "overall": False
        }


