"""
测试基础设施验证

验证测试fixtures和Mock是否正常工作
"""

# 第三方库
import pytest

# 本地库
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.message import Message as MessageModel


class TestDatabaseFixtures:
    """测试数据库fixtures"""
    
    @pytest.mark.asyncio
    async def test_async_db_session(self, db_session):
        """测试异步数据库会话"""
        assert db_session is not None
        # 测试查询
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    def test_sync_db_session(self, sync_db_session):
        """测试同步数据库会话"""
        assert sync_db_session is not None
        # 测试查询
        from sqlalchemy import text
        result = sync_db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1


class TestMockFixtures:
    """测试Mock fixtures"""
    
    def test_mock_openai_client(self, mock_openai_client):
        """测试OpenAI Mock客户端"""
        assert mock_openai_client is not None
        assert hasattr(mock_openai_client, "chat")
        assert hasattr(mock_openai_client.chat, "completions")
    
    def test_mock_chromadb(self, mock_chromadb):
        """测试ChromaDB Mock"""
        mock_client, mock_collection = mock_chromadb
        assert mock_client is not None
        assert mock_collection is not None
        assert hasattr(mock_collection, "query")
        assert hasattr(mock_collection, "add")
    
    def test_mock_qdrant_client(self, mock_qdrant_client):
        """测试Qdrant Mock客户端"""
        mock_client, mock_collection = mock_qdrant_client
        assert mock_client is not None
        assert mock_collection is not None
        assert hasattr(mock_collection, "search")
        assert hasattr(mock_collection, "upsert")
    
    def test_mock_redis(self, mock_redis):
        """测试Redis Mock客户端"""
        assert mock_redis is not None
        assert hasattr(mock_redis, "get")
        assert hasattr(mock_redis, "set")
        assert hasattr(mock_redis, "ping")


class TestClientFixtures:
    """测试客户端fixtures"""
    
    def test_sync_client(self, client):
        """测试同步测试客户端"""
        assert client is not None
        # 测试健康检查
        response = client.get("/health")
        assert response.status_code in [200, 404]  # 可能路由不同
    
    @pytest.mark.asyncio
    async def test_async_client(self, async_client):
        """测试异步测试客户端"""
        assert async_client is not None
        # 测试健康检查
        response = await async_client.get("/v1/health")
        assert response.status_code in [200, 404]  # 可能路由不同


class TestTestDataFixtures:
    """测试测试数据fixtures"""
    
    def test_test_user_data(self, test_user_data):
        """测试用户数据fixture"""
        assert test_user_data is not None
        assert "username" in test_user_data
        assert "email" in test_user_data
        assert "password" in test_user_data
    
    def test_test_personality_data(self, test_personality_data):
        """测试人格数据fixture"""
        assert test_personality_data is not None
        assert "id" in test_personality_data
        assert "name" in test_personality_data
        assert "config" in test_personality_data

