"""
记忆管理API接口

提供记忆的CRUD操作
"""

# 标准库
from typing import Dict

# 第三方库
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# 本地库
from app.engines.memory import MemoryManager, MemoryType
from app.schemas.memory import (
    MemoryCreate,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult as SchemaMemorySearchResult,
    MemoryStatsResponse,
)
from app.utils.logger import logger

router = APIRouter()

# 全局记忆管理器实例
memory_manager = MemoryManager()


class MemoryCreateResponse(BaseModel):
    """创建记忆响应"""
    memory_id: str


@router.post("/", response_model=MemoryCreateResponse)
async def create_memory(memory: MemoryCreate):
    """创建记忆
    
    Args:
        memory: 记忆创建请求
        
    Returns:
        MemoryCreateResponse: 包含memory_id的响应
    """
    try:
        memory_id = await memory_manager.add_memory(
            user_id=memory.user_id,
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
async def search_memories(request: MemorySearchRequest):
    """搜索记忆
    
    Args:
        request: 搜索请求
        
    Returns:
        MemorySearchResponse: 搜索结果
    """
    try:
        # 转换memory_type
        memory_type = None
        if request.memory_type == "user":
            memory_type = MemoryType.USER
        elif request.memory_type == "assistant":
            memory_type = MemoryType.ASSISTANT
        
        results = await memory_manager.search_memories(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            memory_type=memory_type,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
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
async def get_memory_stats(user_id: str):
    """获取记忆统计信息
    
    Args:
        user_id: 用户ID
        
    Returns:
        MemoryStatsResponse: 统计信息
    """
    try:
        stats = await memory_manager.get_memory_stats(user_id)
        return MemoryStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory stats: {str(e)}"
        )


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, user_id: str):
    """删除记忆
    
    Args:
        memory_id: 记忆ID
        user_id: 用户ID
        
    Returns:
        Dict: 删除结果
    """
    try:
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
async def delete_session_memories(user_id: str, session_id: str):
    """删除会话的所有记忆
    
    Args:
        user_id: 用户ID
        session_id: 会话ID
        
    Returns:
        Dict: 删除结果
    """
    try:
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

