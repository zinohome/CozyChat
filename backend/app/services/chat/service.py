"""聊天服务

负责处理非流式聊天生成和消息保存
"""

# 标准库
import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# 本地库
from app.engines.ai import ChatMessage as EngineChatMessage
from app.engines.ai.base import AIEngineBase
from app.utils.logger import logger
from .message_saver import MessageSaver

if TYPE_CHECKING:
    from app.core.personality.models import Personality


class ChatService:
    """聊天服务
    
    处理非流式聊天生成,包括:
    - 调用AI引擎生成回复
    - 消息保存
    """
    
    def __init__(self, message_saver: MessageSaver):
        """初始化ChatService
        
        Args:
            message_saver: 消息保存服务
        """
        self.message_saver = message_saver
    
    async def generate_response(
        self,
        engine: AIEngineBase,
        messages: List[EngineChatMessage],
        tools: Optional[List[Dict[str, Any]]],
        actual_max_tokens: Optional[int],
        temperature: float,
        personality: Optional["Personality"],
        user_id: Optional[str],
        session_id: Optional[str],
        use_memory: bool,
        memory_manager: Optional[Any] = None
    ) -> Any:
        """生成聊天回复(非流式)
        
        Args:
            engine: AI引擎
            messages: 消息列表
            tools: 工具列表
            actual_max_tokens: 最大token数
            temperature: 温度参数
            personality: 人格配置
            user_id: 用户ID
            session_id: 会话ID
            use_memory: 是否使用记忆
            memory_manager: 记忆管理器
            
        Returns:
            Dict[str, Any]: 聊天响应数据
        """
        # 调用AI引擎
        chat_response = await engine.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=actual_max_tokens,
            tools=tools
        )
        
        # 保存记忆(完全异步执行,不阻塞响应)
        if user_id and session_id:
            # 获取最后一条用户消息
            last_user_message = None
            for msg in reversed(messages):
                if msg.role == "user" and msg.content:
                    last_user_message = msg.content
                    break
            
            # 获取助手回复
            assistant_content = ""
            if chat_response.message:
                if hasattr(chat_response.message, 'content'):
                    assistant_content = chat_response.message.content or ""
                elif isinstance(chat_response.message, dict):
                    assistant_content = chat_response.message.get("content", "")
            
            # 创建异步任务保存,不等待完成
            if last_user_message and assistant_content:
                asyncio.create_task(
                    self.message_saver.save_conversation_turn(
                        session_id=session_id,
                        user_id=user_id,
                        user_message=last_user_message,
                        assistant_message=assistant_content,
                        assistant_model=chat_response.model,
                        memory_manager=memory_manager,
                        personality=personality,
                        use_memory=use_memory
                    )
                )
        
        return chat_response

