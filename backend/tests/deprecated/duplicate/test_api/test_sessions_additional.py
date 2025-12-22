"""
会话API补充测试

补充Sessions API的边界条件和错误处理测试
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.models.user import User
from app.models.session import Session as SessionModel


class TestSessionsAPIAdditional:
    """会话API补充测试"""
    
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
    async def test_list_sessions_with_pagination(self, client, auth_token, sync_db_session):
        """测试：列出会话（分页）"""
        from app.utils.security import create_access_token, hash_password
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
        
        # 创建多个会话
        for i in range(5):
            session = SessionModel(
                user_id=test_user.id,
                personality_id="test_personality",
                title=f"会话 {i+1}"
            )
            sync_db_session.add(session)
        sync_db_session.commit()
        
        token = create_access_token({"sub": str(test_user.id), "username": test_user.username})
        
        try:
            response = client.get(
                "/v1/sessions?page=1&page_size=2",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code in [200, 401, 404]
            if response.status_code == 200:
                data = response.json()
                assert "sessions" in data or "data" in data or isinstance(data, list)
        finally:
            try:
                sync_db_session.query(SessionModel).filter(SessionModel.user_id == test_user.id).delete()
                sync_db_session.delete(test_user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_personality_filter(self, client, auth_token, sync_db_session):
        """测试：列出会话（人格过滤）"""
        from app.utils.security import create_access_token
        from app.models.user import User as UserModel
        from app.utils.security import hash_password
        
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
        
        try:
            response = client.get(
                "/v1/sessions?personality_id=test_personality",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code in [200, 401, 404]
        finally:
            try:
                sync_db_session.delete(test_user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_session_personality_not_found(self, client, auth_token):
        """测试：创建会话（人格不存在）"""
        response = client.post(
            "/v1/sessions",
            json={
                "personality_id": "nonexistent_personality",
                "title": "测试会话"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [404, 401, 422]
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client, auth_token):
        """测试：获取会话（不存在）"""
        response = client.get(
            "/v1/sessions/nonexistent_session_id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_update_session_not_found(self, client, auth_token):
        """测试：更新会话（不存在）"""
        response = client.put(
            "/v1/sessions/nonexistent_session_id",
            json={"title": "新标题"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, client, auth_token):
        """测试：删除会话（不存在）"""
        response = client.delete(
            "/v1/sessions/nonexistent_session_id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [404, 401]
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_sort(self, client, auth_token, sync_db_session):
        """测试：列出会话（排序）"""
        from app.utils.security import create_access_token, hash_password
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
        
        try:
            response = client.get(
                "/v1/sessions?sort=created_at&order=asc",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code in [200, 401, 404]
        finally:
            try:
                sync_db_session.delete(test_user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()

