# 腾讯TTS资源包问题排查指南

## 问题描述

测试时遇到错误：
```
code=20002 msg=UnsupportedOperation.PkgExhausted:The resource pack allowance has been exhausted
```

但资源包查询显示：
```
大模型语音合成-预付费包-100万字符
剩余：1,000,000字符(100.00%)
已用：0字符(0.00%)
购买时间：2025-11-17 11:11:37
```

## 原因分析

### 1. 资源包生效延迟 ⏰

**最常见原因**：腾讯云资源包购买后通常需要 **5-15分钟** 才能生效。

**解决方案**：
- 等待15分钟后重试
- 刷新腾讯云控制台确认状态

### 2. AppID绑定问题 🔗

资源包可能购买了，但未正确绑定到您的AppID。

**检查步骤**：

1. 登录腾讯云控制台：https://console.cloud.tencent.com/tts
2. 查看"资源包管理"
3. 确认资源包状态为"已绑定"
4. 确认绑定的AppID与您的 `.env` 中的 `TENCENT_APP_ID` 一致

**示例**：
```
资源包信息：
├── 状态：已生效 ✅
├── 绑定AppID：1318633704 ← 必须与您的AppID一致
└── 剩余：1,000,000字符
```

### 3. 服务开通问题 🔌

AI大模型语音合成需要单独开通服务。

**检查步骤**：

1. 访问：https://console.cloud.tencent.com/tts
2. 查看"服务管理" → "语音合成服务"
3. 确认"AI大模型语音合成"服务状态为"已开通"

### 4. 权限和密钥问题 🔑

**检查API密钥**：

```bash
# 在项目根目录查看 .env
cat .env | grep TENCENT

# 应该看到：
TENCENT_APP_ID=1318633704
TENCENT_SECRET_ID=AKIDxxxxxxxxxxxxxxxxxx
TENCENT_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

**验证密钥**：
1. 登录：https://console.cloud.tencent.com/cam/capi
2. 确认 SECRET_ID 和 SECRET_KEY 正确
3. 确认密钥有"语音合成"权限

### 5. 区域和可用性问题 🌍

某些AI大模型音色可能在特定区域不可用。

**检查方法**：

在腾讯云控制台查看：
- 您的账号是否在中国大陆
- 服务是否在支持的区域

## 解决方案总结

### 方案1：等待生效（最简单）⏳

您的资源包购买时间是 `2025-11-17 11:11:37`，请：

1. **等待15分钟**（到 11:26:37 左右）
2. 重新运行测试：
   ```bash
   cd backend
   python scripts/test_tencent_engines.py
   ```

### 方案2：使用基础音色测试 🎯

如果等待后仍然失败，先用基础音色验证其他功能是否正常：

**临时修改配置**：

编辑 `backend/config/voice/tts.yaml`：

```yaml
engines:
  tts:
    tencent:
      voice: "female"      # 改为基础音色
      voice_type: 0        # 0-5 是基础音色
```

**运行测试**：
```bash
cd backend
python scripts/test_tencent_engines.py
```

如果基础音色也失败，说明是更基础的配置问题（密钥、AppID等）。

### 方案3：联系腾讯云技术支持 📞

如果以上方案都不行：

1. 准备信息：
   - AppID: 1318633704
   - 错误代码: 20002
   - 错误信息: UnsupportedOperation.PkgExhausted
   - 资源包订单号
   - 购买时间: 2025-11-17 11:11:37

2. 提交工单：https://console.cloud.tencent.com/workorder/category
   - 选择"语音合成 TTS"
   - 描述问题："购买大模型语音合成资源包后仍报配额用尽"

## 成功验证清单

测试成功后，您应该看到：

### ✅ SSL连接成功
```
[tencent_speech_sdk] SSL configuration applied using certifi: /path/to/cacert.pem
synthesizer start: begin
synthesizer start: end
conn opened  ← 连接成功
```

### ✅ TTS合成成功
```
收到音频块: 1 (大小: XXXX bytes)
收到音频块: 2 (大小: XXXX bytes)
...
recv FINAL frame
client has closed connection (after recv final), cost XX ms
conn closed, close_status_code=1000 close_msg=None
✅ TTS合成成功
✅ 音频大小: XXXXX bytes
✅ 音频已保存到: output/tencent_tts_ai_female.mp3
```

### ✅ 资源包扣费成功

测试成功后，再次查看资源包：
```
大模型语音合成-预付费包-100万字符
剩余：999,XXX字符(99.XX%)  ← 应该略有减少
已用：XX字符(0.0X%)          ← 应该有使用量
```

## 当前状态总结

根据您的情况：

| 项目 | 状态 | 说明 |
|-----|------|------|
| SSL证书 | ✅ 已修复 | WebSocket连接成功 |
| 代码警告 | ✅ 已修复 | 线程安全问题已解决 |
| 资源包 | ⏳ 等待生效 | 购买时间: 11:11，建议 11:26 后重试 |
| API凭证 | ✅ 正常 | AppID/SecretID/SecretKey 都已配置 |

## 下一步操作

**推荐操作流程**：

```bash
# 1. 等待15分钟（如果当前时间 < 11:26）

# 2. 重新运行测试
cd backend
python scripts/test_tencent_engines.py

# 3. 如果仍然失败，切换到基础音色测试
# 编辑 backend/config/voice/tts.yaml
# 将 voice_type 改为 0

# 4. 再次运行测试
python scripts/test_tencent_engines.py

# 5. 查看生成的音频文件
ls -lh output/tencent_tts_*.mp3
```

## 常见错误代码

| 错误码 | 说明 | 解决方案 |
|-------|------|----------|
| 20002 | 资源包配额用尽 | 检查资源包、等待生效、或购买新资源包 |
| 10004 | 参数错误 | 检查voice_type是否正确 |
| 10006 | 认证失败 | 检查SecretID/SecretKey |
| 10008 | 请求频率超限 | 稍后重试 |
| 20001 | 后台服务异常 | 稍后重试或联系技术支持 |

## 参考文档

- 腾讯云TTS控制台：https://console.cloud.tencent.com/tts
- 资源包购买：https://buy.cloud.tencent.com/tts
- API文档：https://cloud.tencent.com/document/product/1073
- 工单提交：https://console.cloud.tencent.com/workorder/category

---

**最后更新**: 2025-11-17

**相关文档**:
- `docs/腾讯大模型音色配置指南.md`
- `backend/scripts/README_TENCENT_TEST.md`

