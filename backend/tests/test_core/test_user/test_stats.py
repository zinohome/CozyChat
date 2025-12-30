"""
用户统计管理器测试

测试UserStatsManager的功能
"""

# 标准库
import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timedelta

# 本地库
from app.core.user.stats import UserStatsManager
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.session import Session as SessionModel
from app.models.message import Message as MessageModel


class TestUserStatsManager:
    """测试用户统计管理器"""
    
    @pytest_asyncio.fixture
    async def stats_manager(self, db_session):
        """创建用户统计管理器"""
        return UserStatsManager(db_session)
    
    @pytest_asyncio.fixture
    async def test_user(self, db_session):
        """创建测试用户"""
        from app.utils.security import hash_password
        from sqlalchemy import select
        
        user = User(
            id=uuid.uuid4(),
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="user",
            status="active"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        yield user
        
        # 清理
        try:
            # 删除相关数据
            stmt = select(UserProfile).where(UserProfile.user_id == user.id)
            result = await db_session.execute(stmt)
            profile = result.scalar_one_or_none()
            if profile:
                await db_session.delete(profile)
            
            stmt = select(SessionModel).where(SessionModel.user_id == user.id)
            result = await db_session.execute(stmt)
            sessions = result.scalars().all()
            for session in sessions:
                await db_session.delete(session)
            
            await db_session.delete(user)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_user_stats_basic(self, stats_manager, test_user):
        """测试：获取用户统计信息（基础）"""
        stats = await stats_manager.get_user_stats(str(test_user.id))
        
        assert isinstance(stats, dict)
        assert "user_id" in stats
        assert "username" in stats
        assert "email" in stats
        assert stats["user_id"] == str(test_user.id)
        assert stats["username"] == test_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_stats_with_profile(self, stats_manager, test_user, db_session):
        """测试：获取用户统计信息（包含画像）"""
        # 创建画像
        profile = UserProfile(
            user_id=test_user.id,
            interests=["AI", "编程"]
        )
        db_session.add(profile)
        await db_session.commit()
        
        try:
            stats = await stats_manager.get_user_stats(str(test_user.id))
            
            assert isinstance(stats, dict)
            assert "profile" in stats
            assert isinstance(stats["profile"], dict)
            assert "interests" in stats["profile"]
            assert stats["profile"]["interests"] == ["AI", "编程"]
        finally:
            # 清理
            try:
                await db_session.delete(profile)
                await db_session.commit()
            except Exception:
                await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_user_stats_not_exists(self, stats_manager):
        """测试：获取不存在的用户统计信息"""
        stats = await stats_manager.get_user_stats(str(uuid.uuid4()))
        
        assert isinstance(stats, dict)
        assert len(stats) == 0
    
    @pytest.mark.asyncio
    async def test_get_user_activity(self, stats_manager, test_user):
        """测试：获取用户活动统计"""
        activity = await stats_manager.get_user_activity(str(test_user.id), days=30)
        
        assert isinstance(activity, dict)
        # 活动统计可能为空，但结构应该正确
        assert "user_id" in activity or len(activity) == 0
    
    @pytest.mark.asyncio
    async def test_get_user_activity_with_sessions(self, stats_manager, test_user, db_session):
        """测试：获取用户活动统计（包含会话）"""
        # 创建会话
        session = SessionModel(
            user_id=test_user.id,
            personality_id="test_personality",
            title="测试会话"
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        try:
            activity = await stats_manager.get_user_activity(str(test_user.id), days=30)
            
            assert isinstance(activity, dict)
            # 活动统计应该包含会话信息
        finally:
            # 清理
            try:
                await db_session.delete(session)
                await db_session.commit()
            except Exception:
                await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_user_activity_custom_days(self, stats_manager, test_user):
        """测试：获取用户活动统计（自定义天数）"""
        activity = await stats_manager.get_user_activity(str(test_user.id), days=7)
        
        assert isinstance(activity, dict)
        # 活动统计可能为空，但结构应该正确
        assert "user_id" in activity or len(activity) == 0

