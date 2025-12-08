"""
消息检索服务

负责从数据库获取最近的消息原文
"""

# 标准库
from typing import List
from uuid import UUID

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
            # 类型检查器可能报错，但运行时不会有问题
            message_responses = [
                MessageSchema(
                    id=msg.id,  # type: ignore[arg-type]
                    session_id=msg.session_id,  # type: ignore[arg-type]
                    role=msg.role,  # type: ignore[arg-type]
                    content=msg.content,  # type: ignore[arg-type]
                    tokens=getattr(msg, 'tokens', None),  # tokens 可能不存在
                    model=msg.model,  # type: ignore[arg-type]
                    created_at=msg.created_at  # type: ignore[arg-type]
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
