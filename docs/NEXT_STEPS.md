# 下一步操作指南

## ✅ 已完成的修复

### 1. SSL证书问题 - ✅ 已解决
```
[tencent_speech_sdk] SSL configuration applied using certifi
conn opened  ← WebSocket连接成功！
```

### 2. 代码警告 - ✅ 已修复
```python
# 修复了线程间通信的event loop问题
RuntimeWarning: coroutine 'Queue.put' was never awaited  ← 已修复
```

## ⏳ 等待解决的问题

### 资源包生效延迟

您的情况：
- ✅ 资源包已购买：大模型语音合成-预付费包-100万字符
- ✅ 资源包满额：1,000,000字符(100.00%)
- ⏰ 购买时间：2025-11-17 11:11:37
- ⏳ **建议重试时间：2025-11-17 11:26:37 之后**（等待15分钟）

## 🎯 现在请执行

### 步骤1：等待资源包生效（5-15分钟）

```bash
# 查看当前时间
date

# 如果当前时间 < 11:26:37，请等待
# 如果当前时间 >= 11:26:37，继续步骤2
```

### 步骤2：重新运行测试

```bash
cd /Users/zhangjun/CursorProjects/CozyChat/backend
python scripts/test_tencent_engines.py
```

### 步骤3：验证结果

#### 预期成功输出：

```
[tencent_speech_sdk] SSL configuration applied using certifi  ✅
==================================================
测试 3: 腾讯TTS文本合成（AI大模型音色）
==================================================
synthesizer start: begin
synthesizer start: end
conn opened                                                    ✅
收到音频块: 1 (大小: XXXX bytes)                               ✅
收到音频块: 2 (大小: XXXX bytes)
...
recv FINAL frame                                               ✅
client has closed connection (after recv final), cost XX ms    ✅
conn closed, close_status_code=1000 close_msg=None            ✅
✅ TTS合成成功
✅ 音频大小: XXXXX bytes
✅ 音频已保存到: output/tencent_tts_ai_female.mp3            ✅
```

#### 成功标志：

1. ✅ **连接成功**：`conn opened`
2. ✅ **收到音频**：`收到音频块: X`
3. ✅ **正常结束**：`recv FINAL frame`
4. ✅ **正常关闭**：`close_status_code=1000`
5. ✅ **文件生成**：`output/tencent_tts_ai_female.mp3`

### 步骤4：播放音频验证

```bash
# 查看生成的音频文件
ls -lh output/tencent_tts_*.mp3

# 使用系统播放器播放（macOS）
open output/tencent_tts_ai_female.mp3

# 或使用afplay命令
afplay output/tencent_tts_ai_female.mp3
```

## 🔧 如果仍然失败

### 方案A：使用基础音色测试

如果等待15分钟后仍然报"资源包配额用尽"，尝试基础音色：

**1. 修改配置**

编辑 `backend/config/voice/tts.yaml`：

```yaml
engines:
  tts:
    tencent:
      voice: "female"      # ← 改为基础音色
      voice_type: 0        # ← 0-5 是基础音色（不需要AI大模型资源包）
```

**2. 重新测试**

```bash
python scripts/test_tencent_engines.py
```

**3. 判断**

- ✅ 基础音色成功 → 说明AI大模型资源包未生效，联系腾讯云技术支持
- ❌ 基础音色失败 → 说明是密钥或AppID配置问题

### 方案B：检查资源包绑定

1. 访问：https://console.cloud.tencent.com/tts
2. 点击"资源包管理"
3. 确认：
   - 资源包状态：**已生效** ✅
   - 绑定AppID：**1318633704**（与您的 `.env` 中一致）
   - 服务类型：**AI大模型语音合成** ✅

### 方案C：联系技术支持

准备以下信息提交工单：

```
问题描述：购买AI大模型语音合成资源包后仍报配额用尽

详细信息：
- AppID: 1318633704
- 错误代码: 20002
- 错误信息: UnsupportedOperation.PkgExhausted
- 资源包类型: 大模型语音合成-预付费包-100万字符
- 购买时间: 2025-11-17 11:11:37
- 当前剩余: 1,000,000字符(100.00%)
- 测试时间: [您的测试时间]
- 音色类型: 101001 (AI女声)

附加说明：
- WebSocket连接成功（conn opened）
- SSL证书配置正常
- API凭证验证通过
- 基础音色测试结果: [成功/失败]
```

工单提交：https://console.cloud.tencent.com/workorder/category

## 📊 测试状态总结

| 项目 | 状态 | 说明 |
|-----|------|------|
| ✅ SSL证书配置 | **已解决** | WebSocket连接成功 |
| ✅ 代码线程安全 | **已解决** | RuntimeWarning已修复 |
| ✅ API凭证 | **正常** | AppID/SecretID/SecretKey已配置 |
| ✅ 资源包购买 | **已完成** | 100万字符，100%剩余 |
| ⏳ 资源包生效 | **等待中** | 建议11:26后重试 |
| 🎯 TTS合成 | **待验证** | 等待资源包生效后测试 |

## 🎉 预期结果

测试成功后，您将看到：

1. **5个音频文件**：
   ```
   backend/output/
   ├── tencent_tts_ai_female.mp3         (AI女声)
   ├── tencent_tts_stream_ai_male.mp3    (AI男声流式)
   └── ... (如果运行AI音色测试)
   ```

2. **资源包扣费**：
   ```
   剩余：999,XXX字符 (略少于100万)
   已用：XX字符 (有使用记录)
   ```

3. **所有测试通过**：
   ```
   ============================================================
   测试完成！
   ============================================================
   ✅ 5/5 测试通过
   ```

## 📚 相关文档

- **问题排查**: `docs/腾讯TTS资源包问题排查.md`
- **测试指南**: `backend/scripts/README_TENCENT_TEST.md`
- **AI音色配置**: `docs/腾讯大模型音色配置指南.md`

---

**当前时间**: 请运行 `date` 查看

**建议操作**:
1. ⏰ 等到 **11:26:37** 或更晚
2. 🧪 重新运行测试
3. 🎵 验证音频文件
4. 📊 检查资源包扣费

**如有问题，请参考**: `docs/腾讯TTS资源包问题排查.md`

