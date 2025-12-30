"""
用户画像管理器测试

测试UserProfileManager的功能
"""

# 标准库
import pytest
import pytest_asyncio
import uuid

# 本地库
from app.core.user.profile import UserProfileManager
from app.models.user import User
from app.models.user_profile import UserProfile


class TestUserProfileManager:
    """测试用户画像管理器"""
    
    @pytest_asyncio.fixture
    async def profile_manager(self, db_session):
        """创建用户画像管理器"""
        return UserProfileManager(db_session)
    
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
            # 先删除profile（如果存在）
            stmt = select(UserProfile).where(UserProfile.user_id == user.id)
            result = await db_session.execute(stmt)
            profile = result.scalar_one_or_none()
            if profile:
                await db_session.delete(profile)
            await db_session.delete(user)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_profile_not_exists(self, profile_manager, test_user):
        """测试：获取不存在的画像"""
        profile = await profile_manager.get_profile(str(test_user.id))
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_create_profile(self, profile_manager, test_user, db_session):
        """测试：创建画像"""
        profile = await profile_manager.create_or_update_profile(
            user_id=str(test_user.id),
            interests=["AI", "编程", "技术"]
        )
        
        assert profile is not None
        assert profile.user_id == test_user.id
        assert profile.interests == ["AI", "编程", "技术"]
        
        # 清理
        try:
            await db_session.delete(profile)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_update_profile(self, profile_manager, test_user, db_session):
        """测试：更新画像"""
        # 先创建画像
        profile = await profile_manager.create_or_update_profile(
            user_id=str(test_user.id),
            interests=["AI", "编程"]
        )
        await db_session.commit()
        
        # 更新画像
        updated_profile = await profile_manager.create_or_update_profile(
            user_id=str(test_user.id),
            interests=["AI", "编程", "技术", "机器学习"]
        )
        await db_session.commit()
        
        assert updated_profile is not None
        assert updated_profile.user_id == test_user.id
        assert updated_profile.interests == ["AI", "编程", "技术", "机器学习"]
        
        # 清理
        try:
            await db_session.delete(updated_profile)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_or_update_profile_with_habits(self, profile_manager, test_user, db_session):
        """测试：创建或更新画像（包含习惯）"""
        profile = await profile_manager.create_or_update_profile(
            user_id=str(test_user.id),
            interests=["AI"],
            habits={"most_active_time": "morning", "avg_session_duration_minutes": 30}
        )
        await db_session.commit()
        
        assert profile is not None
        assert profile.get_habits()["most_active_time"] == "morning"
        assert profile.get_habits()["avg_session_duration_minutes"] == 30
        
        # 清理
        try:
            await db_session.delete(profile)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_or_update_profile_with_insights(self, profile_manager, test_user, db_session):
        """测试：创建或更新画像（包含洞察）"""
        profile = await profile_manager.create_or_update_profile(
            user_id=str(test_user.id),
            interests=["AI"],
            personality_insights={"communication_style": "formal", "question_types": ["technical"]}
        )
        await db_session.commit()
        
        assert profile is not None
        insights = profile.get_personality_insights()
        assert insights["communication_style"] == "formal"
        assert insights["question_types"] == ["technical"]
        
        # 清理
        try:
            await db_session.delete(profile)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_or_update_profile_with_statistics(self, profile_manager, test_user, db_session):
        """测试：创建或更新画像（包含统计）"""
        profile = await profile_manager.create_or_update_profile(
            user_id=str(test_user.id),
            interests=["AI"],
            statistics={"total_sessions": 10, "total_messages": 100}
        )
        await db_session.commit()
        
        assert profile is not None
        stats = profile.get_statistics()
        assert stats["total_sessions"] == 10
        assert stats["total_messages"] == 100
        
        # 清理
        try:
            await db_session.delete(profile)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_profile_exists(self, profile_manager, test_user, db_session):
        """测试：获取存在的画像"""
        # 先创建画像
        created_profile = await profile_manager.create_or_update_profile(
            user_id=str(test_user.id),
            interests=["AI", "编程"]
        )
        await db_session.commit()
        
        # 获取画像
        profile = await profile_manager.get_profile(str(test_user.id))
        
        assert profile is not None
        assert profile.user_id == test_user.id
        assert profile.interests == ["AI", "编程"]
        
        # 清理
        try:
            await db_session.delete(profile)
            await db_session.commit()
        except Exception:
            await db_session.rollback()

