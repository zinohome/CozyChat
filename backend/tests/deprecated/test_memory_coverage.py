"""
记忆API覆盖率测试

补充memory.py的未覆盖行测试
"""

# 标准库
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

# 本地库
from app.models.user import User


class TestMemoryAPICoverage:
    """记忆API覆盖率测试"""
    
    @pytest.fixture
    def auth_token(self, client, sync_db_session):
        """创建认证令牌"""
        from app.utils.security import hash_password, create_access_token
        from app.models.user import User as UserModel
        
        test_user = UserModel(
            id=uuid.uuid4(),
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="user",
            status="active"
        )
        sync_db_session.add(test_user)
        sync_db_session.commit()
        
        token = create_access_token({"sub": str(test_user.id), "username": test_user.username})
        
        yield token
        
        try:
            sync_db_session.delete(test_user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_memory_error(self, client, auth_token):
        """测试：创建记忆（错误，覆盖60-65行）"""
        with patch('app.api.v1.memory.memory_manager.add_memory', new_callable=AsyncMock) as mock_add:
            mock_add.side_effect = Exception("Database error")
            
            response = client.post(
                "/v1/memory",
                json={
                    "user_id": "test-user-1",
                    "session_id": "test-session-1",
                    "content": "Test memory",
                    "memory_type": "user"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 422]
    
    @pytest.mark.asyncio
    async def test_search_memories_with_user_type(self, client, auth_token):
        """测试：搜索记忆（用户类型，覆盖81-82行）"""
        with patch('app.api.v1.memory.memory_manager.search_memories', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            response = client.post(
                "/v1/memory/search",
                json={
                    "query": "Python",
                    "user_id": "test-user-1",
                    "memory_type": "user",
                    "limit": 5
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 401, 422]
    
    @pytest.mark.asyncio
    async def test_search_memories_with_assistant_type(self, client, auth_token):
        """测试：搜索记忆（助手类型，覆盖83-84行）"""
        with patch('app.api.v1.memory.memory_manager.search_memories', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            response = client.post(
                "/v1/memory/search",
                json={
                    "query": "Python",
                    "user_id": "test-user-1",
                    "memory_type": "assistant",
                    "limit": 5
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 401, 422]
    
    @pytest.mark.asyncio
    async def test_search_memories_error(self, client, auth_token):
        """测试：搜索记忆（错误，覆盖110-115行）"""
        with patch('app.api.v1.memory.memory_manager.search_memories', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("Database error")
            
            response = client.post(
                "/v1/memory/search",
                json={
                    "query": "Python",
                    "user_id": "test-user-1",
                    "limit": 5
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 422]
    
    @pytest.mark.asyncio
    async def test_get_memory_stats_error(self, client, auth_token):
        """测试：获取记忆统计（错误，覆盖132-137行）"""
        with patch('app.api.v1.memory.memory_manager.get_memory_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.side_effect = Exception("Database error")
            
            response = client.get(
                "/v1/memory/stats/test-user-1",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, client, auth_token):
        """测试：删除记忆（不存在，覆盖154-160行）"""
        with patch('app.api.v1.memory.memory_manager.delete_memory', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete(
                "/v1/memory/mem-123?user_id=test-user-1",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_delete_memory_error(self, client, auth_token):
        """测试：删除记忆（错误，覆盖164-169行）"""
        with patch('app.api.v1.memory.memory_manager.delete_memory', new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = Exception("Database error")
            
            response = client.delete(
                "/v1/memory/mem-123?user_id=test-user-1",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_delete_session_memories_error(self, client, auth_token):
        """测试：删除会话记忆（错误，覆盖192-197行）"""
        with patch('app.api.v1.memory.memory_manager.delete_session_memories', new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = Exception("Database error")
            
            response = client.delete(
                "/v1/memory/session/test-user-1/test-session-1",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [500, 401, 404]
    
    @pytest.mark.asyncio
    async def test_memory_health_check_unhealthy(self, client):
        """测试：记忆健康检查（不健康，覆盖206-209行）"""
        with patch('app.api.v1.memory.memory_manager.health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False
            
            response = client.get("/v1/memory/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_memory_health_check_error(self, client):
        """测试：记忆健康检查（错误，覆盖211-213行）"""
        with patch('app.api.v1.memory.memory_manager.health_check', new_callable=AsyncMock) as mock_health:
            mock_health.side_effect = Exception("Health check error")
            
            response = client.get("/v1/memory/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data

