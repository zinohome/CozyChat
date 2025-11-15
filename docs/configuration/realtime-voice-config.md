# Realtime 语音配置说明

## 配置文件结构

CozyChat 的 Realtime 语音功能采用**两层配置结构**：

```
全局默认配置 (realtime.yaml)
       ↓
personality 配置覆盖 (health_assistant.yaml)
```

## 配置文件位置

### 1. 全局默认配置

**文件路径**: `backend/config/voice/realtime.yaml`

**作用**: 提供所有 personality 共享的默认值

**示例**:
```yaml
engines:
  realtime:
    openai:
      provider: "openai"
      model: "gpt-4o-realtime-preview-2024-10-01"
      voice: "shimmer"  # 全局默认语音
      temperature: 0.8
      max_response_output_tokens: 4096
```

### 2. Personality 配置

**文件路径**: `backend/config/personalities/health_assistant.yaml`

**作用**: personality 特定的语音设置（可覆盖全局配置）

**示例**:
```yaml
personality:
  voice:
    realtime:
      enabled: true
      voice: "nova"  # 覆盖全局配置，使用 nova 声音
      instructions: |
        你是一个专业的健康咨询助手...
```

## 配置优先级

### 优先级规则

```
Personality配置 > 全局配置 > 代码默认值
```

### 详细说明

1. **Personality 配置优先级最高**
   - 如果 `health_assistant.yaml` 中的 `voice.realtime.voice` 有值，使用它
   
2. **全局配置作为默认**
   - 如果 personality 没有配置，使用 `realtime.yaml` 中的 `voice`
   
3. **代码默认值作为兜底**
   - 如果以上都没有，使用代码中的默认值 `'shimmer'`

### 配置合并示例

#### 场景1: Personality 有配置

**realtime.yaml**:
```yaml
voice: "shimmer"  # 全局默认
```

**health_assistant.yaml**:
```yaml
voice:
  realtime:
    voice: "nova"  # personality 覆盖
```

**结果**: 使用 `"nova"` ✅

---

#### 场景2: Personality 没有配置

**realtime.yaml**:
```yaml
voice: "shimmer"  # 全局默认
```

**health_assistant.yaml**:
```yaml
voice:
  realtime:
    # voice 未配置
    instructions: "..."
```

**结果**: 使用 `"shimmer"` ✅ (全局配置)

---

#### 场景3: 两者都没配置

**realtime.yaml**:
```yaml
# voice 未配置
```

**health_assistant.yaml**:
```yaml
voice:
  realtime:
    # voice 未配置
```

**结果**: 使用 `"shimmer"` ✅ (代码默认值)

## 可配置参数

### Voice 声音

**参数名**: `voice`

**可选值**:
- `"alloy"` - 中性、专业
- `"echo"` - 男性、深沉
- `"fable"` - 女性、温暖
- `"onyx"` - 男性、有力
- `"nova"` - 女性、活泼
- `"shimmer"` - 女性、柔和

**示例**:
```yaml
# 全局配置
voice: "shimmer"

# 或 personality 配置
voice:
  realtime:
    voice: "nova"
```

### Instructions 提示词

**参数名**: `instructions`

**说明**: 控制 AI 的对话风格和行为

**示例**:
```yaml
voice:
  realtime:
    instructions: |
      你是一个专业的健康咨询助手。
      在语音对话中，请保持简洁、自然的对话风格。
      回复要简短明了，适合语音播放。
```

### Turn Detection 对话检测

**参数名**: `turn_detection`

**说明**: 控制何时检测到用户说话结束

**示例**:
```yaml
voice:
  realtime:
    turn_detection:
      type: "server_vad"  # 服务器端语音活动检测
      threshold: 0.5      # 检测阈值 (0.0-1.0)
```

## 实现原理

### 后端 API

#### 端点: `GET /v1/config/realtime-config`

**功能**: 返回全局默认配置

**响应**:
```json
{
  "voice": "shimmer",
  "model": "gpt-4o-realtime-preview-2024-10-01",
  "temperature": 0.8,
  "max_response_output_tokens": 4096
}
```

### 前端配置合并

#### 代码位置: `frontend/src/hooks/useVoiceAgent.ts`

**合并逻辑**:
```typescript
// 1. 获取全局默认配置
const globalConfig = await configApi.getRealtimeConfig();

// 2. 获取 personality 配置
const personalityRealtimeConfig = voiceConfig?.realtime || {};

// 3. 合并配置（personality > 全局 > 默认）
const voice = personalityRealtimeConfig.voice || globalConfig.voice || 'shimmer';
```

**调试日志**:
```typescript
console.log('🎙️ Realtime Voice 配置:', {
  global: globalConfig.voice,      // 全局配置值
  personality: personalityRealtimeConfig.voice,  // personality 配置值
  final: voice,                    // 最终使用的值
});
```

## 如何修改配置

### 修改全局默认值

编辑 `backend/config/voice/realtime.yaml`:

```yaml
engines:
  realtime:
    openai:
      voice: "nova"  # 修改全局默认声音
      temperature: 0.7
```

**适用场景**: 希望所有 personality 都默认使用新的设置

**影响范围**: 所有未明确配置的 personality

---

### 修改 Personality 配置

编辑 `backend/config/personalities/health_assistant.yaml`:

```yaml
personality:
  voice:
    realtime:
      voice: "fable"  # 只修改这个 personality
      instructions: |
        用温暖的语气回答...
```

**适用场景**: 希望特定 personality 使用特殊的声音

**影响范围**: 仅当前 personality

---

### 重启服务

修改配置后需要**重启后端服务**：

```bash
cd backend
python -m app.main
```

前端会自动获取新的配置，无需重启。

## 调试技巧

### 查看配置合并结果

打开浏览器开发者工具（Console），开始语音通话时会显示：

```
🎙️ Realtime Voice 配置:
  global: "shimmer"
  personality: "nova"
  final: "nova"
```

**解读**:
- `global`: 全局配置的值
- `personality`: personality 配置的值
- `final`: 最终使用的值

### 验证配置是否生效

1. 修改 `realtime.yaml` 或 personality 配置文件
2. 重启后端服务
3. 刷新前端页面
4. 开始语音通话
5. 查看 Console 日志中的配置信息

## 常见问题

### Q: 修改了配置但没有生效？

**A**: 确保已重启后端服务，并刷新了前端页面。

---

### Q: 如何知道当前使用的是哪个配置？

**A**: 查看浏览器 Console 中的 `🎙️ Realtime Voice 配置:` 日志。

---

### Q: 可以为不同的 personality 设置不同的声音吗？

**A**: 可以！在每个 personality 的配置文件中设置 `voice.realtime.voice`。

---

### Q: 全局配置和 personality 配置有冲突怎么办？

**A**: Personality 配置始终优先，不会有冲突。如果 personality 有配置，就使用 personality 的；如果没有，才使用全局配置。

---

### Q: 语速可以配置吗？

**A**: OpenAI Realtime API 目前不支持语速配置。可以通过 `instructions` 引导 AI 调整说话节奏，或选择不同的声音（不同声音有略微不同的语速）。

## 最佳实践

### 1. 全局配置用于通用设置

在 `realtime.yaml` 中设置大多数 personality 都适用的值：

```yaml
voice: "shimmer"      # 大部分场景适用的声音
temperature: 0.8      # 标准温度
```

### 2. Personality 配置用于特殊定制

只在需要特殊处理的 personality 中覆盖：

```yaml
# health_assistant.yaml - 需要温暖的声音
voice:
  realtime:
    voice: "fable"

# technical_assistant.yaml - 需要专业的声音  
voice:
  realtime:
    voice: "alloy"
```

### 3. 保持配置简洁

如果多个 personality 使用相同的声音，应该修改全局配置而不是每个 personality 都配置一遍。

### 4. 使用有意义的命名

在 personality 配置中添加注释说明为什么选择特定的声音：

```yaml
voice:
  realtime:
    voice: "fable"  # 温暖的女声，适合健康咨询场景
```

## 相关文件

- `backend/config/voice/realtime.yaml` - 全局默认配置
- `backend/config/personalities/*.yaml` - Personality 特定配置
- `backend/app/api/v1/config.py` - 配置 API 端点
- `frontend/src/services/config.ts` - 前端 API 调用
- `frontend/src/hooks/useVoiceAgent.ts` - 配置合并逻辑

