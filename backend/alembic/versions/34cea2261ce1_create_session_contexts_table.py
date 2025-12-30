"""create_session_contexts_table

Revision ID: 34cea2261ce1
Revises: 4232b4b50ff0
Create Date: 2025-01-18 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '34cea2261ce1'
down_revision: Union[str, None] = '4232b4b50ff0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建session_contexts表用于存储历史摘要"""
    op.create_table(
        'session_contexts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('context_type', sa.String(50), nullable=False, comment='上下文类型：history_summary'),
        sa.Column('content', sa.Text, nullable=False, comment='摘要文本内容'),
        sa.Column('start_message_index', sa.Integer, nullable=False, comment='起始消息索引'),
        sa.Column('end_message_index', sa.Integer, nullable=False, comment='结束消息索引'),
        sa.Column('message_count', sa.Integer, nullable=False, comment='包含的消息数量'),
        sa.Column('token_count', sa.Integer, nullable=True, comment='摘要的token数量'),
        sa.Column('vector_id', sa.String(255), nullable=True, comment='Qdrant中的向量ID'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, comment='额外的元数据'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # 创建索引
    op.create_index('idx_session_contexts_session_id', 'session_contexts', ['session_id'])
    op.create_index('idx_session_contexts_user_id', 'session_contexts', ['user_id'])
    op.create_index('idx_session_contexts_created_at', 'session_contexts', ['created_at'])
    op.create_index('idx_session_contexts_type', 'session_contexts', ['context_type'])
    
    # 创建复合索引（按session和创建时间查询）
    op.create_index(
        'idx_session_contexts_session_created',
        'session_contexts',
        ['session_id', 'created_at']
    )


def downgrade() -> None:
    """删除session_contexts表"""
    op.drop_index('idx_session_contexts_session_created', table_name='session_contexts')
    op.drop_index('idx_session_contexts_type', table_name='session_contexts')
    op.drop_index('idx_session_contexts_created_at', table_name='session_contexts')
    op.drop_index('idx_session_contexts_user_id', table_name='session_contexts')
    op.drop_index('idx_session_contexts_session_id', table_name='session_contexts')
    op.drop_table('session_contexts')
