"""
Token 工具函数

提供 token 计数和消息历史管理功能
"""
from typing import List, Dict, Any, Optional
from app.engines.ai.base import ChatMessage
from app.utils.logger import logger


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量
    
    使用简单的字符数估算方法（适用于中文和英文混合）
    对于中文：大约 1.5 个字符 = 1 token
    对于英文：大约 4 个字符 = 1 token
    
    Args:
        text: 要估算的文本
        
    Returns:
        估算的 token 数量
    """
    if not text:
        return 0
    
    # 简单估算：中文字符按 1.5 字符/token，英文按 4 字符/token
    # 混合文本取平均值：约 2.5 字符/token
    # 加上消息格式开销（role, content 等），每个消息额外 +5 tokens
    return len(text) // 2 + 5


def estimate_message_tokens(message: ChatMessage) -> int:
    """估算单条消息的 token 数量
    
    Args:
        message: 聊天消息
        
    Returns:
        估算的 token 数量
    """
    tokens = 0
    
    # 角色和内容
    if message.content:
        tokens += estimate_tokens(message.content)
    
    # 工具调用（如果有）
    if message.tool_calls:
        for tool_call in message.tool_calls:
            # 估算工具调用的 token（函数名、参数等）
            if isinstance(tool_call, dict):
                func_name = tool_call.get("function", {}).get("name", "")
                func_args = tool_call.get("function", {}).get("arguments", "")
                tokens += estimate_tokens(func_name) + estimate_tokens(func_args) + 10
    
    # 函数调用（如果有，旧格式）
    if message.function_call:
        if isinstance(message.function_call, dict):
            func_name = message.function_call.get("name", "")
            func_args = message.function_call.get("arguments", "")
            tokens += estimate_tokens(func_name) + estimate_tokens(func_args) + 10
    
    # 消息格式开销（role, name 等）
    tokens += 5
    
    return tokens


def summarize_old_messages(
    old_messages: List[ChatMessage],
    max_summary_tokens: int = 200
) -> Optional[ChatMessage]:
    """将旧消息压缩成摘要
    
    这是一个简化版本，实际生产环境可以使用AI模型生成摘要
    
    Args:
        old_messages: 要摘要的旧消息列表
        max_summary_tokens: 摘要的最大 token 数
        
    Returns:
        摘要消息（如果成功），否则返回 None
    """
    if not old_messages:
        return None
    
    # 提取关键信息：用户问题和AI回答
    summary_parts = []
    for msg in old_messages:
        if msg.role in ["user", "assistant"] and msg.content:
            # 截取前100个字符作为摘要
            content_preview = msg.content[:100] + ("..." if len(msg.content) > 100 else "")
            summary_parts.append(f"{msg.role}: {content_preview}")
    
    if not summary_parts:
        return None
    
    # 组合摘要
    summary_content = "之前的对话摘要：\n" + "\n".join(summary_parts[:5])  # 最多5条
    if len(old_messages) > 5:
        summary_content += f"\n...（还有 {len(old_messages) - 5} 条消息）"
    
    # 创建摘要消息
    summary_message = ChatMessage(
        role="system",
        content=summary_content
    )
    
    # 检查摘要是否超过限制
    if estimate_message_tokens(summary_message) > max_summary_tokens:
        # 如果超过，进一步压缩
        summary_content = "之前的对话摘要（已压缩）"
        summary_message = ChatMessage(
            role="system",
            content=summary_content
        )
    
    return summary_message


def truncate_messages(
    messages: List[ChatMessage],
    max_history_tokens: int,
    keep_system: bool = True,
    min_messages: int = 2,
    enable_summary: bool = True,
    max_summary_tokens: int = 200
) -> List[ChatMessage]:
    """截断消息历史，确保不超过 token 限制
    
    策略：
    1. 始终保留系统消息（如果存在）
    2. 保留最近的用户-助手对话对
    3. 如果截断了旧消息，尝试生成摘要（可选）
    4. 如果仍然超过限制，逐步减少消息数量
    
    Args:
        messages: 消息列表
        max_history_tokens: 最大历史 token 数
        keep_system: 是否保留系统消息
        min_messages: 最少保留的消息数量（不包括系统消息）
        enable_summary: 是否对截断的旧消息生成摘要
        max_summary_tokens: 摘要的最大 token 数
        
    Returns:
        截断后的消息列表（可能包含摘要）
    """
    if not messages:
        return messages
    
    # 分离系统消息和其他消息
    system_messages = []
    other_messages = []
    
    for msg in messages:
        if msg.role == "system":
            system_messages.append(msg)
        else:
            other_messages.append(msg)
    
    # 计算系统消息的 token 数
    system_tokens = sum(estimate_message_tokens(msg) for msg in system_messages)
    
    # 如果系统消息本身就超过限制，只保留系统消息
    if system_tokens >= max_history_tokens:
        logger.warning(
            f"System messages exceed max_history_tokens ({max_history_tokens}), "
            f"keeping only system messages"
        )
        return system_messages if keep_system else []
    
    # 计算可用于历史消息的 token 数（预留一些给摘要）
    summary_reserve = max_summary_tokens if enable_summary else 0
    available_tokens = max_history_tokens - system_tokens - summary_reserve
    
    # 从后往前保留消息，直到达到 token 限制
    truncated_messages = []
    discarded_messages = []
    current_tokens = 0
    
    # 从最后一条消息开始，向前遍历
    for i in range(len(other_messages) - 1, -1, -1):
        msg = other_messages[i]
        msg_tokens = estimate_message_tokens(msg)
        
        # 如果加上这条消息会超过限制，停止
        if current_tokens + msg_tokens > available_tokens:
            # 如果已经保留了最少消息数，停止
            if len(truncated_messages) >= min_messages:
                # 记录被丢弃的消息
                discarded_messages = other_messages[:i+1]
                break
            # 否则继续添加（即使超过限制）
        
        truncated_messages.insert(0, msg)
        current_tokens += msg_tokens
    
    # 如果有被丢弃的消息且启用了摘要，尝试生成摘要
    summary_message = None
    if discarded_messages and enable_summary:
        summary_message = summarize_old_messages(
            discarded_messages,
            max_summary_tokens=max_summary_tokens
        )
        
        if summary_message:
            summary_tokens = estimate_message_tokens(summary_message)
            # 如果摘要加上当前消息仍然在限制内，添加摘要
            if system_tokens + current_tokens + summary_tokens <= max_history_tokens:
                logger.debug(
                    f"Added summary for {len(discarded_messages)} discarded messages",
                    extra={
                        "discarded_count": len(discarded_messages),
                        "summary_tokens": summary_tokens
                    }
                )
            else:
                # 摘要会超过限制，不使用摘要
                summary_message = None
                logger.debug(
                    f"Summary would exceed token limit, skipping summary",
                    extra={
                        "summary_tokens": summary_tokens,
                        "available_tokens": max_history_tokens - system_tokens - current_tokens
                    }
                )
    
    # 组合系统消息、摘要（如果有）和截断后的消息
    result = []
    if keep_system:
        result.extend(system_messages)
    
    # 如果有摘要，添加到系统消息之后
    if summary_message:
        result.append(summary_message)
    
    result.extend(truncated_messages)
    
    # 记录截断信息
    if len(other_messages) > len(truncated_messages):
        logger.info(
            f"Truncated message history: {len(other_messages)} -> {len(truncated_messages)} messages, "
            f"tokens: {system_tokens + current_tokens + (estimate_message_tokens(summary_message) if summary_message else 0)}/{max_history_tokens}, "
            f"summary: {'yes' if summary_message else 'no'}",
            extra={
                "original_count": len(other_messages),
                "truncated_count": len(truncated_messages),
                "discarded_count": len(discarded_messages),
                "system_tokens": system_tokens,
                "history_tokens": current_tokens,
                "summary_tokens": estimate_message_tokens(summary_message) if summary_message else 0,
                "total_tokens": system_tokens + current_tokens + (estimate_message_tokens(summary_message) if summary_message else 0),
                "max_history_tokens": max_history_tokens,
                "has_summary": summary_message is not None
            }
        )
    
    return result

