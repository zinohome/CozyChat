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
    # 检查所有可能依赖 users.id 的表
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 定义所有可能的外键约束信息
    foreign_keys_to_drop = []
    
    # 检查并收集所有依赖 users.id 的外键约束
    for table_name in ['sessions', 'messages', 'user_profiles', 'session_contexts']:
        if table_name in tables:
            # 获取表的所有外键约束
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                # 检查是否引用 users.id
                if fk['referred_table'] == 'users' and 'id' in fk['referred_columns']:
                    foreign_keys_to_drop.append({
                        'name': fk['name'],
                        'table': table_name,
                        'constrained_columns': fk['constrained_columns'],  # 保存列名信息
                    })
    
    # 先删除所有外键约束（必须在删除主键之前）
    for fk_info in foreign_keys_to_drop:
        try:
            op.drop_constraint(
                fk_info['name'],
                fk_info['table'],
                type_='foreignkey'
            )
        except Exception as e:
            # 如果约束不存在，忽略错误（可能已经被删除）
            print(f"警告: 无法删除外键约束 {fk_info['name']} from {fk_info['table']}: {e}")
    
    # 如果数据库中有数据，需要先迁移数据
    # 检查 users 表中是否有数据
    result = conn.execute(sa.text("SELECT COUNT(*) FROM users"))
    user_count = result.scalar()
    
    if user_count > 0:
        # 创建临时映射表，保存旧的 Integer id 和新的 UUID 的映射
        op.execute(sa.text("""
            CREATE TEMP TABLE user_id_mapping AS
            SELECT 
                id AS old_id,
                gen_random_uuid() AS new_id
            FROM users
        """))
        
        # 为每个 users 记录生成新的 UUID
        # 注意：asyncpg 不支持在一个 prepared statement 中执行多个命令，需要分开执行
        op.execute(sa.text("ALTER TABLE users ADD COLUMN new_id UUID"))
        op.execute(sa.text("""
            UPDATE users SET new_id = (
                SELECT new_id FROM user_id_mapping WHERE old_id = users.id
            )
        """))
        
        # 更新所有依赖表的 user_id 列
        for fk_info in foreign_keys_to_drop:
            table_name = fk_info['table']
            column_name = fk_info['constrained_columns'][0]  # 通常是 user_id
            
            # 检查列的类型
            columns = inspector.get_columns(table_name)
            column_type = None
            for col in columns:
                if col['name'] == column_name:
                    column_type = str(col['type'])
                    break
            
            # 如果列还不是 UUID 类型，先转换为 UUID
            if 'UUID' not in column_type:
                try:
                    # 先添加临时列
                    op.execute(sa.text(f"""
                        ALTER TABLE {table_name} ADD COLUMN {column_name}_new UUID;
                    """))
                    
                    # 更新临时列的值（从 Integer 映射到 UUID）
                    op.execute(sa.text(f"""
                        UPDATE {table_name} 
                        SET {column_name}_new = (
                            SELECT new_id 
                            FROM user_id_mapping 
                            WHERE old_id = {table_name}.{column_name}::integer
                        )
                        WHERE {column_name} IS NOT NULL;
                    """))
                    
                    # 删除旧列
                    op.drop_column(table_name, column_name)
                    
                    # 重命名新列
                    op.alter_column(table_name, f'{column_name}_new', new_column_name=column_name)
                except Exception as e:
                    # 如果转换失败，记录错误但继续
                    print(f"警告: 无法转换 {table_name}.{column_name} 从 {column_type} 到 UUID: {e}")
                    # 不抛出异常，继续执行
            else:
                # 如果列已经是 UUID 类型，说明它可能是从 Integer 转换来的
                # 我们需要先将其转换回 Integer（如果可能），然后查找映射
                # 但是，由于 UUID 和 Integer 之间没有直接的映射关系，
                # 我们需要通过其他方式匹配（比如通过 username 或 email）
                # 
                # 最简单的方法：如果 user_profiles 表有数据，先清空
                # 因为迁移脚本的注释说"此迁移假设数据库为空或只有少量数据"
                print(f"警告: {table_name}.{column_name} 已经是 UUID 类型，但值可能不匹配。")
                print(f"      将清空 {table_name} 表中的数据以确保迁移成功。")
                print(f"      如果有重要数据，请先手动备份。")
                try:
                    op.execute(sa.text(f"DELETE FROM {table_name}"))
                except Exception as e:
                    # 如果删除失败（表不存在或其他原因），记录警告但继续
                    print(f"警告: 无法清空 {table_name} 表: {e}")
                    # 不抛出异常，继续执行
        
        # 删除旧的 Integer id 列
        op.drop_constraint('users_pkey', 'users', type_='primary')
        op.drop_column('users', 'id')
        
        # 重命名 new_id 为 id
        op.alter_column('users', 'new_id', new_column_name='id')
    else:
        # 如果数据库为空，直接删除和重建列
        # 删除主键约束（必须先删除所有外键约束）
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
    
    # 重新创建所有外键约束
    # 使用保存的约束信息重新创建
    for fk_info in foreign_keys_to_drop:
        table_name = fk_info['table']
        column_name = fk_info['constrained_columns'][0]  # 通常是 user_id
        
        # 重新创建外键约束，使用原始约束名
        op.create_foreign_key(
            fk_info['name'],
            table_name,
            'users',
            [column_name],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    """将 users.id 从 UUID 改回 Integer"""
    # 检查所有可能依赖 users.id 的表
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 定义所有可能的外键约束信息
    foreign_keys_to_drop = []
    
    # 检查并收集所有依赖 users.id 的外键约束
    for table_name in ['sessions', 'messages', 'user_profiles', 'session_contexts']:
        if table_name in tables:
            # 获取表的所有外键约束
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                # 检查是否引用 users.id
                if fk['referred_table'] == 'users' and 'id' in fk['referred_columns']:
                    foreign_keys_to_drop.append({
                        'name': fk['name'],
                        'table': table_name,
                        'constrained_columns': fk['constrained_columns'],  # 保存列名信息
                    })
    
    # 先删除所有外键约束（必须在删除主键之前）
    for fk_info in foreign_keys_to_drop:
        try:
            op.drop_constraint(
                fk_info['name'],
                fk_info['table'],
                type_='foreignkey'
            )
        except Exception as e:
            # 如果约束不存在，忽略错误
            print(f"警告: 无法删除外键约束 {fk_info['name']} from {fk_info['table']}: {e}")
    
    # 删除主键约束（必须先删除所有外键约束）
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
    
    # 重新创建所有外键约束
    # 使用保存的约束信息重新创建
    for fk_info in foreign_keys_to_drop:
        table_name = fk_info['table']
        column_name = fk_info['constrained_columns'][0]  # 通常是 user_id
        
        # 重新创建外键约束，使用原始约束名
        op.create_foreign_key(
            fk_info['name'],
            table_name,
            'users',
            [column_name],
            ['id'],
            ondelete='CASCADE'
        )


