"""
聊天API接口(重构版)

提供OpenAI兼容的Chat Completions API,使用服务层架构
"""

# 标准库
import uuid
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple
from datetime import timezone, datetime

if TYPE_CHECKING:
    from app.engines.memory.manager import MemoryManager
    from app.core.personality.models import Personality
    from app.schemas.context import ContextBundle

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

# 本地库
from app.api.deps import (
    get_sync_session,
    get_current_active_user,
    get_personality_registry,
    get_tool_manager_factory,
    get_llm_engine_pool,
    get_memory_manager,
    get_context_builder,
)
from app.core.personality import PersonalityRegistry
from app.core.context.builder import ContextBuilder
from app.engines.ai import ChatMessage as EngineChatMessage
from app.engines.ai.engine_pool import LLMEnginePool
from app.config.config import settings
from app.engines.tools.factory import ToolManagerFactory
from app.middleware.rate_limit import rate_limit
from app.models.session import Session as SessionModel
from app.utils.message_utils import (
    detect_message_hints as _detect_message_hints,
    merge_user_preferences as _merge_user_preferences,
    build_user_message_with_preferences as _build_user_message_with_preferences,
    DEFAULT_INSTRUCTION_PREFS,
    PREFERENCE_KEYS,
)
from app.models.message import Message as MessageModel
from app.models.user import User
from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    EngineListResponse,
    SaveVoiceCallMessagesRequest,
    SaveVoiceCallMessagesResponse,
)
from app.utils.logger import logger
from app.services.chat import (
    MessageSaver,
    ToolCallHandler,
    ChatService,
    StreamChatService
)

router = APIRouter()


# 消息处理辅助函数已移至 app.utils.message_utils


def _convert_context_bundle_to_messages(
    context_bundle: "ContextBundle",
    current_message_content: str,
    user_preferences: Optional[Dict[str, Any]] = None
) -> list[EngineChatMessage]:
    """将ContextBundle转换为LLM消息列表"""
    messages = []
    
    # 1. 系统提示词
    for prompt in context_bundle.system_prompts:
        messages.append(EngineChatMessage(role="system", content=prompt))
    
    # 2. 用户画像
    if context_bundle.user_profile:
        profile_text = "## 用户信息\n"
        if isinstance(context_bundle.user_profile, dict):
            for key, value in context_bundle.user_profile.items():
                profile_text += f"- {key}: {value}\n"
        else:
            profile_text += str(context_bundle.user_profile)
        messages.append(EngineChatMessage(role="system", content=profile_text))
    
    # 3. 历史摘要
    if context_bundle.summarized_history:
        summary_text = "## 对话历史摘要\n\n"
        for i, summary in enumerate(context_bundle.summarized_history, 1):
            summary_text += f"**摘要 {i}**:\n{summary}\n\n"
        messages.append(EngineChatMessage(role="system", content=summary_text))
    
    # 4. 检索到的记忆
    if context_bundle.retrieved_memories:
        from app.engines.memory.models import MemoryType
        
        user_memories = [m for m in context_bundle.retrieved_memories if m.memory_type == MemoryType.USER]
        assistant_memories = [m for m in context_bundle.retrieved_memories if m.memory_type == MemoryType.ASSISTANT]
        
        memory_text = "## 相关记忆\n\n"
        if user_memories:
            memory_text += "### 用户相关记忆\n"
            for mem in user_memories[:5]:
                memory_text += f"- {mem.content}\n"
            memory_text += "\n"
        
        if assistant_memories:
            memory_text += "### 对话历史记忆\n"
            for mem in assistant_memories[:5]:
                memory_text += f"- {mem.content}\n"
            memory_text += "\n"
        
        messages.append(EngineChatMessage(role="system", content=memory_text))
    
    # 5. 最近消息
    if context_bundle.recent_messages:
        for msg in context_bundle.recent_messages:
            messages.append(EngineChatMessage(role=msg.role, content=msg.content))
    
    # 6. 用户偏好指令
    final_message, instruction_text = _build_user_message_with_preferences(
        current_message_content,
        user_preferences
    )
    
    if instruction_text:
        messages.append(EngineChatMessage(
            role="system",
            content=f"## 回答要求\n{instruction_text}"
        ))
    
    # 7. 当前用户消息
    messages.append(EngineChatMessage(role="user", content=final_message))
    
    return messages


@router.post("/completions", response_model=ChatCompletionResponse)
@rate_limit("30/minute", per_user=True)
async def create_chat_completion(
    request: Request,
    data: ChatCompletionRequest,
    response: Response,
    db: Session = Depends(get_sync_session),
    personality_registry: PersonalityRegistry = Depends(get_personality_registry),
    tool_factory: ToolManagerFactory = Depends(get_tool_manager_factory),
    engine_pool: LLMEnginePool = Depends(get_llm_engine_pool),
    context_builder: ContextBuilder = Depends(get_context_builder),
    memory_manager: "MemoryManager" = Depends(get_memory_manager),
):
    """创建聊天补全(OpenAI兼容接口)"""
    try:
        # 1. 确定personality_id和user_id
        personality_id, user_id, session = _get_ids_from_request(data, db)
        
        # 2. 加载用户和人格配置
        user_obj = _load_user(user_id, db)
        personality = _load_personality(personality_id, personality_registry)
        
        # 3. 确定模型和引擎参数
        actual_model, actual_engine_type, actual_max_tokens = _determine_engine_params(
            data, personality
        )
        
        # 4. 加载工具
        tools = _load_tools(personality, tool_factory, data)
        
        # 5. 合并用户偏好
        user_prompt_preferences = _merge_user_preferences(personality, user_obj)
        
        # 6. 创建AI引擎
        engine = engine_pool.get_engine(provider=actual_engine_type, model=actual_model)
        
        # 7. 构建上下文
        full_messages = await _build_context(
            data, user_id, personality_id, personality, user_prompt_preferences,
            context_builder, memory_manager, personality_registry, engine_pool
        )
        
        # 8. 初始化服务
        message_saver = MessageSaver(db)
        tool_handler = ToolCallHandler(tool_factory)
        
        # 9. 生成响应
        if data.stream:
            stream_service = StreamChatService(tool_handler, message_saver, personality_registry)
            return StreamingResponse(
                stream_service.generate_stream(
                    engine=engine,
                    messages=full_messages,
                    tools=tools,
                    actual_max_tokens=actual_max_tokens,
                    actual_model=actual_model,
                    temperature=data.temperature,
                    personality_id=personality_id,
                    personality=personality,
                    user_id=user_id,
                    session_id=data.session_id,
                    use_memory=data.use_memory,
                    memory_manager=memory_manager
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            chat_service = ChatService(message_saver)
            chat_response = await chat_service.generate_response(
                engine=engine,
                messages=full_messages,
                tools=tools,
                actual_max_tokens=actual_max_tokens,
                temperature=data.temperature,
                personality=personality,
                user_id=user_id,
                session_id=data.session_id,
                use_memory=data.use_memory,
                memory_manager=memory_manager
            )
            
            return ChatCompletionResponse(
                id=chat_response.id,
                created=chat_response.created,
                model=chat_response.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=chat_response.message.to_dict() if hasattr(chat_response.message, 'to_dict') else chat_response.message,  # type: ignore[arg-type]
                        finish_reason=chat_response.finish_reason
                    )
                ],
                usage=ChatCompletionUsage(**chat_response.usage) if chat_response.usage else ChatCompletionUsage(
                    prompt_tokens=0, completion_tokens=0, total_tokens=0
                )
            )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Chat completion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        )


# 辅助函数

def _get_ids_from_request(data, db):
    """从请求中获取personality_id和user_id"""
    personality_id = data.personality_id
    user_id = data.user_id
    session = None
    
    if data.session_id:
        try:
            session_uuid = uuid.UUID(data.session_id)
            session = db.query(SessionModel).filter(SessionModel.id == session_uuid).first()
            if session:
                if not personality_id:
                    personality_id = str(session.personality_id)  # type: ignore[arg-type]
                if not user_id:
                    user_id = str(session.user_id)  # type: ignore[arg-type]
        except Exception as e:
            logger.warning(f"Failed to get session info: {e}", exc_info=False)
    
    return personality_id, user_id, session


def _load_user(user_id, db):
    """加载用户对象"""
    if user_id:
        try:
            user_uuid = uuid.UUID(str(user_id))
            return db.query(User).filter(User.id == user_uuid).first()
        except Exception as e:
            logger.warning(f"Failed to load user: {e}", exc_info=False)
    return None


def _load_personality(personality_id, personality_registry):
    """加载人格配置"""
    if personality_id:
        try:
            return personality_registry.get_personality(personality_id)
        except Exception as e:
            logger.warning(f"Failed to load personality: {e}", exc_info=True)
    return None


def _determine_engine_params(data, personality):
    """确定引擎参数"""
    actual_model = data.model
    actual_engine_type = data.engine_type or "openai"
    actual_max_tokens = data.max_tokens
    
    if personality:
        actual_model = personality.ai.model
        actual_engine_type = personality.ai.provider
        if actual_max_tokens is None:
            actual_max_tokens = personality.ai.max_tokens
    
    if not actual_model:
        actual_model = "gpt-3.5-turbo"
    
    if actual_max_tokens is None:
        actual_max_tokens = 8192 if "gpt-4" in actual_model.lower() else 4096
    
    return actual_model, actual_engine_type, actual_max_tokens


def _load_tools(personality, tool_factory, data):
    """加载工具列表"""
    tools = data.tools
    
    if personality and personality.tools.enabled and (tools is None or len(tools) == 0):
        tool_manager = tool_factory.get_tool_manager(allowed_tools=personality.tools.allowed_tools)
        tools = tool_manager.get_tools_for_openai(tool_names=personality.tools.allowed_tools)
    
    return tools


async def _build_context(
    data, user_id, personality_id, personality, user_prompt_preferences,
    context_builder, memory_manager, personality_registry, engine_pool
):
    """构建上下文"""
    use_intelligent_context = (
        getattr(settings, 'context_intelligent_enabled', True) and
        user_id and data.session_id and personality_id and len(data.messages) > 0
    )
    
    if use_intelligent_context:
        try:
            current_message_content = data.messages[-1].content or ""
            context_bundle = await context_builder.build_context(
                user_id=user_id,
                session_id=data.session_id,
                current_message=current_message_content,
                personality_config=personality,
                max_tokens=getattr(settings, 'context_max_tokens', 4096)
            )
            return _convert_context_bundle_to_messages(
                context_bundle, current_message_content, user_prompt_preferences
            )
        except Exception as e:
            logger.warning(f"Failed to build intelligent context: {e}", exc_info=True)
    
    # 降级:简单模式
    full_messages = []
    if personality and personality.ai.system_prompt:
        full_messages.append(EngineChatMessage(role="system", content=personality.ai.system_prompt))
    
    for msg in data.messages:
        full_messages.append(EngineChatMessage(
            role=msg.role,
            content=msg.content,
            name=msg.name,
            function_call=msg.function_call,
            tool_calls=msg.tool_calls
        ))
    
    return full_messages


@router.get("/engines", response_model=EngineListResponse)
async def list_engines() -> EngineListResponse:
    """列出所有可用的AI引擎"""
    try:
        from app.engines.ai.factory import AIEngineFactory
        available_engines = AIEngineFactory.list_available_engines()
        
        return EngineListResponse(
            engines=list(available_engines.keys()),
            default_engine="openai",
            descriptions=available_engines
        )
    except Exception as e:
        logger.error(f"Failed to list engines: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list engines"
        )


@router.post("/voice-call-messages", response_model=SaveVoiceCallMessagesResponse)
async def save_voice_call_messages(
    request: SaveVoiceCallMessagesRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """保存语音通话消息到数据库"""
    try:
        session_uuid = uuid.UUID(request.session_id)
        
        # 验证会话
        session = db.query(SessionModel).filter(
            and_(
                SessionModel.id == session_uuid,
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
        # 保存消息
        saved_count = 0
        for msg in request.messages:
            message = MessageModel(
                session_id=session_uuid,
                user_id=user.id,
                role=msg.role,
                content=msg.content,
                created_at=datetime.utcnow(),
                message_metadata={"is_voice_call": True}
            )
            db.add(message)
            saved_count += 1
        
        # 更新会话统计
        session.message_count = (session.message_count or 0) + saved_count  # type: ignore[assignment]
        session.last_message_at = datetime.utcnow()  # type: ignore[assignment]
        
        db.commit()
        
        logger.info(
            "Saved voice call messages",
            extra={"user_id": str(user.id), "session_id": request.session_id, "saved_count": saved_count}
        )
        
        return SaveVoiceCallMessagesResponse(
            message="消息已保存",
            saved_count=saved_count,
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save voice call messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save voice call messages: {str(e)}"
        )

