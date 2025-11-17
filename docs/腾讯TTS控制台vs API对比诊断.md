# 腾讯TTS控制台 vs API 对比诊断指南

## 问题描述

- ✅ 在腾讯云控制台中，使用AI大模型音色正常
- ❌ 通过API调用时，报"资源包配额用尽"错误
- ✅ 资源包确实已购买且有余额（100万字符）

## 诊断步骤

### 步骤1：运行原生SDK测试

使用腾讯SDK原生代码（不经过我们的封装层）测试：

```bash
cd backend
python scripts/test_tencent_raw_sdk.py
```

**这个测试的意义**：
- 排除我们封装层的影响
- 使用与官方示例完全一致的代码
- 直接验证SDK本身是否能工作

### 步骤2：对比控制台配置

登录腾讯云控制台：https://console.cloud.tencent.com/tts

#### 2.1 检查服务开通状态

查看"服务管理"：
- [ ] **基础语音合成服务**：是否已开通？
- [ ] **AI大模型语音合成服务**：是否已开通？ ⭐ 关键

**可能的问题**：AI大模型语音合成服务需要单独开通！

#### 2.2 检查资源包绑定

查看"资源包管理"：

```
资源包信息：
├── 类型：大模型语音合成-预付费包-100万字符
├── 状态：[？] 已生效 / 待生效 / 已过期
├── 绑定AppID：[？] 是否为 1318633704
├── 适用服务：[？] AI大模型语音合成
└── 剩余：1,000,000字符 (100%)
```

**关键检查点**：
1. 状态必须是"已生效"
2. 绑定的AppID必须与您的 `.env` 中一致
3. 适用服务必须是"AI大模型语音合成"

#### 2.3 检查控制台调用参数

在控制台的"在线测试"功能中：

1. 选择您能成功合成的AI大模型音色
2. 查看实际发送的API请求参数
3. 记录以下信息：

```
控制台成功调用的参数：
┌─────────────────────────────────────────┐
│ AppId: [？]                             │
│ VoiceType: [？] (例如：101001)          │
│ FastVoiceType: [？] (可能为空)          │
│ ModelType: [？] (可能是关键)            │
│ Codec: [？]                             │
│ SampleRate: [？]                        │
│ Speed: [？]                             │
│ Volume: [？]                            │
│ EmotionCategory: [？] (是否有此参数？)  │
│ 其他参数: [？]                          │
└─────────────────────────────────────────┘
```

### 步骤3：对比API调用参数

我们的API调用参数（来自SDK代码）：

```python
params = {
    'Action': 'TextToStreamAudioWS',
    'AppId': int(appid),              # 1318633704
    'SecretId': secret_id,
    'ModelType': 1,                   # ⚠️ 硬编码为1
    'VoiceType': 101001,              # AI女声
    'Codec': 'mp3',
    'SampleRate': 16000,
    'Speed': 0,                       # 腾讯格式（-2到2）
    'Volume': 0,
    'SessionId': session_id,
    'Text': text,
    'EnableSubtitle': True,
    'FastVoiceType': '',              # 空字符串
    'Timestamp': timestamp,
    'Expired': timestamp + 86400
}
```

**关键对比点**：

| 参数 | 我们的值 | 控制台的值 | 是否一致？ |
|------|----------|------------|-----------|
| AppId | 1318633704 | ？ | ？ |
| VoiceType | 101001 | ？ | ？ |
| ModelType | 1 | ？ | ⚠️ 重点 |
| FastVoiceType | "" | ？ | ？ |
| 其他参数 | - | ？ | ？ |

### 步骤4：可能的原因分析

#### 原因1：ModelType参数不正确 ⭐ 最可能

腾讯SDK硬编码了 `ModelType = 1`，但AI大模型音色可能需要不同的ModelType值。

**猜测的可能值**：
- `ModelType = 1`：基础语音合成
- `ModelType = 2`：AI大模型语音合成 ？
- `ModelType = 其他`：？

**验证方法**：
1. 在控制台查看成功调用的ModelType值
2. 如果不是1，我们需要修改SDK代码

#### 原因2：服务未单独开通

AI大模型语音合成可能需要：
1. 基础TTS服务开通 ✅
2. AI大模型TTS服务单独开通 ❓

**解决方案**：
1. 访问：https://console.cloud.tencent.com/tts
2. 查找"服务管理"或"服务开通"
3. 确认"AI大模型语音合成"服务已开通

#### 原因3：资源包绑定问题

资源包可能需要特殊的绑定步骤：

**检查清单**：
- [ ] 资源包已生效
- [ ] 资源包绑定到正确的AppID
- [ ] 资源包类型为"AI大模型语音合成"
- [ ] 控制台显示资源包可用

**可能的解决方案**：
1. 在控制台"资源包管理"中，手动绑定资源包到AppID
2. 等待资源包彻底生效（可能需要更长时间）

#### 原因4：地域或可用区限制

AI大模型音色可能有地域限制：

**检查**：
- 账号地区：是否在中国大陆？
- 服务地区：资源包是否有地域限制？

### 步骤5：尝试修改ModelType

如果控制台的ModelType不是1，我们需要修改SDK：

**临时解决方案**（手动修改SDK源码）：

编辑文件：`backend/vendor/tencentcloud-speech-sdk-python/tts/speech_synthesizer_ws.py`

找到第122行：
```python
params['ModelType'] = 1  # ← 这里
```

改为：
```python
params['ModelType'] = 2  # 或控制台显示的值
```

然后重新测试：
```bash
python scripts/test_tencent_raw_sdk.py
```

### 步骤6：抓包对比（高级）

如果以上方法都不行，可以抓包对比控制台和API的实际请求：

**控制台请求**：
```bash
# 在浏览器开发者工具中：
# 1. 打开 Network 标签
# 2. 在控制台进行一次成功的合成
# 3. 查看 WebSocket 连接的握手参数
```

**API请求**：
```bash
# 查看我们的API实际发送的参数
# 在代码中添加日志输出请求参数
```

## 快速诊断清单

### ✅ 已确认的正常项

- [x] SSL证书配置 - WebSocket连接成功
- [x] API凭证 - AppID/SecretID/SecretKey正确
- [x] 资源包购买 - 100万字符已购买
- [x] 控制台可用 - 控制台能正常合成

### ❓ 待确认的项目

- [ ] AI大模型语音合成服务是否单独开通？
- [ ] 资源包是否已绑定到AppID 1318633704？
- [ ] 控制台调用的ModelType是什么值？
- [ ] 控制台调用时是否有其他特殊参数？
- [ ] 资源包是否有地域限制？

## 下一步操作建议

### 方案A：先运行原生SDK测试

```bash
cd backend
python scripts/test_tencent_raw_sdk.py
```

如果仍然失败，说明问题不在我们的封装层。

### 方案B：检查控制台配置

1. 登录控制台：https://console.cloud.tencent.com/tts
2. 进入"服务管理"，确认AI大模型服务已开通
3. 进入"资源包管理"，确认资源包已绑定
4. 进入"在线测试"，查看成功调用的参数

### 方案C：对比参数差异

将控制台的参数和我们的参数进行逐一对比，特别关注：
- ModelType
- FastVoiceType
- 是否有额外的参数（如EmotionCategory）

### 方案D：联系技术支持

准备以下信息提交工单：

```
问题：在控制台可以使用AI大模型音色，但通过API调用报资源包用尽

控制台信息：
- 控制台能成功合成：是
- 使用的音色：AI女声（101001）
- 控制台请求参数：[从开发者工具复制]

API调用信息：
- AppID: 1318633704
- 错误代码: 20002
- 错误信息: UnsupportedOperation.PkgExhausted
- 使用SDK: tencentcloud-speech-sdk-python (官方)
- API请求参数: [见上文]

资源包信息：
- 类型: 大模型语音合成-预付费包-100万字符
- 状态: 已生效
- 剩余: 1,000,000字符 (100%)
- 购买时间: 2025-11-17 11:11:37

疑问：
控制台和API使用的是同一个资源包吗？
是否需要对API调用进行特殊配置才能使用AI大模型资源包？
```

工单地址：https://console.cloud.tencent.com/workorder/category

## 预期结果

如果问题解决，您应该看到：

```
==================================================
测试音色: AI女声 (ai_female)
  VoiceType: 101001
  FastVoiceType: ''

  [开始] session_id=xxx
  [音频] 收到 XXXX bytes
  [音频] 收到 XXXX bytes
  ...
  [结束] 总音频大小: XXXXX bytes
✅ 合成成功！总音频大小: XXXXX bytes
✅ 音频已保存: output/tencent_raw_sdk_101001.mp3
```

## 相关文档

- 腾讯云TTS控制台：https://console.cloud.tencent.com/tts
- 腾讯云TTS API文档：https://cloud.tencent.com/document/product/1073
- 资源包管理文档：https://cloud.tencent.com/document/product/1073/56352

---

**关键结论**：既然控制台能用，说明账号、资源包都没问题。问题出在API调用的参数配置上。请按照上述步骤逐一排查。

