# 腾讯语音SDK维护方案

## 1. 问题分析

**挑战**：
- 腾讯语音SDK（tencentcloud-speech-sdk-python）不能通过pip安装
- 需要手动从GitHub下载和集成
- 如何优雅地维护和更新？

## 2. 方案对比

### 方案A：Git Submodule（推荐⭐⭐⭐⭐⭐）

**原理**：将SDK作为Git子模块，引用官方GitHub仓库

**优点**：
- ✅ 保持与官方仓库同步
- ✅ 更新简单（`git submodule update`）
- ✅ 不污染主仓库
- ✅ 可以锁定特定版本
- ✅ 团队成员自动获取

**缺点**：
- ⚠️ 需要了解Git Submodule
- ⚠️ 克隆项目需要额外步骤

**实现步骤**：

```bash
# 1. 添加子模块
cd backend
git submodule add https://github.com/TencentCloud/tencentcloud-speech-sdk-python.git app/engines/voice/tencent_sdk

# 2. 提交子模块引用
git add .gitmodules app/engines/voice/tencent_sdk
git commit -m "feat(voice): add tencent speech SDK as submodule"

# 3. 更新子模块（当需要更新时）
git submodule update --remote app/engines/voice/tencent_sdk

# 4. 锁定版本（可选）
cd app/engines/voice/tencent_sdk
git checkout <commit-hash>
cd ../../../../..
git add app/engines/voice/tencent_sdk
git commit -m "chore(voice): lock tencent SDK version"
```

**使用方式**：

```python
# 直接导入，无需sys.path
from app.engines.voice.tencent_sdk.common import credential
from app.engines.voice.tencent_sdk.asr import flash_recognizer
from app.engines.voice.tencent_sdk.tts import speech_synthesizer
```

**团队协作**：

```bash
# 克隆项目时
git clone --recurse-submodules <repo-url>

# 或者已克隆后
git submodule update --init --recursive
```

### 方案B：Git Subtree（推荐⭐⭐⭐⭐）

**原理**：将SDK合并到项目目录中，但保留Git历史

**优点**：
- ✅ 不需要额外步骤克隆
- ✅ 保留Git历史
- ✅ 可以合并上游更新

**缺点**：
- ⚠️ 更新需要特殊命令
- ⚠️ 会增大仓库体积

**实现步骤**：

```bash
# 1. 添加subtree
git subtree add --prefix=backend/app/engines/voice/tencent_sdk \
  https://github.com/TencentCloud/tencentcloud-speech-sdk-python.git \
  main --squash

# 2. 更新subtree（当需要更新时）
git subtree pull --prefix=backend/app/engines/voice/tencent_sdk \
  https://github.com/TencentCloud/tencentcloud-speech-sdk-python.git \
  main --squash
```

### 方案C：打包为本地Python包（推荐⭐⭐⭐⭐）

**原理**：创建setup.py，将SDK打包为可安装的包

**优点**：
- ✅ 可以通过pip安装（本地）
- ✅ 统一管理依赖
- ✅ 符合Python包规范
- ✅ 可以版本化

**缺点**：
- ⚠️ 需要维护setup.py
- ⚠️ 需要手动更新SDK代码

**实现步骤**：

```bash
# 1. 创建包结构
backend/packages/tencent-speech-sdk/
├── setup.py
├── tencent_speech_sdk/
│   ├── __init__.py
│   ├── common/
│   ├── asr/
│   └── tts/
└── README.md
```

**setup.py**：

```python
from setuptools import setup, find_packages

setup(
    name="tencent-speech-sdk",
    version="1.0.0",
    description="Tencent Cloud Speech SDK (local package)",
    packages=find_packages(),
    install_requires=[
        "websocket-client==0.48",
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
)
```

**安装方式**：

```bash
# 开发模式安装
cd backend/packages/tencent-speech-sdk
pip install -e .

# 或从requirements安装
pip install -e backend/packages/tencent-speech-sdk
```

**使用方式**：

```python
# 直接导入
from tencent_speech_sdk.common import credential
from tencent_speech_sdk.asr import flash_recognizer
```

### 方案D：直接复制 + 脚本更新（推荐⭐⭐⭐）

**原理**：直接复制SDK到项目，用脚本管理更新

**优点**：
- ✅ 简单直接
- ✅ 不需要Git高级功能
- ✅ 完全控制

**缺点**：
- ⚠️ 需要手动更新
- ⚠️ 可能丢失Git历史
- ⚠️ 更新需要脚本

**实现步骤**：

```bash
# 1. 复制SDK
cp -r example/tencentcloud-speech-sdk-python \
     backend/app/engines/voice/tencent_sdk

# 2. 创建更新脚本
# backend/scripts/update_tencent_sdk.sh
```

**更新脚本**：

```bash
#!/bin/bash
# backend/scripts/update_tencent_sdk.sh

SDK_DIR="backend/app/engines/voice/tencent_sdk"
TEMP_DIR="/tmp/tencent_speech_sdk"

echo "Updating Tencent Speech SDK..."

# 下载最新版本
git clone --depth 1 \
  https://github.com/TencentCloud/tencentcloud-speech-sdk-python.git \
  $TEMP_DIR

# 备份当前版本
if [ -d "$SDK_DIR" ]; then
    cp -r $SDK_DIR "${SDK_DIR}.backup"
fi

# 更新SDK
rm -rf $SDK_DIR
cp -r $TEMP_DIR $SDK_DIR

# 清理
rm -rf $TEMP_DIR

echo "SDK updated successfully!"
echo "Please review changes and commit if needed."
```

### 方案E：Vendor目录 + 版本控制（推荐⭐⭐）

**原理**：将SDK放在vendor目录，通过Git管理

**优点**：
- ✅ 简单直接
- ✅ 版本可控
- ✅ 团队同步

**缺点**：
- ⚠️ 增大仓库体积
- ⚠️ 需要手动更新

## 3. 推荐方案：Git Submodule + 本地包（混合方案）

### 3.1 方案设计

**结合两种方案的优势**：

1. **使用Git Submodule**：保持与官方同步
2. **创建本地包**：便于安装和使用

### 3.2 实现步骤

#### 步骤1：添加Git Submodule

```bash
cd backend
git submodule add https://github.com/TencentCloud/tencentcloud-speech-sdk-python.git \
  vendor/tencentcloud-speech-sdk-python
```

#### 步骤2：创建本地包包装

```bash
# 创建包结构
backend/packages/tencent-speech-sdk/
├── setup.py
├── tencent_speech_sdk/
│   ├── __init__.py
│   └── _sdk_path.py  # 动态路径
└── README.md
```

**setup.py**：

```python
from setuptools import setup, find_packages
import os

# 获取SDK路径（相对于setup.py）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
SDK_PATH = os.path.join(PROJECT_ROOT, "vendor", "tencentcloud-speech-sdk-python")

setup(
    name="tencent-speech-sdk",
    version="1.0.0",
    description="Tencent Cloud Speech SDK wrapper",
    packages=find_packages(),
    install_requires=[
        "websocket-client==0.48",
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
    # 包含SDK路径信息
    package_data={
        "tencent_speech_sdk": ["_sdk_path.py"],
    },
)
```

**_sdk_path.py**：

```python
"""SDK路径配置"""
import os

# SDK路径（相对于项目根目录）
SDK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "vendor",
    "tencentcloud-speech-sdk-python"
)

def get_sdk_path():
    """获取SDK路径"""
    return SDK_PATH
```

**__init__.py**：

```python
"""Tencent Speech SDK Wrapper"""
import sys
import os
from ._sdk_path import get_sdk_path

# 添加SDK路径到sys.path
_sdk_path = get_sdk_path()
if os.path.exists(_sdk_path):
    sys.path.insert(0, _sdk_path)
else:
    raise ImportError(
        f"Tencent Speech SDK not found at {_sdk_path}. "
        "Please run: git submodule update --init --recursive"
    )

# 导出常用模块
from common import credential
from asr import flash_recognizer, speech_recognizer
from tts import speech_synthesizer, speech_synthesizer_ws

__all__ = [
    "credential",
    "flash_recognizer",
    "speech_recognizer",
    "speech_synthesizer",
    "speech_synthesizer_ws",
]
```

#### 步骤3：安装和使用

```bash
# 安装本地包
cd backend
pip install -e packages/tencent-speech-sdk

# 使用
from tencent_speech_sdk import credential, flash_recognizer
```

#### 步骤4：更新流程

```bash
# 1. 更新子模块
git submodule update --remote vendor/tencentcloud-speech-sdk-python

# 2. 检查变更
cd vendor/tencentcloud-speech-sdk-python
git log --oneline -10

# 3. 提交更新
cd ../..
git add vendor/tencentcloud-speech-sdk-python
git commit -m "chore(voice): update tencent speech SDK to latest"
```

## 4. 项目结构

```
backend/
├── vendor/                          # 第三方SDK（Git Submodule）
│   └── tencentcloud-speech-sdk-python/
│       ├── common/
│       ├── asr/
│       └── tts/
├── packages/                        # 本地包
│   └── tencent-speech-sdk/
│       ├── setup.py
│       └── tencent_speech_sdk/
├── app/
│   └── engines/
│       └── voice/
│           ├── stt/
│           │   └── tencent_stt.py
│           └── tts/
│               └── tencent_tts.py
└── requirements/
    └── base.txt
```

## 5. 维护流程

### 5.1 日常使用

```bash
# 克隆项目（包含子模块）
git clone --recurse-submodules <repo-url>

# 或已克隆后初始化
git submodule update --init --recursive
```

### 5.2 更新SDK

```bash
# 1. 更新到最新版本
git submodule update --remote vendor/tencentcloud-speech-sdk-python

# 2. 或更新到特定版本
cd vendor/tencentcloud-speech-sdk-python
git checkout <tag-or-commit>
cd ../..

# 3. 提交更新
git add vendor/tencentcloud-speech-sdk-python
git commit -m "chore(voice): update tencent SDK to v1.x.x"
```

### 5.3 锁定版本

```bash
# 锁定到特定版本（在.gitmodules中）
cd vendor/tencentcloud-speech-sdk-python
git checkout <stable-version-tag>
cd ../..
git add vendor/tencentcloud-speech-sdk-python .gitmodules
git commit -m "chore(voice): lock tencent SDK version"
```

## 6. CI/CD集成

### 6.1 GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive  # 自动初始化子模块
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -e packages/tencent-speech-sdk
          pip install -r requirements/base.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest
```

### 6.2 Docker构建

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 复制代码（包括子模块）
COPY . .

# 初始化子模块（如果需要）
RUN git submodule update --init --recursive || true

# 安装依赖
RUN pip install -e packages/tencent-speech-sdk
RUN pip install -r requirements/base.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

## 7. 文档和规范

### 7.1 README说明

```markdown
# 腾讯语音SDK维护

本项目使用Git Submodule管理腾讯语音SDK。

## 初始化

```bash
git submodule update --init --recursive
```

## 更新SDK

```bash
git submodule update --remote vendor/tencentcloud-speech-sdk-python
git add vendor/tencentcloud-speech-sdk-python
git commit -m "chore: update tencent SDK"
```

## 锁定版本

编辑`.gitmodules`文件，指定特定版本。
```

### 7.2 开发规范

1. **版本管理**：
   - 主分支跟踪最新版本
   - 发布时锁定稳定版本

2. **更新策略**：
   - 定期检查更新（每月）
   - 重大更新需要测试
   - 小版本更新可以直接合并

3. **兼容性**：
   - 保持向后兼容
   - 重大变更需要迁移指南

## 8. 实施状态

### 8.1 已完成

✅ **Git Submodule设置**
- SDK位置：`backend/vendor/tencentcloud-speech-sdk-python`
- 已添加到`.gitmodules`

✅ **本地包包装**
- 包位置：`backend/packages/tencent-speech-sdk/`
- 已创建`setup.py`和包装模块

✅ **依赖更新**
- 已更新`backend/requirements/base.txt`
- 添加了`websocket-client==0.48`和`requests`

### 8.2 安装步骤

**首次安装**：

```bash
# 1. 初始化Git Submodule
git submodule update --init --recursive

# 2. 安装本地包
cd backend
pip install -e packages/tencent-speech-sdk

# 3. 安装其他依赖
pip install -r requirements/base.txt
```

**使用**：

```python
from tencent_speech_sdk import credential, flash_recognizer
from tencent_speech_sdk import speech_recognizer, speech_synthesizer

# 使用示例
cred = credential.Credential(secret_id, secret_key)
recognizer = flash_recognizer.FlashRecognizer(app_id, cred)
```

### 8.3 更新流程

```bash
# 更新SDK到最新版本
git submodule update --remote backend/vendor/tencentcloud-speech-sdk-python

# 检查变更
cd backend/vendor/tencentcloud-speech-sdk-python
git log --oneline -10

# 提交更新
cd ../../..
git add backend/vendor/tencentcloud-speech-sdk-python
git commit -m "chore(voice): update tencent SDK to latest"
```

## 9. 总结

### 9.1 推荐方案

**Git Submodule + 本地包包装**：
- ✅ 保持与官方同步
- ✅ 便于安装和使用
- ✅ 版本可控
- ✅ 团队协作友好
- ✅ **已实施完成**

### 9.2 项目结构

```
backend/
├── vendor/                          # Git Submodule
│   └── tencentcloud-speech-sdk-python/  # 官方SDK
├── packages/                        # 本地包
│   └── tencent-speech-sdk/
│       ├── setup.py
│       ├── README.md
│       └── tencent_speech_sdk/
│           └── __init__.py         # 自动添加SDK路径
└── requirements/
    └── base.txt                     # 已更新依赖
```

### 9.3 注意事项

- ⚠️ 团队需要了解Git Submodule
- ⚠️ 克隆项目需要`--recurse-submodules`或`git submodule update --init --recursive`
- ⚠️ 定期更新SDK版本
- ⚠️ 重大更新需要充分测试

### 9.4 下一步

1. ✅ Git Submodule已设置
2. ✅ 本地包已创建
3. ⏳ 实现腾讯ASR/TTS引擎（使用新SDK）
4. ⏳ 更新CI/CD配置
5. ⏳ 更新项目文档

---

**文档版本**: v1.1  
**创建日期**: 2024-12-19  
**最后更新**: 2024-12-19（已实施）

