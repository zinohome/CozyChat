"""
历史摘要加载服务

负责从数据库加载历史对话摘要
"""

# 标准库
from typing import List
from uuid import UUID

# 第三方库
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# 本地库
from app.models.session_context import SessionContext
from app.utils.logger import logger


class SummaryLoader:
    """历史摘要加载器
    
    负责从数据库加载历史对话摘要
    """
    
    def __init__(self, db: AsyncSession):
        """初始化SummaryLoader
        
        Args:
            db: 数据库会话（异步）
        """
        self.db = db
    
    async def load_history_summaries(
        self,
        session_id: str
    ) -> List[str]:
        """加载历史摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[str]: 摘要文本列表
        """
        try:
            # 查询历史摘要
            stmt = (
                select(SessionContext)
                .where(
                    and_(
                        SessionContext.session_id == UUID(session_id),
                        SessionContext.context_type == 'history_summary'
                    )
                )
                .order_by(SessionContext.created_at)
            )
            
            result = await self.db.execute(stmt)
            summaries = result.scalars().all()
            
            # 注意：SQLAlchemy模型实例的属性在运行时会被正确解析为实际值
            # 类型检查器可能报错，但运行时不会有问题
            summary_texts = [str(s.content) for s in summaries]  # type: ignore[misc]
            
            logger.debug(
                f"Loaded {len(summary_texts)} history summaries",
                extra={"session_id": session_id}
            )
            
            return summary_texts
            
        except Exception as e:
            logger.error(f"Failed to load history summaries: {e}", exc_info=True)
            return []
