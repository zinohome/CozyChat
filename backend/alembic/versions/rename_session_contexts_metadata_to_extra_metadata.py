"""rename_session_contexts_metadata_to_extra_metadata

Revision ID: rename_metadata_to_extra_metadata
Revises: 34cea2261ce1
Create Date: 2025-11-18 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f7e8d9c0b1a2'
down_revision: Union[str, None] = '34cea2261ce1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """将session_contexts表的metadata列重命名为extra_metadata"""
    # 检查列是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('session_contexts')]
    
    if 'metadata' in columns and 'extra_metadata' not in columns:
        op.alter_column('session_contexts', 'metadata', new_column_name='extra_metadata')
    elif 'extra_metadata' not in columns:
        # 如果metadata列也不存在，创建extra_metadata列
        op.add_column('session_contexts', sa.Column('extra_metadata', sa.JSON, nullable=True))


def downgrade() -> None:
    """将extra_metadata列重命名回metadata"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('session_contexts')]
    
    if 'extra_metadata' in columns:
        op.alter_column('session_contexts', 'extra_metadata', new_column_name='metadata')

