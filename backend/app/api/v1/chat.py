"""
聊天API接口

提供OpenAI兼容的Chat Completions API
"""

# 标准库
import json
from typing import AsyncIterator
from datetime import timezone

# 第三方库
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

# 本地库
from app.api.deps import get_sync_session, get_current_active_user
from app.core.personality import PersonalityManager
from app.engines.ai import AIEngineFactory, ChatMessage as EngineChatMessage
from app.engines.tools import builtin  # 导入以注册工具
from app.engines.tools.manager import ToolManager
from app.models.session import Session as SessionModel
from app.models.message import Message as MessageModel
from app.models.user import User
from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    EngineListResponse,
    SaveVoiceCallMessagesRequest,
    SaveVoiceCallMessagesResponse,
)
from app.utils.logger import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_

router = APIRouter()


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: Session = Depends(get_sync_session)
):
    """创建聊天补全（OpenAI兼容接口）
    
    支持流式和非流式两种模式
    
    Args:
        request: 聊天请求
        db: 数据库会话（用于从session_id获取personality_id）
        
    Returns:
        ChatCompletionResponse: 聊天响应（非流式）
        StreamingResponse: SSE流（流式）
        
    Raises:
        HTTPException: 引擎创建失败或API调用失败
    """
    try:
        # 确定personality_id和user_id：优先使用请求中的，否则从session_id获取
        personality_id = request.personality_id
        user_id = request.user_id  # 默认使用请求中的 user_id
        session = None
        
        if request.session_id:
            try:
                import uuid
                session_uuid = uuid.UUID(request.session_id)
                session = db.query(SessionModel).filter(
                    SessionModel.id == session_uuid
                ).first()
                if session:
                    # 如果请求中没有 personality_id，从 session 获取
                    if not personality_id:
                        personality_id = session.personality_id
                        logger.debug(
                            f"Got personality_id from session: {personality_id}",
                            extra={"session_id": request.session_id}
                        )
                    
                    # 如果请求中没有 user_id，从 session 获取
                    if not user_id:
                        user_id = str(session.user_id)
                        logger.debug(
                            f"Got user_id from session: {user_id}",
                            extra={"session_id": request.session_id}
                        )
            except Exception as e:
                logger.warning(
                    f"Failed to get session info: {e}",
                    exc_info=False
                )
        
        # 确定使用的模型和引擎类型：优先使用personality配置，否则使用请求中的或默认值
        actual_model = request.model
        actual_engine_type = request.engine_type or "openai"
        actual_max_tokens = request.max_tokens  # 默认使用请求中的 max_tokens
        
        # 准备工具列表
        tools = request.tools  # 默认使用请求中的工具
        
        # 如果确定了personality_id，从人格配置加载工具和模型
        if personality_id:
            try:
                personality_manager = PersonalityManager()
                personality = personality_manager.get_personality(personality_id)
                
                if personality:
                    # 使用personality配置的模型和引擎类型
                    actual_model = personality.ai.model
                    actual_engine_type = personality.ai.provider
                    
                    # 如果请求中没有指定 max_tokens，使用 personality 配置的 max_tokens
                    if actual_max_tokens is None:
                        actual_max_tokens = personality.ai.max_tokens
                        logger.debug(
                            f"Using max_tokens from personality: {actual_max_tokens}",
                            extra={
                                "personality_id": personality_id,
                                "max_tokens": actual_max_tokens
                            }
                        )
                    
                    logger.debug(
                        f"Using model from personality: {actual_model}",
                        extra={
                            "personality_id": personality_id,
                            "model": actual_model,
                            "engine_type": actual_engine_type,
                            "max_tokens": actual_max_tokens
                        }
                    )
                    
                    # 加载工具
                    if personality.tools.enabled and (tools is None or len(tools) == 0):
                        tool_manager = ToolManager()
                        allowed_tools = personality.tools.allowed_tools
                        tools = tool_manager.get_tools_for_openai(tool_names=allowed_tools)
                        
                        logger.info(
                            f"Loaded tools from personality: {personality_id}",
                            extra={
                                "personality_id": personality_id,
                                "tools_count": len(tools),
                                "allowed_tools": allowed_tools,
                                "tool_names": [t.get("function", {}).get("name") for t in tools] if tools else []
                            }
                        )
                    elif tools:
                        logger.info(
                            f"Using tools from request",
                            extra={
                                "tools_count": len(tools),
                                "tool_names": [t.get("function", {}).get("name") for t in tools] if tools else []
                            }
                        )
                    else:
                        logger.warning(
                            f"No tools available for personality: {personality_id}",
                            extra={
                                "personality_id": personality_id,
                                "tools_enabled": personality.tools.enabled,
                                "allowed_tools": personality.tools.allowed_tools if personality.tools.enabled else []
                            }
                        )
            except Exception as e:
                logger.warning(
                    f"Failed to load personality config: {e}",
                    exc_info=True
                )
                # 如果加载失败，继续使用请求中的配置
        
        # 如果没有模型，使用默认值
        if not actual_model:
            # 从引擎配置获取默认模型
            try:
                from app.utils.config_loader import get_config_loader
                config_loader = get_config_loader()
                engine_config = config_loader.load_engine_config(actual_engine_type)
                actual_model = engine_config.get("default", {}).get("model", "gpt-3.5-turbo")
                logger.debug(
                    f"Using default model from engine config: {actual_model}",
                    extra={"engine_type": actual_engine_type, "model": actual_model}
                )
            except Exception as e:
                logger.warning(f"Failed to load default model from config: {e}", exc_info=False)
                actual_model = "gpt-3.5-turbo"  # 最后的默认值
        
        # 如果 max_tokens 仍然为 None，设置一个合理的默认值
        # 根据模型类型设置不同的默认值
        if actual_max_tokens is None:
            # 根据模型名称判断，GPT-4 系列使用更大的值
            if actual_model and ("gpt-4" in actual_model.lower() or "gpt-4o" in actual_model.lower()):
                actual_max_tokens = 8192  # GPT-4 系列默认 8192
            else:
                actual_max_tokens = 4096  # 其他模型默认 4096
            
            logger.debug(
                f"Using default max_tokens for model: {actual_max_tokens}",
                extra={
                    "model": actual_model,
                    "max_tokens": actual_max_tokens
                }
            )
        
        # 创建AI引擎（使用personality配置的模型或默认模型）
        engine = AIEngineFactory.create_engine(
            engine_type=actual_engine_type,
            model=actual_model
        )
        
        # 构建完整消息列表（包含系统提示词）
        full_messages = []
        
        # 如果确定了personality_id，添加系统提示词
        if personality_id:
            try:
                personality_manager = PersonalityManager()
                personality = personality_manager.get_personality(personality_id)
                
                if personality and personality.ai.system_prompt:
                    # 添加系统提示词
                    system_prompt = personality.ai.system_prompt
                    full_messages.append(
                        EngineChatMessage(
                            role="system",
                            content=system_prompt
                        )
                    )
                    logger.debug(
                        f"Added system prompt from personality",
                        extra={
                            "personality_id": personality_id,
                            "prompt_length": len(system_prompt)
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to add system prompt: {e}",
                    exc_info=False
        )
        
        # 转换并添加用户消息
        for msg in request.messages:
            full_messages.append(
            EngineChatMessage(
                role=msg.role,
                content=msg.content,
                name=msg.name,
                function_call=msg.function_call,
                tool_calls=msg.tool_calls
            )
            )
        
        # 如果确定了personality_id，根据 token_budget 截断消息历史
        # 同时检索相关记忆，避免丢失上下文
        if personality_id:
            try:
                personality_manager = PersonalityManager()
                personality = personality_manager.get_personality(personality_id)
                
                if personality:
                    # 1. 如果启用了记忆系统，先检索相关记忆
                    retrieved_memories = None
                    if personality.memory.enabled and request.use_memory and user_id and request.session_id:
                        try:
                            from app.engines.memory.manager import MemoryManager
                            memory_manager = MemoryManager()
                            
                            # 获取最后一条用户消息作为查询
                            last_user_message = None
                            for msg in reversed(request.messages):
                                if msg.role == "user" and msg.content:
                                    last_user_message = msg.content
                                    break
                            
                            if last_user_message:
                                memory_config = personality.memory
                                include_user = memory_config.save_mode in ["both", "user_only"]
                                include_ai = memory_config.save_mode in ["both", "assistant_only"]
                                
                                retrieved_memories = await memory_manager.retrieve_memories(
                                    user_id=user_id,
                                    session_id=request.session_id,
                                    query=last_user_message,
                                    max_results=memory_config.retrieval.max_results,
                                    include_user_memory=include_user,
                                    include_ai_memory=include_ai,
                                    timeout=memory_config.retrieval.timeout_seconds
                                )
                                
                                # 如果有检索到的记忆，添加到系统提示中
                                if retrieved_memories:
                                    user_memories = retrieved_memories.get("user_memories", [])
                                    ai_memories = retrieved_memories.get("ai_memories", [])
                                    
                                    if user_memories or ai_memories:
                                        memory_context = "\n\n## 相关记忆\n\n"
                                        
                                        if user_memories:
                                            memory_context += "### 用户记忆\n"
                                            for mem in user_memories[:3]:  # 只取前3条
                                                # MemorySearchResult 对象，通过 .memory.content 访问
                                                if hasattr(mem, 'memory') and hasattr(mem.memory, 'content'):
                                                    memory_context += f"- {mem.memory.content}\n"
                                                elif isinstance(mem, dict):
                                                    memory_context += f"- {mem.get('content', '')}\n"
                                        
                                        if ai_memories:
                                            memory_context += "\n### AI记忆\n"
                                            for mem in ai_memories[:3]:  # 只取前3条
                                                # MemorySearchResult 对象，通过 .memory.content 访问
                                                if hasattr(mem, 'memory') and hasattr(mem.memory, 'content'):
                                                    memory_context += f"- {mem.memory.content}\n"
                                                elif isinstance(mem, dict):
                                                    memory_context += f"- {mem.get('content', '')}\n"
                                        
                                        # 将记忆添加到第一个系统消息中
                                        if full_messages and full_messages[0].role == "system":
                                            full_messages[0].content += memory_context
                                        else:
                                            # 如果没有系统消息，创建一个
                                            full_messages.insert(0, EngineChatMessage(
                                                role="system",
                                                content=memory_context
                                            ))
                                        
                                        logger.debug(
                                            f"Added memories to context",
                                            extra={
                                                "personality_id": personality_id,
                                                "user_memories_count": len(user_memories),
                                                "ai_memories_count": len(ai_memories)
                                            }
                                        )
                        except Exception as e:
                            logger.warning(
                                f"Failed to retrieve memories: {e}",
                                exc_info=False
                            )
                    
                    # 2. 根据 token_budget 截断消息历史（包含摘要功能）
                    if personality.ai.token_budget:
                        max_history_tokens = personality.ai.token_budget.max_history_tokens
                        if max_history_tokens > 0:
                            from app.utils.token_utils import truncate_messages
                            full_messages = truncate_messages(
                                full_messages,
                                max_history_tokens=max_history_tokens,
                                keep_system=True,
                                min_messages=2,  # 至少保留最近一轮对话（用户+助手）
                                enable_summary=True,  # 启用摘要功能
                                max_summary_tokens=200  # 摘要最多200 tokens
                            )
                            logger.debug(
                                f"Truncated messages based on token budget",
                                extra={
                                    "personality_id": personality_id,
                                    "max_history_tokens": max_history_tokens,
                                    "final_message_count": len(full_messages),
                                    "has_memories": retrieved_memories is not None
                                }
                            )
            except Exception as e:
                logger.warning(
                    f"Failed to process token budget and memories: {e}",
                    exc_info=False
                )
        
        messages = full_messages
        
        # 流式输出
        if request.stream:
            async def generate_stream() -> AsyncIterator[str]:
                """生成SSE流，支持工具调用"""
                try:
                    current_messages = messages.copy()
                    max_iterations = 10  # 防止无限循环
                    iteration = 0
                    accumulated_content = ""  # 收集AI回复内容，用于保存记忆
                    stream_actual_model = actual_model  # 保存actual_model到闭包中
                    
                    while iteration < max_iterations:
                        iteration += 1
                        
                        # 重置状态
                        tool_call_chunks = []
                        finish_reason = None
                        has_content = False
                        
                        # 第一轮：收集AI响应和工具调用
                        logger.debug(
                            f"Starting chat stream iteration {iteration}",
                            extra={
                                "messages_count": len(current_messages),
                                "has_tools": bool(tools),
                                "tools_count": len(tools) if tools else 0,
                                "first_message": current_messages[0].role if current_messages else None
                            }
                        )
                        
                        async for chunk in engine.chat_stream(
                            messages=current_messages,
                            temperature=request.temperature,
                            max_tokens=actual_max_tokens,
                            tools=tools
                        ):
                            chunk_dict = chunk.to_dict()
                            
                            # 检查是否有工具调用和内容
                            delta = chunk_dict.get("choices", [{}])[0].get("delta", {})
                            if delta.get("content"):
                                has_content = True
                                # 收集AI回复内容，用于保存记忆
                                accumulated_content += delta.get("content", "")
                            if delta.get("tool_calls"):
                                # 收集工具调用增量
                                for tc in delta["tool_calls"]:
                                    idx = tc.get("index", 0)
                                    if idx >= len(tool_call_chunks):
                                        tool_call_chunks.extend([None] * (idx + 1 - len(tool_call_chunks)))
                                    
                                    if tool_call_chunks[idx] is None:
                                        tool_call_chunks[idx] = {
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
                                            tool_call_chunks[idx]["id"] = tc.get("id")
                                        if tc.get("function", {}).get("name"):
                                            tool_call_chunks[idx]["function"]["name"] = tc.get("function", {}).get("name")
                                        if tc.get("function", {}).get("arguments"):
                                            tool_call_chunks[idx]["function"]["arguments"] += tc.get("function", {}).get("arguments", "")
                            
                            # 检查完成原因（只在最后一个chunk中设置）
                            chunk_finish_reason = chunk_dict.get("choices", [{}])[0].get("finish_reason")
                            if chunk_finish_reason:
                                finish_reason = chunk_finish_reason
                            
                            # 转发所有chunk到前端
                            yield f"data: {json.dumps(chunk_dict, ensure_ascii=False)}\n\n"

                        # 检查是否需要继续工具调用循环
                        # 只有在 finish_reason 是 "tool_calls" 且没有内容且确实有工具调用时才继续
                        should_continue_tool_calls = (
                            finish_reason == "tool_calls" 
                            and tool_call_chunks 
                            and len([tc for tc in tool_call_chunks if tc and tc.get("function", {}).get("name")]) > 0
                            and not has_content
                        )
                        
                        if should_continue_tool_calls:
                            # 执行工具
                            tool_manager = ToolManager()
                            tool_results = []
                            
                            for tc in tool_call_chunks:
                                if not tc or not tc.get("function", {}).get("name"):
                                    continue
                                
                                tool_name = tc["function"]["name"]
                                try:
                                    # 解析参数
                                    import json as json_lib
                                    args = json_lib.loads(tc["function"].get("arguments", "{}"))
                                    
                                    # 执行工具
                                    result = await tool_manager.execute_tool(
                                        tool_name=tool_name,
                                        parameters=args
                                    )
                                    
                                    # 格式化结果（content应该是字符串，不是JSON字符串）
                                    if result.get("success"):
                                        result_content = result.get("result", "")
                                        # 如果结果是字典或列表，转换为JSON字符串；否则直接使用字符串
                                        if isinstance(result_content, (dict, list)):
                                            result_content = json_lib.dumps(result_content, ensure_ascii=False)
                                        else:
                                            result_content = str(result_content)
                                        
                                        # 截断过长的工具结果，避免超过token限制
                                        # 根据 max_tokens 和当前消息长度，计算工具结果的最大长度
                                        from app.utils.token_utils import estimate_tokens
                                        
                                        # 估算当前消息的token数
                                        current_tokens = sum(
                                            estimate_tokens(msg.content or "") + 
                                            (len(msg.tool_calls) * 50 if msg.tool_calls else 0)
                                            for msg in current_messages
                                        )
                                        
                                        # 预留一些token给AI回复（假设AI回复最多占max_tokens的80%）
                                        available_for_tool_result = int(actual_max_tokens * 0.2) if actual_max_tokens else 500
                                        
                                        # 如果工具结果太长，截断它
                                        result_tokens = estimate_tokens(result_content)
                                        if result_tokens > available_for_tool_result:
                                            # 计算可以保留的字符数（大约2字符/token）
                                            max_chars = available_for_tool_result * 2
                                            if len(result_content) > max_chars:
                                                truncated_content = result_content[:max_chars] + f"\n\n[结果已截断，原始长度: {len(result_content)} 字符]"
                                                logger.warning(
                                                    f"Tool result too long, truncated: {len(result_content)} -> {len(truncated_content)} chars",
                                                    extra={
                                                        "tool_name": tool_name,
                                                        "original_length": len(result_content),
                                                        "truncated_length": len(truncated_content),
                                                        "original_tokens": result_tokens,
                                                        "truncated_tokens": estimate_tokens(truncated_content)
                                                    }
                                                )
                                                result_content = truncated_content
                                        
                                        tool_results.append({
                                            "role": "tool",
                                            "tool_call_id": tc.get("id", ""),
                                            "content": result_content
                                        })
                                    else:
                                        tool_results.append({
                                            "role": "tool",
                                            "tool_call_id": tc.get("id", ""),
                                            "content": f"工具执行失败: {result.get('error', 'Unknown error')}"
                                        })
                                    
                                    logger.info(
                                        f"Tool executed: {tool_name}",
                                        extra={"tool_name": tool_name, "success": result.get("success")}
                                    )
                                except Exception as e:
                                    logger.error(f"Tool execution error: {e}", exc_info=True)
                                    tool_results.append({
                                        "role": "tool",
                                        "tool_call_id": tc.get("id", ""),
                                        "content": f"工具执行出错: {str(e)}"
                                    })
                            
                            # 将工具结果添加到消息列表，继续对话
                            if tool_results:
                                # 添加assistant消息（包含tool_calls）
                                assistant_tool_calls = []
                                for tc in tool_call_chunks:
                                    if tc and tc.get("function", {}).get("name"):
                                        assistant_tool_calls.append({
                                            "id": tc.get("id", ""),
                                            "type": tc.get("type", "function"),
                                            "function": tc.get("function", {})
                                        })
                                
                                if assistant_tool_calls:
                                    current_messages.append(
                                        EngineChatMessage(
                                            role="assistant",
                                            content="",
                                            tool_calls=assistant_tool_calls
                                        )
                                    )
                                
                                # 添加tool消息（工具执行结果）
                                for tr in tool_results:
                                    current_messages.append(
                                        EngineChatMessage(
                                            role="tool",
                                            content=tr.get("content", ""),
                                            name=tr.get("tool_call_id", "")  # 使用tool_call_id作为name
                                        )
                                    )
                                
                                # 在继续循环前，检查消息总长度，如果超过限制，截断历史消息
                                if personality_id:
                                    try:
                                        personality_manager = PersonalityManager()
                                        personality = personality_manager.get_personality(personality_id)
                                        
                                        if personality and personality.ai.token_budget:
                                            max_history_tokens = personality.ai.token_budget.max_history_tokens
                                            if max_history_tokens > 0:
                                                from app.utils.token_utils import truncate_messages, estimate_message_tokens
                                                
                                                # 计算当前消息的总token数
                                                total_tokens = sum(estimate_message_tokens(msg) for msg in current_messages)
                                                
                                                # 如果超过限制，截断历史消息（保留系统消息、工具调用和工具结果）
                                                if total_tokens > max_history_tokens:
                                                    logger.debug(
                                                        f"Messages exceed token limit before next iteration, truncating: {total_tokens}/{max_history_tokens}",
                                                        extra={
                                                            "total_tokens": total_tokens,
                                                            "max_history_tokens": max_history_tokens,
                                                            "message_count": len(current_messages)
                                                        }
                                                    )
                                                    
                                                    # 截断消息，但至少保留最近的工具调用和结果
                                                    # 保留：系统消息 + 最后一条用户消息 + 工具调用 + 工具结果
                                                    current_messages = truncate_messages(
                                                        current_messages,
                                                        max_history_tokens=max_history_tokens,
                                                        keep_system=True,
                                                        min_messages=4,  # 至少保留：用户消息 + assistant工具调用 + tool结果 + 可能的assistant回复
                                                        enable_summary=True,
                                                        max_summary_tokens=200
                                                    )
                                    except Exception as e:
                                        logger.warning(
                                            f"Failed to truncate messages in tool loop: {e}",
                                            exc_info=False
                                        )
                                
                                # 继续下一轮对话（不发送结束标记）
                                logger.debug(
                                    f"Continuing tool call loop after iteration {iteration}",
                                    extra={
                                        "iteration": iteration,
                                        "tools_executed": len(tool_results),
                                        "messages_count": len(current_messages)
                                    }
                                )
                                continue
                        
                        # 正常完成（finish_reason 不是 tool_calls，或者有内容，或者没有工具调用）
                        # 先发送结束标记，然后再保存记忆（不阻塞响应）
                        logger.debug(
                            f"Stream completed normally after iteration {iteration}",
                            extra={
                                "iteration": iteration,
                                "finish_reason": finish_reason,
                                "has_content": has_content,
                                "has_tool_calls": bool(tool_call_chunks)
                            }
                        )
                        yield "data: [DONE]\n\n"
                        
                        # 保存记忆（如果启用了记忆系统）- 完全异步执行，不阻塞响应
                        if personality_id and user_id and request.session_id:
                            # 获取最后一条用户消息和AI回复（在异步任务外获取，避免闭包问题）
                            last_user_message = None
                            for msg in reversed(current_messages):
                                if msg.role == "user" and msg.content:
                                    last_user_message = msg.content
                                    break
                            
                            assistant_content = accumulated_content
                            
                            # 创建异步任务保存记忆和更新标题，不等待结果
                            if last_user_message and assistant_content:
                                import asyncio
                                from app.engines.memory.manager import MemoryManager
                                from app.core.session import SessionTitleGenerator
                                
                                async def save_memory_and_update_title_async():
                                    """异步保存消息、记忆和更新标题，不阻塞主流程"""
                                    try:
                                        # 需要创建新的数据库会话，因为原会话可能在异步任务中已关闭
                                        from app.models.base import get_sync_db
                                        import uuid
                                        
                                        async_db = next(get_sync_db())
                                        try:
                                            session_uuid = uuid.UUID(request.session_id)
                                            user_uuid = uuid.UUID(user_id)
                                            
                                            # 保存用户消息到数据库
                                            try:
                                                user_message = MessageModel(
                                                    session_id=session_uuid,
                                                    user_id=user_uuid,
                                                    role="user",
                                                    content=last_user_message
                                                )
                                                async_db.add(user_message)
                                                
                                                # 保存助手消息到数据库
                                                # 获取实际使用的模型（使用闭包中的stream_actual_model）
                                                assistant_model = stream_actual_model
                                                
                                                assistant_message = MessageModel(
                                                    session_id=session_uuid,
                                                    user_id=user_uuid,
                                                    role="assistant",
                                                    content=assistant_content,
                                                    model=assistant_model
                                                )
                                                async_db.add(assistant_message)
                                                
                                                # 更新会话的message_count和last_message_at
                                                session = async_db.query(SessionModel).filter(
                                                    SessionModel.id == session_uuid
                                                ).first()
                                                if session:
                                                    session.message_count = (session.message_count or 0) + 2
                                                    from datetime import datetime
                                                    session.last_message_at = datetime.utcnow()
                                                
                                                async_db.commit()
                                                
                                                logger.debug(
                                                    f"Saved messages to database (stream)",
                                                    extra={
                                                        "user_id": user_id,
                                                        "session_id": request.session_id,
                                                        "user_message_length": len(last_user_message),
                                                        "assistant_message_length": len(assistant_content)
                                                    }
                                                )
                                            except Exception as msg_error:
                                                logger.warning(
                                                    f"Failed to save messages to database: {msg_error}",
                                                    exc_info=False
                                                )
                                                async_db.rollback()
                                            
                                            # 保存记忆（如果启用了记忆系统）
                                            personality_manager = PersonalityManager()
                                            personality = personality_manager.get_personality(personality_id)
                                            
                                            if personality and personality.memory.enabled and request.use_memory:
                                                memory_manager = MemoryManager()
                                                
                                                # 使用 async_save=True 异步保存，不阻塞
                                                await memory_manager.add_conversation_turn(
                                                    user_id=user_id,
                                                    session_id=request.session_id,
                                                    user_message=last_user_message,
                                                    assistant_message=assistant_content,
                                                    importance=0.5,
                                                    async_save=True
                                                )
                                                
                                                logger.debug(
                                                    f"Saved conversation to memory (stream)",
                                                    extra={
                                                        "user_id": user_id,
                                                        "session_id": request.session_id,
                                                        "user_message_length": len(last_user_message),
                                                        "assistant_message_length": len(assistant_content)
                                                    }
                                                )
                                            
                                            # 更新会话标题（如果需要）
                                            try:
                                                title_generator = SessionTitleGenerator(async_db)
                                                await title_generator.update_session_title_if_needed(
                                                    session_id=request.session_id,
                                                    personality_id=personality_id
                                                )
                                            except Exception as title_error:
                                                logger.warning(
                                                    f"Failed to update session title (stream): {title_error}",
                                                    exc_info=False
                                                )
                                        finally:
                                            async_db.close()
                                    except Exception as e:
                                        logger.warning(
                                            f"Failed to save memory (stream): {e}",
                                            exc_info=False
                                        )
                                
                                # 创建后台任务，不等待完成
                                asyncio.create_task(save_memory_and_update_title_async())
                        
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
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # 非流式输出
        else:
            response = await engine.chat(
                messages=messages,
                temperature=request.temperature,
                max_tokens=actual_max_tokens,
                tools=tools
            )
            
            # 保存记忆（如果启用了记忆系统）- 完全异步执行，不阻塞响应
            if personality_id and user_id and request.session_id:
                # 获取最后一条用户消息和AI回复（在异步任务外获取，避免闭包问题）
                last_user_message = None
                for msg in reversed(request.messages):
                    if msg.role == "user" and msg.content:
                        last_user_message = msg.content
                        break
                
                assistant_content = ""
                if response.message:
                    if hasattr(response.message, 'content'):
                        assistant_content = response.message.content or ""
                    elif isinstance(response.message, dict):
                        assistant_content = response.message.get("content", "")
                
                # 创建异步任务保存记忆和更新标题，不等待结果
                if last_user_message and assistant_content:
                    import asyncio
                    from app.engines.memory.manager import MemoryManager
                    from app.core.session import SessionTitleGenerator
                    
                    async def save_memory_and_update_title_async():
                        """异步保存消息、记忆和更新标题，不阻塞主流程"""
                        try:
                            # 需要创建新的数据库会话，因为原会话可能在异步任务中已关闭
                            from app.models.base import get_sync_db
                            import uuid
                            
                            async_db = next(get_sync_db())
                            try:
                                session_uuid = uuid.UUID(request.session_id)
                                user_uuid = uuid.UUID(user_id)
                                
                                # 保存用户消息到数据库
                                try:
                                    user_message = MessageModel(
                                        session_id=session_uuid,
                                        user_id=user_uuid,
                                        role="user",
                                        content=last_user_message
                                    )
                                    async_db.add(user_message)
                                    
                                    # 保存助手消息到数据库
                                    assistant_message = MessageModel(
                                        session_id=session_uuid,
                                        user_id=user_uuid,
                                        role="assistant",
                                        content=assistant_content,
                                        model=response.model
                                    )
                                    async_db.add(assistant_message)
                                    
                                    # 更新会话的message_count和last_message_at
                                    session = async_db.query(SessionModel).filter(
                                        SessionModel.id == session_uuid
                                    ).first()
                                    if session:
                                        session.message_count = (session.message_count or 0) + 2
                                        from datetime import datetime
                                        session.last_message_at = datetime.utcnow()
                                    
                                    async_db.commit()
                                    
                                    logger.debug(
                                        f"Saved messages to database (non-stream)",
                                        extra={
                                            "user_id": user_id,
                                            "session_id": request.session_id,
                                            "user_message_length": len(last_user_message),
                                            "assistant_message_length": len(assistant_content)
                                        }
                                    )
                                except Exception as msg_error:
                                    logger.warning(
                                        f"Failed to save messages to database: {msg_error}",
                                        exc_info=False
                                    )
                                    async_db.rollback()
                                
                                # 保存记忆（如果启用了记忆系统）
                                personality_manager = PersonalityManager()
                                personality = personality_manager.get_personality(personality_id)
                                
                                if personality and personality.memory.enabled and request.use_memory:
                                    memory_manager = MemoryManager()
                                    
                                    # 使用 async_save=True 异步保存，不阻塞
                                    await memory_manager.add_conversation_turn(
                                        user_id=user_id,
                                        session_id=request.session_id,
                                        user_message=last_user_message,
                                        assistant_message=assistant_content,
                                        importance=0.5,
                                        async_save=True
                                    )
                                    
                                    logger.debug(
                                        f"Saved conversation to memory (non-stream)",
                                        extra={
                                            "user_id": user_id,
                                            "session_id": request.session_id,
                                            "user_message_length": len(last_user_message),
                                            "assistant_message_length": len(assistant_content)
                                        }
                                    )
                                
                                # 更新会话标题（如果需要）
                                try:
                                    title_generator = SessionTitleGenerator(async_db)
                                    await title_generator.update_session_title_if_needed(
                                        session_id=request.session_id,
                                        personality_id=personality_id
                                    )
                                except Exception as title_error:
                                    logger.warning(
                                        f"Failed to update session title (non-stream): {title_error}",
                                        exc_info=False
                                    )
                            finally:
                                async_db.close()
                        except Exception as e:
                            logger.warning(
                                f"Failed to save memory (non-stream): {e}",
                                exc_info=False
                            )
                    
                    # 创建后台任务，不等待完成
                    asyncio.create_task(save_memory_and_update_title_async())
            
            # 转换为API响应格式
            return ChatCompletionResponse(
                id=response.id,
                created=response.created,
                model=response.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=response.message.to_dict() if hasattr(response.message, 'to_dict') else response.message,
                        finish_reason=response.finish_reason
                    )
                ],
                usage=ChatCompletionUsage(**response.usage) if response.usage else ChatCompletionUsage(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
            )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat completion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        )


@router.get("/engines", response_model=EngineListResponse)
async def list_engines() -> EngineListResponse:
    """列出所有可用的AI引擎
    
    Returns:
        EngineListResponse: 引擎列表
    """
    try:
        available_engines = AIEngineFactory.list_available_engines()
        
        return EngineListResponse(
            engines=list(available_engines.keys()),
            default_engine="openai",
            descriptions=available_engines
        )
    except Exception as e:
        logger.error(f"Failed to list engines: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list engines"
        )


# 注意：模型列表端点已移至 /v1/models（models.py）
# 这里不再提供 /v1/chat/models 端点，请使用 /v1/models


@router.post("/voice-call-messages", response_model=SaveVoiceCallMessagesResponse)
async def save_voice_call_messages(
    request: SaveVoiceCallMessagesRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_session)
):
    """保存语音通话消息到数据库
    
    Args:
        request: 保存语音通话消息请求
        user: 当前用户
        db: 数据库会话
        
    Returns:
        SaveVoiceCallMessagesResponse: 保存结果
        
    Raises:
        HTTPException: 如果会话不存在或不属于当前用户
    """
    try:
        import uuid
        from datetime import datetime
        
        # 验证会话ID
        try:
            session_uuid = uuid.UUID(request.session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            )
        
        # 验证会话是否存在且属于当前用户
        session = db.query(SessionModel).filter(
            and_(
                SessionModel.id == session_uuid,
                SessionModel.user_id == user.id,
                SessionModel.deleted_at.is_(None)
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # 保存消息
        saved_count = 0
        for msg in request.messages:
            try:
                # 解析时间戳（如果有）
                created_at = datetime.utcnow()
                if msg.timestamp:
                    try:
                        # 尝试解析ISO格式时间戳
                        # 支持格式：2025-01-13T10:30:00.000Z 或 2025-01-13T10:30:00
                        timestamp_str = msg.timestamp
                        if timestamp_str.endswith('Z'):
                            timestamp_str = timestamp_str[:-1] + '+00:00'
                        elif '+' not in timestamp_str and '-' in timestamp_str:
                            # 如果没有时区信息，假设是UTC
                            if 'T' in timestamp_str:
                                timestamp_str = timestamp_str + '+00:00'
                        
                        # 使用datetime.fromisoformat解析（Python 3.7+）
                        parsed_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        # 转换为UTC并移除时区信息
                        if parsed_time.tzinfo:
                            parsed_time = parsed_time.astimezone(timezone.utc)
                        created_at = parsed_time.replace(tzinfo=None)
                    except Exception as parse_error:
                        # 如果解析失败，使用当前时间
                        logger.debug(f"Failed to parse timestamp {msg.timestamp}: {parse_error}")
                        pass
                
                message = MessageModel(
                    session_id=session_uuid,
                    user_id=user.id,
                    role=msg.role,
                    content=msg.content,
                    created_at=created_at,
                    message_metadata={"is_voice_call": True}  # 标记为语音通话消息
                )
                db.add(message)
                saved_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to save voice call message: {e}",
                    extra={"user_id": str(user.id), "session_id": request.session_id}
                )
        
        # 更新会话统计信息
        session.message_count = (session.message_count or 0) + saved_count
        session.last_message_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            "Saved voice call messages",
            extra={
                "user_id": str(user.id),
                "session_id": request.session_id,
                "saved_count": saved_count
            }
        )
        
        return SaveVoiceCallMessagesResponse(
            message="消息已保存",
            saved_count=saved_count,
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save voice call messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save voice call messages: {str(e)}"
        )

