"""
消息处理工具函数

提供消息格式化、转换、偏好处理等通用功能
"""

from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from app.engines.ai import ChatMessage as EngineChatMessage
from app.models.user import User
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.core.personality.models import Personality
    from app.schemas.context import ContextBundle

# 默认偏好设置
DEFAULT_INSTRUCTION_PREFS: Dict[str, Any] = {
    "default_language": "zh-CN",
    "response_style": "chatgpt_like",  # brief, chatgpt_like, detailed
    "style_preset": "chatgpt_like",
    "output_format": "structured",
    "prefer_list": False,
    "show_reasoning": False,
}

# 允许的偏好键
PREFERENCE_KEYS = [
    "default_language", "response_style", "style_preset",
    "output_format", "prefer_list", "show_reasoning",
]


def detect_message_hints(content: str) -> Dict[str, Any]:
    """通过简单的关键词识别消息偏好
    
    Args:
        content: 用户消息内容
    
    Returns:
        包含检测到的偏好提示的字典
    
    Examples:
        >>> detect_message_hints("列出所有步骤")
        {'prefer_list': True}
        >>> detect_message_hints("为什么会这样")
        {'response_style': 'detailed'}
    """
    hints: Dict[str, Any] = {}
    if not content:
        return hints
    
    # 检测列表偏好
    list_keywords = ["列出", "有哪些", "清单", "步骤", "几个", "列表"]
    if any(keyword in content for keyword in list_keywords):
        hints["prefer_list"] = True
    
    # 检测详细回答偏好
    reason_keywords = ["为什么", "原因", "怎么回事", "为何"]
    if any(keyword in content for keyword in reason_keywords):
        hints["response_style"] = "detailed"
    
    # 检测行动建议需求
    action_keywords = ["怎么办", "怎么做", "处理", "建议", "方案"]
    if any(keyword in content for keyword in action_keywords):
        hints["needs_action"] = True
    
    return hints


def merge_user_preferences(
    personality_config: Optional["Personality"],
    user: Optional[User]
) -> Dict[str, Any]:
    """合并人格和用户层的偏好设置
    
    优先级: 用户偏好 > 人格偏好 > 默认偏好
    
    Args:
        personality_config: 人格配置对象
        user: 用户对象
    
    Returns:
        合并后的偏好设置字典
    """
    merged = DEFAULT_INSTRUCTION_PREFS.copy()
    
    # 合并人格偏好
    if personality_config and getattr(personality_config, "user_preferences", None):
        try:
            merged.update({
                key: value
                for key, value in asdict(personality_config.user_preferences).items()
                if key in PREFERENCE_KEYS
            })
        except TypeError:
            logger.debug("Failed to convert personality user preferences", exc_info=True)
    
    # 合并用户偏好（优先级最高）
    if user:
        user_prefs = user.get_preferences()
        for key in PREFERENCE_KEYS:
            value = user_prefs.get(key)
            if value is not None:
                merged[key] = value
    
    return merged


def build_user_message_with_preferences(
    content: str,
    preferences: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str]]:
    """根据偏好构建最终的用户消息和系统指令
    
    Args:
        content: 原始用户消息内容
        preferences: 用户偏好设置
    
    Returns:
        (处理后的消息内容, 系统指令文本)
    
    Examples:
        >>> build_user_message_with_preferences("你好", {"response_style": "brief"})
        ("你好", "直接回答问题... 简洁回答(120-150字)...")
    """
    if not content:
        return content, None
    
    # 合并默认偏好
    prefs = DEFAULT_INSTRUCTION_PREFS.copy()
    if preferences:
        prefs.update({k: v for k, v in preferences.items() if v is not None})
    
    # 检测消息提示
    hints = detect_message_hints(content)
    instructions: list[str] = []
    
    # 基础指令
    instructions.append("直接回答问题,避免'以下是...'、'针对您的...'等生硬开场白。")
    
    # 根据风格添加指令
    response_style = hints.get("response_style") or prefs.get("response_style", "chatgpt_like")
    
    if response_style == "brief":
        instructions.append("简洁回答(120-150字),直接给出核心信息")
    elif response_style == "detailed":
        instructions.append("详细专业回答(400-600字),完整说明原因、措施和建议")
    else:  # chatgpt_like
        instructions.append("标准回答(250-350字),包含原因分析、建议措施和注意事项")
    
    # 列表偏好
    if prefs.get("prefer_list") or hints.get("prefer_list"):
        instructions.append("用列表形式组织要点,每条详细说明")
    
    instruction_text = " ".join(instructions).strip()
    return content, instruction_text if instruction_text else None


def format_message_for_display(
    message: EngineChatMessage,
    include_role: bool = True
) -> str:
    """格式化消息用于显示
    
    Args:
        message: 消息对象
        include_role: 是否包含角色前缀
    
    Returns:
        格式化后的消息字符串
    """
    if include_role:
        role_prefix = {
            "user": "👤 用户",
            "assistant": "🤖 助手",
            "system": "⚙️ 系统",
            "tool": "🔧 工具",
        }.get(message.role, message.role)
        return f"{role_prefix}: {message.content}"
    return message.content


def truncate_message_content(
    content: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """截断消息内容
    
    Args:
        content: 消息内容
        max_length: 最大长度
        suffix: 截断后的后缀
    
    Returns:
        截断后的消息内容
    """
    if len(content) <= max_length:
        return content
    return content[:max_length - len(suffix)] + suffix

