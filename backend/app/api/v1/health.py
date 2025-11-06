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


