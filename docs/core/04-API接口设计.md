# CozyChat API接口设计

> **版本**: v2.1 (阶段四优化版本)  
> **最后更新**: 2025-01-XX  
> **变更**: 性能优化、类型注解改进

---

## 📋 版本变更

### v2.1 (2025-01-XX) - 阶段四优化版本
- ✅ **性能优化**: 关键路径性能提升≥15%，数据库查询优化
- ✅ **类型注解改进**: 减少87.9%的type:ignore注释，提升类型安全性
- ✅ **查询优化**: 使用selectinload预加载关联数据，减少N+1查询

### v2.0 (2025-11-18)
- ✅ 新增`POST /v1/sessions/{id}/title` - 会话标题生成API
- ✅ 优化记忆系统API说明（异步写入）
- ✅ 更新Chat API文档（智能上下文）

### v1.0 (2025-11-06)
- 初始版本

---

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

#### 4.3.6 生成会话标题 ✨ v2.0新增

根据会话消息内容自动生成简洁的标题。当消息数达到一定阈值时，前端会自动调用此接口。

```http
POST /v1/sessions/{session_id}/title
Authorization: Bearer <token>
Content-Type: application/json

{
  "force": false,        # 可选：是否强制重新生成标题（默认false）
  "max_messages": 20     # 可选：用于生成标题的最大消息数（默认20）
}

# 响应
{
  "session_id": "session_789",
  "title": "讨论健康饮食建议",
  "generated_at": "2025-11-18T10:32:47Z",
  "used_message_count": 10
}

# 错误响应（消息数不足）
{
  "detail": "消息数不足，需要至少10条消息",
  "current_count": 5,
  "required_count": 10
}
```

**请求参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `force` | boolean | 否 | false | 是否强制重新生成标题 |
| `max_messages` | integer | 否 | 20 | 用于生成标题的最大消息数 |

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | string | 会话ID |
| `title` | string | 生成的标题 |
| `generated_at` | string(ISO8601) | 生成时间 |
| `used_message_count` | integer | 实际使用的消息数 |

**业务逻辑**：

1. **消息数检查**：
   - 会话消息数必须 ≥ `SESSION_TITLE_TRIGGER_LENGTH`（默认10）
   - 消息数不足时返回400错误

2. **标题去重**：
   - 当`force=false`时，检查`title_generated_at`字段
   - 如果已有生成的标题，直接返回，不重复生成
   - 当`force=true`时，强制重新生成

3. **消息选择**：
   - 选取最近的N条消息（N = min(消息总数, max_messages)）
   - 包含完整的对话上下文（user和assistant消息）

4. **标题生成**：
   - 使用配置的模型（默认`gpt-4o-mini`）
   - 温度参数：0.3（更稳定的输出）
   - 最大token数：100
   - 生成简洁、准确的中文标题（10-20字）

**调用时机**：

| 场景 | 触发时机 | 说明 |
|------|---------|------|
| **文本对话** | 消息数达到阈值时 | 前端在`EnhancedChatContainer`中检测消息数，满足条件时异步调用 |
| **语音对话** | 语音转写完成后 | 调用`/v1/chat/voice/save`后，前端检查消息数并触发 |
| **手动触发** | 用户点击"重新生成标题"按钮 | 设置`force=true`强制重新生成 |

**性能考虑**：

- ⚡ 异步执行：不阻塞主对话流程
- 💾 结果缓存：避免重复生成
- 🎯 精简上下文：仅使用最近20条消息，节省token
- ⏱️ 生成时间：通常<2秒

**配置参数**：

```python
# backend/.env 或 config/config.py
SESSION_TITLE_TRIGGER_LENGTH=10       # 触发阈值
SESSION_TITLE_MAX_MESSAGES=20        # 最大消息数
SESSION_TITLE_MODEL=gpt-4o-mini      # 使用的模型
SESSION_TITLE_TEMPERATURE=0.3        # 温度参数
SESSION_TITLE_MAX_TOKENS=100         # 最大token数
```

**前端集成示例**：

```typescript
// frontend/src/features/chat/components/EnhancedChatContainer.tsx
useEffect(() => {
  if (
    messages.length >= TITLE_TRIGGER_LENGTH &&
    !titleGenerated
  ) {
    // 异步生成标题
    sessionApi.generateTitle(sessionId, {
      force: false,
      maxMessages: 20
    }).then(() => {
      // 重新拉取会话列表，更新标题
      queryClient.refetchQueries(['sessions', userId]);
      setTitleGenerated(true);
    });
  }
}, [messages.length]);
```

### 4.4 记忆管理

> **v2.0优化**: 记忆系统全面升级，支持异步写入、混合存储和智能去重。

#### 4.4.1 搜索记忆

```http
POST /v1/memories/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "用户的饮食偏好",
  "session_id": "session_789",  # 可选，限制在某个会话
  "memory_type": "user",         # 可选: user/ai/all (v2.0: 支持混合检索)
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
  "total": 2,
  "source_collection": "mixed_memories"  # v2.0新增：显示数据来源
}
```

**v2.0优化说明**：

1. **混合检索**（Hybrid Three Collections）:
   - 当`memory_type`为`all`或未指定时，优先从`mixed_memories`集合检索
   - 单次查询获取所有相关记忆，性能提升~100ms
   - 返回结果自动标注记忆类型（user/assistant）

2. **异步写入**:
   - 对话过程中的记忆写入操作已异步化
   - 记忆立即推入Redis队列，不阻塞主流程
   - 后台Worker批量写入Qdrant，提升吞吐量
   - 主对话流程时延从400ms降低到<50ms

3. **智能去重**:
   - 后台Worker定期执行相似记忆去重
   - 基于内容相似度和语义相似度
   - 不影响实时对话性能

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

## 8. API总览表 (v2.0)

### 核心功能API

| 类别 | 端点 | 方法 | 说明 | v2.0变更 |
|------|------|------|------|---------|
| **认证** | `/v1/users/login` | POST | 用户登录 | - |
| | `/v1/users/register` | POST | 用户注册 | - |
| | `/v1/users/refresh` | POST | 刷新token | - |
| **对话** | `/v1/chat/completions` | POST | OpenAI兼容API | ✅ 支持智能上下文 |
| | `/v1/chat/stream` | POST | 流式对话 | ✅ 异步记忆写入 |
| | `/v1/chat/voice/save` | POST | 保存语音消息 | - |
| **会话** | `/v1/sessions` | GET | 列出会话 | - |
| | `/v1/sessions` | POST | 创建会话 | - |
| | `/v1/sessions/{id}` | GET | 获取会话详情 | - |
| | `/v1/sessions/{id}` | PUT | 更新会话 | - |
| | `/v1/sessions/{id}` | DELETE | 删除会话 | - |
| | `/v1/sessions/{id}/title` | POST | 生成标题 | ✨ 新增 |
| | `/v1/sessions/{id}/messages` | GET | 获取消息列表 | - |
| **记忆** | `/v1/memories/search` | POST | 搜索记忆 | ✅ 混合检索优化 |
| | `/v1/memories` | POST | 添加记忆 | ✅ 异步写入 |
| | `/v1/memories/{id}` | DELETE | 删除记忆 | - |
| **人格** | `/v1/personalities` | GET | 列出人格 | - |
| | `/v1/personalities/{id}` | GET | 获取人格详情 | - |
| | `/v1/personalities` | POST | 创建人格 | - |
| **工具** | `/v1/tools` | GET | 列出工具 | - |
| | `/v1/tools/execute` | POST | 执行工具 | - |
| **语音** | `/v1/audio/transcriptions` | POST | STT转写 | - |
| | `/v1/audio/speech` | POST | TTS合成 | - |
| | `/v1/audio/speech/stream` | POST | 流式TTS | - |
| **监控** | `/v1/health` | GET | 健康检查 | - |
| | `/v1/monitoring/stats` | GET | 系统统计 | - |

---

**文档版本**: v2.0  
**最后更新**: 2025-11-18  
**维护者**: CozyChat Team

