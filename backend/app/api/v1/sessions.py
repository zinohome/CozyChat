"""
会话管理API

提供会话的创建、查询、更新、删除等功能
"""

# 标准库
from typing import Any, Dict, List, Optional
from datetime import datetime

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

# 本地库
from app.api.deps import get_current_active_user, get_sync_session
from app.core.personality import PersonalityManager
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.message import Message as MessageModel
from app.utils.logger import logger

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ===== 请求/响应模型 =====

class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    personality_id: str = Field(..., description="人格ID")
    title: Optional[str] = Field(None, max_length=255, description="会话标题")


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    session_id: str
    personality_id: str
    title: str
    created_at: str


class SessionListItem(BaseModel):
    """会话列表项"""
    session_id: str
    personality_id: str
    personality_name: Optional[str] = None
    title: str
    message_count: int
    last_message_at: Optional[str] = None
    created_at: str


class SessionsListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionListItem]
    total: int
    page: int
    page_size: int


class MessageInfo(BaseModel):
    """消息信息"""
    id: str
    role: str
    content: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


class SessionDetailResponse(BaseModel):
    """会话详情响应"""
    session_id: str
    personality_id: str
    title: str
    messages: List[MessageInfo]
    total_messages: int
    created_at: str


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(None, max_length=255, description="会话标题")


class UpdateSessionResponse(BaseModel):
    """更新会话响应"""
    session_id: str
    title: str
    updated_at: str


class DeleteSessionResponse(BaseModel):
    """删除会话响应"""
    message: str
    session_id: str


# ===== API路由 =====

@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> CreateSessionResponse:
    """创建会话
    
    Args:
        request: 创建会话请求
        user: 当前用户
        db: 数据库会话
        
    Returns:
        CreateSessionResponse: 创建结果
        
    Raises:
        HTTPException: 如果人格不存在
    """
    try:
        # 验证人格是否存在
        personality_manager = PersonalityManager()
        personality = personality_manager.get_personality(request.personality_id)
        if not personality:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Personality '{request.personality_id}' not found"
            )
        
        # 创建会话
        session = SessionModel(
            user_id=user.id,
            personality_id=request.personality_id,
            title=request.title or "新会话"
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(
            "Session created",
            extra={
                "user_id": str(user.id),
                "session_id": str(session.id),
                "personality_id": request.personality_id
            }
        )
        
        return CreateSessionResponse(
            session_id=str(session.id),
            personality_id=session.personality_id,
            title=session.title,
            created_at=session.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("", response_model=SessionsListResponse)
async def list_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    personality_id: Optional[str] = Query(None, description="人格ID过滤"),
    sort: str = Query("created_at", description="排序字段"),
    order: str = Query("desc", description="排序方向：asc/desc"),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> SessionsListResponse:
    """列出用户会话
    
    Args:
        page: 页码
        page_size: 每页数量
        personality_id: 人格ID过滤
        sort: 排序字段
        order: 排序方向
        user: 当前用户
        db: 数据库会话
        
    Returns:
        SessionsListResponse: 会话列表
    """
    try:
        # 构建查询
        query = db.query(SessionModel).filter(
            and_(
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        )
        
        # 人格过滤
        if personality_id:
            query = query.filter(SessionModel.personality_id == personality_id)
        
        # 排序
        sort_column = getattr(SessionModel, sort, SessionModel.created_at)
        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        sessions = query.offset(offset).limit(page_size).all()
        
        # 获取人格管理器以获取人格名称
        personality_manager = PersonalityManager()
        
        # 构建响应
        items = []
        for session in sessions:
            personality = personality_manager.get_personality(session.personality_id)
            items.append(SessionListItem(
                session_id=str(session.id),
                personality_id=session.personality_id,
                personality_name=personality.name if personality else None,
                title=session.title,
                message_count=session.message_count,
                last_message_at=session.last_message_at.isoformat() if session.last_message_at else None,
                created_at=session.created_at.isoformat()
            ))
        
        logger.info(
            "Listed sessions",
            extra={"user_id": str(user.id), "count": len(items), "total": total}
        )
        
        return SessionsListResponse(
            sessions=items,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> SessionDetailResponse:
    """获取会话详情
    
    Args:
        session_id: 会话ID
        user: 当前用户
        db: 数据库会话
        
    Returns:
        SessionDetailResponse: 会话详情
        
    Raises:
        HTTPException: 如果会话不存在或不属于当前用户
    """
    try:
        import uuid
        session_uuid = uuid.UUID(session_id)
        
        # 查询会话
        session = db.query(SessionModel).filter(
            and_(
                SessionModel.id == session_uuid,
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # 查询消息
        messages = db.query(MessageModel).filter(
            MessageModel.session_id == session_uuid
        ).order_by(MessageModel.created_at).all()
        
        # 构建响应
        message_items = [
            MessageInfo(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
                metadata=msg.metadata or {}
            )
            for msg in messages
        ]
        
        logger.info(
            "Retrieved session detail",
            extra={"user_id": str(user.id), "session_id": session_id}
        )
        
        return SessionDetailResponse(
            session_id=str(session.id),
            personality_id=session.personality_id,
            title=session.title,
            messages=message_items,
            total_messages=len(message_items),
            created_at=session.created_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session"
        )


@router.put("/{session_id}", response_model=UpdateSessionResponse)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> UpdateSessionResponse:
    """更新会话
    
    Args:
        session_id: 会话ID
        request: 更新会话请求
        user: 当前用户
        db: 数据库会话
        
    Returns:
        UpdateSessionResponse: 更新结果
        
    Raises:
        HTTPException: 如果会话不存在或不属于当前用户
    """
    try:
        import uuid
        session_uuid = uuid.UUID(session_id)
        
        # 查询会话
        session = db.query(SessionModel).filter(
            and_(
                SessionModel.id == session_uuid,
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # 更新
        if request.title is not None:
            session.title = request.title
        
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        
        logger.info(
            "Updated session",
            extra={"user_id": str(user.id), "session_id": session_id}
        )
        
        return UpdateSessionResponse(
            session_id=str(session.id),
            title=session.title,
            updated_at=session.updated_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
) -> DeleteSessionResponse:
    """删除会话（软删除）
    
    Args:
        session_id: 会话ID
        user: 当前用户
        db: 数据库会话
        
    Returns:
        DeleteSessionResponse: 删除结果
        
    Raises:
        HTTPException: 如果会话不存在或不属于当前用户
    """
    try:
        import uuid
        session_uuid = uuid.UUID(session_id)
        
        # 查询会话
        session = db.query(SessionModel).filter(
            and_(
                SessionModel.id == session_uuid,
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # 软删除
        session.deleted_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            "Deleted session",
            extra={"user_id": str(user.id), "session_id": session_id}
        )
        
        return DeleteSessionResponse(
            message="会话已删除",
            session_id=session_id
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

