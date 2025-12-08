"""消息保存服务

负责将用户和AI消息保存到数据库,更新会话统计,并触发记忆保存
"""

# 标准库
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

# 本地库
from app.models.message import Message as MessageModel
from app.models.session import Session as SessionModel
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.engines.memory.manager import MemoryManager
    from app.core.personality.models import Personality


# ============================================================================
# 旧实现：MessageSaverLegacy（已移除）
# ============================================================================
# 创建时间：2024-XX-XX
# 移除时间：2025-01-XX
# 状态：✅ 已移除（新实现已验证通过）
# 替代：MessageSaver (使用异步会话)
# 说明：Legacy类已在阶段三清理中移除，代码约160行
# 如需查看历史实现，请查看git历史记录
# ============================================================================


# ============================================================================
# 新实现：MessageSaver
# ============================================================================
# 创建时间：2025-01-XX
# 状态：✅ 新实现，使用异步会话
# 替代：MessageSaverLegacy（已在 v2.0 移除）
# ============================================================================
class MessageSaver:
    """消息保存服务（异步版本）
    
    统一处理流式和非流式对话的消息保存逻辑
    使用异步数据库会话
    """
    
    def __init__(self, db: AsyncSession):
        """初始化MessageSaver
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
    
    async def save_conversation_turn(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        assistant_message: str,
        assistant_model: Optional[str] = None,
        memory_manager: Optional["MemoryManager"] = None,
        personality: Optional["Personality"] = None,
        use_memory: bool = True
    ) -> bool:
        """保存一轮对话(用户消息+助手回复)
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_message: 用户消息内容
            assistant_message: 助手回复内容
            assistant_model: 使用的模型名称
            memory_manager: 记忆管理器(可选)
            personality: 人格配置(可选,用于判断是否保存记忆)
            use_memory: 是否使用记忆系统
            
        Returns:
            bool: 是否保存成功
        """
        try:
            session_uuid = uuid.UUID(session_id)
            user_uuid = uuid.UUID(user_id)
            
            # 保存用户消息到数据库
            try:
                user_msg = MessageModel(
                    session_id=session_uuid,
                    user_id=user_uuid,
                    role="user",
                    content=user_message
                )
                self.db.add(user_msg)
                
                # 保存助手消息到数据库
                assistant_msg = MessageModel(
                    session_id=session_uuid,
                    user_id=user_uuid,
                    role="assistant",
                    content=assistant_message,
                    model=assistant_model
                )
                self.db.add(assistant_msg)
                
                # 更新会话的message_count和last_message_at
                stmt = select(SessionModel).where(SessionModel.id == session_uuid)
                result = await self.db.execute(stmt)
                session = result.scalar_one_or_none()
                if session:
                    session.message_count = (session.message_count or 0) + 2  # type: ignore[assignment]
                    session.last_message_at = datetime.utcnow()  # type: ignore[assignment]
                
                await self.db.commit()
                
                logger.debug(
                    f"Saved messages to database",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "user_message_length": len(user_message),
                        "assistant_message_length": len(assistant_message)
                    }
                )
            except Exception as msg_error:
                logger.warning(
                    f"Failed to save messages to database: {msg_error}",
                    exc_info=False
                )
                await self.db.rollback()
                return False
            
            # 保存记忆(如果启用了记忆系统)
            if memory_manager and personality and personality.memory.enabled and use_memory:
                try:
                    # 使用 async_save=True 异步保存,不阻塞
                    # 不传入importance参数,让系统自动计算重要性分数
                    await memory_manager.add_conversation_turn(
                        user_id=user_id,
                        session_id=session_id,
                        user_message=user_message,
                        assistant_message=assistant_message,
                        async_save=True
                    )
                    
                    logger.debug(
                        f"Saved conversation to memory",
                        extra={
                            "user_id": user_id,
                            "session_id": session_id,
                            "user_message_length": len(user_message),
                            "assistant_message_length": len(assistant_message)
                        }
                    )
                except Exception as memory_error:
                    logger.warning(
                        f"Failed to save memory: {memory_error}",
                        exc_info=False
                    )
            
            return True
            
        except Exception as e:
            logger.warning(
                f"Failed to save conversation turn: {e}",
                exc_info=False
            )
            return False
