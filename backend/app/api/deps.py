"""
API依赖注入

定义FastAPI路由中使用的依赖项
"""

# 标准库
from typing import AsyncGenerator, Optional

# 第三方库
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# 本地库
from app.models.base import get_async_db, get_sync_db
from app.models.user import User
from app.core.user.auth import AuthService
from app.utils.logger import logger
from app.utils.security import decode_token

# 安全相关
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖（异步）
    
    Yields:
        AsyncSession: 数据库会话
    """
    async for session in get_async_db():
        yield session


def get_sync_session() -> Session:
    """获取同步数据库会话依赖
    
    Yields:
        Session: 数据库会话
    """
    for session in get_sync_db():
        yield session


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_sync_session)
) -> Optional[User]:
    """获取当前用户
    
    Args:
        credentials: HTTP Bearer认证凭证
        db: 数据库会话
        
    Returns:
        Optional[User]: 当前用户对象，如果未认证返回None
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        auth_service = AuthService()
        token = credentials.credentials
        user = auth_service.get_current_user_from_token(db, token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_from_token(token: str) -> User:
    """从JWT token获取当前用户（用于WebSocket等场景）
    
    Args:
        token: JWT token字符串
    
    Returns:
        User: 用户对象
    
    Raises:
        HTTPException: 如果token无效或用户不存在
    """
    try:
        # 解码token
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # 从数据库获取用户
        db = next(get_sync_session())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user from token: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前激活用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前激活的用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求管理员角色
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 管理员用户对象
        
    Raises:
        HTTPException: 如果不是管理员则抛出403错误
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


