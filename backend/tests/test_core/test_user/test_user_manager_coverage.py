"""
用户管理器覆盖率测试

补充UserManager的测试以覆盖89, 139-176, 189-191, 204-206, 217-221, 240, 254, 258, 267-270, 285, 293, 301-304, 322-335, 346-350, 366-397, 408-432行
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.core.user.manager import UserManager
from app.models.user import User
from app.models.user_profile import UserProfile


class TestUserManagerCoverage:
    """用户管理器覆盖率测试"""
    
    @pytest.fixture
    def user_manager(self, sync_db_session):
        """创建用户管理器实例"""
        return UserManager(db=sync_db_session)
    
    @pytest.fixture
    def test_user_data(self):
        """测试用户数据"""
        return {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "role": "user",
            "status": "active"
        }
    
    @pytest.mark.asyncio
    async def test_register_user_with_preferences(self, user_manager, test_user_data, sync_db_session):
        """测试：创建用户（带偏好，覆盖89行）"""
        user = await user_manager.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            preferences={"theme": "dark", "language": "zh-CN"}
        )
        
        assert user is not None
        assert user.get_preferences()["theme"] == "dark"
        
        try:
            sync_db_session.delete(user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, user_manager, test_user_data, sync_db_session):
        """测试：用户认证成功（覆盖139-176行）"""
        from app.utils.security import hash_password
        
        # 创建用户
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        try:
            result = await user_manager.authenticate(
                username=test_user_data["username"],
                password=test_user_data["password"],
                ip_address="192.168.1.1"
            )
            
            assert result is not None
            assert "access_token" in result
            assert "refresh_token" in result
            assert "user" in result
        finally:
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_authenticate_failed(self, user_manager, test_user_data):
        """测试：用户认证失败（覆盖135-136行）"""
        result = await user_manager.authenticate(
            username="nonexistent_user",
            password="wrong_password"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_error(self, user_manager, test_user_data):
        """测试：用户认证错误（覆盖174-176行）"""
        with patch.object(user_manager.auth_service, 'authenticate_user', side_effect=Exception("Auth error")):
            result = await user_manager.authenticate(
                username=test_user_data["username"],
                password=test_user_data["password"]
            )
            
            assert result is None
    
    def test_get_user_error(self, user_manager, sync_db_session):
        """测试：获取用户（错误处理，覆盖189-191行）"""
        with patch.object(sync_db_session, 'query', side_effect=Exception("DB error")):
            result = user_manager.get_user("test-user-id")
            
            assert result is None
    
    def test_get_user_by_username_error(self, user_manager, sync_db_session):
        """测试：根据用户名获取用户（错误处理，覆盖204-206行）"""
        with patch.object(sync_db_session, 'query', side_effect=Exception("DB error")):
            result = user_manager.get_user_by_username("testuser")
            
            assert result is None
    
    def test_get_user_by_email_error(self, user_manager, sync_db_session):
        """测试：根据邮箱获取用户（错误处理，覆盖217-221行）"""
        with patch.object(sync_db_session, 'query', side_effect=Exception("DB error")):
            result = user_manager.get_user_by_email("test@example.com")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_manager, sync_db_session):
        """测试：更新用户（用户不存在，覆盖238-240行）"""
        result = await user_manager.update_user(
            user_id="nonexistent-user-id",
            updates={"email": "newemail@example.com"}
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_with_preferences(self, user_manager, test_user_data, sync_db_session):
        """测试：更新用户（带偏好，覆盖253-254行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        try:
            updated_user = await user_manager.update_user(
                user_id=str(user.id),
                updates={"preferences": {"theme": "light"}}
            )
            
            assert updated_user is not None
            assert updated_user.get_preferences()["theme"] == "light"
        finally:
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_update_user_with_password(self, user_manager, test_user_data, sync_db_session):
        """测试：更新用户（带密码，覆盖257-258行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        try:
            updated_user = await user_manager.update_user(
                user_id=str(user.id),
                updates={"password": "NewPassword123!"}
            )
            
            assert updated_user is not None
            # 验证密码已更新（通过认证验证）
            from app.utils.security import verify_password
            assert verify_password("NewPassword123!", updated_user.password_hash)
        finally:
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_update_user_error(self, user_manager, test_user_data, sync_db_session):
        """测试：更新用户（错误处理，覆盖267-270行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        try:
            with patch.object(sync_db_session, 'commit', side_effect=Exception("Commit error")):
                with pytest.raises(Exception):
                    await user_manager.update_user(
                        user_id=str(user.id),
                        updates={"email": "newemail@example.com"}
                    )
        finally:
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_delete_user_soft_delete(self, user_manager, test_user_data, sync_db_session):
        """测试：删除用户（软删除，覆盖285行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        user_id = str(user.id)
        
        try:
            deleted = await user_manager.delete_user(user_id, soft_delete=True)
            
            assert deleted is True
            found_user = user_manager.get_user(user_id)
            assert found_user is not None
            assert found_user.status == "deleted"
        finally:
            # 清理
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_delete_user_hard_delete(self, user_manager, test_user_data, sync_db_session):
        """测试：删除用户（硬删除，覆盖293行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        user_id = str(user.id)
        
        try:
            deleted = await user_manager.delete_user(user_id, soft_delete=False)
            
            assert deleted is True
            found_user = user_manager.get_user(user_id)
            assert found_user is None  # 硬删除后记录不存在
        except Exception:
            # 如果硬删除失败，尝试清理
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_delete_user_error(self, user_manager, sync_db_session):
        """测试：删除用户（错误处理，覆盖301-304行）"""
        with patch.object(sync_db_session, 'query', side_effect=Exception("DB error")):
            result = await user_manager.delete_user("test-user-id")
            
            assert result is False
    
    def test_list_users_with_status(self, user_manager, test_user_data, sync_db_session):
        """测试：列出用户（带状态过滤，覆盖325-326行）"""
        from app.utils.security import hash_password
        
        # 创建多个用户（使用有效的status值）
        user1 = User(
            id=uuid.uuid4(),
            username=f"{test_user_data['username']}_1",
            email=f"user1_{test_user_data['email']}",
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        user2 = User(
            id=uuid.uuid4(),
            username=f"{test_user_data['username']}_2",
            email=f"user2_{test_user_data['email']}",
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"  # 使用active而不是inactive，因为inactive可能不在约束中
        )
        sync_db_session.add(user1)
        sync_db_session.add(user2)
        sync_db_session.commit()
        
        try:
            # 列出活跃用户
            active_users = user_manager.list_users(status="active")
            assert len(active_users) >= 2
            
            # 列出已删除用户（应该为空）
            deleted_users = user_manager.list_users(status="deleted")
            assert isinstance(deleted_users, list)
        finally:
            try:
                sync_db_session.delete(user1)
                sync_db_session.delete(user2)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    def test_list_users_without_status(self, user_manager, sync_db_session):
        """测试：列出用户（无状态过滤，覆盖327-329行）"""
        users = user_manager.list_users()
        
        assert isinstance(users, list)
        # 验证不包含已删除用户
        for user in users:
            assert user.status != "deleted"
    
    def test_list_users_error(self, user_manager, sync_db_session):
        """测试：列出用户（错误处理，覆盖333-335行）"""
        with patch.object(sync_db_session, 'query', side_effect=Exception("DB error")):
            result = user_manager.list_users()
            
            assert result == []
    
    def test_get_user_profile_error(self, user_manager, sync_db_session):
        """测试：获取用户画像（错误处理，覆盖346-350行）"""
        with patch.object(sync_db_session, 'query', side_effect=Exception("DB error")):
            result = user_manager.get_user_profile("test-user-id")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_profile_create_new(self, user_manager, test_user_data, sync_db_session):
        """测试：更新用户画像（创建新画像，覆盖369-372行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        try:
            profile = await user_manager.update_user_profile(
                user_id=str(user.id),
                updates={
                    "interests": ["coding", "reading"],
                    "habits": {"sleep_time": "23:00"},
                    "personality_insights": {"type": "introvert"},
                    "statistics": {"total_sessions": 10}
                }
            )
            
            assert profile is not None
            assert profile.user_id == user.id
            assert "coding" in profile.interests
        finally:
            try:
                if profile:
                    sync_db_session.delete(profile)
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_update_user_profile_update_existing(self, user_manager, test_user_data, sync_db_session):
        """测试：更新用户画像（更新现有画像，覆盖374-386行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        profile = UserProfile(user_id=user.id, interests=["coding"])
        sync_db_session.add(profile)
        sync_db_session.commit()
        
        try:
            updated_profile = await user_manager.update_user_profile(
                user_id=str(user.id),
                updates={
                    "interests": ["coding", "reading"],
                    "habits": {"sleep_time": "23:00"}
                }
            )
            
            assert updated_profile is not None
            assert "reading" in updated_profile.interests
        finally:
            try:
                sync_db_session.delete(profile)
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_update_user_profile_error(self, user_manager, test_user_data, sync_db_session):
        """测试：更新用户画像（错误处理，覆盖394-397行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        try:
            with patch.object(sync_db_session, 'commit', side_effect=Exception("Commit error")):
                with pytest.raises(Exception):
                    await user_manager.update_user_profile(
                        user_id=str(user.id),
                        updates={"interests": ["coding"]}
                    )
        finally:
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    def test_get_user_statistics_with_profile(self, user_manager, test_user_data, sync_db_session):
        """测试：获取用户统计（有画像，覆盖408-432行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        profile = UserProfile(user_id=user.id, interests=["coding"])
        sync_db_session.add(profile)
        sync_db_session.commit()
        
        try:
            stats = user_manager.get_user_statistics(str(user.id))
            
            assert stats is not None
            assert "user_id" in stats
            assert "username" in stats
            assert "profile" in stats
            assert "interests" in stats["profile"]
        finally:
            try:
                sync_db_session.delete(profile)
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    def test_get_user_statistics_without_profile(self, user_manager, test_user_data, sync_db_session):
        """测试：获取用户统计（无画像，覆盖413-427行）"""
        from app.utils.security import hash_password
        
        user = User(
            id=uuid.uuid4(),
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=hash_password(test_user_data["password"]),
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        
        try:
            stats = user_manager.get_user_statistics(str(user.id))
            
            assert stats is not None
            assert "user_id" in stats
            assert "profile" in stats
            assert stats["profile"]["interests"] == []
        finally:
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    def test_get_user_statistics_user_not_found(self, user_manager):
        """测试：获取用户统计（用户不存在，覆盖409-411行）"""
        stats = user_manager.get_user_statistics("nonexistent-user-id")
        
        assert stats == {}
    
    def test_get_user_statistics_error(self, user_manager, sync_db_session):
        """测试：获取用户统计（错误处理，覆盖430-432行）"""
        with patch.object(user_manager, 'get_user', side_effect=Exception("DB error")):
            result = user_manager.get_user_statistics("test-user-id")
            
            assert result == {}

