"""
类型辅助函数

提供类型保护函数和类型转换工具，减少type: ignore的使用
"""

# 标准库
from typing import TYPE_CHECKING, cast, Any

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.session import Session
    from app.models.message import Message


def get_user_status(user: "User") -> str:
    """获取用户状态字符串
    
    类型保护函数，用于安全地获取User.status的值。
    避免直接使用str(user.status)导致的类型检查错误。
    
    Args:
        user: 用户对象
        
    Returns:
        str: 用户状态字符串
    """
    # SQLAlchemy ORM属性在运行时是str类型，但类型检查器认为是Column[str]
    # 使用cast明确告诉类型检查器这是str类型
    return cast(str, user.status)


def get_user_role(user: "User") -> str:
    """获取用户角色字符串
    
    类型保护函数，用于安全地获取User.role的值。
    
    Args:
        user: 用户对象
        
    Returns:
        str: 用户角色字符串
    """
    return cast(str, user.role)


def get_user_password_hash(user: "User") -> str:
    """获取用户密码哈希字符串
    
    类型保护函数，用于安全地获取User.password_hash的值。
    
    Args:
        user: 用户对象
        
    Returns:
        str: 密码哈希字符串
    """
    return cast(str, user.password_hash)


def is_active_user(user: "User") -> bool:
    """检查用户是否激活
    
    类型保护函数，用于检查用户状态是否为active。
    
    Args:
        user: 用户对象
        
    Returns:
        bool: 如果用户状态为active返回True，否则返回False
    """
    return get_user_status(user) == "active"


def is_admin_user(user: "User") -> bool:
    """检查用户是否为管理员
    
    类型保护函数，用于检查用户角色是否为admin。
    
    Args:
        user: 用户对象
        
    Returns:
        bool: 如果用户角色为admin返回True，否则返回False
    """
    return get_user_role(user) == "admin"


def get_session_title(session: "Session") -> str | None:
    """获取会话标题
    
    类型保护函数，用于安全地获取Session.title的值。
    
    Args:
        session: 会话对象
        
    Returns:
        str | None: 会话标题，如果为None则返回None
    """
    if session.title is None:
        return None
    return cast(str, session.title)


def get_message_role(message: "Message") -> str:
    """获取消息角色字符串
    
    类型保护函数，用于安全地获取Message.role的值。
    
    Args:
        message: 消息对象
        
    Returns:
        str: 消息角色字符串
    """
    return cast(str, message.role)


def safe_int(value: Any, default: int = 0) -> int:
    """安全地将值转换为整数
    
    类型保护函数，用于安全地将可能为None的值转换为整数。
    
    Args:
        value: 要转换的值
        default: 如果值为None或转换失败时的默认值
        
    Returns:
        int: 转换后的整数值
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """安全地将值转换为字符串
    
    类型保护函数，用于安全地将可能为None的值转换为字符串。
    
    Args:
        value: 要转换的值
        default: 如果值为None或转换失败时的默认值
        
    Returns:
        str: 转换后的字符串值
    """
    if value is None:
        return default
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def get_session_personality_id(session: "Session") -> str:
    """获取会话人格ID字符串
    
    类型保护函数，用于安全地获取Session.personality_id的值。
    
    Args:
        session: 会话对象
        
    Returns:
        str: 人格ID字符串
    """
    return cast(str, session.personality_id)


def get_session_message_count(session: "Session") -> int:
    """获取会话消息数量
    
    类型保护函数，用于安全地获取Session.message_count的值。
    
    Args:
        session: 会话对象
        
    Returns:
        int: 消息数量
    """
    if session.message_count is None:
        return 0
    return cast(int, session.message_count)


def get_user_username(user: "User") -> str:
    """获取用户名字符串
    
    类型保护函数，用于安全地获取User.username的值。
    
    Args:
        user: 用户对象
        
    Returns:
        str: 用户名字符串
    """
    return cast(str, user.username)


def get_user_email(user: "User") -> str:
    """获取用户邮箱字符串
    
    类型保护函数，用于安全地获取User.email的值。
    
    Args:
        user: 用户对象
        
    Returns:
        str: 邮箱字符串
    """
    return cast(str, user.email)


def get_user_display_name(user: "User") -> str | None:
    """获取用户显示名称
    
    类型保护函数，用于安全地获取User.display_name的值。
    
    Args:
        user: 用户对象
        
    Returns:
        str | None: 显示名称，如果为None则返回None
    """
    if user.display_name is None:
        return None
    return cast(str, user.display_name)


def get_user_avatar_url(user: "User") -> str | None:
    """获取用户头像URL
    
    类型保护函数，用于安全地获取User.avatar_url的值。
    
    Args:
        user: 用户对象
        
    Returns:
        str | None: 头像URL，如果为None则返回None
    """
    if user.avatar_url is None:
        return None
    return cast(str, user.avatar_url)


def get_user_bio(user: "User") -> str | None:
    """获取用户简介
    
    类型保护函数，用于安全地获取User.bio的值。
    
    Args:
        user: 用户对象
        
    Returns:
        str | None: 简介，如果为None则返回None
    """
    if user.bio is None:
        return None
    return cast(str, user.bio)


def get_message_content(message: "Message") -> str:
    """获取消息内容字符串
    
    类型保护函数，用于安全地获取Message.content的值。
    
    Args:
        message: 消息对象
        
    Returns:
        str: 消息内容字符串
    """
    return cast(str, message.content)
