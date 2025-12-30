"""
用户管理API

提供用户注册、登录、信息查询、偏好管理等功能
"""

# 标准库
from typing import Any, Dict, List, Optional

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 本地库
from app.api.deps import get_current_active_user_async, get_db
from app.config.config import settings
from app.core.user.manager import UserManager
from app.core.user.profile import UserProfileManager
from app.core.user.stats import UserStatsManager
from app.middleware.rate_limit import rate_limit
from app.models.user import User
from app.utils.logger import logger
from app.utils.type_helpers import (
    get_user_username,
    get_user_email,
    get_user_role,
    get_user_display_name,
    get_user_avatar_url,
    get_user_bio
)

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
    response_style: Optional[str] = Field(
        None,
        description="回答风格（brief/chatgpt_like/detailed）"
    )
    style_preset: Optional[str] = Field(
        None,
        description="风格预设（chatgpt_like/elder_friendly/medical_detail）"
    )
    output_format: Optional[str] = Field(
        None,
        description="输出格式（structured/list/paragraph）"
    )
    prefer_list: Optional[bool] = Field(None, description="偏好使用列表呈现")
    theme: Optional[str] = Field(
        None, 
        description="主题",
        pattern="^(blue|green|purple|orange|pink|cyan)$"
    )
    auto_tts: Optional[bool] = Field(None, description="自动TTS")
    always_show_voice_input: Optional[bool] = Field(None, description="总是显示语音输入按钮（宽屏幕下也显示）")
    voice_input_mode: Optional[str] = Field(
        None,
        description="语音输入交互模式（press/click/auto）",
        pattern="^(press|click|auto)$"
    )
    timezone: Optional[str] = Field(None, description="时区（如：Asia/Shanghai）")
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
@rate_limit("3/minute", per_user=False)  # 按IP限流，防止注册滥用
async def register_user(
    request: Request,
    data: UserRegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)  # 统一使用异步会话
) -> Dict[str, Any]:
    """用户注册
    
    Args:
        request: 注册请求
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 注册结果
        
    Raises:
        HTTPException: 如果注册被禁用或注册失败
    """
    # 检查是否允许注册
    if not settings.allow_registration:
        logger.warning(
            "Registration attempt blocked",
            extra={"username": data.username, "email": data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户注册功能已禁用，请联系管理员"
        )
    
    try:
        manager = UserManager(db)
        user = await manager.register_user(
            username=data.username,
            email=data.email,
            password=data.password,
            display_name=data.display_name
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
@rate_limit("5/minute", per_user=False)  # 按IP限流，防止暴力破解
async def login_user(
    request: Request,
    data: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)  # 统一使用异步会话
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
            username=data.username,
            password=data.password
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
    current_user: User = Depends(get_current_active_user_async)  # 使用异步版本的认证
) -> UserResponse:
    """获取当前用户信息
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        UserResponse: 用户信息
    """
    return UserResponse(
        id=str(current_user.id),
        username=get_user_username(current_user),
        email=get_user_email(current_user),
        role=get_user_role(current_user),
        display_name=get_user_display_name(current_user),
        avatar_url=get_user_avatar_url(current_user),
        bio=get_user_bio(current_user),
        preferences=current_user.get_preferences(),
        created_at=current_user.created_at.isoformat()
    )


@router.put("/me")
async def update_current_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
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
    current_user: User = Depends(get_current_active_user_async)  # 使用异步版本的认证
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
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
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
        
        # 验证主题值（如果提供）
        if "theme" in updates and updates["theme"]:
            # 迁移旧数据：如果 theme 是 "light"，转换为 "blue"
            if updates["theme"] == "light":
                logger.info(
                    f"Migrating theme from 'light' to 'blue'",
                    extra={"user_id": str(current_user.id)}
                )
                updates["theme"] = "blue"
            
            valid_themes = ["blue", "green", "purple", "orange", "pink", "cyan"]
            if updates["theme"] not in valid_themes:
                logger.warning(
                    f"Invalid theme value: {updates['theme']}, using default 'blue'",
                    extra={"user_id": str(current_user.id), "invalid_theme": updates["theme"]}
                )
                updates["theme"] = "blue"  # 使用默认主题
        
        logger.info(f"Updating user preferences: user_id={current_user.id}, updates={updates}")
        
        user = await manager.update_user(
            user_id=str(current_user.id),
            updates={"preferences": updates}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 刷新数据库会话，确保获取最新数据（异步版本）
        await db.refresh(user)
        
        updated_preferences = user.get_preferences()
        logger.info(f"User preferences updated: user_id={current_user.id}, preferences={updated_preferences}")
        
        return {
            "message": "偏好更新成功",
            "preferences": updated_preferences
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
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
) -> Dict[str, Any]:
    """获取用户资料（包含基本信息和画像）
    
    Args:
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 用户资料（包含 display_name, bio, avatar_url, interests 等）
    """
    try:
        # 获取用户画像（使用异步版本）
        profile_manager = UserProfileManager(db)
        profile = await profile_manager.get_profile(str(current_user.id))
        
        # 构建用户资料响应，包含用户基本信息和画像
        result: Dict[str, Any] = {
            "user_id": str(current_user.id),
            "display_name": get_user_display_name(current_user),
            "avatar_url": get_user_avatar_url(current_user),
            "bio": get_user_bio(current_user),
        }
        
        # 添加用户画像信息
        if profile:
            result["interests"] = profile.interests
            result["habits"] = profile.get_habits()
            result["personality_insights"] = profile.get_personality_insights()
            result["statistics"] = profile.get_statistics()
            result["generated_at"] = profile.generated_at.isoformat() if profile.generated_at else None
        else:
            result["interests"] = []
            result["habits"] = {}
            result["personality_insights"] = {}
            result["statistics"] = {}
            result["generated_at"] = None
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料失败"
        )


class UserProfileUpdateRequest(BaseModel):
    """用户资料更新请求"""
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    interests: Optional[List[str]] = Field(None, description="兴趣列表")


@router.put("/me/profile")
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
) -> Dict[str, Any]:
    """更新用户资料（包含基本信息和画像）
    
    Args:
        request: 用户资料更新请求
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 更新后的用户资料
    """
    try:
        manager = UserManager(db)
        updates = request.model_dump(exclude_unset=True)
        
        # 分离用户基本信息和画像信息
        user_updates: Dict[str, Any] = {}
        profile_updates: Dict[str, Any] = {}
        
        if "display_name" in updates:
            user_updates["display_name"] = updates["display_name"]
        if "avatar_url" in updates:
            user_updates["avatar_url"] = updates["avatar_url"]
        if "bio" in updates:
            user_updates["bio"] = updates["bio"]
        if "interests" in updates:
            profile_updates["interests"] = updates["interests"]
        
        # 更新用户基本信息
        if user_updates:
            user = await manager.update_user(
                user_id=str(current_user.id),
                updates=user_updates
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
        else:
            # 如果没有更新用户基本信息，直接获取当前用户
            user = current_user
        
        # 更新用户画像
        if profile_updates:
            await manager.update_user_profile(
                user_id=str(current_user.id),
                updates=profile_updates
            )
        
        # 获取更新后的用户资料（使用异步版本）
        profile_manager = UserProfileManager(db)
        profile = await profile_manager.get_profile(str(current_user.id))
        
        # 构建响应
        result: Dict[str, Any] = {
            "user_id": str(current_user.id),
            "display_name": get_user_display_name(user),
            "avatar_url": get_user_avatar_url(user),
            "bio": get_user_bio(user),
        }
        
        if profile:
            result["interests"] = profile.interests
            result["habits"] = profile.get_habits()
            result["personality_insights"] = profile.get_personality_insights()
            result["statistics"] = profile.get_statistics()
            result["generated_at"] = profile.generated_at.isoformat() if profile.generated_at else None
        else:
            result["interests"] = []
            result["habits"] = {}
            result["personality_insights"] = {}
            result["statistics"] = {}
            result["generated_at"] = None
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户资料失败"
        )


@router.get("/me/stats")
async def get_user_statistics(
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
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
        stats = await stats_manager.get_user_stats(str(current_user.id))
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )

