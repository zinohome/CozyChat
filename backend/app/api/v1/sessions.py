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
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, and_, func, select

# 本地库
from app.api.deps import (
    get_current_active_user_async,
    get_db,
    get_personality_registry,
    get_llm_engine_pool,
    get_sync_session,
)
from app.core.personality import PersonalityRegistry
from app.engines.ai.engine_pool import LLMEnginePool
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.message import Message as MessageModel
from app.utils.logger import logger
from app.utils.type_helpers import (
    get_session_title,
    get_session_personality_id,
    get_session_message_count,
    get_message_role,
    get_message_content,
    safe_int
)
from typing import cast
from datetime import datetime

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
    user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
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
        await db.commit()
        await db.refresh(session)
        
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
            # SQLAlchemy ORM属性赋值，使用cast明确类型
            from typing import cast
            from datetime import datetime
            session.message_count = cast(int, 1)
            session.last_message_at = cast(datetime, welcome_message.created_at)
            await db.commit()
            
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
            personality_id=get_session_personality_id(session),
            title=get_session_title(session) or "",
            created_at=session.created_at.replace(tzinfo=timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
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
    user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
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
        # 构建查询（异步版本）
        stmt = select(SessionModel).where(
            and_(
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        )
        
        # 人格过滤
        if personality_id:
            stmt = stmt.where(SessionModel.personality_id == personality_id)
        
        # 排序
        # 如果按 last_message_at 排序，需要处理 null 值（使用 created_at 作为后备）
        if sort == "last_message_at":
            # 使用 COALESCE 处理 null 值：如果 last_message_at 为 null，使用 created_at
            # 使用部分索引 idx_sessions_user_deleted_lastmsg 优化此查询
            sort_column = func.coalesce(SessionModel.last_message_at, SessionModel.created_at)
            if order == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(sort_column)
        else:
            # 使用部分索引 idx_sessions_user_deleted_created 优化此查询
            sort_column = getattr(SessionModel, sort, SessionModel.created_at)
            if order == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(sort_column)
        
        # 总数（优化：使用子查询避免重复计算）
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()
        
        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        # 构建响应
        items = []
        for session in sessions:
            personality = personality_registry.get_personality(get_session_personality_id(session))
            items.append(SessionListItem(
                session_id=str(session.id),
                personality_id=get_session_personality_id(session),
                personality_name=cast(str, personality.name) if personality else None,
                title=get_session_title(session) or "",
                message_count=get_session_message_count(session),
                last_message_at=cast(datetime, session.last_message_at).replace(tzinfo=timezone.utc).isoformat() if session.last_message_at is not None else None,
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
    user: User = Depends(get_current_active_user_async),
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
        
        # 查询会话（异步版本，使用selectinload优化，避免N+1查询）
        from sqlalchemy.orm import selectinload
        stmt = select(SessionModel).options(
            selectinload(SessionModel.messages)
        ).where(
            and_(
                SessionModel.id == session_uuid,
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # 消息已通过selectinload加载，直接使用关系属性
        # 按创建时间排序
        messages = sorted(session.messages, key=lambda m: m.created_at)
        
        # 构建响应
        message_items = []
        for msg in messages:
            # 注意：Message 模型中有 metadata = Base.metadata（SQLAlchemy 元数据对象）
            # 实际的 JSONB 字段是 message_metadata，必须使用 message_metadata 而不是 metadata
            # 使用is not None检查，避免comparison-overlap错误
            msg_metadata: Dict[str, Any] = {}
            if msg.message_metadata is not None:
                msg_metadata = cast(Dict[str, Any], msg.message_metadata)
            
            # 确保 metadata 是字典类型
            if not isinstance(msg_metadata, dict):
                msg_metadata = {}
            
            message_items.append(
                MessageInfo(
                    id=str(msg.id),
                    role=get_message_role(msg),
                    content=get_message_content(msg),
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
            personality_id=get_session_personality_id(session),
            title=get_session_title(session) or "",
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
    user: User = Depends(get_current_active_user_async),
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
        # SQLAlchemy ORM属性赋值，使用cast明确类型
        from typing import cast
        from datetime import datetime
        if request.title is not None:
            session.title = cast(str, request.title)
        
        session.updated_at = cast(datetime, datetime.utcnow())
        await db.commit()
        await db.refresh(session)
        
        logger.info(
            "Updated session",
            extra={"user_id": str(user.id), "session_id": session_id}
        )
        
        return UpdateSessionResponse(
            session_id=str(session.id),
            title=get_session_title(session) or "",
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
        await db.rollback()
        logger.error(f"Failed to update session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )


@router.post("/{session_id}/title", response_model=GenerateTitleResponse)
async def generate_session_title(
    session_id: str,
    request: GenerateTitleRequest,
    user: User = Depends(get_current_active_user_async),  # 使用异步版本的认证
    db: AsyncSession = Depends(get_db),  # 统一使用异步会话
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
        # 使用配置适配器获取会话配置（优先YAML，回退到Settings）
        from app.utils.config_adapter import get_config_adapter
        config_adapter = get_config_adapter()
        session_config = config_adapter.get_session_config()
        title_config = session_config.get("title", {})
        trigger_length = title_config.get("trigger_length", settings.session_title_trigger_length)
        
        # 优先使用session.message_count字段（性能更好，避免时序问题）
        # 如果字段为None或0，再查询实际消息数
        session_msg_count = get_session_message_count(session)
        if session_msg_count > 0:
            message_count = session_msg_count
        else:
            # Fallback: 查询实际消息数
            stmt = select(MessageModel).where(
                and_(
                    MessageModel.session_id == session_uuid,
                    MessageModel.role.in_(["user", "assistant"])
                )
            ).order_by(MessageModel.created_at.asc())
            result = await db.execute(stmt)
            messages = result.scalars().all()
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
                    title=get_session_title(session) or "",
                    generated_at=session.title_generated_at.replace(tzinfo=timezone.utc).isoformat(),
                    used_message_count=safe_int(message_count)
                )
        
        # 生成标题
        title_generator = SessionTitleGenerator(db)
        
        # 查询消息内容（用于生成标题）
        # 构建消息内容（限制消息数量）
        # 使用配置适配器获取会话配置（优先YAML，回退到Settings）
        from app.utils.config_adapter import get_config_adapter
        config_adapter = get_config_adapter()
        session_config = config_adapter.get_session_config()
        title_config = session_config.get("title", {})
        max_messages = request.max_messages or title_config.get("max_messages", settings.session_title_max_messages)
        stmt = select(MessageModel).where(
            and_(
                MessageModel.session_id == session_uuid,
                MessageModel.role.in_(["user", "assistant"])
            )
        ).order_by(MessageModel.created_at.asc()).limit(max_messages)
        result = await db.execute(stmt)
        messages = result.scalars().all()
        messages_for_title = messages
        
        # 构建消息文本
        message_texts = []
        for msg in messages_for_title:
            msg_role = get_message_role(msg)
            msg_content = get_message_content(msg)
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
        
        # 使用配置适配器获取会话配置（优先YAML，回退到Settings）
        from app.utils.config_adapter import get_config_adapter
        config_adapter = get_config_adapter()
        session_config = config_adapter.get_session_config()
        title_config = session_config.get("title", {})
        
        engine = engine_pool.get_engine(
            provider="openai",
            model=title_config.get("model", settings.session_title_model)
        )
        
        response = await engine.chat(
            messages=[EngineChatMessage(role="user", content=prompt)],
            temperature=title_config.get("temperature", settings.session_title_temperature),
            max_tokens=title_config.get("max_tokens", settings.session_title_max_tokens)
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
            # SQLAlchemy ORM属性赋值，使用cast明确类型
            from typing import cast
            from datetime import datetime
            session.title = cast(str, title)
            session.title_generated_at = cast(datetime, datetime.utcnow())
            session.updated_at = cast(datetime, datetime.utcnow())
            await db.commit()
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
        await db.rollback()
        logger.error(f"Failed to generate session title: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate session title"
        )


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_active_user_async),
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
        stmt = select(SessionModel).where(
            and_(
                SessionModel.id == session_uuid,
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # 软删除会话
        # SQLAlchemy ORM属性赋值，使用cast明确类型
        from typing import cast
        from datetime import datetime
        session.deleted_at = cast(datetime, datetime.utcnow())
        
        # 删除该会话的所有消息（物理删除，因为消息通常不需要恢复）
        # 注意：虽然 Message 表有 CASCADE，但软删除不会触发，需要手动删除
        from sqlalchemy import delete
        delete_stmt = delete(MessageModel).where(
            MessageModel.session_id == session_uuid
        )
        result = await db.execute(delete_stmt)
        deleted_messages_count = result.rowcount
        
        await db.commit()
        
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
        await db.rollback()
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

