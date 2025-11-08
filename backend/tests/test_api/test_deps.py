"""
依赖注入测试

测试API依赖注入的功能
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import (
    get_db,
    get_sync_session,
    get_current_user,
    get_current_user_from_token,
    get_current_active_user,
    require_admin
)
from app.models.user import User
from app.core.user.auth import AuthService


class TestDeps:
    """测试依赖注入"""
    
    @pytest.fixture
    def test_user(self, sync_db_session):
        """测试用户"""
        user = User(
            id=uuid.uuid4(),
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            role="user",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)
        yield user
        try:
            sync_db_session.delete(user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.fixture
    def admin_user(self, sync_db_session):
        """管理员用户"""
        user = User(
            id=uuid.uuid4(),
            username=f"admin_{uuid.uuid4().hex[:8]}",
            email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            role="admin",
            status="active"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)
        yield user
        try:
            sync_db_session.delete(user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.fixture
    def inactive_user(self, sync_db_session):
        """未激活用户"""
        user = User(
            id=uuid.uuid4(),
            username=f"inactive_{uuid.uuid4().hex[:8]}",
            email=f"inactive_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            role="user",
            status="suspended"
        )
        sync_db_session.add(user)
        sync_db_session.commit()
        sync_db_session.refresh(user)
        yield user
        try:
            sync_db_session.delete(user)
            sync_db_session.commit()
        except Exception:
            sync_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_get_db(self, db_session):
        """测试：获取数据库会话（异步）"""
        async for session in get_db():
            assert session is not None
            # 验证会话类型
            from sqlalchemy.ext.asyncio import AsyncSession
            assert isinstance(session, AsyncSession)
            break
    
    def test_get_sync_session(self, sync_db_session):
        """测试：获取同步数据库会话"""
        for session in get_sync_session():
            assert session is not None
            # 验证会话类型
            from sqlalchemy.orm import Session
            assert isinstance(session, Session)
            break
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, test_user, sync_db_session, mocker):
        """测试：获取当前用户成功"""
        # Mock credentials
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"
        
        # Mock AuthService
        mock_auth_service = MagicMock(spec=AuthService)
        mock_auth_service.get_current_user_from_token = MagicMock(return_value=test_user)
        mocker.patch('app.api.deps.AuthService', return_value=mock_auth_service)
        
        result = await get_current_user(
            credentials=mock_credentials,
            db=sync_db_session
        )
        
        assert result == test_user
        mock_auth_service.get_current_user_from_token.assert_called_once_with(
            sync_db_session, "valid_token"
        )
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self, sync_db_session):
        """测试：获取当前用户（无凭证）"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                credentials=None,
                db=sync_db_session
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "未提供认证令牌" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, sync_db_session, mocker):
        """测试：获取当前用户（无效token）"""
        # Mock credentials
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"
        
        # Mock AuthService返回None
        mock_auth_service = MagicMock(spec=AuthService)
        mock_auth_service.get_current_user_from_token = MagicMock(return_value=None)
        mocker.patch('app.api.deps.AuthService', return_value=mock_auth_service)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                credentials=mock_credentials,
                db=sync_db_session
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "无效的认证令牌" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_auth_error(self, sync_db_session, mocker):
        """测试：获取当前用户（认证错误）"""
        # Mock credentials
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"
        
        # Mock AuthService抛出异常
        mock_auth_service = MagicMock(spec=AuthService)
        mock_auth_service.get_current_user_from_token = MagicMock(side_effect=Exception("Auth error"))
        mocker.patch('app.api.deps.AuthService', return_value=mock_auth_service)
        mocker.patch('app.api.deps.logger.error')
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                credentials=mock_credentials,
                db=sync_db_session
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "认证失败" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_success(self, test_user, sync_db_session, mocker):
        """测试：从token获取当前用户成功"""
        from app.utils.security import create_access_token
        
        # 确保用户已提交到数据库（刷新以确保数据持久化）
        sync_db_session.commit()
        sync_db_session.refresh(test_user)
        
        # 再次提交以确保数据在数据库中
        sync_db_session.commit()
        
        token = create_access_token({"sub": str(test_user.id), "username": test_user.username})
        
        # get_current_user_from_token会创建新的数据库会话，需要确保用户在新会话中可用
        # 由于get_current_user_from_token内部使用get_sync_session()创建新会话，
        # 而新会话会查询数据库，所以用户应该能被找到
        # 但get_sync_session()使用的是SyncSessionLocal，可能与测试数据库不同
        # 我们需要mock get_sync_session来返回测试会话
        with patch('app.api.deps.get_sync_session') as mock_get_sync_session:
            mock_get_sync_session.return_value = iter([sync_db_session])
            result = await get_current_user_from_token(token)
            
            assert result is not None
            assert str(result.id) == str(test_user.id)
            assert result.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_invalid_token(self, mocker):
        """测试：从token获取当前用户（无效token）"""
        # Mock decode_token返回None
        mocker.patch('app.api.deps.decode_token', return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_no_user_id(self, mocker):
        """测试：从token获取当前用户（无user_id）"""
        # Mock decode_token返回无sub的payload
        mocker.patch('app.api.deps.decode_token', return_value={"username": "test"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token("token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_user_not_found(self, sync_db_session, mocker):
        """测试：从token获取当前用户（用户不存在）"""
        from app.utils.security import create_access_token
        
        # 使用不存在的用户ID
        fake_user_id = str(uuid.uuid4())
        token = create_access_token({"sub": fake_user_id, "username": "nonexistent"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token(token)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_error(self, mocker):
        """测试：从token获取当前用户（错误处理）"""
        # Mock decode_token抛出异常
        mocker.patch('app.api.deps.decode_token', side_effect=Exception("Decode error"))
        mocker.patch('app.api.deps.logger.error')
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token("token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, test_user):
        """测试：获取当前激活用户成功"""
        result = await get_current_active_user(current_user=test_user)
        
        assert result == test_user
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, inactive_user):
        """测试：获取当前激活用户（未激活）"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=inactive_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "用户未激活" in exc_info.value.detail
    
    def test_require_admin_success(self, admin_user):
        """测试：要求管理员角色成功"""
        result = require_admin(current_user=admin_user)
        
        assert result == admin_user
    
    def test_require_admin_not_admin(self, test_user):
        """测试：要求管理员角色（非管理员）"""
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=test_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "需要管理员权限" in exc_info.value.detail

