"""
用户管理API

提供用户注册、登录、信息查询、偏好管理等功能
"""

# 标准库
from typing import Any, Dict, Optional

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

# 本地库
from app.api.deps import get_current_active_user, get_sync_session
from app.core.user.manager import UserManager
from app.core.user.profile import UserProfileManager
from app.core.user.stats import UserStatsManager
from app.models.user import User
from app.utils.logger import logger

router = APIRouter(tags=["users"])


# ===== 请求/响应模型 =====

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    invite_code: Optional[str] = Field(None, description="邀请码（可选）")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")


class UserPreferencesUpdateRequest(BaseModel):
    """用户偏好更新请求"""
    default_personality: Optional[str] = Field(None, description="默认人格ID")
    language: Optional[str] = Field(None, description="语言")
    theme: Optional[str] = Field(None, description="主题")
    auto_tts: Optional[bool] = Field(None, description="自动TTS")
    show_reasoning: Optional[bool] = Field(None, description="显示推理过程")


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: str
    role: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    preferences: Dict[str, Any]
    created_at: str


class AuthResponse(BaseModel):
    """认证响应"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]


# ===== API路由 =====

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_sync_session)
) -> Dict[str, Any]:
    """用户注册
    
    Args:
        request: 注册请求
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 注册结果
    """
    try:
        manager = UserManager(db)
        user = await manager.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            display_name=request.display_name
        )
        
        return {
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "message": "注册成功"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User registration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败"
        )


@router.post("/login")
async def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_sync_session)
) -> AuthResponse:
    """用户登录
    
    Args:
        request: 登录请求
        db: 数据库会话
        
    Returns:
        AuthResponse: 认证响应
    """
    try:
        manager = UserManager(db)
        result = await manager.authenticate(
            username=request.username,
            password=request.password
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        return AuthResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """获取当前用户信息
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        UserResponse: 用户信息
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        preferences=current_user.get_preferences(),
        created_at=current_user.created_at.isoformat()
    )


@router.put("/me")
async def update_current_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> Dict[str, Any]:
    """更新当前用户信息
    
    Args:
        request: 更新请求
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 更新结果
    """
    try:
        manager = UserManager(db)
        updates = request.model_dump(exclude_unset=True)
        
        user = await manager.update_user(
            user_id=str(current_user.id),
            updates=updates
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return {
            "message": "更新成功",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "bio": user.bio
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )


@router.get("/me/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取用户偏好设置
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        Dict[str, Any]: 偏好设置
    """
    return {
        "preferences": current_user.get_preferences()
    }


@router.put("/me/preferences")
async def update_user_preferences(
    request: UserPreferencesUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> Dict[str, Any]:
    """更新用户偏好设置
    
    Args:
        request: 偏好更新请求
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 更新结果
    """
    try:
        manager = UserManager(db)
        updates = request.model_dump(exclude_unset=True)
        
        user = await manager.update_user(
            user_id=str(current_user.id),
            updates={"preferences": updates}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return {
            "message": "偏好更新成功",
            "preferences": user.get_preferences()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )


@router.get("/me/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> Dict[str, Any]:
    """获取用户画像
    
    Args:
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 用户画像
    """
    try:
        profile_manager = UserProfileManager(db)
        profile = profile_manager.get_profile(str(current_user.id))
        
        if not profile:
            return {
                "user_id": str(current_user.id),
                "profile": {
                    "interests": [],
                    "habits": {},
                    "personality_insights": {},
                    "statistics": {}
                },
                "generated_at": None
            }
        
        return {
            "user_id": str(current_user.id),
            "profile": {
                "interests": profile.interests,
                "habits": profile.get_habits(),
                "personality_insights": profile.get_personality_insights(),
                "statistics": profile.get_statistics()
            },
            "generated_at": profile.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户画像失败"
        )


@router.get("/me/stats")
async def get_user_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> Dict[str, Any]:
    """获取用户统计信息
    
    Args:
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 统计信息
    """
    try:
        stats_manager = UserStatsManager(db)
        stats = stats_manager.get_user_stats(str(current_user.id))
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )

