# 提示词优化和 User Prompt 实现方案

## 📋 优化总结

### ✅ 已完成的优化

1. **简化 system_prompt**（从 ~400 字减少到 ~250 字）
   - 去除冗余描述
   - 使用积极指令替代否定式
   - 添加具体工具调用示例

2. **优化工具使用规则**
   - 每个工具都有明确的适用场景
   - 包含完整的调用示例（用户问题 → 工具调用 → 回答格式）
   - 使用积极指令："立即调用"而非"不要猜测"

3. **添加输出格式要求**
   - 明确回复结构（开头、主体、结尾）
   - 控制回答长度（50-400字）

4. **优化语音对话提示词**
   - 简化 realtime_instructions
   - 保持核心功能

---

## 🎯 User Prompt 实现方案

### 方案概述

根据用户偏好（`user_preferences.response_style`）动态构建用户消息，在用户消息前添加个性化指令。

### 实现步骤

#### 步骤1：修改 AIConfig 模型（可选）

如果需要支持模板引擎（如 Jinja2），可以在 `AIConfig` 中添加 `user_prompt_template` 字段：

```python
# backend/app/core/personality/models.py

@dataclass
class AIConfig:
    """AI引擎配置"""
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = ""
    user_prompt_template: Optional[str] = None  # 新增：用户提示词模板
    token_budget: TokenBudget = field(default_factory=TokenBudget)
```

#### 步骤2：在 Personality.from_config 中解析 user_prompt_template

```python
# backend/app/core/personality/models.py

# 在 from_config 方法中
ai = AIConfig(
    provider=ai_data.get("provider", "openai"),
    model=ai_data.get("model", "gpt-3.5-turbo"),
    temperature=ai_data.get("temperature", 0.7),
    max_tokens=ai_data.get("max_tokens", 4096),
    system_prompt=ai_data.get("system_prompt", ""),
    user_prompt_template=ai_data.get("user_prompt_template"),  # 新增
    token_budget=token_budget
)
```

#### 步骤3：创建用户消息构建函数

```python
# backend/app/api/v1/chat.py

def _build_user_message(
    user_message: str,
    personality_config: Optional["Personality"] = None,
    user_preferences: Optional[Dict[str, Any]] = None
) -> str:
    """根据用户偏好构建用户消息
    
    Args:
        user_message: 用户原始消息
        personality_config: 人格配置（可选，用于获取模板）
        user_preferences: 用户偏好设置
        
    Returns:
        str: 完整的用户消息（包含个性化指令）
    """
    if not user_preferences:
        return user_message
    
    instructions = []
    
    # 根据 response_style 添加指令
    response_style = user_preferences.get('response_style', 'detailed')
    if response_style == 'brief':
        instructions.append("请用简洁的方式回答，控制在100字以内。")
    elif response_style == 'detailed':
        instructions.append("请提供详细的回答，包含背景、原因和建议。")
    elif response_style == 'conversational':
        instructions.append("请用对话的方式回答，就像朋友之间的聊天。")
    
    # 根据 show_reasoning 添加指令
    if user_preferences.get('show_reasoning', False):
        instructions.append("请在回答中展示你的推理过程。")
    
    # 组合指令和原始消息
    if instructions:
        return f"[指令：{' '.join(instructions)}]\n\n{user_message}"
    
    return user_message
```

#### 步骤4：在消息构建时调用

```python
# backend/app/api/v1/chat.py

def _convert_context_bundle_to_messages(
    context_bundle: "ContextBundle",
    current_message_content: str,
    personality_config: Optional["Personality"] = None,  # 新增参数
    user_preferences: Optional[Dict[str, Any]] = None  # 新增参数
) -> list[EngineChatMessage]:
    """将ContextBundle转换为LLM消息列表"""
    messages = []
    
    # ... 前面的代码保持不变 ...
    
    # 6. 当前用户消息（使用个性化构建）
    user_message = _build_user_message(
        current_message_content,
        personality_config=personality_config,
        user_preferences=user_preferences
    )
    
    messages.append(EngineChatMessage(
        role="user",
        content=user_message
    ))
    
    return messages
```

#### 步骤5：在聊天接口中传递 user_preferences

```python
# backend/app/api/v1/chat.py

@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: Request,
    data: ChatCompletionRequest,
    ...
):
    # ... 现有代码 ...
    
    # 获取用户偏好（从用户设置或会话中）
    user_preferences = None
    if hasattr(user, 'preferences'):
        user_preferences = user.preferences
    elif hasattr(personality_config, 'user_preferences'):
        # 从人格配置中获取默认偏好
        user_preferences = personality_config.user_preferences.__dict__ if hasattr(personality_config.user_preferences, '__dict__') else None
    
    # 构建消息时传递偏好
    messages = _convert_context_bundle_to_messages(
        context_bundle=context_bundle,
        current_message_content=data.messages[-1].content,
        personality_config=personality_config,
        user_preferences=user_preferences
    )
    
    # ... 后续代码 ...
```

---

## 📝 在 YAML 配置中添加 user_prompt_template（可选）

如果实现了模板引擎支持，可以在 `health_assistant.yaml` 中添加：

```yaml
  ai:
    provider: "openai"
    model: "gpt-4.1"
    temperature: 0.7
    max_tokens: 8192
    system_prompt: |
      # ... 系统提示词 ...
    
    # 可选：用户提示词模板（如果支持模板引擎）
    user_prompt_template: |
      {% if user_preferences.response_style == 'brief' %}
      请用简洁的方式回答，控制在100字以内。
      
      {% elif user_preferences.response_style == 'detailed' %}
      请提供详细的回答，包含背景、原因和建议。
      
      {% elif user_preferences.response_style == 'conversational' %}
      请用对话的方式回答，就像朋友之间的聊天。
      
      {% endif %}
      {% if user_preferences.show_reasoning %}
      请在回答中展示你的推理过程。
      
      {% endif %}
      {{ user_message }}
```

---

## 🧪 测试验证

### 1. 工具调用测试

测试以下场景，验证工具是否正常调用：

```python
# 测试用例
test_cases = [
    ("现在几点了？", "time"),  # 应该调用 time 工具
    ("帮我算一下125的5次方", "calculator"),  # 应该调用 calculator 工具
    ("北京今天天气怎么样？", "amap_weather"),  # 应该调用 amap_weather 工具
]
```

### 2. 回答质量测试

测试不同 `response_style` 的效果：

```python
# 简洁模式
user_preferences = {"response_style": "brief"}
# 预期：回答控制在100字以内

# 详细模式
user_preferences = {"response_style": "detailed"}
# 预期：回答包含背景、原因、建议

# 对话模式
user_preferences = {"response_style": "conversational"}
# 预期：回答自然、口语化
```

---

## 📊 优化效果对比

### 提示词长度

| 项目 | 优化前 | 优化后 | 减少 |
|------|--------|--------|------|
| system_prompt | ~400字 | ~250字 | 37.5% |
| realtime_instructions | ~80字 | ~50字 | 37.5% |

### 工具调用规则

| 项目 | 优化前 | 优化后 |
|------|--------|--------|
| 指令类型 | 否定式（"不要"） | 积极指令（"立即调用"） |
| 示例 | 无 | 每个工具都有完整示例 |
| 参数说明 | 无 | 明确参数格式 |

### 预期效果

- ✅ 工具调用准确率提升 **20-30%**
- ✅ 回答格式更统一
- ✅ 回答长度更合适（通过 user prompt 控制）
- ✅ 个性化体验更好（根据用户偏好调整）

---

## 🚀 实施优先级

### 🔴 高优先级（已完成）

1. ✅ 优化 system_prompt（简洁化、积极指令、具体示例）
2. ✅ 优化 realtime_instructions
3. ✅ 添加输出格式要求

### 🟡 中优先级（建议实施）

4. 实现 user prompt 功能（根据用户偏好调整回答）
5. 添加工具调用测试用例
6. 验证回答质量改进

### 🟢 低优先级（可选）

7. 支持模板引擎（Jinja2）实现更灵活的 user prompt
8. 根据用户历史对话自动学习偏好
9. A/B 测试不同提示词版本

---

## 📚 参考文档

- [提示词优化分析报告](./59-提示词优化分析报告.md)
- [User Prompt 使用指南](./60-User-Prompt使用指南.md)
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)

---

**文档版本**: 1.0  
**创建日期**: 2025-01-XX  
**最后更新**: 2025-01-XX

