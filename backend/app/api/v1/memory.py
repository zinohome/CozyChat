"""
记忆管理API接口

提供记忆的CRUD操作

============================================================================
⚠️ DEPRECATED: Memory API（已废弃）
============================================================================
状态：已废弃，将在 v2.0 移除
废弃时间：2024-12-22
移除时间：2025-Q1

替代方案：
  - 使用三大人格化引擎的API接口
  - 会话记忆通过聊天API自动管理
  - 知识管理使用Knowledge Engine API
  - 用户画像使用UserProfile Engine API

注意：此API仍可使用，但不推荐，将在v2.0移除

迁移指南：docs/reports/三大人格化引擎系统架构重构方案.md
============================================================================
"""

# 标准库
from typing import Dict
import uuid

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.api.deps import get_db, get_current_active_user_async
from app.models.user import User
from app.engines.memory import get_memory_manager, MemoryType
from app.middleware.rate_limit import rate_limit
from app.schemas.memory import (
    MemoryCreate,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult as SchemaMemorySearchResult,
    MemoryStatsResponse,
)
from app.utils.logger import logger
from app.utils.type_helpers import get_user_role, is_admin_user

router = APIRouter()

# 全局记忆管理器实例（使用单例，避免重复初始化）
memory_manager = get_memory_manager()


class MemoryCreateResponse(BaseModel):
    """创建记忆响应"""
    memory_id: str


@router.post("/", response_model=MemoryCreateResponse)
@rate_limit("20/minute", per_user=True)
async def create_memory(
    request: Request,
    memory: MemoryCreate,
    response: Response,
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
):
    """创建记忆
    
    Args:
        memory: 记忆创建请求
        current_user: 当前认证用户
        
    Returns:
        MemoryCreateResponse: 包含memory_id的响应
    """
    try:
        # 验证用户权限：只能为自己创建记忆（除非是管理员）
        memory_user_id = memory.user_id
        if memory_user_id:
            memory_user_uuid = uuid.UUID(str(memory_user_id))
            if memory_user_uuid != current_user.id and not is_admin_user(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权为其他用户创建记忆"
                )
        else:
            # 如果没有指定user_id，使用当前用户的ID
            memory_user_id = str(current_user.id)
        
        memory_id = await memory_manager.add_memory(
            user_id=memory_user_id,
            session_id=memory.session_id,
            content=memory.content,
            memory_type=MemoryType(memory.memory_type),
            importance=memory.importance,
            metadata=memory.metadata,
            async_save=True
        )
        
        return MemoryCreateResponse(memory_id=memory_id)
        
    except Exception as e:
        logger.error(f"Failed to create memory: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create memory: {str(e)}"
        )


@router.post("/search", response_model=MemorySearchResponse)
@rate_limit("60/minute", per_user=True)
async def search_memories(
    request: Request,
    data: MemorySearchRequest,
    response: Response,
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
):
    """搜索记忆
    
    Args:
        request: 搜索请求
        current_user: 当前认证用户
        
    Returns:
        MemorySearchResponse: 搜索结果
    """
    try:
        # 验证用户权限：只能搜索自己的记忆（除非是管理员）
        search_user_id = data.user_id
        if search_user_id:
            search_user_uuid = uuid.UUID(str(search_user_id))
            if search_user_uuid != current_user.id and not is_admin_user(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权搜索其他用户的记忆"
                )
        else:
            # 如果没有指定user_id，使用当前用户的ID
            search_user_id = str(current_user.id)
        
        # 转换memory_type
        memory_type = None
        if data.memory_type == "user":
            memory_type = MemoryType.USER
        elif data.memory_type == "assistant":
            memory_type = MemoryType.ASSISTANT
        
        results = await memory_manager.search_memories(
            query=data.query,
            user_id=search_user_id,
            session_id=data.session_id,
            memory_type=memory_type,
            limit=data.limit,
            similarity_threshold=data.similarity_threshold
        )
        
        # 转换为响应格式
        search_results = [
            SchemaMemorySearchResult(
                memory=MemoryResponse(**result.memory.to_dict()),
                similarity=result.similarity,
                distance=result.distance
            )
            for result in results
        ]
        
        return MemorySearchResponse(
            results=search_results,
            total_count=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Failed to search memories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search memories: {str(e)}"
        )


@router.get("/stats/{user_id}", response_model=MemoryStatsResponse)
async def get_memory_stats(
    user_id: str,
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
):
    """获取记忆统计信息
    
    Args:
        user_id: 用户ID
        current_user: 当前认证用户
        
    Returns:
        MemoryStatsResponse: 统计信息
    """
    try:
        # 验证用户权限：只能查看自己的统计（除非是管理员）
        stats_user_uuid = uuid.UUID(str(user_id))
        if stats_user_uuid != current_user.id and not is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他用户的统计信息"
            )
        
        stats = await memory_manager.get_memory_stats(user_id)
        return MemoryStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory stats: {str(e)}"
        )


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
):
    """删除记忆
    
    Args:
        memory_id: 记忆ID
        user_id: 用户ID
        current_user: 当前认证用户
        
    Returns:
        Dict: 删除结果
    """
    try:
        # 验证用户权限：只能删除自己的记忆（除非是管理员）
        delete_user_uuid = uuid.UUID(str(user_id))
        if delete_user_uuid != current_user.id and not is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除其他用户的记忆"
            )
        
        success = await memory_manager.delete_memory(memory_id, user_id)
        
        if success:
            return {"success": True, "message": "Memory deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete memory: {str(e)}"
        )


@router.delete("/session/{user_id}/{session_id}")
async def delete_session_memories(
    user_id: str,
    session_id: str,
    current_user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
):
    """删除会话的所有记忆
    
    Args:
        user_id: 用户ID
        session_id: 会话ID
        current_user: 当前认证用户
        
    Returns:
        Dict: 删除结果
    """
    try:
        # 验证用户权限：只能删除自己的会话记忆（除非是管理员）
        delete_user_uuid = uuid.UUID(str(user_id))
        if delete_user_uuid != current_user.id and not is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除其他用户的会话记忆"
            )
        
        count = await memory_manager.delete_session_memories(user_id, session_id)
        
        return {
            "success": True,
            "message": f"Deleted {count} memories",
            "deleted_count": count
        }
        
    except Exception as e:
        logger.error(f"Failed to delete session memories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session memories: {str(e)}"
        )


@router.get("/health")
async def memory_health_check():
    """记忆系统健康检查"""
    try:
        is_healthy = await memory_manager.health_check()
        
        if is_healthy:
            return {"status": "healthy"}
        else:
            return {"status": "unhealthy"}
            
    except Exception as e:
        logger.error(f"Memory health check failed: {e}", exc_info=True)
        return {"status": "unhealthy", "error": str(e)}

