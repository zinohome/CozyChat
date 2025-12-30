"""
消息服务

统一处理消息相关的所有操作，包括保存、查询、更新等
"""

# 标准库
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.engines.memory.manager import MemoryManager
    from app.core.personality.models import Personality
    from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.services.chat.message_saver import MessageSaver
from app.utils.logger import logger


class MessageService:
    """消息服务
    
    统一处理消息相关的所有操作
    """
    
    def __init__(self, db: "AsyncSession"):
        """初始化MessageService
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
        self.message_saver = MessageSaver(db)
        logger.info("MessageService initialized")
    
    async def save_conversation_turn(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        assistant_message: str,
        assistant_model: str,
        memory_manager: Optional["MemoryManager"] = None,
        personality: Optional["Personality"] = None
    ) -> None:
        """保存对话轮次
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_message: 用户消息
            assistant_message: 助手回复
            assistant_model: 使用的模型
            memory_manager: 记忆管理器（可选）
            personality: 人格配置（可选）
        """
        await self.message_saver.save_conversation_turn(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            assistant_model=assistant_model,
            memory_manager=memory_manager,
            personality=personality
        )
    
    async def save_user_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        model: Optional[str] = None
    ) -> str:
        """保存用户消息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            content: 消息内容
            model: 模型名称（可选）
            
        Returns:
            str: 消息ID
        """
        return await self.message_saver.save_user_message(
            session_id=session_id,
            user_id=user_id,
            content=content,
            model=model
        )
    
    async def save_assistant_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        model: str,
        tokens: Optional[int] = None
    ) -> str:
        """保存助手消息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            content: 消息内容
            model: 模型名称
            tokens: token数量（可选）
            
        Returns:
            str: 消息ID
        """
        return await self.message_saver.save_assistant_message(
            session_id=session_id,
            user_id=user_id,
            content=content,
            model=model,
            tokens=tokens
        )
