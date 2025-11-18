"""
核心编排器

协调AI引擎、记忆、工具等模块，处理完整的对话流程
"""

# 标准库
import time
from typing import Any, AsyncIterator, Dict, List, Optional

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.engines.ai.base import AIEngineBase, ChatMessage, MessageRole
from app.engines.ai.factory import AIEngineFactory
from app.engines.memory.manager import MemoryManager
from app.engines.memory.models import MemoryType
from app.engines.tools.manager import ToolManager
from app.core.context.builder import ContextBuilder
from app.utils.logger import logger
from .manager import PersonalityManager
from .models import Personality


class Orchestrator:
    """核心编排器
    
    负责协调所有模块，处理完整的对话流程：
    1. 人格加载
    2. 智能上下文构建（使用ContextBuilder）
    3. 工具准备
    4. AI生成
    5. 记忆保存
    """
    
    def __init__(
        self,
        personality_manager: PersonalityManager,
        memory_manager: MemoryManager,
        tool_manager: ToolManager,
        context_builder: Optional[ContextBuilder] = None,
        db: Optional[AsyncSession] = None
    ):
        """初始化编排器
        
        Args:
            personality_manager: 人格管理器
            memory_manager: 记忆管理器
            tool_manager: 工具管理器
            context_builder: 上下文构建器（可选，如果提供则使用智能上下文）
            db: 数据库会话（可选，用于ContextBuilder）
        """
        self.personality_manager = personality_manager
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.context_builder = context_builder
        self.db = db
        self.ai_engines: Dict[str, AIEngineBase] = {}  # personality_id -> ai_engine
        
        logger.info(
            "Orchestrator initialized",
            extra={"use_context_builder": context_builder is not None}
        )
    
    async def process_chat_request(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        session_id: str,
        personality_id: str,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """处理聊天请求的核心流程
        
        Args:
            messages: 消息历史
            user_id: 用户ID
            session_id: 会话ID
            personality_id: 人格ID
            stream: 是否流式
            **kwargs: 其他参数
            
        Returns:
            流式: AsyncIterator[Dict]
            非流式: Dict
        """
        start_time = time.time()
        
        # 1. 加载人格配置
        personality = self.personality_manager.get_personality(personality_id)
        if not personality:
            raise ValueError(f"Personality not found: {personality_id}")
        
        logger.info(
            f"Processing chat request",
            extra={
                "personality_id": personality_id,
                "personality_name": personality.name,
                "user_id": user_id,
                "session_id": session_id,
                "stream": stream,
                "use_context_builder": self.context_builder is not None
            }
        )
        
        # 2. 获取或创建AI引擎
        ai_engine = await self._get_or_create_ai_engine(personality)
        
        # 3. 构建智能上下文（使用ContextBuilder）或降级到传统方式
        if self.context_builder and self.db:
            # 使用ContextBuilder构建智能上下文
            full_messages = await self._build_context_with_builder(
                personality,
                messages,
                user_id,
                session_id
            )
        else:
            # 降级：使用传统方式构建上下文
            logger.warning("ContextBuilder not available, using fallback context building")
            full_messages = await self._build_context_fallback(
                personality,
                messages,
                user_id,
                session_id
            )
        
        # 4. 准备工具列表
        tools = await self._prepare_tools(personality)
        
        # 5. 调用AI引擎生成回复
        if stream:
            return self._stream_generate(
                ai_engine,
                full_messages,
                tools,
                user_id,
                session_id,
                personality,
                start_time
            )
        else:
            return await self._generate(
                ai_engine,
                full_messages,
                tools,
                user_id,
                session_id,
                personality,
                start_time
            )
    
    async def _get_or_create_ai_engine(self, personality: Personality) -> AIEngineBase:
        """获取或创建AI引擎
        
        Args:
            personality: Personality对象
            
        Returns:
            AIEngineBase: AI引擎实例
        """
        personality_id = personality.id
        
        if personality_id not in self.ai_engines:
            # 创建AI引擎
            ai_config = personality.ai
            engine = AIEngineFactory.create_engine(
                engine_type=ai_config.provider,
                model=ai_config.model,
                api_key=None,  # 从配置读取
                base_url=None  # 从配置读取
            )
            self.ai_engines[personality_id] = engine
            
            logger.info(
                f"Created AI engine for personality: {personality.name}",
                extra={"personality_id": personality_id, "provider": ai_config.provider}
            )
        
        return self.ai_engines[personality_id]
    
    async def _build_context_with_builder(
        self,
        personality: Personality,
        messages: List[Dict[str, str]],
        user_id: str,
        session_id: str
    ) -> List[ChatMessage]:
        """使用ContextBuilder构建智能上下文
        
        Args:
            personality: Personality对象
            messages: 消息历史
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            List[ChatMessage]: 完整的消息列表
        """
        # 获取最后一条用户消息
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        if not last_user_message:
            last_user_message = ""
        
        # 使用ContextBuilder构建上下文
        context_bundle = await self.context_builder.build_context(
            user_id=user_id,
            session_id=session_id,
            current_message=last_user_message,
            personality_config=personality,
            include_memories=personality.memory.enabled,
            include_summaries=True
        )
        
        # 将ContextBundle转换为消息列表
        full_messages = []
        
        # 1. 系统提示词
        for prompt in context_bundle.system_prompts:
            full_messages.append(
                ChatMessage(role=MessageRole.SYSTEM, content=prompt)
            )
        
        # 2. 历史摘要（如果有）
        if context_bundle.summarized_history:
            summary_text = "## 对话历史摘要\n\n"
            for i, summary in enumerate(context_bundle.summarized_history, 1):
                summary_text += f"**摘要 {i}**:\n{summary}\n\n"
            full_messages.append(
                ChatMessage(role=MessageRole.SYSTEM, content=summary_text)
            )
        
        # 3. 检索到的记忆（如果有）
        if context_bundle.retrieved_memories:
            memory_text = "## 相关记忆\n\n"
            for mem in context_bundle.retrieved_memories:
                memory_text += f"- {mem.content}\n"
            full_messages.append(
                ChatMessage(role=MessageRole.SYSTEM, content=memory_text)
            )
        
        # 4. 最近消息（从ContextBundle获取）
        for msg in context_bundle.recent_messages:
            role = MessageRole(msg.role)
            full_messages.append(
                ChatMessage(role=role, content=msg.content)
            )
        
        logger.debug(
            f"Built context with ContextBuilder",
            extra={
                "system_prompts_count": len(context_bundle.system_prompts),
                "summaries_count": len(context_bundle.summarized_history),
                "memories_count": len(context_bundle.retrieved_memories),
                "recent_messages_count": len(context_bundle.recent_messages),
                "total_messages": len(full_messages)
            }
        )
        
        return full_messages
    
    async def _build_context_fallback(
        self,
        personality: Personality,
        messages: List[Dict[str, str]],
        user_id: str,
        session_id: str
    ) -> List[ChatMessage]:
        """降级：使用传统方式构建上下文（当ContextBuilder不可用时）
        
        Args:
            personality: Personality对象
            messages: 消息历史
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            List[ChatMessage]: 完整的消息列表
        """
        # 获取最后一条用户消息作为查询
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        # 检索记忆（如果启用）
        memories = {"user_memories": [], "ai_memories": []}
        if personality.memory.enabled and last_user_message:
            try:
                memory_config = personality.memory
                include_user = memory_config.save_mode in ["both", "user_only"]
                include_ai = memory_config.save_mode in ["both", "assistant_only"]
                
                memories = await self.memory_manager.retrieve_memories(
                    user_id=user_id,
                    session_id=session_id,
                    query=last_user_message,
                    max_results=memory_config.retrieval.max_results,
                    include_user_memory=include_user,
                    include_ai_memory=include_ai,
                    timeout=memory_config.retrieval.timeout_seconds,
                    similarity_threshold=memory_config.retrieval.similarity_threshold
                )
            except Exception as e:
                logger.error(f"Memory retrieval failed in fallback: {e}", exc_info=True)
        
        # 构建系统提示
        system_prompt = personality.ai.system_prompt
        
        # 添加记忆信息
        user_memories = memories.get("user_memories", [])
        ai_memories = memories.get("ai_memories", [])
        
        if user_memories or ai_memories:
            max_results = personality.memory.retrieval.max_results
            memory_context = "\n\n## 相关记忆\n\n"
            
            if user_memories:
                memory_context += "### 用户记忆\n"
                for mem in user_memories[:max_results]:
                    memory_context += f"- {mem.memory.content}\n"
            
            if ai_memories:
                memory_context += "\n### AI记忆\n"
                for mem in ai_memories[:max_results]:
                    memory_context += f"- {mem.memory.content}\n"
            
            system_prompt += memory_context
        
        # 构建消息列表
        full_messages = []
        
        if system_prompt:
            full_messages.append(
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)
            )
        
        for msg in messages:
            role = MessageRole(msg.get("role", "user"))
            content = msg.get("content", "")
            full_messages.append(ChatMessage(role=role, content=content))
        
        return full_messages
    
    async def _prepare_tools(self, personality: Personality) -> List[Dict[str, Any]]:
        """准备工具列表
        
        Args:
            personality: Personality对象
            
        Returns:
            List[Dict[str, Any]]: 工具列表（OpenAI function格式）
        """
        if not personality.tools.enabled:
            return []
        
        # 获取允许的工具
        allowed_tools = personality.tools.allowed_tools
        
        # 获取工具列表
        tools = self.tool_manager.get_tools_for_openai(tool_names=allowed_tools)
        
        logger.debug(
            f"Prepared tools for personality: {personality.name}",
            extra={"personality_id": personality.id, "tools_count": len(tools)}
        )
        
        return tools
    
    
    async def _generate(
        self,
        ai_engine: AIEngineBase,
        messages: List[ChatMessage],
        tools: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
        personality: Personality,
        start_time: float
    ) -> Dict[str, Any]:
        """生成回复（非流式）
        
        Args:
            ai_engine: AI引擎
            messages: 消息列表
            tools: 工具列表
            user_id: 用户ID
            session_id: 会话ID
            personality: Personality对象
            start_time: 开始时间
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            # 调用AI引擎
            response = await ai_engine.chat(
                messages=messages,
                stream=False,
                temperature=personality.ai.temperature,
                max_tokens=personality.ai.max_tokens,
                tools=tools if tools else None
            )
            
            # 保存记忆
            if personality.memory.enabled:
                last_user_message = None
                for msg in reversed(messages):
                    if msg.role == MessageRole.USER:
                        last_user_message = msg.content
                        break
                
                if last_user_message:
                    # response是ChatResponse对象，需要通过message.content获取内容
                    assistant_content = response.message.content if response.message else ""
                    # 不传入importance参数，让系统自动计算重要性分数
                    await self.memory_manager.add_conversation_turn(
                        user_id=user_id,
                        session_id=session_id,
                        user_message=last_user_message,
                        assistant_message=assistant_content
                    )
            
            elapsed_time = time.time() - start_time
            
            logger.info(
                f"Chat request completed",
                extra={
                    "personality_id": personality.id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "elapsed_time": elapsed_time,
                    "tokens_used": getattr(response, "usage", {}).get("total_tokens", 0) if response.usage else 0
                }
            )
            
            # response是ChatResponse对象，需要通过message.content获取内容
            content = response.message.content if response.message else ""
            return {
                "content": content,
                "role": "assistant",
                "usage": response.usage or {},
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}", exc_info=True)
            raise
    
    async def _stream_generate(
        self,
        ai_engine: AIEngineBase,
        messages: List[ChatMessage],
        tools: List[Dict[str, Any]],
        user_id: str,
        session_id: str,
        personality: Personality,
        start_time: float
    ) -> AsyncIterator[Dict[str, Any]]:
        """生成回复（流式）
        
        Args:
            ai_engine: AI引擎
            messages: 消息列表
            tools: 工具列表
            user_id: 用户ID
            session_id: 会话ID
            personality: Personality对象
            start_time: 开始时间
            
        Yields:
            Dict[str, Any]: 流式生成结果
        """
        try:
            full_content = ""
            
            async for chunk in ai_engine.chat_stream(
                messages=messages,
                temperature=personality.ai.temperature,
                max_tokens=personality.ai.max_tokens,
                tools=tools if tools else None
            ):
                if chunk.content:
                    full_content += chunk.content
                    yield {
                        "content": chunk.content,
                        "role": "assistant",
                        "delta": True
                    }
            
            # 保存记忆
            if personality.memory.enabled:
                last_user_message = None
                for msg in reversed(messages):
                    if msg.role == MessageRole.USER:
                        last_user_message = msg.content
                        break
                
                if last_user_message:
                    # 不传入importance参数，让系统自动计算重要性分数
                    await self.memory_manager.add_conversation_turn(
                        user_id=user_id,
                        session_id=session_id,
                        user_message=last_user_message,
                        assistant_message=full_content
                    )
            
            elapsed_time = time.time() - start_time
            
            logger.info(
                f"Stream chat request completed",
                extra={
                    "personality_id": personality.id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "elapsed_time": elapsed_time
                }
            )
            
            # 发送完成标记
            yield {
                "content": "",
                "role": "assistant",
                "delta": False,
                "done": True,
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            logger.error(f"Stream chat generation failed: {e}", exc_info=True)
            yield {
                "content": f"生成失败: {str(e)}",
                "role": "assistant",
                "delta": False,
                "error": True
            }

