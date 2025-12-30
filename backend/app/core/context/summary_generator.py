"""
历史摘要生成器

负责将长对话历史压缩为简洁的摘要
"""

# 标准库
import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

# 第三方库
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

# 本地库
from app.config.config import settings
from app.utils.logger import logger
from app.engines.ai.engine_pool import LLMEnginePool
from app.engines.memory.qdrant_engine import QdrantMemoryEngine
from app.models.message import Message
from app.models.session_context import SessionContext
from app.schemas.context import HistorySummaryCreate, HistorySummaryResponse


# 摘要生成的提示词模板
SUMMARY_PROMPT_TEMPLATE = """请将以下对话历史压缩为简洁的摘要，保留：
1. 讨论的主要话题和内容
2. 用户的关键需求和决策
3. 重要的结论和待办事项
4. 情感基调和互动特点

对话内容：
{conversation}

请生成200字以内的摘要："""


class SummaryGenerator:
    """历史摘要生成器
    
    使用LLM生成对话历史的结构化摘要。
    """
    
    def __init__(
        self,
        engine_pool: LLMEnginePool,
        db: Session,
        memory_engine: Optional[QdrantMemoryEngine] = None
    ):
        """初始化SummaryGenerator
        
        Args:
            engine_pool: LLM引擎池
            db: 数据库会话
            memory_engine: 记忆引擎（可选，用于存储摘要向量）
        """
        self.engine_pool = engine_pool
        self.db = db
        self.memory_engine = memory_engine
        
        logger.info("SummaryGenerator initialized")
    
    async def generate_summary(
        self,
        session_id: str,
        user_id: str,
        start_message_index: int,
        end_message_index: int,
        force: bool = False
    ) -> Optional[HistorySummaryResponse]:
        """生成历史摘要
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            start_message_index: 起始消息索引
            end_message_index: 结束消息索引
            force: 是否强制重新生成
            
        Returns:
            Optional[HistorySummaryResponse]: 生成的摘要，失败返回None
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 检查是否已存在摘要
            if not force:
                existing = await self._check_existing_summary(
                    session_id,
                    start_message_index,
                    end_message_index
                )
                if existing:
                    logger.info(
                        f"Summary already exists for range {start_message_index}-{end_message_index}",
                        extra={"session_id": session_id}
                    )
                    return existing
            
            # 获取消息列表
            messages = await self._get_messages(
                session_id,
                start_message_index,
                end_message_index
            )
            
            if not messages:
                logger.warning(
                    f"No messages found in range {start_message_index}-{end_message_index}",
                    extra={"session_id": session_id}
                )
                return None
            
            # 构建对话文本
            conversation_text = self._format_conversation(messages)
            
            # 调用LLM生成摘要
            summary_text = await self._call_llm_for_summary(conversation_text)
            
            if not summary_text:
                logger.error("LLM returned empty summary")
                return None
            
            # 存储摘要
            summary_response = await self._store_summary(
                session_id=session_id,
                user_id=user_id,
                content=summary_text,
                start_index=start_message_index,
                end_index=end_message_index,
                message_count=len(messages)
            )
            
            elapsed = asyncio.get_event_loop().time() - start_time
            
            logger.info(
                f"Summary generated successfully in {elapsed:.3f}s",
                extra={
                    "session_id": session_id,
                    "message_range": f"{start_message_index}-{end_message_index}",
                    "message_count": len(messages),
                    "summary_length": len(summary_text),
                    "elapsed_time": elapsed
                }
            )
            
            return summary_response
            
        except Exception as e:
            logger.error(
                f"Failed to generate summary: {e}",
                exc_info=True,
                extra={
                    "session_id": session_id,
                    "range": f"{start_message_index}-{end_message_index}"
                }
            )
            return None
    
    async def should_generate_summary(
        self,
        session_id: str
    ) -> bool:
        """判断是否应该生成新摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否应该生成摘要
        """
        try:
            # 获取会话的总消息数
            stmt = select(Message).where(Message.session_id == UUID(session_id))
            result = self.db.execute(stmt)
            total_messages = len(result.scalars().all())
            
            # 获取已摘要的消息范围
            stmt = (
                select(SessionContext)
                .where(
                    and_(
                        SessionContext.session_id == UUID(session_id),
                        SessionContext.context_type == 'history_summary'
                    )
                )
                .order_by(desc(SessionContext.end_message_index))
                .limit(1)
            )
            result = self.db.execute(stmt)
            last_summary = result.scalar_one_or_none()
            
            if last_summary:
                # 计算未摘要的消息数
                from typing import cast
                end_index = cast(int, last_summary.end_message_index) if last_summary.end_message_index is not None else 0
                unsummarized_count = total_messages - end_index
            else:
                # 没有任何摘要
                unsummarized_count = total_messages
            
            # 判断是否达到阈值
            # 明确类型转换，避免comparison-overlap错误
            # 使用配置适配器获取上下文配置（优先YAML，回退到Settings）
            from app.utils.config_adapter import get_config_adapter
            config_adapter = get_config_adapter()
            context_config = config_adapter.get_context_config()
            summary_config = context_config.get("summary", {})
            threshold: int = summary_config.get("trigger_count", settings.context_summary_trigger_count)
            return bool(unsummarized_count >= threshold)
            
        except Exception as e:
            logger.error(f"Failed to check summary trigger: {e}", exc_info=True)
            return False
    
    async def _check_existing_summary(
        self,
        session_id: str,
        start_index: int,
        end_index: int
    ) -> Optional[HistorySummaryResponse]:
        """检查是否已存在摘要
        
        Args:
            session_id: 会话ID
            start_index: 起始索引
            end_index: 结束索引
            
        Returns:
            Optional[HistorySummaryResponse]: 已存在的摘要
        """
        try:
            stmt = (
                select(SessionContext)
                .where(
                    and_(
                        SessionContext.session_id == UUID(session_id),
                        SessionContext.context_type == 'history_summary',
                        SessionContext.start_message_index == start_index,
                        SessionContext.end_message_index == end_index
                    )
                )
            )
            result = self.db.execute(stmt)
            summary = result.scalar_one_or_none()
            
            if summary:
                return HistorySummaryResponse.model_validate(summary)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check existing summary: {e}", exc_info=True)
            return None
    
    async def _get_messages(
        self,
        session_id: str,
        start_index: int,
        end_index: int
    ) -> List[Message]:
        """获取指定范围的消息
        
        Args:
            session_id: 会话ID
            start_index: 起始索引
            end_index: 结束索引
            
        Returns:
            List[Message]: 消息列表
        """
        try:
            # 查询消息
            stmt = (
                select(Message)
                .where(Message.session_id == UUID(session_id))
                .order_by(Message.created_at)
            )
            result = self.db.execute(stmt)
            all_messages = result.scalars().all()
            
            # 切片获取指定范围，转换为List
            return list(all_messages[start_index:end_index + 1])
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}", exc_info=True)
            return []
    
    def _format_conversation(
        self,
        messages: List[Message]
    ) -> str:
        """格式化对话文本
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 格式化的对话文本
        """
        lines = []
        for msg in messages:
            from app.utils.type_helpers import get_message_role
            msg_role = get_message_role(msg)
            role = "用户" if msg_role == "user" else "助手"
            lines.append(f"{role}: {msg.content}")
        
        return "\n".join(lines)
    
    async def _call_llm_for_summary(
        self,
        conversation_text: str
    ) -> Optional[str]:
        """调用LLM生成摘要
        
        Args:
            conversation_text: 对话文本
            
        Returns:
            Optional[str]: 生成的摘要文本
        """
        try:
            # 构建prompt
            prompt = SUMMARY_PROMPT_TEMPLATE.format(conversation=conversation_text)
            
            # 使用配置适配器获取上下文配置（优先YAML，回退到Settings）
            from app.utils.config_adapter import get_config_adapter
            config_adapter = get_config_adapter()
            context_config = config_adapter.get_context_config()
            summary_config = context_config.get("summary", {})
            
            # 获取LLM引擎
            engine = self.engine_pool.get_engine(
                provider="openai",
                model=summary_config.get("model", settings.context_summary_model)
            )
            
            # 调用LLM
            from app.engines.ai import ChatMessage
            messages = [ChatMessage(role="user", content=prompt)]
            # LLMEnginePool.get_engine返回AIEngineBase实例，但类型检查器可能无法推断
            # 使用类型注释明确类型
            from typing import cast
            from app.engines.ai.base import AIEngineBase
            ai_engine: AIEngineBase = cast(AIEngineBase, engine)
            response = await ai_engine.chat(
                messages=messages,
                temperature=summary_config.get("temperature", settings.context_summary_temperature),
                max_tokens=300  # 限制摘要长度
            )
            
            # 提取响应内容
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                summary_text = response.message.content or ""
            elif isinstance(response, dict):
                summary_text = response.get("content", "")
            else:
                summary_text = str(response)
            return summary_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to call LLM for summary: {e}", exc_info=True)
            return None
    
    async def _store_summary(
        self,
        session_id: str,
        user_id: str,
        content: str,
        start_index: int,
        end_index: int,
        message_count: int
    ) -> HistorySummaryResponse:
        """存储摘要
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            content: 摘要内容
            start_index: 起始索引
            end_index: 结束索引
            message_count: 消息数量
            
        Returns:
            HistorySummaryResponse: 存储的摘要响应
        """
        try:
            # 估算token数
            token_count = int(len(content) * 1.5)
            
            # 如果有memory_engine，同时存储到Qdrant
            vector_id = None
            if self.memory_engine:
                try:
                    from app.engines.memory.models import Memory, MemoryType
                    
                    memory = Memory(
                        id=str(uuid4()),
                        user_id=user_id,
                        session_id=session_id,
                        memory_type=MemoryType.ASSISTANT,  # 摘要属于AI生成的内容
                        content=content,
                        importance=0.8,  # 摘要很重要
                        metadata={
                            "is_summary": True,
                            "message_range": f"{start_index}-{end_index}",
                            "message_count": message_count
                        }
                    )
                    
                    vector_id = await self.memory_engine.add_memory(memory)
                except Exception as e:
                    logger.warning(f"Failed to store summary vector: {e}")
            
            # 创建数据库记录
            summary = SessionContext(
                id=uuid4(),
                session_id=UUID(session_id),
                user_id=UUID(user_id),
                context_type='history_summary',
                content=content,
                start_message_index=start_index,
                end_message_index=end_index,
                message_count=message_count,
                token_count=token_count,
                vector_id=vector_id,
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(summary)
            self.db.commit()
            self.db.refresh(summary)
            
            return HistorySummaryResponse.model_validate(summary)
            
        except Exception as e:
            logger.error(f"Failed to store summary: {e}", exc_info=True)
            self.db.rollback()
            raise

