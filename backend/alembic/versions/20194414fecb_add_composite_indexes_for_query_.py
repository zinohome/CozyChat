"""add_composite_indexes_for_query_optimization

Revision ID: 20194414fecb
Revises: 8372326a9832
Create Date: 2025-11-17 20:56:06.496655

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20194414fecb'
down_revision = '8372326a9832'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加复合索引以优化查询性能
    
    优化点：
    1. Session表：添加 (user_id, deleted_at, last_message_at) 和 (user_id, deleted_at, created_at) 复合索引
       用于优化最常见的查询：按用户查询未删除会话，并按时间排序
    
    2. Message表：添加 (user_id, created_at) 复合索引
       用于优化按用户查询消息的场景
    """
    # Session表复合索引
    # 1. (user_id, deleted_at, last_message_at) - 用于按最后消息时间排序
    op.create_index(
        'idx_sessions_user_deleted_lastmsg',
        'sessions',
        ['user_id', 'deleted_at', 'last_message_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')  # 部分索引，只索引未删除的会话
    )
    
    # 2. (user_id, deleted_at, created_at) - 用于按创建时间排序
    op.create_index(
        'idx_sessions_user_deleted_created',
        'sessions',
        ['user_id', 'deleted_at', 'created_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')  # 部分索引，只索引未删除的会话
    )
    
    # 3. (user_id, deleted_at) - 用于基本查询（虽然已有user_id索引，但复合索引对包含deleted_at的查询更高效）
    op.create_index(
        'idx_sessions_user_deleted',
        'sessions',
        ['user_id', 'deleted_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')  # 部分索引
    )
    
    # Message表复合索引
    # 4. (user_id, created_at) - 用于按用户查询消息
    op.create_index(
        'idx_messages_user_created',
        'messages',
        ['user_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """回滚索引"""
    op.drop_index('idx_messages_user_created', table_name='messages')
    op.drop_index('idx_sessions_user_deleted', table_name='sessions')
    op.drop_index('idx_sessions_user_deleted_created', table_name='sessions')
    op.drop_index('idx_sessions_user_deleted_lastmsg', table_name='sessions')


