"""add_performance_optimization_indexes

Revision ID: f99ada8c6f7e
Revises: f7e8d9c0b1a2
Create Date: 2025-11-20 11:05:41.523936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f99ada8c6f7e'
down_revision = 'f7e8d9c0b1a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加性能优化索引
    
    优化目标：
    1. User表：添加复合索引优化用户查询
    2. Session表：添加额外的复合索引
    3. Message表：添加role相关的复合索引
    4. 部分索引：只索引常用数据，减少索引大小
    """
    
    # ==================== User表索引 ====================
    
    # 1. (status, role) 复合索引 - 用于按状态和角色筛选用户（如查询所有活跃的admin）
    op.create_index(
        'idx_users_status_role',
        'users',
        ['status', 'role'],
        unique=False
    )
    
    # 2. (email_verified, status) 复合索引 - 用于查询已验证的活跃用户
    op.create_index(
        'idx_users_email_verified_status',
        'users',
        ['email_verified', 'status'],
        unique=False
    )
    
    # 3. 部分索引：只索引活跃用户的username（减少索引大小）
    op.create_index(
        'idx_users_username_active',
        'users',
        ['username'],
        unique=False,
        postgresql_where=sa.text("status = 'active'")
    )
    
    # 4. 部分索引：只索引活跃用户的email（减少索引大小）
    op.create_index(
        'idx_users_email_active',
        'users',
        ['email'],
        unique=False,
        postgresql_where=sa.text("status = 'active'")
    )
    
    # 5. last_login_at索引 - 用于查询最近登录的用户
    op.create_index(
        'idx_users_last_login_at',
        'users',
        ['last_login_at'],
        unique=False
    )
    
    # ==================== Session表额外索引 ====================
    
    # 6. (personality_id, user_id) 复合索引 - 用于按人格查询特定用户的会话
    op.create_index(
        'idx_sessions_personality_user',
        'sessions',
        ['personality_id', 'user_id'],
        unique=False
    )
    
    # 7. 部分索引：只索引未删除会话的personality_id（减少索引大小）
    op.create_index(
        'idx_sessions_personality_active',
        'sessions',
        ['personality_id'],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL")
    )
    
    # 8. (user_id, personality_id, last_message_at) 三列复合索引
    # 用于查询特定用户特定人格的会话，并按最后消息时间排序
    op.create_index(
        'idx_sessions_user_personality_lastmsg',
        'sessions',
        ['user_id', 'personality_id', 'last_message_at'],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL")
    )
    
    # ==================== Message表额外索引 ====================
    
    # 9. (role, session_id) 复合索引 - 用于按角色筛选会话消息（如只查询assistant的回复）
    op.create_index(
        'idx_messages_role_session',
        'messages',
        ['role', 'session_id'],
        unique=False
    )
    
    # 10. (session_id, role, created_at) 三列复合索引
    # 用于按会话和角色查询，并按时间排序
    op.create_index(
        'idx_messages_session_role_created',
        'messages',
        ['session_id', 'role', 'created_at'],
        unique=False
    )
    
    # 11. 部分索引：只索引assistant消息的session_id（用于统计AI回复）
    op.create_index(
        'idx_messages_session_assistant',
        'messages',
        ['session_id'],
        unique=False,
        postgresql_where=sa.text("role = 'assistant'")
    )
    
    # 12. 部分索引：只索引user消息的session_id（用于统计用户输入）
    op.create_index(
        'idx_messages_session_user',
        'messages',
        ['session_id'],
        unique=False,
        postgresql_where=sa.text("role = 'user'")
    )
    
    # 13. (user_id, role, created_at) 复合索引 - 用于按用户和角色查询消息
    op.create_index(
        'idx_messages_user_role_created',
        'messages',
        ['user_id', 'role', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """回滚索引"""
    # 按创建的相反顺序删除索引
    op.drop_index('idx_messages_user_role_created', table_name='messages')
    op.drop_index('idx_messages_session_user', table_name='messages')
    op.drop_index('idx_messages_session_assistant', table_name='messages')
    op.drop_index('idx_messages_session_role_created', table_name='messages')
    op.drop_index('idx_messages_role_session', table_name='messages')
    
    op.drop_index('idx_sessions_user_personality_lastmsg', table_name='sessions')
    op.drop_index('idx_sessions_personality_active', table_name='sessions')
    op.drop_index('idx_sessions_personality_user', table_name='sessions')
    
    op.drop_index('idx_users_last_login_at', table_name='users')
    op.drop_index('idx_users_email_active', table_name='users')
    op.drop_index('idx_users_username_active', table_name='users')
    op.drop_index('idx_users_email_verified_status', table_name='users')
    op.drop_index('idx_users_status_role', table_name='users')


