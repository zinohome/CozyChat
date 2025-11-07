"""
用户管理器测试

测试用户管理器的创建、更新、删除等功能
"""

# 标准库
import pytest
import uuid
from unittest.mock import MagicMock, patch

# 本地库
from app.core.user.manager import UserManager
from app.models.user import User


class TestUserManager:
    """测试用户管理器"""
    
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
    async def test_create_user_success(self, user_manager, test_user_data, sync_db_session):
        """测试：创建用户成功"""
        user = await user_manager.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            role=test_user_data["role"]
        )
        
        assert user is not None
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        assert user.role == test_user_data["role"]
        
        # 清理
        try:
            sync_db_session.delete(user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_manager, test_user_data, sync_db_session):
        """测试：创建重复用户名的用户"""
        # 先创建一个用户
        user1 = await user_manager.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        try:
            # 尝试创建相同用户名的用户
            with pytest.raises((ValueError, Exception)):
                user2 = await user_manager.register_user(
                    username=test_user_data["username"],
                    email=f"different_{test_user_data['email']}",
                    password="DifferentPassword123!"
                )
        finally:
            # 清理
            try:
                sync_db_session.delete(user1)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_manager, test_user_data, sync_db_session):
        """测试：通过ID获取用户"""
        # 创建用户
        user = await user_manager.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        try:
            # 获取用户（使用get_user方法）
            found_user = user_manager.get_user(str(user.id))
            
            assert found_user is not None
            assert found_user.id == user.id
            assert found_user.username == user.username
        finally:
            # 清理
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_user_by_username(self, user_manager, test_user_data, sync_db_session):
        """测试：通过用户名获取用户"""
        # 创建用户
        user = await user_manager.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        try:
            # 获取用户
            found_user = user_manager.get_user_by_username(test_user_data["username"])
            
            assert found_user is not None
            assert found_user.username == test_user_data["username"]
        finally:
            # 清理
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_manager, test_user_data, sync_db_session):
        """测试：更新用户"""
        # 创建用户
        user = await user_manager.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        try:
            # 使用唯一的邮箱地址，避免唯一约束冲突
            import uuid
            unique_email = f"newemail_{uuid.uuid4().hex[:8]}@example.com"
            
            # 更新用户（使用字典参数）
            updated_user = await user_manager.update_user(
                user_id=str(user.id),
                updates={
                    "email": unique_email,
                    "role": "admin"
                }
            )
            
            assert updated_user is not None
            assert updated_user.email == unique_email
            assert updated_user.role == "admin"
        finally:
            # 清理
            try:
                sync_db_session.delete(user)
                sync_db_session.commit()
            except Exception:
                sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_delete_user(self, user_manager, test_user_data, sync_db_session):
        """测试：删除用户（软删除）"""
        # 创建用户
        user = await user_manager.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        user_id = str(user.id)
        
        # 软删除用户（默认）
        deleted = await user_manager.delete_user(user_id, soft_delete=True)
        
        assert deleted is True
        
        # 验证用户已软删除（status变为deleted，但记录仍存在）
        found_user = user_manager.get_user(user_id)
        assert found_user is not None  # 软删除后记录仍存在
        assert found_user.status == "deleted"  # 状态变为deleted
        assert found_user.deleted_at is not None  # deleted_at已设置

