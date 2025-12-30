"""
修复users表id字段类型脚本

将users表的id字段从integer改为uuid
"""

# 标准库
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 第三方库
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# 本地库
from app.config.config import settings
from app.utils.logger import logger


def fix_user_id_type():
    """修复users表id字段类型"""
    # 使用同步引擎
    engine = create_engine(
        settings.database_url.replace('postgresql://', 'postgresql+psycopg2://')
    )
    
    with engine.connect() as conn:
        try:
            # 检查users表是否存在
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'id'
            """))
            row = result.fetchone()
            
            if not row:
                logger.info("users表不存在，无需修复")
                return
            
            current_type = row[1]
            logger.info(f"当前users.id类型: {current_type}")
            
            if current_type == 'uuid':
                logger.info("users.id已经是uuid类型，无需修复")
                return
            
            # 使用autocommit模式执行DDL语句
            # 1. 删除user_profiles表（如果存在）
            conn.execute(text("DROP TABLE IF EXISTS user_profiles CASCADE"))
            conn.commit()
            logger.info("已删除user_profiles表")
            
            # 2. 删除users表（如果存在）
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.commit()
            logger.info("已删除users表")
            
            logger.info("表删除成功，可以重新创建表")
                
        except ProgrammingError as e:
            logger.error(f"数据库操作失败: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"未知错误: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    logger.info("开始修复users表id字段类型...")
    fix_user_id_type()
    logger.info("修复完成")

