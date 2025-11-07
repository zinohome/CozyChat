"""
Pytest配置和共享fixture

提供测试所需的数据库、客户端等fixture
"""

# 标准库
import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# 第三方库
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

# 本地库
from app.main import app
from app.models.base import Base, get_async_db, get_sync_db
from app.config.config import settings


# ===== 测试数据库配置 =====
# 确保所有模型都已导入
from app.models import User, UserProfile, Session, Message

# 配置所有映射器，确保关系正确建立
# 这必须在所有模型导入完成后调用
from sqlalchemy.orm import configure_mappers
try:
    configure_mappers()
except Exception as e:
    # 如果配置失败，记录但不阻止测试
    import warnings
    warnings.warn(f"Mapper configuration warning in tests: {e}", UserWarning)

# 使用测试PostgreSQL数据库
TEST_DATABASE_URL = "postgresql://cozychat:passw0rd@192.168.66.10:5432/cozychat_test"
TEST_DATABASE_URL_ASYNC = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# 同步测试引擎
test_sync_engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    pool_pre_ping=True
)

# SQLAlchemy 2.0: sessionmaker直接传入engine作为第一个位置参数
TestSyncSessionLocal = sessionmaker(
    test_sync_engine,
    autoflush=False,
    expire_on_commit=False
)

# 异步测试引擎
test_async_engine = create_async_engine(
    TEST_DATABASE_URL_ASYNC,
    poolclass=NullPool,
    echo=False,
    pool_pre_ping=True
)

# SQLAlchemy 2.0: async_sessionmaker不再使用bind参数，而是直接传入engine
TestAsyncSessionLocal = async_sessionmaker(
    test_async_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)


# ===== Pytest配置 =====
# 注意：当使用pytest-asyncio的auto模式时，不需要手动定义event_loop fixture
# pytest-asyncio会自动管理事件循环
# 如果必须自定义，使用以下代码（但通常不需要）：
# @pytest.fixture(scope="session")
# def event_loop_policy():
#     """设置事件循环策略"""
#     policy = asyncio.get_event_loop_policy()
#     yield policy


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话（异步）
    
    每个测试函数运行前创建所有表，运行后清理
    """
    # 创建所有表
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    # 清理所有表（可选，保留数据用于调试）
    # async with test_async_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def sync_db_session() -> Generator[Session, None, None]:
    """创建测试数据库会话（同步）
    
    每个测试函数运行前创建所有表，运行后清理
    """
    # 创建所有表
    Base.metadata.create_all(test_sync_engine)
    
    # 创建会话
    session = TestSyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    
    # 清理所有表（可选，保留数据用于调试）
    # Base.metadata.drop_all(test_sync_engine)


@pytest.fixture
def client() -> TestClient:
    """创建同步测试客户端"""
    return TestClient(app)


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端
    
    覆盖数据库依赖以使用测试数据库
    """
    async def override_get_async_db():
        yield db_session
    
    def override_get_sync_db():
        session = TestSyncSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_async_db] = override_get_async_db
    app.dependency_overrides[get_sync_db] = override_get_sync_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


# ===== Mock外部服务 =====

@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI客户端"""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.audio.transcriptions.create = AsyncMock()
    mock_client.audio.speech.create = AsyncMock()
    mock_client.models.list = AsyncMock()
    
    # 默认返回值
    mock_client.chat.completions.create.return_value = MagicMock(
        id="test-123",
        choices=[MagicMock(
            message=MagicMock(role="assistant", content="Test response"),
            finish_reason="stop"
        )],
        usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        model="gpt-3.5-turbo"
    )
    
    return mock_client


@pytest.fixture
def mock_chromadb(mocker):
    """Mock ChromaDB客户端"""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    
    # Mock collection方法
    mock_collection.add = Mock()
    mock_collection.query = Mock(return_value={
        "ids": [["id1", "id2"]],
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{"user_id": "user1"}, {"user_id": "user2"}]],
        "distances": [[0.1, 0.2]]
    })
    mock_collection.delete = Mock()
    mock_collection.get = Mock(return_value={
        "ids": ["id1"],
        "documents": ["doc1"],
        "metadatas": [{"user_id": "user1"}]
    })
    mock_collection.count = Mock(return_value=10)
    
    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
    mock_client.create_collection = Mock(return_value=mock_collection)
    mock_client.get_collection = Mock(return_value=mock_collection)
    
    return mock_client, mock_collection


@pytest.fixture
def mock_qdrant_client(mocker):
    """Mock Qdrant客户端"""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    
    # Mock Qdrant方法
    mock_collection.scroll = Mock(return_value=([], None))
    mock_collection.search = Mock(return_value=[
        MagicMock(id="id1", score=0.9, payload={"user_id": "user1"})
    ])
    mock_collection.upsert = Mock()
    mock_collection.delete = Mock()
    mock_collection.count = Mock(return_value=10)
    
    mock_client.get_collection = Mock(return_value=mock_collection)
    mock_client.create_collection = Mock()
    mock_client.collection_exists = Mock(return_value=True)
    
    return mock_client, mock_collection


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis客户端"""
    mock_client = MagicMock()
    mock_client.ping = Mock(return_value=True)
    mock_client.get = Mock(return_value=None)
    mock_client.set = Mock(return_value=True)
    mock_client.delete = Mock(return_value=1)
    mock_client.exists = Mock(return_value=False)
    mock_client.keys = Mock(return_value=[])
    mock_client.close = Mock()
    
    return mock_client


@pytest.fixture
def temp_chromadb_dir():
    """创建临时ChromaDB目录"""
    temp_dir = tempfile.mkdtemp(prefix="test_chromadb_")
    yield temp_dir
    # 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


# ===== 测试用户和数据 =====

@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "display_name": "Test User"
    }


@pytest.fixture
def test_personality_data():
    """测试人格数据"""
    return {
        "id": "test_personality",
        "name": "Test Personality",
        "description": "Test personality for testing",
        "version": "1.0.0",
        "config": {
            "ai": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7
            },
            "memory": {
                "enabled": True,
                "save_mode": "both"
            },
            "tools": {
                "enabled": True,
                "allowed_tools": ["calculator"]
            }
        }
    }


# ===== 环境变量配置 =====

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """设置测试环境变量"""
    # 测试数据库配置
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    
    # Redis配置（测试时使用Mock）
    monkeypatch.setenv("REDIS_URL", "redis://192.168.66.10:6379/0")
    monkeypatch.setenv("REDIS_PASSWORD", "redis_passw0rd")
    
    # Qdrant配置
    monkeypatch.setenv("QDRANT_URL", "http://192.168.66.10:6333")
    
    # ChromaDB配置（使用临时目录）
    temp_dir = tempfile.mkdtemp(prefix="test_chromadb_")
    monkeypatch.setenv("CHROMADB_PERSIST_DIR", temp_dir)
    
    yield
    
    # 清理临时目录
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


# ===== 测试标记 =====
# 使用pytest标记来区分不同类型的测试

@pytest.fixture
def chromadb_memory_engine():
    """ChromaDB记忆引擎fixture"""
    from app.engines.memory.chromadb_engine import ChromaDBMemoryEngine
    temp_dir = tempfile.mkdtemp(prefix="test_chromadb_")
    engine = ChromaDBMemoryEngine(persist_directory=temp_dir)
    yield engine
    # 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def qdrant_memory_engine():
    """Qdrant记忆引擎fixture（如果已实现）"""
    # TODO: 如果实现了Qdrant引擎，这里返回Qdrant实例
    # 目前返回None，表示未实现
    return None
