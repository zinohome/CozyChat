"""
认证API

提供Token刷新等功能
"""

# 标准库
from typing import Any, Dict

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

# 本地库
from app.api.deps import get_sync_session
from app.core.user.auth import AuthService
from app.models.user import User
from app.utils.logger import logger
from sqlalchemy.orm import Session

router = APIRouter(tags=["auth"])
security = HTTPBearer()


# ===== 请求/响应模型 =====

class RefreshTokenRequest(BaseModel):
    """Token刷新请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """Token刷新响应"""
    access_token: str = Field(..., description="新的访问令牌")
    expires_in: int = Field(..., description="过期时间（秒）")


# ===== API路由 =====

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_sync_session)
) -> RefreshTokenResponse:
    """刷新访问令牌
    
    使用刷新令牌获取新的访问令牌
    
    Args:
        request: 刷新令牌请求
        db: 数据库会话
        
    Returns:
        RefreshTokenResponse: 新的访问令牌
        
    Raises:
        HTTPException: 如果刷新令牌无效或过期
    """
    try:
        auth_service = AuthService()
        
        # 验证刷新令牌
        payload = auth_service.verify_token(request.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # 检查令牌类型（应该是refresh token）
        token_type = payload.get("type")
        if token_type and token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # 获取用户信息
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # 验证用户是否存在且活跃
        # 将user_id转换为UUID（如果它是字符串）
        try:
            import uuid as uuid_module
            if isinstance(user_id, str):
                user_id_uuid = uuid_module.UUID(user_id)
            else:
                user_id_uuid = user_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format"
            )
        
        user = db.query(User).filter(User.id == user_id_uuid).first()
        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # 生成新的访问令牌
        access_token = auth_service.create_access_token(
            user_id=str(user.id),
            username=user.username,
            role=user.role
        )
        
        logger.info(
            "Token refreshed",
            extra={"user_id": str(user.id), "username": user.username}
        )
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=3600  # 默认1小时
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

