# 腾讯语音SDK安装指南

## 前置条件

1. 已克隆项目
2. Python 3.8+
3. Git已安装

## 安装步骤

### 1. 初始化Git Submodule

```bash
# 在项目根目录执行
git submodule update --init --recursive
```

或者克隆项目时直接包含子模块：

```bash
git clone --recurse-submodules <repo-url>
```

### 2. 安装本地包

```bash
cd backend
pip install -e packages/tencent-speech-sdk
```

### 3. 安装其他依赖

```bash
pip install -r requirements/base.txt
```

## 验证安装

```python
# 测试导入
from tencent_speech_sdk import credential, flash_recognizer
from tencent_speech_sdk import speech_recognizer, speech_synthesizer

print("✅ Tencent Speech SDK installed successfully!")
```

## 常见问题

### Q: 导入失败，提示SDK not found

**A**: 需要先初始化Git Submodule：

```bash
git submodule update --init --recursive
```

### Q: websocket-client版本错误

**A**: 必须使用0.48版本：

```bash
pip install websocket-client==0.48
```

### Q: 如何更新SDK？

**A**: 

```bash
# 更新到最新版本
git submodule update --remote backend/vendor/tencentcloud-speech-sdk-python

# 提交更新
git add backend/vendor/tencentcloud-speech-sdk-python
git commit -m "chore(voice): update tencent SDK"
```

## 项目结构

```
backend/
├── vendor/                          # Git Submodule
│   └── tencentcloud-speech-sdk-python/  # 官方SDK
├── packages/                        # 本地包
│   └── tencent-speech-sdk/
│       ├── setup.py
│       └── tencent_speech_sdk/
│           └── __init__.py
└── requirements/
    └── base.txt
```

