# Git Clone 无需登录配置说明

## 📋 方案概述

Docker 构建时优先从 Git 克隆代码，避免复制本地的 `venv`、`node_modules` 等不需要的文件。

## 🔧 配置方法

### 方案1: 使用公开仓库（推荐，最简单）

如果仓库是公开的，直接配置仓库地址即可，无需任何认证：

```bash
# 在 deployment 目录下创建 .env 文件（或设置环境变量）
export GIT_REPO_URL=https://github.com/zinohome/CozyChat.git

# 构建时使用
docker-compose build
```

**优点**：
- ✅ 无需配置认证
- ✅ 最简单直接
- ✅ 适合开源项目

### 方案2: 使用 Personal Access Token（私有仓库）

对于私有仓库，可以使用 Personal Access Token：

#### 2.1 创建 Personal Access Token

1. 登录 GitHub/GitLab
2. 进入 Settings → Developer settings → Personal access tokens
3. 创建 token（需要 `repo` 权限）
4. 复制 token

#### 2.2 配置 Token

**方式A：在 URL 中包含 Token**

```bash
# 在 deployment 目录下创建 .env 文件
GIT_REPO_URL=https://YOUR_TOKEN@github.com/zinohome/CozyChat.git
```

**方式B：使用环境变量（更安全）**

修改 `install.sh`，添加 token 支持：

```bash
# 在 install.sh 中添加
if [ -n "$GIT_TOKEN" ]; then
    GIT_REPO_URL=$(echo $GIT_REPO_URL | sed "s|https://|https://${GIT_TOKEN}@|")
fi
```

然后在 `.env` 中配置：

```bash
GIT_REPO_URL=https://github.com/zinohome/CozyChat.git
GIT_TOKEN=ghp_your_token_here
```

### 方案3: 使用 SSH Key（私有仓库，推荐）

#### 3.1 生成 SSH Key

```bash
ssh-keygen -t ed25519 -C "docker-build" -f ~/.ssh/docker_build_key
```

#### 3.2 将公钥添加到 Git 服务

```bash
cat ~/.ssh/docker_build_key.pub
# 复制公钥内容，添加到 GitHub/GitLab 的 SSH Keys
```

#### 3.3 修改 Dockerfile 使用 SSH

修改 `Dockerfile`：

```dockerfile
# 复制 SSH key（仅在构建时使用）
ARG SSH_PRIVATE_KEY
RUN mkdir -p /root/.ssh && \
    echo "$SSH_PRIVATE_KEY" > /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519 && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# 修改 install.sh 使用 SSH URL
# git clone git@github.com:zinohome/CozyChat.git .
```

#### 3.4 构建时传入 SSH Key

```bash
# 读取私钥并传入构建参数
export SSH_PRIVATE_KEY=$(cat ~/.ssh/docker_build_key)

docker build \
  --build-arg SSH_PRIVATE_KEY="$SSH_PRIVATE_KEY" \
  --build-arg GIT_REPO_URL=git@github.com:zinohome/CozyChat.git \
  -t cozychat/backend:v0.1.0 \
  -f deployment/backend/docker/Dockerfile \
  .
```

**注意**：使用 SSH 时，需要修改 `install.sh` 中的仓库地址为 SSH 格式。

### 方案4: 使用 Git Credential Helper（不推荐）

可以在 Dockerfile 中配置 credential helper，但需要将凭证嵌入镜像，安全性较差。

## 🚀 推荐配置

### 公开仓库配置

在 `deployment` 目录下创建 `.env` 文件：

```bash
# Git仓库配置
GIT_REPO_URL=https://github.com/zinohome/CozyChat.git
```

然后构建：

```bash
docker-compose build
```

### 私有仓库配置（使用 Token）

在 `deployment` 目录下创建 `.env` 文件：

```bash
# Git仓库配置（Token在URL中）
GIT_REPO_URL=https://YOUR_TOKEN@github.com/zinohome/CozyChat.git
```

**安全提示**：
- ⚠️ 不要将包含 token 的 `.env` 文件提交到 Git
- ✅ 使用 `.gitignore` 忽略 `.env` 文件
- ✅ 生产环境使用环境变量或密钥管理服务

## 📝 当前实现

当前 `install.sh` 已配置：

1. **禁用交互式提示**：
   ```bash
   export GIT_TERMINAL_PROMPT=0
   export GIT_ASKPASS=/bin/echo
   ```

2. **支持环境变量配置**：
   ```bash
   git clone ${GIT_REPO_URL:-https://github.com/zinohome/CozyChat.git}
   ```

3. **自动降级**：
   - 如果 Git 克隆失败，自动使用 COPY 的代码（如果存在）

## 🔍 验证配置

### 测试公开仓库

```bash
# 设置公开仓库地址
export GIT_REPO_URL=https://github.com/zinohome/CozyChat.git

# 测试克隆（不需要认证）
git clone $GIT_REPO_URL /tmp/test-clone
```

### 测试私有仓库（使用 Token）

```bash
# 设置带 Token 的仓库地址
export GIT_REPO_URL=https://YOUR_TOKEN@github.com/zinohome/CozyChat.git

# 测试克隆
git clone $GIT_REPO_URL /tmp/test-clone
```

## ⚠️ 注意事项

1. **公开仓库**：最简单，无需任何配置
2. **私有仓库 + Token**：Token 会出现在 URL 中，注意安全
3. **私有仓库 + SSH**：最安全，但配置较复杂
4. **备选方案**：如果 Git 克隆失败，会自动使用 COPY 的代码（需要取消注释 Dockerfile 中的 COPY）

## 🔐 安全建议

1. **不要提交敏感信息**：
   - `.env` 文件添加到 `.gitignore`
   - Token 不要硬编码在代码中

2. **使用环境变量**：
   - 在 CI/CD 中通过环境变量传入
   - 使用密钥管理服务（如 1Panel 的密钥管理）

3. **定期轮换 Token**：
   - 定期更新 Personal Access Token
   - 使用最小权限原则

## 📚 相关文件

- `deployment/backend/docker/bd_build/install.sh` - 后端安装脚本
- `deployment/frontend/docker/bd_build/install.sh` - 前端安装脚本
- `deployment/docker-compose.yml` - Docker Compose 配置

