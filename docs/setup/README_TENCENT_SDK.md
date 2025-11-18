# 腾讯语音SDK安装和维护指南

## 快速开始

### 首次安装

```bash
# 1. 初始化Git Submodule
git submodule update --init --recursive

# 2. 安装本地包
cd backend
pip install -e packages/tencent-speech-sdk

# 3. 安装依赖
pip install -r requirements/base.txt
```

### 验证安装

```python
from tencent_speech_sdk import credential, flash_recognizer
print("✅ SDK installed successfully!")
```

## 维护和更新

### 更新SDK到最新版本

```bash
# 更新子模块
git submodule update --remote backend/vendor/tencentcloud-speech-sdk-python

# 检查变更
cd backend/vendor/tencentcloud-speech-sdk-python
git log --oneline -10

# 提交更新
cd ../../..
git add backend/vendor/tencentcloud-speech-sdk-python
git commit -m "chore(voice): update tencent SDK to latest"
```

### 锁定到特定版本

```bash
cd backend/vendor/tencentcloud-speech-sdk-python
git checkout <tag-or-commit>
cd ../../..
git add backend/vendor/tencentcloud-speech-sdk-python
git commit -m "chore(voice): lock tencent SDK version"
```

## 项目结构

```
backend/
├── vendor/                          # Git Submodule
│   └── tencentcloud-speech-sdk-python/  # 官方SDK
├── packages/                        # 本地包
│   └── tencent-speech-sdk/
│       ├── setup.py
│       ├── README.md
│       └── tencent_speech_sdk/
│           └── __init__.py
└── requirements/
    └── base.txt
```

## 团队协作

### 克隆项目（包含子模块）

```bash
git clone --recurse-submodules <repo-url>
```

### 已克隆项目，初始化子模块

```bash
git submodule update --init --recursive
```

## 详细文档

- [维护方案](../docs/腾讯语音SDK维护方案.md)
- [接入方案](../docs/腾讯语音SDK接入方案.md)
- [只使用官方语音SDK方案](../docs/只使用官方语音SDK方案.md)

