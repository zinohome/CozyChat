# User Prompt 使用指南

## 📋 目录

1. [System Prompt vs User Prompt](#system-prompt-vs-user-prompt)
2. [User Prompt 的作用和影响](#user-prompt-的作用和影响)
3. [在 CozyChat 中的实现方案](#在-cozychat-中的实现方案)
4. [使用场景和示例](#使用场景和示例)
5. [最佳实践](#最佳实践)

---

## System Prompt vs User Prompt

### 概念区别

在 OpenAI API 中，消息有三种角色：

| 角色 | 用途 | 特点 | 示例 |
|------|------|------|------|
| **system** | 定义 AI 的角色、能力和行为规则 | - 在整个对话中持续有效<br>- 定义 AI 的"人格"<br>- 通常放在消息列表开头 | "你是一个专业的健康咨询助手" |
| **user** | 用户的具体问题和指令 | - 每次对话都会变化<br>- 包含用户的实际需求<br>- 可以包含指令和问题 | "请用简洁的方式解释高血压" |
| **assistant** | AI 的回复 | - AI 生成的内容<br>- 基于 system 和 user 消息 | "高血压是指..." |

### 关键区别

```
System Prompt (系统提示词):
├── 定义"你是谁"（角色）
├── 定义"你能做什么"（能力）
├── 定义"你如何回答"（风格）
└── 在整个对话中持续有效

User Prompt (用户提示词):
├── 用户的具体问题
├── 用户的指令（如"用简洁方式"）
├── 用户的偏好（如"用列表形式"）
└── 每次对话都会变化
```

---

## User Prompt 的作用和影响

### 1. 对模型回答的影响

#### 影响程度对比

```
System Prompt: 影响整个对话的"基调"和"规则"
    ↓
User Prompt: 影响单次回答的"内容"和"格式"
```

#### 具体影响

| 方面 | System Prompt 影响 | User Prompt 影响 |
|------|-------------------|------------------|
| **回答风格** | 整体风格（友好、专业等） | 单次回答的格式（列表、段落等） |
| **回答内容** | 回答的范围和边界 | 回答的具体主题和深度 |
| **回答长度** | 默认长度偏好 | 单次回答的长度要求 |
| **回答格式** | 默认格式偏好 | 单次回答的格式要求 |
| **工具使用** | 工具使用规则 | 是否在此次对话中使用工具 |

### 2. 优先级关系

```
优先级（从高到低）:
1. User Prompt 中的明确指令（如"用列表"）
2. System Prompt 中的默认规则（如"详细回答"）
3. 模型的默认行为
```

**示例**:
```
System Prompt: "你是一个健康助手，通常提供详细的回答"

User Prompt: "请用3个要点简要说明高血压"

结果: AI 会优先遵循 User Prompt 的"简要"要求，而不是 System Prompt 的"详细"偏好
```

---

## 在 CozyChat 中的实现方案

### 当前实现分析

**当前状态**: CozyChat 目前**没有专门的 user_prompt 配置**，只有：
- ✅ `system_prompt`: 在 `personality.yaml` 中定义
- ✅ `user_preferences`: 用户偏好设置（但未直接用于提示词）
- ✅ 用户消息：直接作为 user role 发送

### 实现方案 1: 在 Personality 配置中添加 user_prompt

#### 方案设计

```yaml
# backend/config/personalities/health_assistant.yaml
personality:
  ai:
    system_prompt: |
      你是一个专业的健康咨询助手...
    
    # 新增：用户提示词模板
    user_prompt_template: |
      # 用户偏好指令
      {% if user_preferences.response_style == "brief" %}
      请用简洁的方式回答，控制在100字以内。
      {% elif user_preferences.response_style == "detailed" %}
      请提供详细的回答，包含背景、原因和建议。
      {% endif %}
      
      {% if user_preferences.show_reasoning %}
      请在回答中展示你的推理过程。
      {% endif %}
      
      # 用户的具体问题
      {{ user_message }}
```

#### 代码实现

```python
# backend/app/core/context/builder.py

def _build_user_prompt(
    self,
    user_message: str,
    user_preferences: Optional[Dict[str, Any]] = None
) -> str:
    """构建用户提示词
    
    Args:
        user_message: 用户原始消息
        user_preferences: 用户偏好设置
        
    Returns:
        str: 完整的用户提示词
    """
    user_prompt_parts = []
    
    # 1. 从 personality 配置获取 user_prompt_template（如果有）
    if hasattr(self.personality_config, 'ai') and \
       hasattr(self.personality_config.ai, 'user_prompt_template'):
        template = self.personality_config.ai.user_prompt_template
        # 使用模板引擎渲染（如 Jinja2）
        user_prompt_parts.append(render_template(template, {
            'user_message': user_message,
            'user_preferences': user_preferences or {}
        }))
    else:
        # 2. 如果没有模板，根据用户偏好动态构建
        if user_preferences:
            if user_preferences.get('response_style') == 'brief':
                user_prompt_parts.append("请用简洁的方式回答，控制在100字以内。")
            elif user_preferences.get('response_style') == 'detailed':
                user_prompt_parts.append("请提供详细的回答，包含背景、原因和建议。")
            
            if user_preferences.get('show_reasoning'):
                user_prompt_parts.append("请在回答中展示你的推理过程。")
        
        # 3. 添加用户原始消息
        user_prompt_parts.append(user_message)
    
    return "\n\n".join(user_prompt_parts)
```

### 实现方案 2: 在消息构建时动态添加用户指令

#### 方案设计

在 `_convert_context_bundle_to_messages` 函数中，在用户消息前添加指令：

```python
# backend/app/api/v1/chat.py

def _convert_context_bundle_to_messages(
    context_bundle,
    current_message_content: str,
    user_preferences: Optional[Dict[str, Any]] = None
) -> list[EngineChatMessage]:
    """将ContextBundle转换为LLM消息列表"""
    messages = []
    
    # ... system messages ...
    
    # 构建用户消息（包含指令）
    user_prompt = _build_user_message(
        current_message_content,
        user_preferences
    )
    
    messages.append(EngineChatMessage(
        role="user",
        content=user_prompt
    ))
    
    return messages

def _build_user_message(
    content: str,
    preferences: Optional[Dict[str, Any]] = None
) -> str:
    """构建用户消息，包含指令和原始内容"""
    parts = []
    
    # 添加用户偏好指令
    if preferences:
        if preferences.get('response_style') == 'brief':
            parts.append("[指令：请用简洁的方式回答，控制在100字以内]")
        elif preferences.get('response_style') == 'detailed':
            parts.append("[指令：请提供详细的回答，包含背景、原因和建议]")
        
        if preferences.get('show_reasoning'):
            parts.append("[指令：请在回答中展示你的推理过程]")
    
    # 添加用户原始消息
    parts.append(content)
    
    return "\n\n".join(parts) if len(parts) > 1 else content
```

### 实现方案 3: 支持用户消息中的指令解析

#### 方案设计

允许用户在消息中使用特殊指令：

```python
# 用户消息示例:
# "@brief 请解释高血压"
# "@detailed 请解释高血压"
# "@list 请列出高血压的预防方法"

def _parse_user_message_with_instructions(content: str) -> tuple[str, Dict[str, Any]]:
    """解析用户消息中的指令
    
    Returns:
        tuple: (清理后的消息内容, 指令字典)
    """
    instructions = {}
    
    # 解析 @brief, @detailed, @list 等指令
    if content.startswith("@brief"):
        instructions['response_style'] = 'brief'
        content = content.replace("@brief", "").strip()
    elif content.startswith("@detailed"):
        instructions['response_style'] = 'detailed'
        content = content.replace("@detailed", "").strip()
    elif content.startswith("@list"):
        instructions['output_format'] = 'list'
        content = content.replace("@list", "").strip()
    
    return content, instructions
```

---

## 使用场景和示例

### 场景 1: 根据用户偏好调整回答风格

**当前实现**:
```python
# 用户偏好: response_style = "brief"
# 用户消息: "什么是高血压？"
# 结果: AI 可能仍然给出详细回答（因为 system_prompt 说"详细回答"）
```

**使用 User Prompt 后**:
```python
# System Prompt: "你是一个健康助手，通常提供详细的回答"
# User Prompt: "[指令：请用简洁的方式回答，控制在100字以内]\n\n什么是高血压？"
# 结果: AI 会优先遵循 User Prompt 的"简洁"指令
```

### 场景 2: 动态调整回答格式

**示例**:
```python
# 用户消息: "请列出高血压的预防方法"
# User Prompt 构建:
"""
[指令：请用列表形式回答，每个要点一行]

请列出高血压的预防方法
"""

# AI 回答:
"""
1. 控制盐分摄入
2. 保持适量运动
3. 戒烟限酒
4. 控制体重
5. 定期监测血压
"""
```

### 场景 3: 临时覆盖系统默认行为

**示例**:
```python
# System Prompt: "你是一个健康助手，通常提供详细的回答，包含医学背景"
# User Prompt: "[指令：请用通俗易懂的语言，避免医学术语]\n\n什么是高血压？"

# AI 回答: 会用通俗语言，而不是医学术语
```

---

## 最佳实践

### 1. User Prompt 设计原则

#### ✅ 应该做的

1. **明确具体**: 指令要清晰明确
   ```
   ✅ "[指令：请用3个要点简要说明]"
   ❌ "[指令：简单点]"
   ```

2. **适度使用**: 不要过度使用指令，让对话自然
   ```
   ✅ 只在需要时添加指令
   ❌ 每条消息都加指令
   ```

3. **与 System Prompt 配合**: User Prompt 应该补充而非替代 System Prompt
   ```
   System Prompt: 定义整体风格
   User Prompt: 调整单次回答
   ```

#### ❌ 不应该做的

1. **不要在 User Prompt 中重复 System Prompt 的内容**
   ```
   ❌ System: "你是健康助手"
      User: "[指令：你是健康助手，请回答...]"
   ```

2. **不要在 User Prompt 中定义角色**
   ```
   ❌ User: "[指令：你现在是一个医生，请...]"
   ✅ User: "[指令：请用专业术语回答]"
   ```

3. **不要使用冲突的指令**
   ```
   ❌ User: "[指令：请简洁回答，控制在50字以内，但要详细说明背景]"
   ```

### 2. 优先级管理

```
优先级（从高到低）:
1. User Prompt 中的明确指令（最高优先级）
2. User Preferences（用户偏好）
3. System Prompt 中的默认规则
4. 模型的默认行为
```

### 3. 实现建议

#### 推荐方案: 方案 2（动态添加用户指令）

**优点**:
- ✅ 不需要修改配置文件
- ✅ 灵活，可以根据用户偏好动态调整
- ✅ 不影响现有代码结构

**实现步骤**:
1. 在 `_convert_context_bundle_to_messages` 中添加用户偏好处理
2. 根据 `user_preferences` 动态构建用户消息
3. 保持向后兼容（如果没有偏好，直接使用原始消息）

#### 代码示例

```python
# backend/app/api/v1/chat.py

def _build_user_message_with_preferences(
    content: str,
    user_preferences: Optional[Dict[str, Any]] = None
) -> str:
    """根据用户偏好构建用户消息"""
    if not user_preferences:
        return content
    
    instructions = []
    
    # 根据 response_style 添加指令
    response_style = user_preferences.get('response_style')
    if response_style == 'brief':
        instructions.append("请用简洁的方式回答，控制在100字以内。")
    elif response_style == 'detailed':
        instructions.append("请提供详细的回答，包含背景、原因和建议。")
    elif response_style == 'conversational':
        instructions.append("请用对话的方式回答，就像朋友之间的聊天。")
    
    # 根据 show_reasoning 添加指令
    if user_preferences.get('show_reasoning'):
        instructions.append("请在回答中展示你的推理过程。")
    
    # 组合指令和原始消息
    if instructions:
        return f"[指令：{' '.join(instructions)}]\n\n{content}"
    
    return content
```

---

## 总结

### System Prompt vs User Prompt

| 特性 | System Prompt | User Prompt |
|------|--------------|-------------|
| **作用范围** | 整个对话 | 单次回答 |
| **定义内容** | 角色、能力、规则 | 具体指令、格式要求 |
| **优先级** | 较低（默认规则） | 较高（明确指令） |
| **变化频率** | 很少变化 | 每次对话都可能变化 |
| **使用场景** | 定义 AI 的"人格" | 调整单次回答的"风格" |

### 在 CozyChat 中的应用

1. **当前状态**: 只有 `system_prompt`，没有专门的 `user_prompt`
2. **优化方向**: 可以根据 `user_preferences` 动态构建用户指令
3. **实现方式**: 在消息构建时，根据用户偏好添加指令前缀

### 预期效果

实施 User Prompt 后：
- ✅ 更好地响应用户偏好（简洁/详细）
- ✅ 更灵活的回答格式控制
- ✅ 更好的个性化体验
- ✅ 保持 System Prompt 的稳定性

---

**文档版本**: 1.0  
**创建日期**: 2025-11-18  
**最后更新**: 2025-11-18

