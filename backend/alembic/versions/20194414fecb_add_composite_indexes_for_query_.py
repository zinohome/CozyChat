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
    # 检查表是否存在，如果不存在则先创建
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 如果 sessions 表不存在，先创建
    if 'sessions' not in tables:
        op.create_table(
            'sessions',
            sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('personality_id', sa.String(100), nullable=False),
            sa.Column('title', sa.String(255), nullable=False, server_default='新会话'),
            sa.Column('metadata', sa.dialects.postgresql.JSONB, nullable=False, server_default='{}'),
            sa.Column('message_count', sa.Integer, nullable=False, server_default='0'),
            sa.Column('total_tokens_used', sa.BigInteger, nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('last_message_at', sa.DateTime, nullable=True),
            sa.Column('deleted_at', sa.DateTime, nullable=True),
        )
        # 创建基本索引
        op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
        op.create_index('idx_sessions_personality_id', 'sessions', ['personality_id'])
        op.create_index('idx_sessions_created_at', 'sessions', ['created_at'])
        op.create_index('idx_sessions_last_message_at', 'sessions', ['last_message_at'])
    
    # 如果 messages 表不存在，先创建
    if 'messages' not in tables:
        op.create_table(
            'messages',
            sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('session_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(20), nullable=False),
            sa.Column('content', sa.Text, nullable=False),
            sa.Column('model', sa.String(100), nullable=True),
            sa.Column('temperature', sa.Float, nullable=True),
            sa.Column('tokens_used', sa.dialects.postgresql.JSONB, nullable=True),
            sa.Column('tool_calls', sa.dialects.postgresql.JSONB, nullable=True),
            sa.Column('memories_used', sa.dialects.postgresql.JSONB, nullable=True),
            sa.Column('metadata', sa.dialects.postgresql.JSONB, nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name='check_role'),
        )
        # 创建基本索引
        op.create_index('idx_messages_session_id', 'messages', ['session_id'])
        op.create_index('idx_messages_user_id', 'messages', ['user_id'])
        op.create_index('idx_messages_created_at', 'messages', ['created_at'])
        op.create_index('idx_messages_role', 'messages', ['role'])
        op.create_index('idx_messages_session_created', 'messages', ['session_id', 'created_at'])
    
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
    # 检查表是否存在再删除索引
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 删除 messages 表的索引
    if 'messages' in tables:
        indexes = {idx['name']: idx for idx in inspector.get_indexes('messages')}
        if 'idx_messages_user_created' in indexes:
            try:
                op.drop_index('idx_messages_user_created', table_name='messages')
            except Exception:
                pass  # 索引可能不存在
    
    # 删除 sessions 表的索引
    if 'sessions' in tables:
        indexes = {idx['name']: idx for idx in inspector.get_indexes('sessions')}
        if 'idx_sessions_user_deleted_lastmsg' in indexes:
            try:
                op.drop_index('idx_sessions_user_deleted_lastmsg', table_name='sessions')
            except Exception:
                pass
        if 'idx_sessions_user_deleted_created' in indexes:
            try:
                op.drop_index('idx_sessions_user_deleted_created', table_name='sessions')
            except Exception:
                pass
        if 'idx_sessions_user_deleted' in indexes:
            try:
                op.drop_index('idx_sessions_user_deleted', table_name='sessions')
            except Exception:
                pass


