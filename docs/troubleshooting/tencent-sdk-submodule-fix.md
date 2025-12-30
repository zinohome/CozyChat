# Tencent Speech SDK Submodule 修复指南

## 问题描述

在生产环境部署后，STT（语音转文字）功能返回500错误，错误信息：

```
Failed to import Tencent Speech SDK modules: No module named 'common'
SDK path: /opt/cozychat/backend/vendor/tencentcloud-speech-sdk-python
Please ensure the SDK is properly installed via git submodule.
```

## 问题原因

Tencent Speech SDK 通过 Git Submodule 管理，位于 `backend/vendor/tencentcloud-speech-sdk-python`。如果部署时没有初始化 submodule，该目录会不存在或为空，导致导入失败。

## 解决方案

### 方案1：重新构建镜像（推荐）

如果使用 Docker 部署，重新构建镜像时会自动初始化 submodule（已修复部署脚本）：

```bash
cd deployment/backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

### 方案2：手动修复现有容器

如果无法重新构建，可以在现有容器中手动初始化 submodule：

```bash
# 进入容器
docker exec -it <container_name> bash

# 进入项目目录
cd /opt/cozychat

# 如果.git目录存在，初始化submodule
if [ -d ".git" ]; then
    git submodule update --init --recursive
else
    # 如果.git目录不存在，需要手动克隆submodule
    cd backend
    git clone https://github.com/TencentCloud/tencentcloud-speech-sdk-python.git vendor/tencentcloud-speech-sdk-python
fi

# 验证SDK是否存在
ls -la backend/vendor/tencentcloud-speech-sdk-python/common/

# 重启服务
exit
docker restart <container_name>
```

### 方案3：使用Dockerfile COPY（如果使用Dockerfile部署）

如果使用 Dockerfile 直接构建，确保在构建时包含 submodule：

```dockerfile
# 在Dockerfile中添加
RUN git submodule update --init --recursive
```

或者在构建时使用：

```bash
docker build --recursive-submodules .
```

## 验证修复

修复后，可以通过以下方式验证：

1. **检查vendor目录**：
```bash
ls -la backend/vendor/tencentcloud-speech-sdk-python/common/
```

应该看到 `__init__.py`, `credential.py`, `log.py`, `utils.py` 等文件。

2. **测试导入**：
```python
# 在Python中测试
from tencent_speech_sdk import credential
print("✅ SDK导入成功")
```

3. **测试STT API**：
```bash
curl -X POST https://chat.naivehero.top/v1/audio/transcriptions \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.wav"
```

## 预防措施

1. **部署脚本已修复**：`deployment/backend/docker/bd_build/install.sh` 现在会自动初始化 submodule
2. **使用 `--recurse-submodules` 克隆**：部署脚本现在使用 `git clone --recurse-submodules` 来确保 submodule 被正确初始化
3. **验证步骤**：安装脚本会验证 vendor 目录是否存在，如果不存在会尝试初始化

## 相关文件

- 部署脚本：`deployment/backend/docker/bd_build/install.sh`
- SDK包装包：`backend/packages/tencent-speech-sdk/`
- SDK源码：`backend/vendor/tencentcloud-speech-sdk-python/` (Git Submodule)

## 注意事项

- 如果使用 Git 克隆项目，必须使用 `--recurse-submodules` 参数或运行 `git submodule update --init --recursive`
- vendor 目录是 Git Submodule，不能直接复制，必须通过 Git 初始化
- 如果 vendor 目录为空，Python 无法找到 `common` 模块，会导致导入失败

