"""
聊天编排器

统一编排所有服务，处理完整的对话流程：
1. 请求验证和准备
2. 上下文构建
3. 工具准备
4. AI生成
5. 消息保存
6. 错误处理
"""

# 标准库
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Tuple, cast

if TYPE_CHECKING:
    from app.core.personality.models import Personality
    from app.core.personality import PersonalityRegistry
    from app.engines.ai.base import AIEngineBase
    from app.engines.ai.engine_pool import LLMEnginePool
    from app.engines.memory.manager import MemoryManager
    from app.engines.tools.factory import ToolManagerFactory
    from app.models.user import User
    from app.models.session import Session as SessionModel
    from sqlalchemy.ext.asyncio import AsyncSession

# 第三方库
from fastapi.responses import StreamingResponse

# 本地库
from app.engines.ai import ChatMessage as EngineChatMessage
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from app.services.chat import ChatService, MessageSaver, StreamChatService, ToolCallHandler
from app.utils.exceptions import ChatServiceError, ValidationError, ResourceNotFoundError
from app.utils.logger import logger
from app.utils.message_utils import (
    merge_user_preferences as _merge_user_preferences,
)
from app.utils.message_converter import convert_context_bundle_to_messages

if TYPE_CHECKING:
    from app.core.context.builder import ContextBuilder
    from app.services.context.context_service import ContextService


@dataclass
class PreparedRequest:
    """准备好的请求数据"""
    personality_id: str
    user_id: str
    session_id: Optional[str]
    session: Optional["SessionModel"]
    user_obj: Optional["User"]
    personality: "Personality"
    model: str
    engine_type: str
    max_tokens: int


class ChatOrchestrator:
    """聊天编排器
    
    统一编排所有服务，处理完整的对话流程
    """
    
    def __init__(
        self,
        personality_registry: "PersonalityRegistry",
        tool_factory: "ToolManagerFactory",
        engine_pool: "LLMEnginePool",
        context_builder: "ContextBuilder",
        memory_manager: "MemoryManager",
        context_service: Optional["ContextService"] = None,
    ):
        """初始化聊天编排器
        
        Args:
            personality_registry: 人格注册表
            tool_factory: 工具管理器工厂
            engine_pool: LLM引擎池
            context_builder: 上下文构建器（旧版，用于兼容）
            memory_manager: 记忆管理器
            context_service: 上下文服务（新版，优先使用）
        """
        self.personality_registry = personality_registry
        self.tool_factory = tool_factory
        self.engine_pool = engine_pool
        self.memory_manager = memory_manager
        # 优先使用新的ContextService，如果不存在则使用旧的ContextBuilder（兼容模式）
        self.context_service = context_service
        self.context_builder = context_builder if context_service is None else None
    
    async def process_request(
        self,
        request: ChatCompletionRequest,
        user: "User",
        db: "AsyncSession"
    ) -> Any:  # ChatCompletionResponse | StreamingResponse
        """处理聊天请求
        
        Args:
            request: 聊天请求
            user: 当前用户
            db: 数据库会话（异步）
            
        Returns:
            ChatCompletionResponse | StreamingResponse: 聊天响应
            
        Raises:
            ChatServiceError: 聊天服务异常
            ValidationError: 验证错误
            ResourceNotFoundError: 资源未找到
        """
        try:
            # 1. 验证和准备
            prepared = await self._prepare_request(request, user, db)
            
            # 2. 构建上下文
            messages = await self._build_context(
                request=request,
                user_id=prepared.user_id,
                session_id=prepared.session_id,
                personality=prepared.personality,
                user_obj=prepared.user_obj,
                db=db
            )
            
            # 3. 准备工具
            tools = await self._prepare_tools(
                personality=prepared.personality,
                requested_tools=request.tools
            )
            
            # 4. 获取AI引擎
            engine = self.engine_pool.get_engine(
                provider=prepared.engine_type,
                model=prepared.model
            )
            
            # 5. 初始化服务
            message_saver = MessageSaver(db)
            tool_handler = ToolCallHandler(self.tool_factory)
            
            # 6. 生成响应
            if request.stream:
                stream_service = StreamChatService(
                    tool_handler,
                    message_saver,
                    self.personality_registry
                )
                return StreamingResponse(
                    stream_service.generate_stream(
                        engine=engine,
                        messages=messages,
                        tools=tools,
                        actual_max_tokens=prepared.max_tokens,
                        actual_model=prepared.model,
                        temperature=request.temperature,
                        personality_id=prepared.personality_id,
                        personality=prepared.personality,
                        user_id=prepared.user_id,
                        session_id=prepared.session_id,
                        use_memory=request.use_memory,
                        memory_manager=self.memory_manager
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
                    messages=messages,
                    tools=tools,
                    actual_max_tokens=prepared.max_tokens,
                    temperature=request.temperature,
                    personality=prepared.personality,
                    user_id=prepared.user_id,
                    session_id=prepared.session_id,
                    use_memory=request.use_memory,
                    memory_manager=self.memory_manager
                )
                
                # 7. 构建响应
                from app.schemas.chat import ChatCompletionChoice, ChatCompletionUsage
                return ChatCompletionResponse(
                    id=chat_response.id,
                    created=chat_response.created,
                    model=chat_response.model,
                    choices=[
                        ChatCompletionChoice(
                            index=0,
                            message=cast(Dict[str, Any], chat_response.message.to_dict() if hasattr(chat_response.message, 'to_dict') else chat_response.message),
                            finish_reason=chat_response.finish_reason
                        )
                    ],
                    usage=ChatCompletionUsage(
                        prompt_tokens=chat_response.usage.get("prompt_tokens", 0) if isinstance(chat_response.usage, dict) else (chat_response.usage.prompt_tokens if hasattr(chat_response.usage, 'prompt_tokens') else 0),
                        completion_tokens=chat_response.usage.get("completion_tokens", 0) if isinstance(chat_response.usage, dict) else (chat_response.usage.completion_tokens if hasattr(chat_response.usage, 'completion_tokens') else 0),
                        total_tokens=chat_response.usage.get("total_tokens", 0) if isinstance(chat_response.usage, dict) else (chat_response.usage.total_tokens if hasattr(chat_response.usage, 'total_tokens') else 0)
                    ) if chat_response.usage else ChatCompletionUsage(
                        prompt_tokens=0, completion_tokens=0, total_tokens=0
                    )
                )
                
        except (ValidationError, ResourceNotFoundError) as e:
            # 业务异常，直接抛出
            raise
        except Exception as e:
            logger.error(f"Chat orchestration failed: {e}", exc_info=True)
            raise ChatServiceError(f"Chat completion failed: {str(e)}") from e
    
    async def _prepare_request(
        self,
        request: ChatCompletionRequest,
        user: "User",
        db: "AsyncSession"
    ) -> "PreparedRequest":
        """准备请求数据
        
        Args:
            request: 聊天请求
            user: 当前用户
            db: 数据库会话
            
        Returns:
            PreparedRequest: 准备好的请求数据
            
        Raises:
            ValidationError: 验证错误
            ResourceNotFoundError: 资源未找到
        """
        from dataclasses import dataclass
        from sqlalchemy import select, and_
        from app.models.session import Session as SessionModel
        
        # 1. 确定personality_id和user_id（验证用户权限）
        personality_id = request.personality_id
        user_id = request.user_id
        session = None
        
        # 如果请求中指定了user_id，必须与当前用户匹配（除非是管理员）
        if user_id:
            user_uuid = uuid.UUID(str(user_id))
            from app.utils.type_helpers import get_user_role, is_admin_user
            if user_uuid != user.id and not is_admin_user(user):
                raise ValidationError("无权访问其他用户的数据")
            user_id = str(user.id)  # 使用当前用户的ID
        else:
            # 如果没有指定user_id，使用当前用户的ID
            user_id = str(user.id)
        
        if request.session_id:
            try:
                session_uuid = uuid.UUID(request.session_id)
                # 使用selectinload优化，避免后续访问session属性时的额外查询
                from sqlalchemy.orm import selectinload
                stmt = select(SessionModel).options(
                    selectinload(SessionModel.user)  # 预加载用户信息（如果需要）
                ).where(
                    and_(
                        SessionModel.id == session_uuid,
                        SessionModel.user_id == user.id,  # 确保只能访问自己的会话
                        SessionModel.deleted_at.is_(None)
                    )
                )
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                if session:
                    if not personality_id:
                        from app.utils.type_helpers import get_session_personality_id
                        personality_id = get_session_personality_id(session)
                    user_id = str(user.id)  # 使用当前用户的ID
                else:
                    raise ResourceNotFoundError("会话不存在或无权访问")
            except (ValidationError, ResourceNotFoundError):
                raise
            except Exception as e:
                logger.warning(f"Failed to get session info: {e}", exc_info=False)
                raise ValidationError(f"无效的会话ID: {str(e)}")
        
        if not personality_id:
            raise ValidationError("personality_id is required")
        
        # 2. 加载用户和人格配置
        user_obj = None
        if user_id:
            try:
                from app.models.user import User
                user_uuid = uuid.UUID(str(user_id))
                stmt = select(User).where(User.id == user_uuid)
                result = await db.execute(stmt)
                user_obj = result.scalar_one_or_none()
            except Exception as e:
                logger.warning(f"Failed to load user: {e}", exc_info=False)
        
        personality = self.personality_registry.get_personality(personality_id)
        if not personality:
            raise ResourceNotFoundError(f"Personality '{personality_id}' not found")
        
        # 3. 确定模型和引擎参数
        actual_model = request.model or personality.ai.model
        actual_engine_type = request.engine_type or personality.ai.provider or "openai"
        actual_max_tokens = request.max_tokens or personality.ai.max_tokens
        
        if not actual_model:
            actual_model = "gpt-3.5-turbo"
        
        if actual_max_tokens is None:
            actual_max_tokens = 8192 if "gpt-4" in actual_model.lower() else 4096
        
        return PreparedRequest(
            personality_id=personality_id,
            user_id=user_id,
            session_id=request.session_id,
            session=session,
            user_obj=user_obj,
            personality=personality,
            model=actual_model,
            engine_type=actual_engine_type,
            max_tokens=actual_max_tokens
        )
    
    async def _build_context(
        self,
        request: ChatCompletionRequest,
        user_id: str,
        session_id: Optional[str],
        personality: "Personality",
        user_obj: Optional["User"],
        db: "AsyncSession"
    ) -> List[EngineChatMessage]:
        """构建上下文
        
        Args:
            request: 聊天请求
            user_id: 用户ID
            session_id: 会话ID
            personality: 人格配置
            user_obj: 用户对象
            db: 数据库会话
            
        Returns:
            List[EngineChatMessage]: 完整的消息列表
        """
        from app.config.config import settings
        
        # 检查是否使用智能上下文
        use_intelligent_context = (
            getattr(settings, 'context_intelligent_enabled', True) and
            user_id and session_id and personality and len(request.messages) > 0
        )
        
        if use_intelligent_context:
            try:
                current_message_content = request.messages[-1].content or ""
                
                # 合并用户偏好
                user_prompt_preferences = _merge_user_preferences(personality, user_obj)
                
                # 使用ContextService构建上下文（统一使用新实现）
                if self.context_service:
                    context_bundle = await self.context_service.build_context(
                        user_id=user_id,
                        session_id=session_id,
                        current_message=current_message_content,
                        personality_config=personality,
                        max_tokens=getattr(settings, 'context_max_tokens', 4096)
                    )
                elif self.context_builder:
                    # 降级：使用旧的ContextBuilder（兼容模式，将在v2.0移除）
                    logger.warning("Using legacy ContextBuilder, please migrate to ContextService")
                    context_bundle = await self.context_builder.build_context(
                        user_id=user_id,
                        session_id=session_id,
                        current_message=current_message_content,
                        personality_config=personality,
                        max_tokens=getattr(settings, 'context_max_tokens', 4096)
                    )
                else:
                    raise ChatServiceError("No context service available")
                
                # 转换为消息格式（使用统一的转换函数）
                return convert_context_bundle_to_messages(
                    context_bundle,
                    current_message_content,
                    user_prompt_preferences
                )
            except Exception as e:
                logger.warning(f"Failed to build intelligent context: {e}", exc_info=True)
        
        # 降级：简单模式
        full_messages = []
        if personality and personality.ai.system_prompt:
            full_messages.append(EngineChatMessage(role="system", content=personality.ai.system_prompt))
        
        for msg in request.messages:
            full_messages.append(EngineChatMessage(
                role=msg.role,
                content=msg.content,
                name=msg.name,
                function_call=msg.function_call,
                tool_calls=msg.tool_calls
            ))
        
        return full_messages
    
    async def _prepare_tools(
        self,
        personality: "Personality",
        requested_tools: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        """准备工具列表
        
        Args:
            personality: 人格配置
            requested_tools: 请求的工具列表
            
        Returns:
            Optional[List[Dict[str, Any]]]: 工具列表
        """
        tools = requested_tools
        
        if personality and personality.tools.enabled and (tools is None or len(tools) == 0):
            tool_manager = self.tool_factory.get_tool_manager(allowed_tools=personality.tools.allowed_tools)
            tools = tool_manager.get_tools_for_openai(tool_names=personality.tools.allowed_tools)
        
        return tools
