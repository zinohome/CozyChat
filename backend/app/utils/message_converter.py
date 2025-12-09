"""
消息转换工具

统一处理ContextBundle到消息列表的转换逻辑
"""

# 标准库
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.schemas.context import ContextBundle
    from app.engines.ai import ChatMessage as EngineChatMessage

# 本地库
from app.engines.ai import ChatMessage as EngineChatMessage
from app.utils.message_utils import build_user_message_with_preferences
from app.utils.logger import logger
from app.utils.type_helpers import get_message_role, safe_str


def convert_context_bundle_to_messages(
    context_bundle: "ContextBundle",
    current_message_content: str,
    user_preferences: Optional[Dict[str, Any]] = None
) -> List[EngineChatMessage]:
    """将ContextBundle转换为消息列表
    
    统一的转换逻辑，避免代码重复
    
    Args:
        context_bundle: 上下文包
        current_message_content: 当前消息内容
        user_preferences: 用户偏好（可选）
        
    Returns:
        List[EngineChatMessage]: 消息列表
    """
    messages = []
    
    # 1. 系统提示词
    for prompt in context_bundle.system_prompts:
        messages.append(EngineChatMessage(role="system", content=prompt))
    
    # 2. 用户画像
    if context_bundle.user_profile:
        profile_text = "## 用户信息\n"
        if isinstance(context_bundle.user_profile, dict):
            # 处理结构化用户画像
            if context_bundle.user_profile.get("interests"):
                profile_text += f"兴趣: {', '.join(context_bundle.user_profile['interests'])}\n"
            if context_bundle.user_profile.get("habits"):
                habits = context_bundle.user_profile["habits"]
                if isinstance(habits, dict):
                    if habits.get("most_active_time"):
                        profile_text += f"最活跃时间: {habits['most_active_time']}\n"
            if context_bundle.user_profile.get("username"):
                profile_text += f"用户名: {context_bundle.user_profile['username']}\n"
        else:
            profile_text += str(context_bundle.user_profile)
        messages.append(EngineChatMessage(role="system", content=profile_text))
    
    # 3. 历史摘要
    if context_bundle.summarized_history:
        if isinstance(context_bundle.summarized_history, list):
            # 多个摘要
            summary_text = "## 历史对话摘要\n\n"
            for i, summary in enumerate(context_bundle.summarized_history, 1):
                summary_text += f"**摘要 {i}**:\n{summary}\n\n"
        else:
            # 单个摘要
            summary_text = f"## 历史对话摘要\n{context_bundle.summarized_history}"
        messages.append(EngineChatMessage(role="system", content=summary_text))
    
    # 4. 检索到的记忆
    if context_bundle.retrieved_memories:
        from app.engines.memory.models import MemoryType
        
        # 按类型分组记忆
        user_memories = []
        assistant_memories = []
        
        for memory in context_bundle.retrieved_memories:
            # 处理Memory对象或字典
            if hasattr(memory, 'memory_type'):
                memory_type = memory.memory_type
                content = memory.content if hasattr(memory, 'content') else str(memory)
            elif isinstance(memory, dict):
                memory_type = memory.get("memory_type")
                content = memory.get("content", "")
            else:
                # 降级处理
                content = str(memory)
                memory_type = None
            
            if memory_type == MemoryType.USER:
                user_memories.append(content)
            elif memory_type == MemoryType.ASSISTANT:
                assistant_memories.append(content)
            else:
                # 未知类型，默认添加到用户记忆
                user_memories.append(content)
        
        memory_text = "## 相关记忆\n\n"
        if user_memories:
            memory_text += "### 用户相关记忆\n"
            for mem in user_memories[:5]:
                memory_text += f"- {mem}\n"
            memory_text += "\n"
        
        if assistant_memories:
            memory_text += "### 对话历史记忆\n"
            for mem in assistant_memories[:5]:
                memory_text += f"- {mem}\n"
            memory_text += "\n"
        
        if user_memories or assistant_memories:
            messages.append(EngineChatMessage(role="system", content=memory_text))
    
    # 5. 最近消息
    if context_bundle.recent_messages:
        for msg in context_bundle.recent_messages:
            # 处理不同的消息格式
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = get_message_role(msg)
                content = safe_str(msg.content)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                logger.warning(f"Unknown message format: {type(msg)}")
                continue
            
            messages.append(EngineChatMessage(role=role, content=content))
    
    # 6. 用户偏好指令和当前消息
    if user_preferences:
        preference_text = build_user_message_with_preferences(
            current_message_content,
            user_preferences
        )
        messages.append(EngineChatMessage(role="user", content=preference_text))
    else:
        # 7. 当前用户消息
        messages.append(EngineChatMessage(role="user", content=current_message_content))
    
    return messages
