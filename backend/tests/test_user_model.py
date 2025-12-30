"""
用户模型测试

测试User数据模型的创建和操作
"""

# 标准库
from datetime import datetime

# 第三方库
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.models.user import User


@pytest.mark.asyncio
class TestUserModel:
    """测试User模型"""
    
    async def test_create_user(self, db_session: AsyncSession):
        """测试创建用户"""
        import uuid
        # 使用唯一的用户名和邮箱，避免重复键错误
        unique_id = uuid.uuid4().hex[:8]
        user = User(
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="hashed_password_123",
            display_name="Test User"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == f"testuser_{unique_id}"
        assert user.email == f"test_{unique_id}@example.com"
        assert user.is_active is True
        assert user.role == "user"  # 默认角色
        assert user.created_at is not None
        
        # 清理
        await db_session.delete(user)
        await db_session.commit()
    
    async def test_user_repr(self, db_session: AsyncSession):
        """测试用户__repr__方法"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        user = User(
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="hashed_password_123"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        repr_str = repr(user)
        assert f"testuser_{unique_id}" in repr_str
        assert f"test_{unique_id}@example.com" in repr_str
        
        # 清理
        await db_session.delete(user)
        await db_session.commit()
    
    async def test_user_is_authenticated(self, db_session: AsyncSession):
        """测试用户认证属性"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123",
            status="active"  # 必须设置为active才能通过is_authenticated检查
        )
        
        assert user.is_authenticated is True
    
    async def test_update_last_login(self, db_session: AsyncSession):
        """测试更新最后登录时间"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        user = User(
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="hashed_password_123"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        assert user.last_login_at is None
        
        user.update_last_login()
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.last_login_at is not None
        assert isinstance(user.last_login_at, datetime)
        
        # 清理
        await db_session.delete(user)
        await db_session.commit()
    
    async def test_query_user_by_username(self, db_session: AsyncSession):
        """测试根据用户名查询用户"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        username = f"testuser_{unique_id}"
        email = f"test_{unique_id}@example.com"
        
        user = User(
            username=username,
            email=email,
            password_hash="hashed_password_123"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        # 查询用户
        result = await db_session.execute(
            select(User).where(User.username == username)
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.username == username
        assert found_user.email == email
        
        # 清理
        await db_session.delete(user)
        await db_session.commit()

