"""
消息检索服务

负责从数据库获取最近的消息原文
"""

# 标准库
from typing import List, cast
from uuid import UUID
from datetime import datetime

# 第三方库
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.models.message import Message as DBMessage
from app.schemas.context import Message as MessageSchema
from app.utils.logger import logger


class MessageRetriever:
    """消息检索器
    
    负责从数据库获取最近的消息原文
    """
    
    def __init__(self, db: AsyncSession):
        """初始化MessageRetriever
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
    
    async def get_recent_messages(
        self,
        session_id: str,
        count: int
    ) -> List[MessageSchema]:
        """获取最近的消息原文
        
        Args:
            session_id: 会话ID
            count: 消息数量
            
        Returns:
            List[MessageSchema]: 消息列表（从旧到新）
        """
        try:
            # 查询数据库获取最近的消息
            stmt = (
                select(DBMessage)
                .where(DBMessage.session_id == UUID(session_id))
                .order_by(desc(DBMessage.created_at))
                .limit(count)
            )
            
            result = await self.db.execute(stmt)
            messages = result.scalars().all()
            
            # 转换为响应模型并反转顺序（从旧到新）
            # 注意：SQLAlchemy模型实例的属性在运行时会被正确解析为实际值
            # 使用cast明确类型，避免type: ignore
            from typing import cast
            from datetime import datetime
            message_responses = [
                MessageSchema(
                    id=cast(str, msg.id),
                    session_id=cast(str, msg.session_id),
                    role=cast(str, msg.role),
                    content=cast(str, msg.content),
                    tokens=getattr(msg, 'tokens', None),  # tokens 可能不存在
                    model=cast(str | None, msg.model),
                    created_at=cast(datetime, msg.created_at)
                )
                for msg in reversed(messages)
            ]
            
            logger.debug(
                f"Retrieved {len(message_responses)} recent messages",
                extra={"session_id": session_id, "count": count}
            )
            
            return message_responses
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}", exc_info=True)
            return []
