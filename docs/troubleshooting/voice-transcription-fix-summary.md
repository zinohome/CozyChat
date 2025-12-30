# 语音转录问题修复总结

## 问题症状

用户语音始终无法获取转录文本，日志显示：
- 配置未生效：`hasConfig: false, config: undefined`
- `session.update` 未收到确认响应
- `input_audio` 项的 `transcript` 为 `null`
- 未出现任何 `input_audio_transcription.*` 事件

## 根本原因

发现了**两个关键问题**：

1. **配置时机错误**：`transcription` 配置必须在创建 ephemeral token 时完成，而不是在连接后
2. **参数结构错误**：API 不接受扁平的 `input_audio_transcription` 参数，正确的结构是嵌套的 `session.audio.input.transcription`

参考：
- [OpenAI 社区讨论](https://community.openai.com/t/realtime-api-input-audio-transcription-is-not-showing/971804)
- 通过 curl 测试验证了正确的 API 格式

> "Make sure when you do the session request to include the `input_audio_transcription` field as part of the session request to get the ephemeral token." - activescott

## 修复内容

### 1. 后端修复

**文件**: `backend/app/api/v1/config.py`

**修改**: 在 `get_realtime_token` 端点创建 ephemeral token 时添加转录配置

```python
# ❌ 修复前（第 147-152 行）- 缺少转录配置
json={
    'session': {
        'type': 'realtime',
        'model': 'gpt-realtime'
    }
}

# ❌ 第一次尝试（错误）- 使用了错误的扁平结构
json={
    'session': {
        'type': 'realtime',
        'model': 'gpt-realtime',
        'input_audio_transcription': {  # ❌ API 不认识这个参数
            'model': 'whisper-1'
        }
    }
}

# ✅ 修复后（正确）- 使用嵌套结构，与 curl 测试结果一致
json={
    'session': {
        'type': 'realtime',
        'model': 'gpt-4o-realtime-preview-2025-06-03',  # ✅ 使用正确的模型名
        # ✅ 关键：使用正确的嵌套结构 audio.input.transcription
        'audio': {
            'input': {
                'transcription': {
                    'model': 'whisper-1'
                }
            }
        }
    }
}
```

**关键发现**：
- 通过 curl 测试发现 API 返回的 session 结构是 `session.audio.input.transcription`
- API 错误提示：`Unknown parameter: 'session.input_audio_transcription'`
- 模型名称必须是完整的：`gpt-4o-realtime-preview-2025-06-03`

### 2. 前端修复

**文件**: `frontend/src/hooks/useVoiceAgent.ts`

#### 修改 1：移除前端配置代码

```typescript
// ❌ 修复前：在前端尝试配置（无效）
const sessionConfig: any = {
  input_audio_transcription: {
    model: 'whisper-1',
    language: 'zh-CN',
  },
};

const session = new RealtimeSession(agent, {
  apiKey: realtimeToken.token,
  transport: transport,
  model: realtimeToken.model,
  config: sessionConfig as any,  // ❌ 配置不会生效
});

// ✅ 修复后：完全依赖后端配置
const session = new RealtimeSession(agent, {
  apiKey: realtimeToken.token,  // ✅ 后端生成的 token 已包含转录配置
  transport: transport,
  model: realtimeToken.model,  // ✅ 自动使用后端返回的正确模型名
});
```

#### 修改 2：使用正确的事件名

```typescript
// ❌ 修复前
(session as any).on('input_audio_transcription.done', (event: any) => {
  // ...
});

// ✅ 修复后
(session as any).on('conversation.item.input_audio_transcription.completed', (event: any) => {
  const transcript = event?.transcript;
  if (transcript && callbacks?.onUserTranscript) {
    callbacks.onUserTranscript(transcript);
  }
});
```

#### 修改 3：检查正确的配置路径

```typescript
// ❌ 修复前：检查错误的路径
const config = event.session.input_audio_transcription;

// ✅ 修复后：使用正确的嵌套路径
const config = event.session.audio?.input?.transcription;
if (config) {
  console.log('✅ 转录配置已确认生效:', config);
}
```

## 关键要点

1. ✅ **参数结构至关重要** - API 使用嵌套结构 `session.audio.input.transcription`，不是扁平的 `session.input_audio_transcription`

2. ✅ **后端配置是关键** - 转录配置必须在创建 ephemeral token 时完成，不能在连接后通过 `session.update` 添加

3. ✅ **使用完整模型名** - 必须使用 `gpt-4o-realtime-preview-2025-06-03`，不能简写为 `gpt-realtime`

4. ✅ **正确的事件名** - 用户转录事件是 `conversation.item.input_audio_transcription.completed`，不是 `input_audio_transcription.done`

5. ✅ **验证配置生效** - 监听 `session.started` 事件，检查 `event.session.audio?.input?.transcription` 是否存在

6. ✅ **从 `event.transcript` 获取文本** - 转录文本在 `event.transcript` 字段中

7. ✅ **通过 curl 验证 API** - 遇到问题时，先用 curl 直接测试 API，确认正确的参数格式

## 测试验证

### 1. 后端测试（用 curl 验证）

```bash
curl -X POST https://oneapi.naivehero.top/v1/realtime/client_secrets \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session": {
      "type": "realtime",
      "model": "gpt-4o-realtime-preview-2025-06-03",
      "audio": {
        "input": {
          "transcription": {
            "model": "whisper-1"
          }
        }
      }
    }
  }'
```

**成功响应**应该包含：

```json
{
  "value": "ek_...",
  "session": {
    "audio": {
      "input": {
        "transcription": {
          "model": "whisper-1"
        }
      }
    }
  }
}
```

### 2. 前端测试（查看日志）

修复后，应该在日志中看到：

```
✅ RealtimeSession 连接成功，等待 session.started 事件确认配置
🔍 Transport 事件: { type: 'session.started', hasAudioInputTranscription: true }
✅ 转录配置已确认生效: { model: 'whisper-1', hasConfig: true }
🎤 conversation.item.input_audio_transcription.completed 事件触发
✅ 获取用户转录文本: [用户说的话]
```

**如果看到错误**：

```
❌ Failed to generate ephemeral client key (New API): 400
"Unknown parameter: 'session.input_audio_transcription'."
```

说明参数结构错误，需要检查后端代码。

## 相关资源

- [OpenAI 社区 - Input audio transcription](https://community.openai.com/t/input-audio-transcription-in-realtime-api/1007401/5)
- [OpenAI 社区 - 转录不显示问题](https://community.openai.com/t/realtime-api-input-audio-transcription-is-not-showing/971804)
- [TypeScript Realtime API 示例](https://github.com/activescott/typescript-openai-realtime-api/)
- [OpenAI Realtime API 文档](https://platform.openai.com/docs/guides/realtime-webrtc)

## 后续步骤

1. 重启后端服务以应用配置更改
2. 刷新前端页面
3. 测试语音通话功能
4. 检查日志确认配置生效
5. 验证用户语音转录是否正常显示

