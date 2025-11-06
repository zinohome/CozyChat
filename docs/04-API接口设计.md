# CozyChat API接口设计

## 1. API设计原则

### 1.1 RESTful规范
- 使用标准HTTP方法（GET/POST/PUT/DELETE）
- 资源导向的URL设计
- 统一的响应格式
- 合理的HTTP状态码

### 1.2 OpenAI兼容性
- 完全兼容OpenAI Chat Completions API
- 扩展参数保持向后兼容
- 支持标准的function calling格式

### 1.3 版本控制
- API版本前缀：`/v1/`, `/v2/`
- 保持旧版本API稳定性
- 提前通知breaking changes

## 2. 认证和授权

### 2.1 JWT认证

```http
POST /v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

# 响应
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "username": "user@example.com",
    "role": "user"
  }
}
```

### 2.2 Token刷新

```http
POST /v1/auth/refresh
Authorization: Bearer <refresh_token>

# 响应
{
  "access_token": "eyJhbGci...",
  "expires_in": 3600
}
```

### 2.3 API Key认证（OpenAI兼容）

```http
POST /v1/chat/completions
Authorization: Bearer <api_key>
Content-Type: application/json

{...}
```

## 3. OpenAI兼容接口

### 3.1 Chat Completions（核心接口）

#### 3.1.1 非流式请求

```http
POST /v1/chat/completions
Authorization: Bearer <token>
Content-Type: application/json

{
  // ===== OpenAI标准参数 =====
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "你是一个有帮助的助手"
    },
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "web_search",
        "description": "搜索网络",
        "parameters": {...}
      }
    }
  ],
  
  // ===== CozyChat扩展参数 =====
  "personality_id": "health_assistant",  // 人格ID
  "user_id": "user_123",                 // 用户ID（可选，从token中提取）
  "session_id": "session_456",           // 会话ID
  "use_memory": true,                    // 是否使用记忆
  "memory_options": {                    // 记忆选项
    "include_user_memory": true,
    "include_ai_memory": true,
    "memory_limit": 5
  }
}

# 响应（OpenAI标准格式）
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是小研，很高兴为你服务。"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 15,
    "total_tokens": 35
  },
  
  // ===== CozyChat扩展字段 =====
  "personality": {
    "id": "health_assistant",
    "name": "健康助手小研"
  },
  "memories_used": [
    {
      "type": "user",
      "content": "用户偏好清淡饮食",
      "similarity": 0.85
    }
  ],
  "tools_called": []
}
```

#### 3.1.2 流式请求（SSE）

```http
POST /v1/chat/completions
Authorization: Bearer <token>
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [...],
  "stream": true,
  "personality_id": "health_assistant"
}

# SSE响应流
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"你"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"好"},"finish_reason":null}]}

...

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### 3.2 Models API

```http
# 列出所有可用模型
GET /v1/models
Authorization: Bearer <token>

# 响应
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai",
      "provider": "openai",
      "capabilities": {
        "function_calling": true,
        "streaming": true
      }
    },
    {
      "id": "llama2:13b",
      "object": "model",
      "created": 1677610602,
      "owned_by": "meta",
      "provider": "ollama",
      "capabilities": {
        "function_calling": false,
        "streaming": true
      }
    }
  ]
}

# 获取单个模型详情
GET /v1/models/{model_id}
Authorization: Bearer <token>

# 响应
{
  "id": "gpt-4",
  "object": "model",
  "created": 1677610602,
  "owned_by": "openai",
  "provider": "openai",
  "capabilities": {...},
  "pricing": {
    "prompt": 0.03,
    "completion": 0.06,
    "currency": "USD",
    "unit": "1K tokens"
  }
}
```

### 3.3 Audio API

#### 3.3.1 语音转文本（STT）

```http
POST /v1/audio/transcriptions
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <audio_file>
model: whisper-1
language: zh
personality_id: health_assistant  # 扩展参数

# 响应
{
  "text": "你好，我想咨询一下健康问题"
}
```

#### 3.3.2 文本转语音（TTS）

```http
POST /v1/audio/speech
Authorization: Bearer <token>
Content-Type: application/json

{
  "model": "tts-1",
  "input": "你好，我是小研",
  "voice": "shimmer",
  "speed": 1.0,
  "personality_id": "health_assistant"  # 扩展参数，自动选择人格配置的语音
}

# 响应: audio/mpeg 二进制流
<binary audio data>
```

## 4. CozyChat扩展接口

### 4.1 人格管理

#### 4.1.1 列出所有人格

```http
GET /v1/personalities
Authorization: Bearer <token>

# 响应
{
  "personalities": [
    {
      "id": "health_assistant",
      "name": "健康助手小研",
      "description": "专业的健康咨询助手",
      "icon": "🏥",
      "tags": ["health", "medical"],
      "is_default": true,
      "created_at": "2025-11-06T10:00:00Z"
    },
    {
      "id": "professional",
      "name": "专业助手",
      "description": "正式的专业助手",
      "icon": "💼",
      "tags": ["business", "formal"],
      "is_default": false,
      "created_at": "2025-11-06T10:00:00Z"
    }
  ],
  "total": 2
}
```

#### 4.1.2 获取人格详情

```http
GET /v1/personalities/{personality_id}
Authorization: Bearer <token>

# 响应
{
  "id": "health_assistant",
  "name": "健康助手小研",
  "description": "专业的健康咨询助手",
  "config": {
    "ai": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.7,
      "system_prompt": "..."
    },
    "memory": {...},
    "tools": {...},
    "voice": {...}
  },
  "metadata": {...}
}
```

#### 4.1.3 创建自定义人格

```http
POST /v1/personalities
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "我的助手",
  "description": "个性化定制的助手",
  "config": {
    "ai": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.8,
      "system_prompt": "你是一个友好的助手..."
    },
    "memory": {
      "enabled": true,
      "save_mode": "both"
    },
    "tools": {
      "enabled": true,
      "allowed_tools": ["web_search", "calculator"]
    },
    "voice": {
      "stt": {"provider": "openai"},
      "tts": {"provider": "openai", "voice": "nova"}
    }
  }
}

# 响应
{
  "id": "custom_123",
  "name": "我的助手",
  "created_at": "2025-11-06T12:00:00Z",
  "message": "人格创建成功"
}
```

#### 4.1.4 更新人格配置

```http
PUT /v1/personalities/{personality_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "更新后的名称",
  "config": {
    "ai": {
      "temperature": 0.9
    }
  }
}

# 响应
{
  "id": "custom_123",
  "message": "人格更新成功",
  "updated_at": "2025-11-06T13:00:00Z"
}
```

### 4.2 用户管理

#### 4.2.1 用户注册

```http
POST /v1/users/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "invite_code": "ABC123"  # 可选，如果开启邀请制
}

# 响应
{
  "user_id": "user_456",
  "username": "newuser",
  "email": "user@example.com",
  "created_at": "2025-11-06T14:00:00Z",
  "message": "注册成功"
}
```

#### 4.2.2 获取用户信息

```http
GET /v1/users/me
Authorization: Bearer <token>

# 响应
{
  "id": "user_123",
  "username": "user",
  "email": "user@example.com",
  "role": "user",
  "profile": {
    "avatar": "https://...",
    "display_name": "张三",
    "bio": "热爱AI的开发者"
  },
  "preferences": {
    "default_personality": "health_assistant",
    "language": "zh-CN",
    "theme": "light"
  },
  "stats": {
    "total_sessions": 42,
    "total_messages": 1337,
    "total_memories": 89
  },
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### 4.2.3 更新用户偏好

```http
PUT /v1/users/me/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "default_personality": "professional",
  "language": "en-US",
  "theme": "dark",
  "auto_tts": true
}

# 响应
{
  "message": "偏好更新成功",
  "preferences": {...}
}
```

#### 4.2.4 用户画像

```http
GET /v1/users/me/profile
Authorization: Bearer <token>

# 响应
{
  "user_id": "user_123",
  "profile": {
    "interests": ["健康", "科技", "阅读"],
    "habits": {
      "most_active_time": "evening",
      "avg_session_duration": 15.5,
      "favorite_topics": ["健康咨询", "营养建议"]
    },
    "personality_insights": {
      "communication_style": "友好且详细",
      "question_types": ["health", "nutrition", "exercise"]
    }
  },
  "generated_at": "2025-11-06T15:00:00Z"
}
```

### 4.3 会话管理

#### 4.3.1 创建会话

```http
POST /v1/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "personality_id": "health_assistant",
  "title": "健康咨询会话"  # 可选
}

# 响应
{
  "session_id": "session_789",
  "personality_id": "health_assistant",
  "title": "健康咨询会话",
  "created_at": "2025-11-06T16:00:00Z"
}
```

#### 4.3.2 列出用户会话

```http
GET /v1/sessions
Authorization: Bearer <token>

# 查询参数
?page=1&page_size=20&personality_id=health_assistant&sort=created_at&order=desc

# 响应
{
  "sessions": [
    {
      "session_id": "session_789",
      "personality_id": "health_assistant",
      "personality_name": "健康助手小研",
      "title": "健康咨询会话",
      "message_count": 42,
      "last_message_at": "2025-11-06T18:00:00Z",
      "created_at": "2025-11-06T16:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

#### 4.3.3 获取会话详情

```http
GET /v1/sessions/{session_id}
Authorization: Bearer <token>

# 响应
{
  "session_id": "session_789",
  "personality_id": "health_assistant",
  "title": "健康咨询会话",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "你好",
      "created_at": "2025-11-06T16:05:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "你好！我是小研...",
      "created_at": "2025-11-06T16:05:02Z",
      "metadata": {
        "model": "gpt-4",
        "tokens_used": 35,
        "memories_used": 2,
        "tools_called": []
      }
    }
  ],
  "total_messages": 2,
  "created_at": "2025-11-06T16:00:00Z"
}
```

#### 4.3.4 更新会话

```http
PUT /v1/sessions/{session_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "更新后的标题"
}

# 响应
{
  "session_id": "session_789",
  "title": "更新后的标题",
  "updated_at": "2025-11-06T17:00:00Z"
}
```

#### 4.3.5 删除会话

```http
DELETE /v1/sessions/{session_id}
Authorization: Bearer <token>

# 响应
{
  "message": "会话已删除",
  "session_id": "session_789"
}
```

### 4.4 记忆管理

#### 4.4.1 搜索记忆

```http
POST /v1/memories/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "用户的饮食偏好",
  "session_id": "session_789",  # 可选，限制在某个会话
  "memory_type": "user",         # 可选: user/ai/all
  "limit": 10
}

# 响应
{
  "memories": [
    {
      "id": "mem_001",
      "type": "user",
      "content": "用户偏好清淡饮食，少油少盐",
      "similarity": 0.92,
      "importance": 0.8,
      "session_id": "session_789",
      "created_at": "2025-11-05T10:00:00Z"
    },
    {
      "id": "mem_002",
      "type": "ai",
      "content": "已为用户推荐低钠饮食方案",
      "similarity": 0.85,
      "importance": 0.7,
      "session_id": "session_789",
      "created_at": "2025-11-05T10:05:00Z"
    }
  ],
  "total": 2
}
```

#### 4.4.2 手动添加记忆

```http
POST /v1/memories
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "用户对花生过敏",
  "memory_type": "user",
  "importance": 0.9,
  "metadata": {
    "category": "health",
    "tags": ["allergy", "food"]
  }
}

# 响应
{
  "memory_id": "mem_003",
  "message": "记忆已保存"
}
```

#### 4.4.3 删除记忆

```http
DELETE /v1/memories/{memory_id}
Authorization: Bearer <token>

# 响应
{
  "message": "记忆已删除",
  "memory_id": "mem_003"
}
```

#### 4.4.4 清空会话记忆

```http
DELETE /v1/memories/sessions/{session_id}
Authorization: Bearer <token>

# 响应
{
  "message": "会话记忆已清空",
  "deleted_count": 15
}
```

### 4.5 工具管理

#### 4.5.1 列出所有可用工具

```http
GET /v1/tools
Authorization: Bearer <token>

# 查询参数
?type=builtin  # builtin / mcp / all

# 响应
{
  "tools": [
    {
      "name": "web_search",
      "type": "builtin",
      "description": "搜索互联网获取最新信息",
      "parameters": {...},
      "enabled": true
    },
    {
      "name": "health_mcp__search_medicine",
      "type": "mcp",
      "description": "搜索药品信息",
      "server": "health_mcp",
      "parameters": {...},
      "enabled": true
    }
  ],
  "total": 8
}
```

#### 4.5.2 执行单个工具

```http
POST /v1/tools/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "tool_name": "web_search",
  "parameters": {
    "query": "2025年AI发展趋势",
    "max_results": 3
  }
}

# 响应
{
  "tool_name": "web_search",
  "result": "1. AI多模态技术突破...\n2. 大模型持续进化...",
  "execution_time": 1.2,
  "success": true
}
```

### 4.6 性能监控

#### 4.6.1 获取系统统计

```http
GET /v1/monitoring/stats
Authorization: Bearer <admin_token>

# 响应
{
  "system": {
    "uptime": 86400,
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 35.6
  },
  "api": {
    "total_requests": 15234,
    "avg_response_time": 245,
    "error_rate": 0.02
  },
  "database": {
    "connections": 12,
    "query_count": 45678,
    "cache_hit_rate": 0.85
  },
  "ai_engines": [
    {
      "provider": "openai",
      "status": "healthy",
      "requests": 1234,
      "avg_latency": 1200
    }
  ]
}
```

#### 4.6.2 获取用户统计

```http
GET /v1/monitoring/users/me/stats
Authorization: Bearer <token>

# 响应
{
  "user_id": "user_123",
  "period": "last_30_days",
  "stats": {
    "total_messages": 256,
    "total_sessions": 15,
    "avg_messages_per_session": 17,
    "total_tokens_used": 45678,
    "favorite_personality": "health_assistant",
    "most_used_tools": [
      {"name": "web_search", "count": 12},
      {"name": "calculator", "count": 5}
    ],
    "active_days": 18,
    "total_voice_minutes": 45.2
  }
}
```

## 5. WebSocket接口

### 5.1 连接建立

```javascript
// 客户端连接
const ws = new WebSocket('wss://api.cozychat.ai/v1/ws/chat?token=<jwt_token>');

// 连接成功
ws.onopen = () => {
  console.log('WebSocket connected');
};

// 接收消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### 5.2 实时语音对话

```javascript
// 开始实时语音对话
ws.send(JSON.stringify({
  type: 'start_realtime',
  personality_id: 'health_assistant',
  session_id: 'session_789',
  config: {
    voice: 'shimmer',
    language: 'zh-CN'
  }
}));

// 服务器响应
{
  "type": "realtime_started",
  "session_id": "realtime_session_123",
  "status": "ready"
}

// 发送音频数据
ws.send(JSON.stringify({
  type: 'audio_chunk',
  audio_data: '<base64_audio>',
  timestamp: 1699000000
}));

// 接收AI音频响应
{
  "type": "audio_response",
  "audio_data": "<base64_audio>",
  "transcript": "我理解你的意思了...",
  "timestamp": 1699000001
}

// 停止实时对话
ws.send(JSON.stringify({
  type: 'stop_realtime'
}));
```

## 6. 错误处理

### 6.1 统一错误响应格式

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "参数 'personality_id' 无效",
    "details": {
      "parameter": "personality_id",
      "value": "invalid_id",
      "expected": "valid personality ID"
    },
    "request_id": "req_123456",
    "timestamp": "2025-11-06T12:00:00Z"
  }
}
```

### 6.2 常见错误码

| 错误码 | HTTP状态码 | 说明 |
|-------|-----------|------|
| `authentication_failed` | 401 | 认证失败 |
| `permission_denied` | 403 | 权限不足 |
| `resource_not_found` | 404 | 资源不存在 |
| `invalid_parameter` | 400 | 参数无效 |
| `rate_limit_exceeded` | 429 | 超过速率限制 |
| `internal_error` | 500 | 服务器内部错误 |
| `service_unavailable` | 503 | 服务不可用 |
| `model_unavailable` | 503 | AI模型不可用 |

## 7. 速率限制

### 7.1 限制规则

```yaml
免费用户:
  - 每分钟: 10次请求
  - 每小时: 100次请求
  - 每天: 500次请求

付费用户:
  - 每分钟: 60次请求
  - 每小时: 1000次请求
  - 每天: 无限制

企业用户:
  - 无限制
```

### 7.2 限制响应头

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699000000
```

---

**文档版本**: v1.0  
**最后更新**: 2025-11-06

