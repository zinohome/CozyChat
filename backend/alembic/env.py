"""
Alembic环境配置

配置数据库迁移环境，支持异步SQLAlchemy
"""

# 标准库
import asyncio
from logging.config import fileConfig

# 第三方库
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 本地库
# 导入Base以获取所有模型的元数据
from app.models.base import Base
from app.config.config import settings

# 导入所有模型，确保它们被注册
from app.models.user import User  # noqa: F401

# Alembic Config对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
target_metadata = Base.metadata

# 从环境变量获取数据库URL
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """离线模式运行迁移
    
    在此模式下，不需要实际的数据库连接，仅生成SQL脚本
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式运行迁移
    
    使用异步引擎连接数据库并执行迁移
    """
    # 将postgresql://替换为postgresql+asyncpg://
    async_url = settings.database_url.replace(
        "postgresql://",
        "postgresql+asyncpg://"
    )
    
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = async_url
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式运行迁移
    
    创建Engine并将其与连接关联
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


