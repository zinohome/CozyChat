# Tencent Speech SDK Local Package

腾讯语音SDK的本地包装包。

## 安装

```bash
cd backend
pip install -e packages/tencent-speech-sdk
```

## 使用

```python
from tencent_speech_sdk import credential, flash_recognizer, speech_recognizer
from tencent_speech_sdk import speech_synthesizer, speech_synthesizer_ws

# 使用示例
cred = credential.Credential(secret_id, secret_key)
recognizer = flash_recognizer.FlashRecognizer(app_id, cred)
```

## 更新SDK

SDK通过Git Submodule管理，更新方式：

```bash
# 更新到最新版本
git submodule update --remote backend/vendor/tencentcloud-speech-sdk-python

# 提交更新
git add backend/vendor/tencentcloud-speech-sdk-python
git commit -m "chore(voice): update tencent SDK"
```

## 初始化（首次克隆项目）

```bash
git submodule update --init --recursive
```

