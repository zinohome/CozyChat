"""change_users_id_from_integer_to_uuid

Revision ID: 899db38cf807
Revises: c01c55832e12
Create Date: 2025-11-12 09:49:03.575425

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '899db38cf807'
down_revision = 'c01c55832e12'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """将 users.id 从 Integer 改为 UUID
    
    注意：此迁移假设数据库为空或只有少量数据。
    如果数据库中有大量数据，需要先迁移数据。
    """
    # 检查是否存在 user_profiles 表（可能在其他迁移中创建）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 如果存在 user_profiles 表，先删除外键约束
    if 'user_profiles' in tables:
        # 删除外键约束
        op.drop_constraint(
            'user_profiles_user_id_fkey',
            'user_profiles',
            type_='foreignkey'
        )
    
    # 删除主键约束（必须先删除主键才能删除列）
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # 删除旧的 Integer id 列
    op.drop_column('users', 'id')
    
    # 创建新的 UUID id 列
    op.add_column(
        'users',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        )
    )
    
    # 重新创建主键约束
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # 重新创建索引
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    
    # 如果存在 user_profiles 表，重新创建外键约束
    if 'user_profiles' in tables:
        op.create_foreign_key(
            'user_profiles_user_id_fkey',
            'user_profiles',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    """将 users.id 从 UUID 改回 Integer"""
    # 检查是否存在 user_profiles 表
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 如果存在 user_profiles 表，先删除外键约束
    if 'user_profiles' in tables:
        op.drop_constraint(
            'user_profiles_user_id_fkey',
            'user_profiles',
            type_='foreignkey'
        )
    
    # 删除主键约束（必须先删除主键才能删除列）
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # 删除 UUID id 列
    op.drop_column('users', 'id')
    
    # 创建 Integer id 列
    op.add_column(
        'users',
        sa.Column(
            'id',
            sa.Integer(),
            autoincrement=True,
            nullable=False
        )
    )
    
    # 重新创建主键约束
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # 重新创建索引
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    
    # 如果存在 user_profiles 表，重新创建外键约束
    if 'user_profiles' in tables:
        op.create_foreign_key(
            'user_profiles_user_id_fkey',
            'user_profiles',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )


