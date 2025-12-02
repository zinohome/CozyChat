"""create_user_profiles_table

Revision ID: 60ba2da8fff0
Revises: f99ada8c6f7e
Create Date: 2025-12-02 23:40:17.766652

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '60ba2da8fff0'
down_revision = 'f99ada8c6f7e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 user_profiles 表
    
    用户画像表，存储用户画像和行为数据
    """
    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'user_profiles' not in tables:
        op.create_table(
            'user_profiles',
            # 主键和外键
            sa.Column(
                'user_id',
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey('users.id', ondelete='CASCADE'),
                primary_key=True,
                nullable=False
            ),
            # 兴趣标签
            sa.Column(
                'interests',
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default='{}'
            ),
            # 使用习惯（JSONB）
            sa.Column(
                'habits',
                postgresql.JSONB,
                nullable=False,
                server_default=sa.text("'{\"most_active_time\": \"evening\", \"avg_session_duration_minutes\": 0, \"favorite_topics\": []}'::jsonb")
            ),
            # 人格洞察（JSONB）
            sa.Column(
                'personality_insights',
                postgresql.JSONB,
                nullable=False,
                server_default=sa.text("'{\"communication_style\": \"\", \"question_types\": [], \"interaction_patterns\": {}}'::jsonb")
            ),
            # 统计数据（JSONB）
            sa.Column(
                'statistics',
                postgresql.JSONB,
                nullable=False,
                server_default='{}'
            ),
            # 时间戳
            sa.Column(
                'generated_at',
                sa.DateTime(),
                nullable=False,
                server_default=sa.text('CURRENT_TIMESTAMP')
            ),
            sa.Column(
                'updated_at',
                sa.DateTime(),
                nullable=False,
                server_default=sa.text('CURRENT_TIMESTAMP')
            ),
            sa.Column(
                'created_at',
                sa.DateTime(),
                nullable=False,
                server_default=sa.text('CURRENT_TIMESTAMP')
            ),
        )
        
        # 创建索引
        op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'], unique=False)
    else:
        print("警告: user_profiles 表已存在，跳过创建")


def downgrade() -> None:
    """删除 user_profiles 表"""
    # 检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'user_profiles' in tables:
        # 先删除索引
        try:
            op.drop_index('ix_user_profiles_user_id', table_name='user_profiles')
        except Exception:
            pass  # 索引可能不存在
        
        # 删除表
        op.drop_table('user_profiles')


