# CozyChat Docker Compose 部署指南

## 📋 目录结构

```
deployment/
├── backend/
│   └── docker/
│       ├── Dockerfile
│       ├── build.sh
│       └── bd_build/
│           ├── install.sh
│           └── 50_start_h.sh
├── frontend/
│   └── docker/
│       ├── Dockerfile
│       ├── build.sh
│       └── bd_build/
│           ├── install.sh
│           └── 50_start_h.sh
├── backend.env.example      # 后端环境变量示例
├── frontend.env.example      # 前端环境变量示例
├── docker-compose.yml        # Docker Compose 配置
└── README.md                 # 本文件
```

## 🚀 快速部署

### 前置要求

1. **Docker 和 Docker Compose** 已安装
2. **1Panel** 已安装并创建了 `1panel-network` 网络
3. **PostgreSQL** 和 **Redis** 服务已运行（在1Panel中或独立部署）
4. 确保 `1panel-network` 网络已创建：
   ```bash
   docker network create 1panel-network
   ```

### 步骤 1: 准备环境变量

#### 1.1 复制环境变量示例文件

```bash
cd deployment
cp backend.env.example backend.env
cp frontend.env.example frontend.env
```

#### 1.2 配置后端环境变量

编辑 `backend.env`，至少配置以下必需项：

```bash
# 必需配置
APP_SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
DATABASE_URL=postgresql://user:password@postgres-host:5432/cozychat
REDIS_URL=redis://redis-host:6379/0
OPENAI_API_KEY=sk-your-openai-api-key

# CORS配置（生产环境必须配置实际域名）
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

#### 1.3 配置前端环境变量

编辑 `frontend.env`，至少配置以下必需项：

```bash
# 必需配置
VITE_API_BASE_URL=https://api.your-domain.com
```

### 步骤 2: 准备代码

#### 2.1 方式一：使用本地代码（默认，推荐）

Dockerfile 默认会复制本地代码到镜像中。确保在项目根目录执行构建：

```bash
# 构建时会在项目根目录（包含backend和frontend目录）
# Dockerfile会自动复制代码到镜像
```

#### 2.2 方式二：使用Git克隆

如果要从Git仓库克隆代码，需要修改 Dockerfile：

1. **后端**：编辑 `backend/docker/Dockerfile`，注释掉 `COPY backend` 和 `COPY packages` 行
2. **前端**：编辑 `frontend/docker/Dockerfile`，注释掉 `COPY frontend` 行
3. 编辑 `install.sh`，将 `https://github.com/your-repo/CozyChat.git` 替换为实际仓库地址

### 步骤 3: 构建镜像

#### 方式一：使用 docker-compose 构建（推荐）

```bash
cd deployment
docker-compose build
```

#### 方式二：使用 build.sh 脚本构建

```bash
# 构建后端镜像
cd backend/docker
./build.sh

# 构建前端镜像
cd frontend/docker
./build.sh
```

**注意**：使用 `build.sh` 时，需要在项目根目录执行，因为 Dockerfile 的 context 是项目根目录。

### 步骤 4: 启动服务

```bash
cd deployment
docker-compose up -d
```

### 步骤 5: 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f qdrant
```

### 步骤 6: 验证部署

1. **检查服务状态**：
   ```bash
   docker-compose ps
   ```

2. **检查后端健康**：
   ```bash
   curl http://localhost:8000/health
   ```

3. **检查前端**：
   访问 `http://your-frontend-domain:5173`

## 🔧 配置说明

### 后端环境变量

详细配置说明请参考 `backend.env.example` 文件中的注释。

**关键配置项**：

- `DATABASE_URL`: PostgreSQL连接URL
- `REDIS_URL`: Redis连接URL
- `QDRANT_URL`: Qdrant连接URL（Docker Compose会自动配置为 `http://qdrant:6333`）
- `OPENAI_API_KEY`: OpenAI API密钥
- `CORS_ORIGINS`: 允许的前端域名（JSON数组格式）

### 前端环境变量

详细配置说明请参考 `frontend.env.example` 文件中的注释。

**关键配置项**：

- `VITE_API_BASE_URL`: 后端API地址（生产环境必须配置）

### 数据持久化

以下目录会自动挂载到宿主机：

- `/data/cozychat/backend/logs` - 后端日志
- `/data/cozychat/backend/data` - 后端数据（ChromaDB等）
- `/data/cozychat/frontend/dist` - 前端构建产物
- `/data/qdrant/data` - Qdrant数据

**首次部署前创建目录**：

```bash
sudo mkdir -p /data/cozychat/backend/{logs,data}
sudo mkdir -p /data/cozychat/frontend/dist
sudo mkdir -p /data/qdrant/data
sudo chmod -R 755 /data/cozychat
sudo chmod -R 755 /data/qdrant
```

## 📝 常用命令

### 启动服务

```bash
docker-compose up -d
```

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f qdrant
```

### 进入容器

```bash
# 进入后端容器
docker exec -it cozychat-backend bash

# 进入前端容器
docker exec -it cozychat-frontend bash
```

### 重新构建镜像

```bash
# 重新构建并启动
docker-compose up -d --build

# 仅重新构建特定服务
docker-compose build backend
docker-compose build frontend
```

### 清理

```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、卷
docker-compose down -v

# 删除镜像
docker rmi cozychat/backend:v0.1.0
docker rmi cozychat/frontend:v0.1.0
```

## 🔍 故障排查

### 后端无法连接数据库

1. 检查 `DATABASE_URL` 配置是否正确
2. 确保PostgreSQL服务在 `1panel-network` 网络中，或使用外部IP
3. 检查网络连接：
   ```bash
   docker exec -it cozychat-backend ping postgres-host
   ```

### 后端无法连接Redis

1. 检查 `REDIS_URL` 配置是否正确
2. 确保Redis服务在 `1panel-network` 网络中，或使用外部IP
3. 检查网络连接：
   ```bash
   docker exec -it cozychat-backend ping redis-host
   ```

### 前端无法连接后端

1. 检查 `VITE_API_BASE_URL` 配置是否正确
2. 检查后端服务是否正常运行：
   ```bash
   docker-compose logs backend
   ```
3. 检查CORS配置，确保前端域名在 `CORS_ORIGINS` 中

### Qdrant连接失败

1. 检查Qdrant服务是否正常运行：
   ```bash
   docker-compose logs qdrant
   ```
2. 检查后端 `QDRANT_URL` 配置为 `http://qdrant:6333`
3. 确保所有服务在同一网络 `1panel-network` 中

### 容器启动失败

1. 查看详细日志：
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```
2. 检查环境变量配置是否正确
3. 检查数据目录权限：
   ```bash
   ls -la /data/cozychat/
   ```

## 🔐 安全建议

1. **生产环境必须修改**：
   - `APP_SECRET_KEY`
   - `JWT_SECRET_KEY`
   - 数据库密码
   - Redis密码（如果启用）

2. **禁用Demo模式**：
   ```bash
   DEMO_MODE=false
   ```

3. **限制注册**：
   ```bash
   ALLOW_REGISTRATION=false
   ```

4. **配置CORS**：
   只允许实际的前端域名，不要使用 `["*"]`

5. **使用HTTPS**：
   生产环境必须使用HTTPS，配置反向代理（如Nginx、Caddy）

## 📚 相关文档

- [后端README](../../backend/README.md)
- [前端README](../../frontend/README.md)
- [Demo模式使用指南](../../docs/guides/Demo模式使用指南.md)

## 🆘 获取帮助

如遇问题，请查看：
1. 容器日志：`docker-compose logs`
2. 应用日志：`/data/cozychat/backend/logs/app.log`
3. 项目文档：`docs/` 目录

