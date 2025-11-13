"""
人格模型

定义人格配置的数据结构
"""

# 标准库
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# 本地库
from app.utils.logger import logger


@dataclass
class PersonalityTraits:
    """人格特征"""
    friendliness: float = 0.7  # 友好度 0-1
    formality: float = 0.5    # 正式度 0-1
    humor: float = 0.3         # 幽默感 0-1
    empathy: float = 0.6       # 共情能力 0-1


@dataclass
class TokenBudget:
    """Token预算配置"""
    max_history_tokens: int = 4000
    max_memory_tokens: int = 1000
    max_tool_tokens: int = 500


@dataclass
class AIConfig:
    """AI引擎配置"""
    provider: str = "openai"  # openai / ollama / lmstudio
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = ""
    token_budget: TokenBudget = field(default_factory=TokenBudget)


@dataclass
class MemoryStrategy:
    """记忆策略配置"""
    enabled: bool = True
    importance_threshold: float = 0.5
    max_memories: int = 100
    ttl_days: int = 90


@dataclass
class MemoryRetrieval:
    """记忆检索配置"""
    max_results: int = 5
    similarity_threshold: float = 0.7
    timeout_seconds: float = 0.5
    cache_ttl_seconds: int = 300


@dataclass
class MemoryConfig:
    """记忆配置"""
    enabled: bool = True
    vector_db: str = "chromadb"  # chromadb / qdrant
    save_mode: str = "both"      # both / user_only / assistant_only
    strategy: Dict[str, MemoryStrategy] = field(default_factory=dict)
    retrieval: MemoryRetrieval = field(default_factory=MemoryRetrieval)


@dataclass
class ToolPermissions:
    """工具权限配置"""
    max_concurrent_calls: int = 3
    timeout_seconds: float = 30.0


@dataclass
class ToolConfig:
    """工具配置"""
    enabled: bool = True
    allowed_tools: List[str] = field(default_factory=list)
    mcp_servers: List[Dict[str, Any]] = field(default_factory=list)
    permissions: ToolPermissions = field(default_factory=ToolPermissions)


@dataclass
class VoiceConfig:
    """语音配置"""
    stt: Dict[str, Any] = field(default_factory=dict)
    tts: Dict[str, Any] = field(default_factory=dict)
    realtime: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserPreferences:
    """用户偏好配置"""
    default_language: str = "zh-CN"
    response_style: str = "detailed"  # brief / detailed / conversational
    auto_tts: bool = False
    show_reasoning: bool = False


@dataclass
class Personality:
    """人格配置模型"""
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    welcome_message: Optional[str] = None  # 新建会话时的欢迎词
    traits: PersonalityTraits = field(default_factory=PersonalityTraits)
    ai: AIConfig = field(default_factory=AIConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    user_preferences: UserPreferences = field(default_factory=UserPreferences)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Personality":
        """从配置字典创建Personality对象
        
        Args:
            config: 配置字典
            
        Returns:
            Personality: Personality对象
        """
        # 解析基本信息
        welcome_message = config.get("welcome_message")
        
        # 解析traits
        traits_data = config.get("traits", {})
        traits = PersonalityTraits(
            friendliness=traits_data.get("friendliness", 0.7),
            formality=traits_data.get("formality", 0.5),
            humor=traits_data.get("humor", 0.3),
            empathy=traits_data.get("empathy", 0.6)
        )
        
        # 解析AI配置
        ai_data = config.get("ai", {})
        token_budget_data = ai_data.get("token_budget", {})
        token_budget = TokenBudget(
            max_history_tokens=token_budget_data.get("max_history_tokens", 4000),
            max_memory_tokens=token_budget_data.get("max_memory_tokens", 1000),
            max_tool_tokens=token_budget_data.get("max_tool_tokens", 500)
        )
        ai = AIConfig(
            provider=ai_data.get("provider", "openai"),
            model=ai_data.get("model", "gpt-3.5-turbo"),
            temperature=ai_data.get("temperature", 0.7),
            max_tokens=ai_data.get("max_tokens", 4096),
            system_prompt=ai_data.get("system_prompt", ""),
            token_budget=token_budget
        )
        
        # 解析记忆配置
        memory_data = config.get("memory", {})
        strategy_data = memory_data.get("strategy", {})
        strategy = {}
        for key in ["user_memory", "ai_memory"]:
            if key in strategy_data:
                s_data = strategy_data[key]
                strategy[key] = MemoryStrategy(
                    enabled=s_data.get("enabled", True),
                    importance_threshold=s_data.get("importance_threshold", 0.5),
                    max_memories=s_data.get("max_memories", 100),
                    ttl_days=s_data.get("ttl_days", 90)
                )
        
        retrieval_data = memory_data.get("retrieval", {})
        retrieval = MemoryRetrieval(
            max_results=retrieval_data.get("max_results", 5),
            similarity_threshold=retrieval_data.get("similarity_threshold", 0.7),
            timeout_seconds=retrieval_data.get("timeout_seconds", 0.5),
            cache_ttl_seconds=retrieval_data.get("cache_ttl_seconds", 300)
        )
        memory = MemoryConfig(
            enabled=memory_data.get("enabled", True),
            vector_db=memory_data.get("vector_db", "chromadb"),
            save_mode=memory_data.get("save_mode", "both"),
            strategy=strategy,
            retrieval=retrieval
        )
        
        # 解析工具配置
        tools_data = config.get("tools", {})
        permissions_data = tools_data.get("permissions", {})
        permissions = ToolPermissions(
            max_concurrent_calls=permissions_data.get("max_concurrent_calls", 3),
            timeout_seconds=permissions_data.get("timeout_seconds", 30.0)
        )
        tools = ToolConfig(
            enabled=tools_data.get("enabled", True),
            allowed_tools=tools_data.get("allowed_tools", []),
            mcp_servers=tools_data.get("mcp_servers", []),
            permissions=permissions
        )
        
        # 解析语音配置
        voice_data = config.get("voice", {})
        voice = VoiceConfig(
            stt=voice_data.get("stt", {}),
            tts=voice_data.get("tts", {}),
            realtime=voice_data.get("realtime", {})
        )
        
        # 解析用户偏好
        prefs_data = config.get("user_preferences", {})
        user_preferences = UserPreferences(
            default_language=prefs_data.get("default_language", "zh-CN"),
            response_style=prefs_data.get("response_style", "detailed"),
            auto_tts=prefs_data.get("auto_tts", False),
            show_reasoning=prefs_data.get("show_reasoning", False)
        )
        
        return cls(
            id=config.get("id", ""),
            name=config.get("name", ""),
            version=config.get("version", "1.0.0"),
            description=config.get("description", ""),
            welcome_message=welcome_message,
            traits=traits,
            ai=ai,
            memory=memory,
            tools=tools,
            voice=voice,
            user_preferences=user_preferences,
            metadata=config.get("metadata", {})
        )
    
    def to_config(self) -> Dict[str, Any]:
        """转换为配置字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "welcome_message": self.welcome_message,
            "traits": {
                "friendliness": self.traits.friendliness,
                "formality": self.traits.formality,
                "humor": self.traits.humor,
                "empathy": self.traits.empathy
            },
            "ai": {
                "provider": self.ai.provider,
                "model": self.ai.model,
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens,
                "system_prompt": self.ai.system_prompt,
                "token_budget": {
                    "max_history_tokens": self.ai.token_budget.max_history_tokens,
                    "max_memory_tokens": self.ai.token_budget.max_memory_tokens,
                    "max_tool_tokens": self.ai.token_budget.max_tool_tokens
                }
            },
            "memory": {
                "enabled": self.memory.enabled,
                "vector_db": self.memory.vector_db,
                "save_mode": self.memory.save_mode,
                "strategy": {
                    k: {
                        "enabled": v.enabled,
                        "importance_threshold": v.importance_threshold,
                        "max_memories": v.max_memories,
                        "ttl_days": v.ttl_days
                    }
                    for k, v in self.memory.strategy.items()
                },
                "retrieval": {
                    "max_results": self.memory.retrieval.max_results,
                    "similarity_threshold": self.memory.retrieval.similarity_threshold,
                    "timeout_seconds": self.memory.retrieval.timeout_seconds,
                    "cache_ttl_seconds": self.memory.retrieval.cache_ttl_seconds
                }
            },
            "tools": {
                "enabled": self.tools.enabled,
                "allowed_tools": self.tools.allowed_tools,
                "mcp_servers": self.tools.mcp_servers,
                "permissions": {
                    "max_concurrent_calls": self.tools.permissions.max_concurrent_calls,
                    "timeout_seconds": self.tools.permissions.timeout_seconds
                }
            },
            "voice": {
                "stt": self.voice.stt,
                "tts": self.voice.tts,
                "realtime": self.voice.realtime
            },
            "user_preferences": {
                "default_language": self.user_preferences.default_language,
                "response_style": self.user_preferences.response_style,
                "auto_tts": self.user_preferences.auto_tts,
                "show_reasoning": self.user_preferences.show_reasoning
            },
            "metadata": self.metadata
        }
    
    def update(self, updates: Dict[str, Any]):
        """更新人格配置
        
        Args:
            updates: 更新字典
        """
        # 这里可以实现部分更新逻辑
        # 简化实现：重新创建对象
        updated_config = self.to_config()
        updated_config.update(updates)
        updated = Personality.from_config(updated_config)
        
        # 更新所有字段
        self.__dict__.update(updated.__dict__)

