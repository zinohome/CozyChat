# 实时语音转录语言识别问题修复

## 问题描述

**现象**：用户说中文时，实时语音转录偶尔会将中文转录为英文。

**原因分析**：

1. **缺少语言参数**：在创建 OpenAI Realtime API 的 ephemeral token 时，transcription 配置中只指定了 `model: 'whisper-1'`，但没有指定 `language` 参数。

2. **Whisper 自动检测不准确**：当没有明确指定语言时，Whisper 会尝试自动检测语言。在某些情况下（如音频质量、背景噪音、说话速度等），可能会误判为英文。

3. **配置未传递**：虽然项目中有语言配置（personality 配置和全局 STT 配置），但在创建实时语音 token 时没有读取和传递这些配置。

## 修复方案

### 1. 添加语言参数读取逻辑

在 `backend/app/api/v1/config.py` 的 `get_realtime_token` 函数中：

- ✅ 从 personality 配置中读取语言（优先级：`voice.stt.language` > `user_preferences.default_language`）
- ✅ 如果没有 personality 配置，从全局 STT 配置中读取
- ✅ 将语言代码转换为 ISO-639-1 格式（`zh-CN` -> `zh`）

### 2. 在 transcription 配置中添加 language 参数

在创建 ephemeral token 的请求中，在 `transcription` 配置中添加 `language` 参数：

```python
'transcription': {
    'model': 'whisper-1',
    'language': 'zh'  # ISO-639-1 格式
}
```

### 3. 语言代码转换

添加 `normalize_language_code` 函数，将各种格式的语言代码转换为 ISO-639-1 格式：

- `zh-CN` -> `zh`
- `en-US` -> `en`
- `zh` -> `zh`（保持不变）

## 修复代码位置

**文件**：`backend/app/api/v1/config.py`

**主要修改**：

1. **添加语言配置读取逻辑**（第 170-303 行）：
   - 从 personality 配置读取语言
   - 从全局 STT 配置读取语言
   - 语言代码标准化

2. **在 transcription 配置中添加 language 参数**（第 322-326 行）：
   ```python
   'transcription': {
       'model': 'whisper-1',
       **({'language': language_code} if language_code else {})
   }
   ```

## 配置优先级

语言配置的优先级（从高到低）：

1. **Personality STT 配置**：`personality.voice.stt.language`
2. **Personality 用户偏好**：`personality.user_preferences.default_language`
3. **全局 STT 配置**：`config/voice/stt.yaml` 中默认引擎的 `language`
4. **默认值**：如果所有配置都没有指定语言，默认使用 `zh`（中文）

> **注意**：默认使用中文是为了避免 Whisper 自动检测时误判为英文，确保中文用户的转录准确性。

## 测试验证

修复后，应该验证：

1. ✅ 创建实时语音 token 时，transcription 配置包含 `language: 'zh'`
2. ✅ 中文语音转录准确率提高
3. ✅ 不再出现中文被误识别为英文的情况

## 相关配置

### Personality 配置示例

```yaml
voice:
  stt:
    provider: "openai"
    language: "zh-CN"  # 会被转换为 'zh' 传递给 API
```

### 全局 STT 配置

```yaml
# backend/config/voice/stt.yaml
engines:
  stt:
    default: "tencent"
    tencent:
      language: "zh-CN"  # 会被转换为 'zh' 传递给 API
```

## 注意事项

1. **语言代码格式**：OpenAI Realtime API 要求使用 ISO-639-1 格式（如 `zh`、`en`），而不是 BCP 47 格式（如 `zh-CN`、`en-US`）。

2. **默认语言**：如果所有配置都没有指定语言，`language_code` 将默认设置为 `zh`（中文），而不是 `None`。这样可以避免 Whisper 自动检测时误判为英文，确保中文用户的转录准确性。

3. **日志记录**：修复后添加了详细的日志记录，可以在日志中查看使用的语言配置。

## 参考文档

- [OpenAI Realtime API 文档](https://platform.openai.com/docs/guides/realtime-transcription)
- [ISO-639-1 语言代码列表](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
