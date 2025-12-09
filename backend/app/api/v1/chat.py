"""
聊天API接口(简化版)

提供OpenAI兼容的Chat Completions API，使用编排器模式
"""

# 标准库
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.orchestration.chat_orchestrator import ChatOrchestrator

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.api.deps import (
    get_db,
    get_current_active_user_async,
    get_chat_orchestrator,
)
from app.middleware.rate_limit import rate_limit
from app.models.user import User
from app.schemas.chat import (
    ChatCompletionRequest,
    EngineListResponse,
    SaveVoiceCallMessagesRequest,
    SaveVoiceCallMessagesResponse,
)
from app.utils.exceptions import ChatServiceError, ValidationError, ResourceNotFoundError
from app.utils.logger import logger

router = APIRouter()


@router.post("/completions", response_model=None)
@rate_limit("30/minute", per_user=True)
async def create_chat_completion(
    request: Request,
    data: ChatCompletionRequest,
    response: Response,
    current_user: User = Depends(get_current_active_user_async),
    db: AsyncSession = Depends(get_db),
    orchestrator: "ChatOrchestrator" = Depends(get_chat_orchestrator),
):
    """创建聊天补全(OpenAI兼容接口)
    
    使用编排器模式，简化API层逻辑
    """
    # 基本参数验证
    if not data.messages:
        raise ValidationError("messages cannot be empty")
    
    # 调用编排器处理请求（异常由全局异常处理器处理）
    return await orchestrator.process_request(
        request=data,
        user=current_user,
        db=db
    )


@router.get("/engines", response_model=EngineListResponse)
async def list_engines(
    current_user: User = Depends(get_current_active_user_async),
) -> EngineListResponse:
    """列出所有可用的AI引擎"""
    from app.engines.ai.factory import AIEngineFactory
    available_engines = AIEngineFactory.list_available_engines()
    
    return EngineListResponse(
        engines=list(available_engines.keys()),
        default_engine="openai",
        descriptions=available_engines
    )


@router.post("/voice-call-messages", response_model=SaveVoiceCallMessagesResponse)
async def save_voice_call_messages(
    request: SaveVoiceCallMessagesRequest,
    user: User = Depends(get_current_active_user_async),
    db: AsyncSession = Depends(get_db)
):
    """保存语音通话消息到数据库"""
    import uuid
    from datetime import datetime
    from sqlalchemy import select, and_
    from app.models.session import Session as SessionModel
    from app.models.message import Message as MessageModel
    
    try:
        session_uuid = uuid.UUID(request.session_id)
        
        # 验证会话
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
            raise ResourceNotFoundError("Session not found")
        
        # 保存消息（过滤空消息）
        saved_count = 0
        for msg in request.messages:
            # 验证消息内容不为空
            if not msg.content or not msg.content.strip():
                logger.warning(
                    f"Skipping message with empty content",
                    extra={"user_id": str(user.id), "session_id": request.session_id, "role": msg.role}
                )
                continue
            
            # 验证role字段
            if msg.role not in ['user', 'assistant', 'system', 'tool']:
                logger.warning(
                    f"Skipping message with invalid role: {msg.role}",
                    extra={"user_id": str(user.id), "session_id": request.session_id}
                )
                continue
            
            try:
                message = MessageModel(
                    session_id=session_uuid,
                    user_id=user.id,
                    role=msg.role,
                    content=msg.content.strip(),
                    created_at=datetime.utcnow(),
                    message_metadata={"is_voice_call": True}
                )
                db.add(message)
                saved_count += 1
            except Exception as msg_error:
                logger.error(
                    f"Failed to create message object: {msg_error}",
                    extra={"user_id": str(user.id), "session_id": request.session_id, "role": msg.role},
                    exc_info=True
                )
                continue
        
        # 如果没有保存任何消息，返回友好提示
        if saved_count == 0:
            return SaveVoiceCallMessagesResponse(
                message="没有有效的消息需要保存（所有消息内容为空）",
                saved_count=0,
                session_id=request.session_id
            )
        
        # 更新会话统计
        # SQLAlchemy ORM属性赋值，使用cast明确类型
        from typing import cast
        from datetime import datetime
        current_count = cast(int, session.message_count) if session.message_count is not None else 0
        session.message_count = cast(int, current_count + saved_count)
        session.last_message_at = cast(datetime, datetime.utcnow())
        
        await db.commit()
        
        logger.info(
            "Saved voice call messages",
            extra={"user_id": str(user.id), "session_id": request.session_id, "saved_count": saved_count}
        )
        
        return SaveVoiceCallMessagesResponse(
            message="消息已保存",
            saved_count=saved_count,
            session_id=request.session_id
        )
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save voice call messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save voice call messages: {str(e)}"
        )

