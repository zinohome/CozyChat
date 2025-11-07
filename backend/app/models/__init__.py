"""数据模型模块"""
from .base import Base

# 按依赖顺序导入模型，确保关系可以正确解析
# 1. 先导入没有依赖的模型
from .user import User

# 2. 导入依赖User的模型
from .user_profile import UserProfile

# 3. 导入Session（依赖User，但不依赖Message）
from .session import Session

# 4. 导入Message（依赖Session和User）
from .message import Message

# 配置所有映射器，确保关系正确建立
# 这必须在所有模型导入完成后调用
# 注意：由于不同模型使用不同的基类（UserBase, ProfileBase等），
# 但它们共享Base.metadata，所以关系应该可以正确解析
from sqlalchemy.orm import configure_mappers

# 延迟配置映射器，在conftest.py中配置
__all__ = ["Base", "User", "UserProfile", "Session", "Message"]


