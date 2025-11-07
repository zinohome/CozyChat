"""
数据库基础模型

定义所有模型的基类和数据库引擎配置
"""

# 标准库
from datetime import datetime
from typing import AsyncGenerator

# 第三方库
from sqlalchemy import Column, DateTime, Integer, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 本地库
from app.config.config import settings
from app.utils.logger import logger


class Base(DeclarativeBase):
    """所有数据模型的基类
    
    提供公共字段和方法
    """
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )


# ===== 同步数据库引擎 =====
# 优化连接池配置
sync_engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # 连接前检查，确保连接有效
    echo=settings.db_echo,
    future=True,
    # 连接池优化参数
    pool_reset_on_return="commit",  # 返回连接池时重置事务
    connect_args={
        "connect_timeout": 10,  # 连接超时
        "application_name": "cozychat_backend"  # 应用名称（用于监控）
    }
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


# ===== 异步数据库引擎 =====
# 将postgresql://转换为postgresql+asyncpg://
async_database_url = settings.database_url.replace(
    "postgresql://", 
    "postgresql+asyncpg://"
)

async_engine = create_async_engine(
    async_database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # 连接前检查，确保连接有效
    echo=settings.db_echo,
    future=True,
    # 连接池优化参数
    pool_reset_on_return="commit",  # 返回连接池时重置事务
    connect_args={
        "command_timeout": 30,  # 命令超时
        "server_settings": {
            "application_name": "cozychat_backend_async"  # 应用名称（用于监控）
        }
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def get_sync_db() -> Session:
    """获取同步数据库会话（用于依赖注入）
    
    Returns:
        Session: 数据库会话
        
    Yields:
        Session: 数据库会话，使用完毕后自动关闭
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话（用于依赖注入）
    
    Returns:
        AsyncSession: 异步数据库会话
        
    Yields:
        AsyncSession: 异步数据库会话，使用完毕后自动关闭
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库
    
    创建所有表（仅用于开发环境，生产环境使用Alembic迁移）
    
    注意：此函数会尝试创建所有表，如果表已存在会跳过（不会报错）
    """
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        # 如果表已存在或其他错误，记录但不阻止启动
        logger.warning(f"Database initialization warning: {e}", exc_info=False)


async def close_db() -> None:
    """关闭数据库连接"""
    await async_engine.dispose()
    logger.info("Database connections closed")


