# 腾讯语音引擎测试指南

## 环境要求

确保已配置环境变量（在项目根目录的 `.env` 文件中）：

```bash
TENCENT_APP_ID=your_app_id
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
```

## 测试步骤

### 1. 基础功能测试（包含AI大模型音色）

```bash
cd backend
python scripts/test_tencent_engines.py
```

**测试内容**：
- ✅ ASR健康检查
- ✅ TTS健康检查
- ✅ TTS音色列表（包括AI大模型音色）
- ✅ TTS文本合成（使用AI女声 - ai_female/101001）
- ✅ TTS流式合成（使用AI男声 - ai_male/101002）

**预期成功输出**：

```
============================================================
腾讯语音引擎测试
============================================================

==================================================
环境检查
==================================================
✅ TENCENT_APP_ID: ********** (已设置)
✅ TENCENT_SECRET_ID: ********** (已设置)
✅ TENCENT_SECRET_KEY: ********** (已设置)

[tencent_speech_sdk] SSL configuration applied using certifi: /path/to/cacert.pem

==================================================
测试 1: 腾讯ASR健康检查
==================================================
✅ ASR引擎健康检查通过

==================================================
测试 2: 腾讯TTS健康检查
==================================================
✅ TTS引擎健康检查通过

==================================================
测试 5: 腾讯TTS音色列表
==================================================
✅ 可用音色: female, male, mature_male, energetic_male, warm_female, warm_male, 0, 1, 2, 3, 4, 5, ai_female, ai_male, ai_narrator, ai_warm_female, ai_energetic, 101001, 101002, 101003, 101004, 101005

==================================================
测试 3: 腾讯TTS文本合成（AI大模型音色）
==================================================
合成文本: 你好，这是腾讯AI大模型语音合成测试。
使用音色: ai_female (AI女声)
synthesizer start: begin
synthesizer start: end
conn opened
synthesizer wait: begin
recv FINAL frame
client has closed connection (after recv final), cost XX ms
conn closed, close_status_code=1000 close_msg=None
synthesizer wait: end
✅ TTS合成成功
✅ 音频大小: XXXXX bytes
✅ 音频已保存到: output/tencent_tts_ai_female.mp3

==================================================
测试 4: 腾讯TTS流式合成（AI大模型音色）
==================================================
合成文本: 这是一段较长的文本，用于测试AI大模型流式合成功能...
使用音色: ai_male (AI男声)
synthesizer start: begin
synthesizer start: end
conn opened
synthesizer wait: begin
收到音频块: 1 (大小: XXXX bytes)
收到音频块: 2 (大小: XXXX bytes)
...
recv FINAL frame
client has closed connection (after recv final), cost XX ms
conn closed, close_status_code=1000 close_msg=None
synthesizer wait: end
✅ 流式合成成功
✅ 总音频块数: X
✅ 总音频大小: XXXXX bytes
✅ 音频已保存到: output/tencent_tts_stream_ai_male.mp3

============================================================
测试完成！
============================================================
✅ 5/5 测试通过
```

### 2. AI大模型音色专项测试

```bash
cd backend
python scripts/test_tencent_ai_voice.py
```

**测试内容**：
- 测试所有5种AI大模型音色（101001-101005）
- 验证WebSocket连接和SSL证书配置

**预期成功输出**：

```
============================================================
腾讯AI大模型音色测试
============================================================

[tencent_speech_sdk] SSL configuration applied using certifi: /path/to/cacert.pem

测试 1/5: ai_female (101001 - AI女声)
synthesizer start: begin
synthesizer start: end
conn opened
✅ 成功: 音频大小 = XXXXX bytes

测试 2/5: ai_male (101002 - AI男声)
synthesizer start: begin
synthesizer start: end
conn opened
✅ 成功: 音频大小 = XXXXX bytes

...

============================================================
测试完成！
============================================================
✅ 5/5 AI音色测试通过
```

## 关键成功标志

### ✅ SSL证书配置成功

```
[tencent_speech_sdk] SSL configuration applied using certifi: /path/to/cacert.pem
```

### ✅ WebSocket连接成功

```
synthesizer start: begin
synthesizer start: end
conn opened                    # ← 连接成功
```

### ✅ TTS合成成功

```
recv FINAL frame              # ← 接收到完成信号
client has closed connection (after recv final), cost XX ms
conn closed, close_status_code=1000 close_msg=None  # ← 正常关闭（1000）
```

### ✅ 音频输出成功

```
✅ 音频大小: XXXXX bytes
✅ 音频已保存到: output/tencent_tts_*.mp3
```

## 故障排查

### 问题1：SSL证书验证失败

**症状**：
```
error=[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1006)
```

**解决方案**：
1. 确认看到SSL配置消息：
   ```
   [tencent_speech_sdk] SSL configuration applied using certifi: /path/to/cacert.pem
   ```
2. 如果没有看到，检查 `certifi` 是否安装：
   ```bash
   pip list | grep certifi
   ```
3. 如果未安装，安装它：
   ```bash
   pip install certifi
   ```

### 问题2：资源包配额已用尽

**症状**：
```
error: The resource pack allowance has been exhausted (code: UnsupportedOperation.PkgExhausted)
```

**解决方案**：
1. **使用AI大模型音色（101001-101005）**：
   - 需要购买"大模型语音合成"资源包
   - 购买链接：https://console.cloud.tencent.com/tts
   
2. **使用基础音色（0-5）**：
   - 需要购买"基础语音合成"资源包
   - 购买链接：https://console.cloud.tencent.com/tts

3. **检查资源包配置**：
   - 默认测试使用AI大模型音色
   - 如果只有基础资源包，修改 `backend/config/voice/tts.yaml`：
     ```yaml
     voice: "female"  # 或 0-5 的任意值
     voice_type: 0
     ```

### 问题3：环境变量未设置

**症状**：
```
❌ TENCENT_APP_ID: 未设置
```

**解决方案**：
在项目根目录的 `.env` 文件中添加：
```bash
TENCENT_APP_ID=your_app_id
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
```

### 问题4：WebSocket连接超时

**症状**：
```
synthesizer start: begin
synthesizer start: end
synthesizer wait: begin
synthesizer wait: end  # ← 没有 "conn opened"
```

**可能原因**：
1. 网络问题，无法连接到 `wss://tts.cloud.tencent.com`
2. 防火墙阻止WebSocket连接
3. API凭证错误

**解决方案**：
1. 检查网络连接
2. 验证API凭证是否正确
3. 检查防火墙设置

## 音频文件输出

测试成功后，音频文件会保存在：

```
backend/output/
  tencent_tts_ai_female.mp3      # AI女声合成
  tencent_tts_stream_ai_male.mp3 # AI男声流式合成
  tencent_ai_voice_101001.mp3    # AI大模型音色测试
  tencent_ai_voice_101002.mp3
  ...
```

使用任意音频播放器验证音频内容。

## 测试配置修改

如果需要测试不同的音色或参数，可以修改测试脚本：

```python
# scripts/test_tencent_engines.py

# 修改合成文本
text = "你好，这是腾讯AI大模型语音合成测试。"

# 修改音色
audio_data = await engine.synthesize(text, voice="ai_female", speed=1.0)

# 修改语速（0.25-4.0）
audio_data = await engine.synthesize(text, voice="ai_female", speed=1.5)
```

## 支持的音色列表

### 基础音色（0-5）- 需要"基础语音合成"资源包

| ID | 名称 | 描述 |
|----|------|------|
| 0 | female | 女声 |
| 1 | male | 男声 |
| 2 | mature_male | 成熟男声 |
| 3 | energetic_male | 充满活力的男声 |
| 4 | warm_female | 温暖的女声 |
| 5 | warm_male | 温暖的男声 |

### AI大模型音色（101001-101005）- 需要"大模型语音合成"资源包

| ID | 名称 | 描述 |
|--------|---------|------|
| 101001 | ai_female | AI女声（温柔、自然） |
| 101002 | ai_male | AI男声（磁性、稳重） |
| 101003 | ai_narrator | AI旁白（专业、清晰） |
| 101004 | ai_warm_female | AI温暖女声 |
| 101005 | ai_energetic | AI活力声音 |

## 联系支持

如果遇到其他问题，请：
1. 查看日志文件：`backend/logs/app.log`
2. 检查腾讯云控制台：https://console.cloud.tencent.com/tts
3. 参考文档：`docs/腾讯大模型音色配置指南.md`
