# 前端环境变量配置指南

## 问题说明

Vite 的环境变量（以 `VITE_` 开头）需要在**构建时**注入，而不是运行时。这意味着：

- ✅ **构建时**：环境变量会被编译到代码中
- ❌ **运行时**：无法通过 `.env` 文件修改已构建的代码

## 解决方案

### 方案1：构建时注入（推荐）

在构建 Docker 镜像时，通过构建参数传递环境变量：

```bash
# 使用构建脚本（自动读取环境变量文件）
cd deployment/frontend/docker
./build.sh

# 或手动构建
docker build \
  --build-arg VITE_AMAP_MAPS_API_KEY=e3365b3ab88cf050d11cb9637803721e \
  --build-arg VITE_TAVILY_API_KEY=your_tavily_key \
  --build-arg VITE_API_BASE_URL=https://chat.naivehero.top \
  -t cozychat/frontend:v0.1.1 \
  -f deployment/frontend/docker/Dockerfile .
```

### 方案2：使用环境变量文件

构建脚本会自动读取以下文件（按优先级）：

1. `frontend/.env`（项目根目录）
2. `deployment/frontend.env`（部署目录）
3. `deployment/frontend.env.example`（示例文件）

在构建前，确保环境变量文件存在并包含所需变量：

```bash
# frontend/.env 或 deployment/frontend.env
VITE_AMAP_MAPS_API_KEY=e3365b3ab88cf050d11cb9637803721e
VITE_TAVILY_API_KEY=your_tavily_key
VITE_API_BASE_URL=https://chat.naivehero.top
VITE_LOG_LEVEL=info
```

### 方案3：运行时注入（不推荐，需要特殊处理）

如果需要运行时修改环境变量，需要使用运行时替换方案，但这会增加复杂性。

## 当前问题排查

### 问题：环境变量已配置但仍报错

**可能原因**：
1. 环境变量是在运行时配置的，但代码是在构建时编译的
2. 需要重新构建镜像

**解决方法**：
1. 确保环境变量在构建时可用
2. 重新构建前端镜像：
   ```bash
   cd deployment/frontend/docker
   ./build.sh
   ```
3. 重新部署：
   ```bash
   docker-compose pull frontend
   docker-compose up -d frontend
   ```

### 验证环境变量

构建后，可以通过以下方式验证：

```bash
# 进入容器
docker exec -it cozychat-frontend bash

# 检查构建后的代码（环境变量已被编译进去）
grep -r "VITE_AMAP_MAPS_API_KEY" /opt/cozychat/frontend/dist/
```

## 环境变量列表

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `VITE_API_BASE_URL` | 后端API地址 | ✅ | - |
| `VITE_AMAP_MAPS_API_KEY` | 高德地图API Key | ❌ | - |
| `VITE_TAVILY_API_KEY` | Tavily搜索API Key | ❌ | - |
| `VITE_LOG_LEVEL` | 日志级别 | ❌ | `debug`(dev) / `info`(prod) |
| `VITE_APP_VERSION` | 应用版本 | ❌ | `0.1.1` |
| `VITE_DEMO_MODE` | Demo模式 | ❌ | `false` |
| `VITE_DEMO_USERNAME` | Demo用户名 | ❌ | `demo` |
| `VITE_DEMO_PASSWORD` | Demo密码 | ❌ | `demo123` |
| `VITE_SENTRY_DSN` | Sentry DSN | ❌ | - |
| `VITE_SENTRY_ENVIRONMENT` | Sentry环境 | ❌ | `production` |

## 注意事项

1. **环境变量必须以 `VITE_` 开头**，否则不会被注入
2. **构建后无法修改**：环境变量在构建时编译到代码中，运行时无法修改
3. **敏感信息**：不要在代码中硬编码 API Key，使用环境变量
4. **版本控制**：`.env` 文件不应提交到 Git，使用 `.env.example` 作为模板

## 相关文件

- 构建脚本：`deployment/frontend/docker/build.sh`
- Dockerfile：`deployment/frontend/docker/Dockerfile`
- 安装脚本：`deployment/frontend/docker/bd_build/install.sh`
- 环境变量示例：`deployment/frontend.env.example`

