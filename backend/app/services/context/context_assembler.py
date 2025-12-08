"""
上下文组装服务

负责将各个组件组装成完整的上下文包
"""

# 标准库
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.core.personality.models import Personality
    from app.schemas.context import Message as MessageSchema

# 本地库
from app.schemas.context import ContextBundle
from app.utils.logger import logger


class ContextAssembler:
    """上下文组装器
    
    负责将各个组件组装成完整的上下文包
    """
    
    def assemble_context(
        self,
        personality_config: "Personality",
        recent_messages: List["MessageSchema"],
        summaries: List[str],
        memories: List[Any],
        user_profile: Optional[Dict[str, Any]],
        max_tokens: int
    ) -> ContextBundle:
        """组装上下文包
        
        Args:
            personality_config: 人格配置
            recent_messages: 最近消息
            summaries: 历史摘要
            memories: 检索到的记忆
            user_profile: 用户画像
            max_tokens: 最大token数
            
        Returns:
            ContextBundle: 上下文包
        """
        # 构建系统提示词
        system_prompts = []
        
        # 1. 人格定义
        if personality_config and hasattr(personality_config, 'ai'):
            # 从AI配置中获取system_prompt
            ai_config = personality_config.ai
            if hasattr(ai_config, 'system_prompt') and ai_config.system_prompt:
                system_prompts.append(ai_config.system_prompt)
            elif hasattr(personality_config, 'description') and personality_config.description:
                system_prompts.append(personality_config.description)
        
        # 2. 用户画像
        if user_profile:
            profile_text = f"用户信息: {user_profile.get('username', '未知')}"
            if user_profile.get('preferences'):
                profile_text += f"，偏好: {user_profile['preferences']}"
            system_prompts.append(profile_text)
        
        # 粗略估算token数
        # 简单按字符数估算：中文约1.5token/字，英文约0.25token/词
        estimated_tokens = sum(len(p) * 1.5 for p in system_prompts)
        estimated_tokens += sum(len(s) * 1.5 for s in summaries)
        # memories 是 MemorySearchResult 列表，需要提取 memory.content
        for m in memories:
            if hasattr(m, 'memory'):
                # MemorySearchResult 对象
                estimated_tokens += len(m.memory.content) * 1.5
            elif hasattr(m, 'content'):
                # 已经是 Memory 对象
                estimated_tokens += len(m.content) * 1.5
        estimated_tokens += sum(len(msg.content) * 1.5 for msg in recent_messages if msg.content)
        
        # 将 MemorySearchResult 列表转换为 Memory 列表（ContextBundle 需要 Memory 类型）
        memory_list = []
        for mem_result in memories:
            if hasattr(mem_result, 'memory'):
                # MemorySearchResult 对象，提取 memory 属性
                memory_list.append(mem_result.memory)
            elif hasattr(mem_result, 'content'):
                # 已经是 Memory 对象
                memory_list.append(mem_result)
        
        logger.debug(
            f"Assembling context bundle",
            extra={
                "system_prompts_count": len(system_prompts),
                "recent_messages_count": len(recent_messages),
                "summaries_count": len(summaries),
                "memories_count": len(memory_list),
                "user_profile": user_profile is not None,
                "estimated_tokens": int(estimated_tokens)
            }
        )
        
        return ContextBundle(
            system_prompts=system_prompts,
            recent_messages=recent_messages,
            summarized_history=summaries,
            retrieved_memories=memory_list,  # 使用转换后的 Memory 列表
            user_profile=user_profile,
            total_tokens=int(estimated_tokens),
            metadata={
                "max_tokens": max_tokens,
                "personality_id": personality_config.id if hasattr(personality_config, 'id') else None
            }
        )
    
    def build_fallback_context(
        self,
        personality_config: "Personality"
    ) -> ContextBundle:
        """构建降级上下文（当主流程失败时使用）
        
        Args:
            personality_config: 人格配置
            
        Returns:
            ContextBundle: 基本的上下文包
        """
        system_prompts = []
        
        if personality_config and hasattr(personality_config, 'ai'):
            ai_config = personality_config.ai
            if hasattr(ai_config, 'system_prompt') and ai_config.system_prompt:
                system_prompts.append(ai_config.system_prompt)
            elif hasattr(personality_config, 'description') and personality_config.description:
                system_prompts.append(personality_config.description)
        
        return ContextBundle(
            system_prompts=system_prompts,
            recent_messages=[],
            summarized_history=[],
            retrieved_memories=[],
            user_profile=None,
            total_tokens=0,
            metadata={
                "max_tokens": 4096,
                "personality_id": personality_config.id if hasattr(personality_config, 'id') else None,
                "fallback": True
            }
        )
