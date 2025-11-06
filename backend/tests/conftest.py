"""
Pytest配置和共享fixture

提供测试所需的数据库、客户端等fixture
"""

# 标准库
import asyncio
from typing import AsyncGenerator, Generator

# 第三方库
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# 本地库
from app.main import app
from app.models.base import Base, get_async_db
from app.config.config import settings


# ===== 测试数据库配置 =====
TEST_DATABASE_URL = settings.database_url.replace(
    settings.postgres_db or "cozychat_dev",
    "cozychat_test"
).replace("postgresql://", "postgresql+asyncpg://")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


# ===== Pytest配置 =====
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话
    
    每个测试函数运行前创建所有表，运行后清理
    """
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestSessionLocal() as session:
        yield session
    
    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client() -> TestClient:
    """创建同步测试客户端"""
    return TestClient(app)


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端
    
    覆盖数据库依赖以使用测试数据库
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()
