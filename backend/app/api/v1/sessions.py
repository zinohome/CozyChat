"""
会话管理API

提供会话的创建、查询、更新、删除等功能
"""

# 标准库
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

# 本地库
from app.api.deps import (
    get_current_active_user,
    get_sync_session,
    get_personality_registry,
    get_llm_engine_pool,
)
from app.core.personality import PersonalityRegistry
from app.engines.ai.engine_pool import LLMEnginePool
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


class GenerateTitleRequest(BaseModel):
    """生成标题请求"""
    force: bool = Field(default=False, description="是否强制重新生成标题")
    max_messages: Optional[int] = Field(None, description="用于生成标题的最大消息数")


class GenerateTitleResponse(BaseModel):
    """生成标题响应"""
    session_id: str
    title: str
    generated_at: str
    used_message_count: int


# ===== API路由 =====

@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session),
    personality_registry: PersonalityRegistry = Depends(get_personality_registry),
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
        personality = personality_registry.get_personality(request.personality_id)
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
        
        # 如果 personality 有欢迎词，自动创建一条助手消息
        if personality.welcome_message:
            welcome_message = MessageModel(
                session_id=session.id,
                user_id=user.id,
                role="assistant",
                content=personality.welcome_message,
                message_metadata={"is_welcome": True}  # 标记为欢迎消息
            )
            db.add(welcome_message)
            # 更新会话统计信息
            session.message_count = 1  # type: ignore[assignment]
            session.last_message_at = welcome_message.created_at  # type: ignore[assignment]
            db.commit()
            
            logger.info(
                "Welcome message added to session",
                extra={
                    "user_id": str(user.id),
                    "session_id": str(session.id),
                    "personality_id": request.personality_id
                }
            )
        
        logger.info(
            "Session created",
            extra={
                "user_id": str(user.id),
                "session_id": str(session.id),
                "personality_id": request.personality_id,
                "has_welcome_message": bool(personality.welcome_message)
            }
        )
        
        return CreateSessionResponse(
            session_id=str(session.id),
            personality_id=str(session.personality_id),  # type: ignore[arg-type]
            title=str(session.title),  # type: ignore[arg-type]
            created_at=session.created_at.replace(tzinfo=timezone.utc).isoformat()
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
    db: Session = Depends(get_sync_session),
    personality_registry: PersonalityRegistry = Depends(get_personality_registry),
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
        # 如果按 last_message_at 排序，需要处理 null 值（使用 created_at 作为后备）
        if sort == "last_message_at":
            # 使用 COALESCE 处理 null 值：如果 last_message_at 为 null，使用 created_at
            # 使用部分索引 idx_sessions_user_deleted_lastmsg 优化此查询
            sort_column = func.coalesce(SessionModel.last_message_at, SessionModel.created_at)
            if order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
        else:
            # 使用部分索引 idx_sessions_user_deleted_created 优化此查询
            sort_column = getattr(SessionModel, sort, SessionModel.created_at)
            if order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
        
        # 总数（优化：使用子查询避免重复计算）
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        sessions = query.offset(offset).limit(page_size).all()
        
        # 构建响应
        items = []
        for session in sessions:
            personality = personality_registry.get_personality(str(session.personality_id))  # type: ignore[arg-type]
            items.append(SessionListItem(
                session_id=str(session.id),
                personality_id=str(session.personality_id),  # type: ignore[arg-type]
                personality_name=str(personality.name) if personality else None,  # type: ignore[arg-type]
                title=str(session.title),  # type: ignore[arg-type]
                message_count=int(session.message_count),  # type: ignore[arg-type]
                last_message_at=session.last_message_at.replace(tzinfo=timezone.utc).isoformat() if session.last_message_at is not None else None,  # type: ignore[arg-type]
                created_at=session.created_at.replace(tzinfo=timezone.utc).isoformat()
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
        # 记录接收到的 session_id，用于调试
        logger.debug(
            f"Received session_id: {session_id}, type: {type(session_id)}, length: {len(session_id)}"
        )
        
        # 尝试解析 UUID
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError as e:
            logger.warning(
                f"Invalid UUID format: {session_id}, error: {e}",
                extra={"session_id": session_id, "user_id": str(user.id)}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid session ID format: {str(e)}"
            )
        
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
        message_items = []
        for msg in messages:
            # 注意：Message 模型中有 metadata = Base.metadata（SQLAlchemy 元数据对象）
            # 实际的 JSONB 字段是 message_metadata，必须使用 message_metadata 而不是 metadata
            msg_metadata = msg.message_metadata if msg.message_metadata is not None else {}  # type: ignore[comparison-overlap]
            
            # 确保 metadata 是字典类型
            if not isinstance(msg_metadata, dict):
                msg_metadata = {}
            
            message_items.append(
                MessageInfo(
                    id=str(msg.id),
                    role=str(msg.role),  # type: ignore[arg-type]
                    content=str(msg.content),  # type: ignore[arg-type]
                    created_at=msg.created_at.replace(tzinfo=timezone.utc).isoformat(),
                    metadata=msg_metadata
                )
            )
        
        logger.info(
            "Retrieved session detail",
            extra={"user_id": str(user.id), "session_id": session_id, "message_count": len(message_items)}
        )
        
        return SessionDetailResponse(
            session_id=str(session.id),
            personality_id=str(session.personality_id),  # type: ignore[arg-type]
            title=str(session.title),  # type: ignore[arg-type]
            messages=message_items,
            total_messages=len(message_items),
            created_at=session.created_at.replace(tzinfo=timezone.utc).isoformat()
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
            session.title = request.title  # type: ignore[assignment]
        
        session.updated_at = datetime.utcnow()  # type: ignore[assignment]
        db.commit()
        db.refresh(session)
        
        logger.info(
            "Updated session",
            extra={"user_id": str(user.id), "session_id": session_id}
        )
        
        return UpdateSessionResponse(
            session_id=str(session.id),
            title=str(session.title),  # type: ignore[arg-type]
            updated_at=session.updated_at.replace(tzinfo=timezone.utc).isoformat()
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


@router.post("/{session_id}/title", response_model=GenerateTitleResponse)
async def generate_session_title(
    session_id: str,
    request: GenerateTitleRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session),
    engine_pool: LLMEnginePool = Depends(get_llm_engine_pool),
) -> GenerateTitleResponse:
    """生成或更新会话标题
    
    根据会话消息内容生成简洁的标题。
    
    Args:
        session_id: 会话ID
        request: 生成标题请求
        user: 当前用户
        db: 数据库会话
        
    Returns:
        GenerateTitleResponse: 生成的标题信息
        
    Raises:
        HTTPException: 如果会话不存在、不属于当前用户或生成失败
    """
    try:
        import uuid
        from app.config.config import settings
        from app.core.session import SessionTitleGenerator
        
        session_uuid = uuid.UUID(session_id)
        
        # 查询会话并验证权限
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
        
        # 检查是否应该生成标题
        trigger_length = settings.session_title_trigger_length
        
        # 优先使用session.message_count字段（性能更好，避免时序问题）
        # 如果字段为None或0，再查询实际消息数
        session_msg_count = int(session.message_count) if session.message_count is not None else 0  # type: ignore[arg-type]
        if session_msg_count > 0:
            message_count = session_msg_count
        else:
            # Fallback: 查询实际消息数
            messages = db.query(MessageModel).filter(
                and_(
                    MessageModel.session_id == session_uuid,
                    MessageModel.role.in_(["user", "assistant"])
                )
            ).order_by(MessageModel.created_at.asc()).all()
            message_count = len(messages)
        
        if not request.force:
            # 非强制模式下的检查
            if message_count < trigger_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Message count ({message_count}) is below trigger threshold ({trigger_length})"
                )
            
            # 如果已经有生成的标题，不再重复生成
            if session.title_generated_at is not None:
                return GenerateTitleResponse(
                    session_id=session_id,
                    title=str(session.title),  # type: ignore[arg-type]
                    generated_at=session.title_generated_at.replace(tzinfo=timezone.utc).isoformat(),
                    used_message_count=int(message_count)  # type: ignore[arg-type]
                )
        
        # 生成标题
        title_generator = SessionTitleGenerator(db)
        
        # 查询消息内容（用于生成标题）
        # 构建消息内容（限制消息数量）
        max_messages = request.max_messages or settings.session_title_max_messages
        messages = db.query(MessageModel).filter(
            and_(
                MessageModel.session_id == session_uuid,
                MessageModel.role.in_(["user", "assistant"])
            )
        ).order_by(MessageModel.created_at.asc()).limit(max_messages).all()
        messages_for_title = messages
        
        # 构建消息文本
        message_texts = []
        for msg in messages_for_title:
            msg_role = str(msg.role)  # type: ignore[arg-type]
            msg_content = str(msg.content)  # type: ignore[arg-type]
            role_name = "用户" if msg_role == "user" else "助手"
            content = msg_content[:200] if len(msg_content) > 200 else msg_content
            message_texts.append(f"{role_name}: {content}")
        
        messages_text = "\n".join(message_texts)
        
        # 构建提示词
        prompt_template = (
            "请根据以下对话内容，生成一个简洁的会话标题（不超过50个字）。"
            "标题应该概括对话的主要话题或核心内容。\n\n对话内容：\n{messages}\n\n"
            "请只返回标题，不要包含其他内容。"
        )
        prompt = prompt_template.format(messages=messages_text)
        
        # 创建AI引擎生成标题
        from app.engines.ai import ChatMessage as EngineChatMessage
        
        engine = engine_pool.get_engine(
            provider="openai",
            model=settings.session_title_model
        )
        
        response = await engine.chat(
            messages=[EngineChatMessage(role="user", content=prompt)],
            temperature=settings.session_title_temperature,
            max_tokens=settings.session_title_max_tokens
        )
        
        # 提取标题
        if response.message:
            if hasattr(response.message, 'content') and response.message.content:
                title = response.message.content.strip()
            elif isinstance(response.message, dict):
                title = response.message.get("content", "").strip()
            else:
                title = str(response.message).strip()
            
            # 清理标题
            title = title.replace('"', '').replace("'", '').replace('\n', ' ').strip()
            
            # 限制长度
            if len(title) > 50:
                title = title[:50]
            
            # 更新会话标题
            session.title = title  # type: ignore[assignment]
            session.title_generated_at = datetime.utcnow()  # type: ignore[assignment]
            session.updated_at = datetime.utcnow()  # type: ignore[assignment]
            db.commit()
            db.refresh(session)
            
            logger.info(
                "Generated session title via API",
                extra={
                    "user_id": str(user.id),
                    "session_id": session_id,
                    "title": title,
                    "message_count": message_count,
                    "used_message_count": len(messages_for_title)
                }
            )
            
            return GenerateTitleResponse(
                session_id=session_id,
                title=title,
                generated_at=session.title_generated_at.replace(tzinfo=timezone.utc).isoformat(),
                used_message_count=len(messages_for_title)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate title: AI response has no content"
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
        logger.error(f"Failed to generate session title: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate session title"
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
        
        # 软删除会话
        session.deleted_at = datetime.utcnow()  # type: ignore[assignment]
        
        # 删除该会话的所有消息（物理删除，因为消息通常不需要恢复）
        # 注意：虽然 Message 表有 CASCADE，但软删除不会触发，需要手动删除
        deleted_messages_count = db.query(MessageModel).filter(
            MessageModel.session_id == session_uuid
        ).delete()
        
        db.commit()
        
        logger.info(
            "Deleted session and messages",
            extra={
                "user_id": str(user.id),
                "session_id": session_id,
                "deleted_messages_count": deleted_messages_count
            }
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

