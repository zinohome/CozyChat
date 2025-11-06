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
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
    
    async def test_user_repr(self, db_session: AsyncSession):
        """测试用户__repr__方法"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str
    
    async def test_user_is_authenticated(self, db_session: AsyncSession):
        """测试用户认证属性"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )
        
        assert user.is_authenticated is True
    
    async def test_update_last_login(self, db_session: AsyncSession):
        """测试更新最后登录时间"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        assert user.last_login is None
        
        user.update_last_login()
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
    
    async def test_query_user_by_username(self, db_session: AsyncSession):
        """测试根据用户名查询用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        # 查询用户
        result = await db_session.execute(
            select(User).where(User.username == "testuser")
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.username == "testuser"
        assert found_user.email == "test@example.com"

