"""
聊天相关的Pydantic schemas

定义Chat API的请求和响应数据模型
"""

# 标准库
from typing import Any, Dict, List, Literal, Optional

# 第三方库
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: Literal["system", "user", "assistant", "function", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionRequest(BaseModel):
    """聊天补全请求模型（OpenAI兼容）"""
    
    # ===== OpenAI标准字段 =====
    model: Optional[str] = Field(default=None, description="模型名称（可选，如果提供了personality_id，将使用personality配置的模型）")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="最大token数")
    stream: bool = Field(default=False, description="是否流式输出")
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="工具列表")
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Top P参数")
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    
    # ===== CozyChat扩展字段 =====
    engine_type: str = Field(default="openai", description="引擎类型（openai/ollama）")
    personality_id: Optional[str] = Field(default=None, description="人格ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    use_memory: bool = Field(default=False, description="是否使用记忆")
    memory_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="记忆选项: include_user_memory, include_ai_memory, memory_limit, similarity_threshold"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "你好"}
                ],
                "temperature": 0.7,
                "stream": False,
                "engine_type": "openai"
            }
        }
    }


class ChatCompletionChoice(BaseModel):
    """聊天补全选择"""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatCompletionUsage(BaseModel):
    """Token使用情况"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """聊天补全响应模型（OpenAI兼容）"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage
    
    # CozyChat扩展字段
    personality: Optional[Dict[str, str]] = None
    memories_used: Optional[List[Dict[str, Any]]] = None
    tools_called: Optional[List[str]] = None


class ChatCompletionStreamChunk(BaseModel):
    """流式聊天补全响应块"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


class EngineListResponse(BaseModel):
    """引擎列表响应"""
    engines: List[str]
    default_engine: str
    descriptions: Dict[str, str]


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "cozychat"
    
    # 扩展信息
    engine_type: str
    description: Optional[str] = None
    context_window: Optional[int] = None
    supports_tools: bool = False
    supports_vision: bool = False


class ModelListResponse(BaseModel):
    """模型列表响应（OpenAI兼容）"""
    object: str = "list"
    data: List[ModelInfo]

