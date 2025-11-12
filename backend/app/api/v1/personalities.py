"""
人格管理API

提供人格的查询、创建、更新等功能
"""

# 标准库
from typing import Any, Dict, List, Optional

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# 本地库
from app.api.deps import get_current_active_user
from app.core.personality import PersonalityManager
from app.core.personality.models import Personality
from app.models.user import User
from app.utils.logger import logger

router = APIRouter(prefix="/personalities", tags=["personalities"])


# ===== 请求/响应模型 =====

class PersonalityListItem(BaseModel):
    """人格列表项"""
    id: str
    name: str
    description: str
    icon: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_default: bool = False
    created_at: Optional[str] = None


class PersonalityListResponse(BaseModel):
    """人格列表响应"""
    personalities: List[PersonalityListItem]
    total: int


class PersonalityDetailResponse(BaseModel):
    """人格详情响应"""
    id: str
    name: str
    description: str
    config: Dict[str, Any]
    metadata: Dict[str, Any]


class CreatePersonalityRequest(BaseModel):
    """创建人格请求"""
    name: str = Field(..., min_length=1, max_length=100, description="人格名称")
    description: str = Field(..., min_length=1, max_length=500, description="人格描述")
    config: Dict[str, Any] = Field(..., description="人格配置")


class CreatePersonalityResponse(BaseModel):
    """创建人格响应"""
    id: str
    name: str
    created_at: str
    message: str


class UpdatePersonalityRequest(BaseModel):
    """更新人格请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="人格名称")
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="人格描述")
    config: Optional[Dict[str, Any]] = Field(None, description="人格配置")


class UpdatePersonalityResponse(BaseModel):
    """更新人格响应"""
    id: str
    message: str
    updated_at: str


# ===== API路由 =====

@router.get("", response_model=PersonalityListResponse)
async def list_personalities(
    user: User = Depends(get_current_active_user)
) -> PersonalityListResponse:
    """列出所有人格
    
    Args:
        user: 当前用户
        
    Returns:
        PersonalityListResponse: 人格列表
    """
    try:
        manager = PersonalityManager()
        personalities = manager.list_personalities()
        
        items = [
            PersonalityListItem(
                id=p["id"],
                name=p["name"],
                description=p.get("description", ""),
                icon=p.get("icon", ""),
                tags=p.get("tags", []),
                is_default=p.get("id") == "default",
                created_at=None  # 可以从metadata中获取
            )
            for p in personalities
        ]
        
        logger.info(
            "Listed personalities",
            extra={"user_id": str(user.id), "count": len(items)}
        )
        
        return PersonalityListResponse(
            personalities=items,
            total=len(items)
        )
        
    except Exception as e:
        logger.error(f"Failed to list personalities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list personalities"
        )


@router.get("/{personality_id}", response_model=PersonalityDetailResponse)
async def get_personality(
    personality_id: str,
    user: User = Depends(get_current_active_user)
) -> PersonalityDetailResponse:
    """获取人格详情
    
    Args:
        personality_id: 人格ID
        user: 当前用户
        
    Returns:
        PersonalityDetailResponse: 人格详情
        
    Raises:
        HTTPException: 如果人格不存在
    """
    try:
        manager = PersonalityManager()
        personality = manager.get_personality(personality_id)
        
        if not personality:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Personality '{personality_id}' not found"
            )
        
        logger.info(
            "Retrieved personality detail",
            extra={"user_id": str(user.id), "personality_id": personality_id}
        )
        
        return PersonalityDetailResponse(
            id=personality.id,
            name=personality.name,
            description=personality.description,
            config=personality.to_config(),
            metadata=personality.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get personality: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personality"
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreatePersonalityResponse)
async def create_personality(
    request: CreatePersonalityRequest,
    user: User = Depends(get_current_active_user)
) -> CreatePersonalityResponse:
    """创建自定义人格
    
    Args:
        request: 创建人格请求
        user: 当前用户
        
    Returns:
        CreatePersonalityResponse: 创建结果
        
    Raises:
        HTTPException: 如果配置无效或人格ID已存在
    """
    try:
        manager = PersonalityManager()
        
        # 构建人格配置
        config = {
            "id": f"user_{user.id}_{request.name.lower().replace(' ', '_')}",
            "name": request.name,
            "description": request.description,
            **request.config
        }
        
        personality = manager.create_personality(config)
        
        logger.info(
            "Created personality",
            extra={
                "user_id": str(user.id),
                "personality_id": personality.id
            }
        )
        
        return CreatePersonalityResponse(
            id=personality.id,
            name=personality.name,
            created_at=personality.metadata.get("created_at", ""),
            message="人格创建成功"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create personality: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create personality"
        )


@router.put("/{personality_id}", response_model=UpdatePersonalityResponse)
async def update_personality(
    personality_id: str,
    request: UpdatePersonalityRequest,
    user: User = Depends(get_current_active_user)
) -> UpdatePersonalityResponse:
    """更新人格配置
    
    Args:
        personality_id: 人格ID
        request: 更新人格请求
        user: 当前用户
        
    Returns:
        UpdatePersonalityResponse: 更新结果
        
    Raises:
        HTTPException: 如果人格不存在或配置无效
    """
    try:
        manager = PersonalityManager()
        
        # 构建更新字典
        updates: Dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.config is not None:
            updates.update(request.config)
        
        personality = manager.update_personality(personality_id, updates)
        
        logger.info(
            "Updated personality",
            extra={
                "user_id": str(user.id),
                "personality_id": personality_id
            }
        )
        
        return UpdatePersonalityResponse(
            id=personality.id,
            message="人格更新成功",
            updated_at=personality.metadata.get("updated_at", "")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update personality: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update personality"
        )

