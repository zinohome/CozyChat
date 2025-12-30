"""流式聊天服务

负责处理流式聊天生成,包括工具调用循环和消息保存
"""

# 标准库
import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING, cast

# 本地库
from app.engines.ai import ChatMessage as EngineChatMessage
from app.engines.ai.base import AIEngineBase
from app.utils.logger import logger
from app.utils.token_utils import truncate_messages, estimate_message_tokens
from .tool_handler import ToolCallHandler
from .message_saver import MessageSaver

if TYPE_CHECKING:
    from app.core.personality.models import Personality
    from app.core.personality import PersonalityRegistry


class StreamChatService:
    """流式聊天服务
    
    处理流式聊天生成,包括:
    - SSE流生成
    - 工具调用循环
    - 消息保存
    """
    
    def __init__(
        self,
        tool_handler: ToolCallHandler,
        message_saver: MessageSaver,
        personality_registry: Optional["PersonalityRegistry"] = None
    ):
        """初始化StreamChatService
        
        Args:
            tool_handler: 工具调用处理器
            message_saver: 消息保存服务
            personality_registry: 人格注册表
        """
        self.tool_handler = tool_handler
        self.message_saver = message_saver
        self.personality_registry = personality_registry
    
    async def generate_stream(
        self,
        engine: AIEngineBase,
        messages: List[EngineChatMessage],
        tools: Optional[List[Dict[str, Any]]],
        actual_max_tokens: Optional[int],
        actual_model: str,
        temperature: float,
        personality_id: Optional[str],
        personality: Optional["Personality"],
        user_id: Optional[str],
        session_id: Optional[str],
        use_memory: bool,
        memory_manager: Optional[Any] = None
    ) -> AsyncIterator[str]:
        """生成SSE流,支持工具调用
        
        Args:
            engine: AI引擎
            messages: 消息列表
            tools: 工具列表
            actual_max_tokens: 最大token数
            actual_model: 使用的模型
            temperature: 温度参数
            personality_id: 人格ID
            personality: 人格配置
            user_id: 用户ID
            session_id: 会话ID
            use_memory: 是否使用记忆
            memory_manager: 记忆管理器
            
        Yields:
            str: SSE格式的流数据
        """
        try:
            current_messages = messages.copy()
            max_iterations = 10  # 防止无限循环
            iteration = 0
            accumulated_content = ""  # 收集AI回复内容
            
            while iteration < max_iterations:
                iteration += 1
                
                # 重置状态
                tool_call_chunks: List[Optional[Dict[str, Any]]] = []
                finish_reason = None
                has_content = False
                
                # 第一轮:收集AI响应和工具调用
                logger.debug(
                    f"Starting chat stream iteration {iteration}",
                    extra={
                        "messages_count": len(current_messages),
                        "has_tools": bool(tools)
                    }
                )
                
                stream = engine.chat_stream(
                    messages=current_messages,
                    temperature=temperature,
                    max_tokens=actual_max_tokens,
                    tools=tools
                )
                # chat_stream返回AsyncIterator[StreamChunk]，使用类型注释明确类型
                from app.engines.ai.base import StreamChunk
                from typing import AsyncIterator
                typed_stream: AsyncIterator[StreamChunk] = cast(AsyncIterator[StreamChunk], stream)
                async for chunk in typed_stream:
                    chunk_dict = chunk.to_dict()
                    
                    # 检查是否有工具调用和内容
                    delta = chunk_dict.get("choices", [{}])[0].get("delta", {})
                    if delta.get("content"):
                        has_content = True
                        accumulated_content += delta.get("content", "")
                    if delta.get("tool_calls"):
                        # 收集工具调用增量
                        tool_call_chunks = self._merge_tool_call_chunks(
                            tool_call_chunks,
                            delta["tool_calls"]
                        )
                    
                    # 检查完成原因
                    chunk_finish_reason = chunk_dict.get("choices", [{}])[0].get("finish_reason")
                    if chunk_finish_reason:
                        finish_reason = chunk_finish_reason
                    
                    # 转发chunk到前端
                    yield f"data: {json.dumps(chunk_dict, ensure_ascii=False)}\n\n"
                
                # 检查是否需要继续工具调用循环
                should_continue_tool_calls = (
                    finish_reason == "tool_calls" 
                    and tool_call_chunks 
                    and len([tc for tc in tool_call_chunks if tc and tc.get("function", {}).get("name")]) > 0
                    and not has_content
                )
                
                if should_continue_tool_calls:
                    # 过滤掉None值
                    valid_tool_calls = [tc for tc in tool_call_chunks if tc is not None]
                    
                    # 执行工具
                    tool_results = await self.tool_handler.execute_tool_calls(
                        valid_tool_calls,
                        actual_max_tokens,
                        available_tokens=int(actual_max_tokens * 0.2) if actual_max_tokens else 500
                    )
                    
                    if tool_results:
                        # 添加assistant消息(包含tool_calls)
                        formatted_calls = ToolCallHandler.format_tool_calls_for_message(valid_tool_calls)
                        if formatted_calls:
                            current_messages.append(
                                EngineChatMessage(
                                    role="assistant",
                                    content="",
                                    tool_calls=formatted_calls
                                )
                            )
                        
                        # 添加tool消息(工具执行结果)
                        for tr in tool_results:
                            current_messages.append(
                                EngineChatMessage(
                                    role="tool",
                                    content=tr.get("content", ""),
                                    name=tr.get("tool_call_id", "")
                                )
                            )
                        
                        # 截断消息(如果需要)
                        if personality_id and self.personality_registry:
                            current_messages = await self._truncate_messages_if_needed(
                                current_messages,
                                personality_id,
                                actual_max_tokens
                            )
                        
                        # 继续下一轮对话
                        logger.debug(
                            f"Continuing tool call loop after iteration {iteration}",
                            extra={"iteration": iteration, "tools_executed": len(tool_results)}
                        )
                        continue
                
                # 正常完成
                logger.debug(
                    f"Stream completed normally after iteration {iteration}",
                    extra={
                        "iteration": iteration,
                        "finish_reason": finish_reason,
                        "has_content": has_content
                    }
                )
                yield "data: [DONE]\n\n"
                
                # 保存记忆(完全异步执行,不阻塞响应)
                if user_id and session_id and accumulated_content:
                    # 获取最后一条用户消息
                    last_user_message = None
                    for msg in reversed(current_messages):
                        if msg.role == "user" and msg.content:
                            last_user_message = msg.content
                            break
                    
                    if last_user_message:
                        asyncio.create_task(
                            self.message_saver.save_conversation_turn(
                                session_id=session_id,
                                user_id=user_id,
                                user_message=last_user_message,
                                assistant_message=accumulated_content,
                                assistant_model=actual_model,
                                memory_manager=memory_manager,
                                personality=personality,
                                use_memory=use_memory
                            )
                        )
                
                break
            
            if iteration >= max_iterations:
                logger.warning("Max iterations reached in tool calling loop")
                yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Stream generation error: {e}", exc_info=True)
            error_data = {
                "error": {
                    "message": str(e),
                    "type": "stream_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    def _merge_tool_call_chunks(
        self,
        existing_chunks: List[Optional[Dict[str, Any]]],
        new_chunks: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """合并工具调用增量
        
        Args:
            existing_chunks: 已有的工具调用chunk列表
            new_chunks: 新的工具调用chunk列表
            
        Returns:
            List[Dict[str, Any]]: 合并后的工具调用列表
        """
        for tc in new_chunks:
            idx = tc.get("index", 0)
            if idx >= len(existing_chunks):
                existing_chunks.extend([None] * (idx + 1 - len(existing_chunks)))
            
            if existing_chunks[idx] is None:
                existing_chunks[idx] = {
                    "id": tc.get("id", ""),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": tc.get("function", {}).get("arguments", "")
                    }
                }
            else:
                # 合并增量
                if tc.get("id"):
                    existing_chunks[idx]["id"] = tc.get("id")
                if tc.get("function", {}).get("name"):
                    existing_chunks[idx]["function"]["name"] = tc.get("function", {}).get("name")
                if tc.get("function", {}).get("arguments"):
                    existing_chunks[idx]["function"]["arguments"] += tc.get("function", {}).get("arguments", "")
        
        return existing_chunks
    
    async def _truncate_messages_if_needed(
        self,
        messages: List[EngineChatMessage],
        personality_id: str,
        actual_max_tokens: Optional[int]
    ) -> List[EngineChatMessage]:
        """如果消息超过限制,则截断
        
        Args:
            messages: 消息列表
            personality_id: 人格ID
            actual_max_tokens: 最大token数
            
        Returns:
            List[EngineChatMessage]: 截断后的消息列表
        """
        try:
            if not self.personality_registry:
                return messages
            
            # personality_id已经是str类型，直接使用
            personality = self.personality_registry.get_personality(personality_id)
            
            if personality and personality.ai.token_budget:
                max_history_tokens = personality.ai.token_budget.max_history_tokens
                if max_history_tokens > 0:
                    # 计算当前消息的总token数
                    total_tokens = sum(estimate_message_tokens(msg) for msg in messages)
                    
                    # 如果超过限制,截断历史消息
                    if total_tokens > max_history_tokens:
                        logger.debug(
                            f"Messages exceed token limit, truncating: {total_tokens}/{max_history_tokens}",
                            extra={
                                "total_tokens": total_tokens,
                                "max_history_tokens": max_history_tokens,
                                "message_count": len(messages)
                            }
                        )
                        
                        messages = truncate_messages(
                            messages,
                            max_history_tokens=max_history_tokens,
                            keep_system=True,
                            min_messages=4,
                            enable_summary=True,
                            max_summary_tokens=200
                        )
        except Exception as e:
            logger.warning(
                f"Failed to truncate messages in tool loop: {e}",
                exc_info=False
            )
        
        return messages

