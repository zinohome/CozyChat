"""
会话标题生成器

根据会话消息内容自动生成会话标题
"""

# 标准库
from typing import List, Optional, Dict, Any
import asyncio

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

# 本地库
from app.core.personality import PersonalityManager
from app.engines.ai import AIEngineFactory, ChatMessage as EngineChatMessage
from app.models.session import Session as SessionModel
from app.models.message import Message as MessageModel
from app.utils.config_loader import get_config_loader
from app.utils.logger import logger
from app.utils.type_helpers import get_session_title, get_message_role, safe_str
from typing import cast
from datetime import datetime


# ============================================================================
# 旧实现：SessionTitleGeneratorLegacy（已移除）
# ============================================================================
# 创建时间：2024-XX-XX
# 移除时间：2025-01-XX
# 状态：✅ 已移除（新实现已验证通过）
# 替代：SessionTitleGenerator (使用异步会话)
# 说明：Legacy类已在阶段三清理中移除，代码约280行
# 如需查看历史实现，请查看git历史记录
# ============================================================================


# ============================================================================
# 新实现：SessionTitleGenerator
# ============================================================================
# 创建时间：2025-01-XX
# 状态：✅ 新实现，使用异步会话
# 替代：SessionTitleGeneratorLegacy（已在 v2.0 移除）
# ============================================================================
class SessionTitleGenerator:
    """会话标题生成器（异步版本）
    
    根据会话消息内容自动生成简洁的标题
    使用异步数据库会话
    """
    
    def __init__(self, db: AsyncSession):
        """初始化标题生成器
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
        self.config_loader = get_config_loader()
        self._config: Optional[Dict[str, Any]] = None
    
    def _get_config(self) -> Dict[str, Any]:
        """获取会话配置（带缓存）
        
        Returns:
            Dict[str, Any]: 会话配置
        """
        if self._config is None:
            self._config = self.config_loader.load_session_config()
        return self._config
    
    def _should_auto_generate_title(self, message_count: int) -> bool:
        """判断是否应该自动生成标题
        
        Args:
            message_count: 消息数量
            
        Returns:
            bool: 是否应该生成标题
        """
        config = self._get_config()
        auto_title_config = config.get("auto_title", {})
        
        if not auto_title_config.get("enabled", True):
            return False
        
        threshold = auto_title_config.get("message_threshold", 6)
        return message_count > threshold
    
    async def generate_title(
        self,
        session_id: str,
        personality_id: Optional[str] = None
    ) -> Optional[str]:
        """生成会话标题
        
        Args:
            session_id: 会话ID
            personality_id: 人格ID（可选，用于选择AI模型）
            
        Returns:
            Optional[str]: 生成的标题，失败返回None
        """
        try:
            import uuid
            session_uuid = uuid.UUID(session_id)
            
            # 查询会话（异步）
            stmt = select(SessionModel).where(SessionModel.id == session_uuid)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return None
            
            # 查询消息（只查询用户和助手消息，排除系统消息）（异步）
            stmt = select(MessageModel).where(
                and_(
                    MessageModel.session_id == session_uuid,
                    MessageModel.role.in_(["user", "assistant"])
                )
            ).order_by(MessageModel.created_at.asc())
            result = await self.db.execute(stmt)
            messages = result.scalars().all()
            
            if not messages:
                logger.debug(f"No messages found for session: {session_id}")
                return None
            
            # 检查是否应该生成标题
            message_count = len(messages)
            if not self._should_auto_generate_title(message_count):
                logger.debug(
                    f"Message count ({message_count}) below threshold, skipping title generation",
                    extra={"session_id": session_id}
                )
                return None
            
            # 如果标题已经是自动生成的（不是默认的"新会话"），跳过
            session_title = get_session_title(session) or ""
            if session_title and session_title != "新会话":
                logger.debug(
                    f"Session already has a custom title: {session_title}",
                    extra={"session_id": session_id}
                )
                return None
            
            # 构建消息内容摘要（只取前10条消息，避免token过多）
            message_texts = []
            for msg in messages[:10]:
                msg_role = get_message_role(msg)
                msg_content = safe_str(msg.content)
                role_name = "用户" if msg_role == "user" else "助手"
                content = msg_content[:200] if len(msg_content) > 200 else msg_content  # 每条消息最多200字符
                message_texts.append(f"{role_name}: {content}")
            
            messages_text = "\n".join(message_texts)
            
            # 获取配置
            config = self._get_config()
            generation_config = config.get("auto_title", {}).get("generation", {})
            max_length = generation_config.get("max_length", 50)
            prompt_template = generation_config.get(
                "prompt_template",
                "请根据以下对话内容，生成一个简洁的会话标题（不超过{max_length}个字）。\n标题应该概括对话的主要话题或核心内容。\n\n对话内容：\n{messages}\n\n请只返回标题，不要包含其他内容。"
            )
            
            # 构建提示词
            prompt = prompt_template.format(
                messages=messages_text,
                max_length=max_length
            )
            
            # 确定使用的模型
            model = generation_config.get("model")
            if not model and personality_id:
                # 使用personality配置的模型
                personality_manager = PersonalityManager()
                personality = personality_manager.get_personality(personality_id)
                if personality and personality.ai:
                    model = personality.ai.model
                    engine_type = personality.ai.provider or "openai"
                else:
                    model = "gpt-3.5-turbo"
                    engine_type = "openai"
            else:
                model = model or "gpt-3.5-turbo"
                engine_type = "openai"
            
            # 创建AI引擎
            engine = AIEngineFactory.create_engine(
                engine_type=engine_type,
                model=model
            )
            
            # 调用AI生成标题
            response = await engine.chat(
                messages=[
                    EngineChatMessage(
                        role="user",
                        content=prompt
                    )
                ],
                temperature=0.3,  # 使用较低的温度，确保标题简洁一致
                max_tokens=100  # 标题不需要太多tokens
            )
            
            # 提取标题
            if response.message:
                if hasattr(response.message, 'content') and response.message.content:
                    title = response.message.content.strip()
                elif isinstance(response.message, dict):
                    title = response.message.get("content", "").strip()
                else:
                    title = str(response.message).strip()
                
                # 清理标题（移除可能的引号、换行等）
                title = title.replace('"', '').replace("'", '').replace('\n', ' ').strip()
                
                # 限制长度
                if len(title) > max_length:
                    title = title[:max_length]
                
                logger.info(
                    f"Generated session title",
                    extra={
                        "session_id": session_id,
                        "title": title,
                        "message_count": message_count
                    }
                )
                
                return title
            else:
                logger.warning(f"AI response has no message content for session: {session_id}")
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to generate session title: {e}",
                exc_info=True,
                extra={"session_id": session_id}
            )
            return None
    
    async def update_session_title_if_needed(
        self,
        session_id: str,
        personality_id: Optional[str] = None
    ) -> bool:
        """如果需要，更新会话标题
        
        Args:
            session_id: 会话ID
            personality_id: 人格ID
            
        Returns:
            bool: 是否成功更新了标题
        """
        try:
            import uuid
            from sqlalchemy import and_
            session_uuid = uuid.UUID(session_id)
            
            # 查询会话（异步）
            stmt = select(SessionModel).where(SessionModel.id == session_uuid)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                return False
            
            # 查询消息数量（异步）
            stmt = select(func.count(MessageModel.id)).where(
                and_(
                    MessageModel.session_id == session_uuid,
                    MessageModel.role.in_(["user", "assistant"])
                )
            )
            result = await self.db.execute(stmt)
            message_count = result.scalar_one()
            
            # 检查是否应该生成标题
            if not self._should_auto_generate_title(message_count):
                return False
            
            # 如果标题已经是自动生成的（不是默认的"新会话"），跳过
            session_title = get_session_title(session) or ""
            if session_title and session_title != "新会话":
                return False
            
            # 生成标题
            title = await self.generate_title(session_id, personality_id)
            
            if title:
                # 更新会话标题
                # SQLAlchemy ORM属性赋值，使用cast明确类型
                session.title = cast(str, title)
                session.updated_at = cast(datetime, datetime.utcnow())
                await self.db.commit()
                await self.db.refresh(session)
                
                logger.info(
                    f"Updated session title automatically",
                    extra={
                        "session_id": session_id,
                        "title": title,
                        "message_count": message_count
                    }
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                f"Failed to update session title: {e}",
                exc_info=True,
                extra={"session_id": session_id}
            )
            await self.db.rollback()
            return False
