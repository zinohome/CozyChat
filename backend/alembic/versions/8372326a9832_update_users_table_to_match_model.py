"""update_users_table_to_match_model

Revision ID: 8372326a9832
Revises: 899db38cf807
Create Date: 2025-11-12 09:58:21.030489

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8372326a9832'
down_revision = '899db38cf807'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """更新 users 表以匹配模型定义
    
    1. 将 hashed_password 重命名为 password_hash
    2. 删除不需要的字段（full_name, is_active, is_superuser, last_login）
    3. 添加缺失的字段（role, status, display_name, avatar_url, bio, email_verified, 等）
    4. 更新 preferences 字段类型从 Text 改为 JSONB
    5. 添加约束和索引
    """
    # 检查表是否存在以及当前字段
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name']: col for col in inspector.get_columns('users')}
    
    # 1. 重命名 hashed_password 为 password_hash（如果存在）
    if 'hashed_password' in columns and 'password_hash' not in columns:
        op.alter_column('users', 'hashed_password', new_column_name='password_hash')
    
    # 2. 删除不需要的字段
    for col_name in ['full_name', 'is_active', 'is_superuser', 'last_login']:
        if col_name in columns:
            op.drop_column('users', col_name)
    
    # 3. 添加缺失的字段
    if 'role' not in columns:
        op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
        op.create_index('ix_users_role', 'users', ['role'], unique=False)
    
    if 'status' not in columns:
        op.add_column('users', sa.Column('status', sa.String(20), nullable=False, server_default='active'))
        op.create_index('ix_users_status', 'users', ['status'], unique=False)
    
    if 'display_name' not in columns:
        op.add_column('users', sa.Column('display_name', sa.String(100), nullable=True))
    
    if 'avatar_url' not in columns:
        op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))
    
    if 'bio' not in columns:
        op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    
    if 'email_verified' not in columns:
        op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    
    if 'email_verified_at' not in columns:
        op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    
    if 'last_login_at' not in columns:
        op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    
    if 'last_login_ip' not in columns:
        op.add_column('users', sa.Column('last_login_ip', postgresql.INET(), nullable=True))
    
    if 'total_sessions' not in columns:
        op.add_column('users', sa.Column('total_sessions', sa.Integer(), nullable=False, server_default='0'))
    
    if 'total_messages' not in columns:
        op.add_column('users', sa.Column('total_messages', sa.Integer(), nullable=False, server_default='0'))
    
    if 'total_tokens_used' not in columns:
        op.add_column('users', sa.Column('total_tokens_used', sa.BigInteger(), nullable=False, server_default='0'))
    
    if 'deleted_at' not in columns:
        op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # 4. 更新 preferences 字段类型从 Text 改为 JSONB
    if 'preferences' in columns:
        # 先检查当前类型
        current_type = str(columns['preferences']['type'])
        if 'TEXT' in current_type.upper() or 'VARCHAR' in current_type.upper():
            # 将 Text 转换为 JSONB
            # 先处理空值或无效 JSON，设置为默认值
            op.execute("""
                UPDATE users 
                SET preferences = '{}'::jsonb 
                WHERE preferences IS NULL OR preferences = '' OR preferences::text = ''
            """)
            # 尝试转换，如果失败则使用默认值
            op.execute("""
                ALTER TABLE users 
                ALTER COLUMN preferences TYPE JSONB 
                USING CASE 
                    WHEN preferences::text ~ '^[{}[].*[}\]]$' THEN preferences::jsonb
                    ELSE '{}'::jsonb
                END
            """)
    
    # 5. 添加约束
    try:
        op.create_check_constraint('check_role', 'users', "role IN ('admin', 'user', 'guest')")
    except Exception:
        pass  # 约束可能已存在
    
    try:
        op.create_check_constraint('check_status', 'users', "status IN ('active', 'suspended', 'deleted')")
    except Exception:
        pass  # 约束可能已存在
    
    # 6. 确保索引存在
    indexes = {idx['name']: idx for idx in inspector.get_indexes('users')}
    
    if 'idx_users_username' not in indexes:
        op.create_index('idx_users_username', 'users', ['username'], unique=False)
    
    if 'idx_users_email' not in indexes:
        op.create_index('idx_users_email', 'users', ['email'], unique=False)
    
    if 'idx_users_status' not in indexes:
        op.create_index('idx_users_status', 'users', ['status'], unique=False)
    
    if 'idx_users_created_at' not in indexes:
        op.create_index('idx_users_created_at', 'users', ['created_at'], unique=False)


def downgrade() -> None:
    """回滚更改"""
    # 注意：这是一个复杂的回滚，可能需要根据实际情况调整
    # 这里只做基本的回滚
    
    # 删除新添加的字段
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'total_tokens_used')
    op.drop_column('users', 'total_messages')
    op.drop_column('users', 'total_sessions')
    op.drop_column('users', 'last_login_ip')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'display_name')
    op.drop_column('users', 'status')
    op.drop_column('users', 'role')
    
    # 将 password_hash 改回 hashed_password
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
    
    # 将 preferences 改回 Text
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN preferences TYPE TEXT 
        USING preferences::text
    """)
    
    # 添加回旧字段
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('full_name', sa.String(100), nullable=True))
    
    # 删除约束
    try:
        op.drop_constraint('check_status', 'users', type_='check')
    except Exception:
        pass
    
    try:
        op.drop_constraint('check_role', 'users', type_='check')
    except Exception:
    pass


