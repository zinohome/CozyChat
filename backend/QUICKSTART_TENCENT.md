# 腾讯语音引擎快速开始 🚀

## 3步启用腾讯引擎

### 1️⃣ 配置环境变量

编辑项目根目录的 `.env` 文件：

```bash
TENCENT_APP_ID=1318633704
TENCENT_SECRET_ID=AKIDxxxxxxxxxxxxx
TENCENT_SECRET_KEY=xxxxxxxxxxxxxxxx
```

### 2️⃣ 修改人格配置

编辑 `backend/config/personalities/health_assistant.yaml`：

```yaml
voice:
  stt:
    provider: "tencent"     # ← 改这里
    model: "16k_zh"
    language: "zh-CN"
  
  tts:
    provider: "tencent"     # ← 改这里
    voice: "ai_female"      # AI女声（推荐）
    voice_type: 101001
    speed: 1.0
```

### 3️⃣ 重启应用

```bash
cd backend
uvicorn app.main:app --reload
```

**完成！** 🎉

---

## 🧪 快速测试

```bash
# 测试TTS
curl -X POST "http://localhost:8000/api/v1/audio/speech" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "你好，这是测试",
    "personality_id": "health_assistant"
  }' \
  --output test.mp3

# 播放
open test.mp3
```

---

## 🎨 AI大模型音色

| 音色 | voice值 | voice_type | 特点 |
|-----|---------|------------|------|
| AI女声 | ai_female | 101001 | 温柔、自然 ⭐ 推荐 |
| AI男声 | ai_male | 101002 | 磁性、稳重 |
| AI旁白 | ai_narrator | 101003 | 专业、清晰 |
| AI温暖女声 | ai_warm_female | 101004 | 温暖、治愈 |
| AI活力 | ai_energetic | 101005 | 充满活力 |

---

## 📚 完整文档

详细集成指南：`docs/腾讯语音引擎集成指南.md`

---

**注意**：需要购买"AI大模型语音合成"资源包  
购买地址：https://console.cloud.tencent.com/tts

