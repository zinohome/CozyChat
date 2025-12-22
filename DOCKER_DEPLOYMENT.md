# CozyChat v1.1.0 Docker部署指南

**版本**: v1.1.0  
**更新时间**: 2024-12-22  
**支持特性**: 三大人格化引擎系统

---

## 📋 部署架构

### 服务组件

```
┌─────────────────────────────────────────────────────────┐
│                  CozyChat v1.1.0                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Backend    │  │  PostgreSQL  │  │    Redis     │ │
│  │  (FastAPI)   │  │  (主数据库)   │  │   (缓存)     │ │
│  └──────┬───────┘  └──────────────┘  └──────────────┘ │
│         │                                               │
│         ├─────────────────┐                            │
│         │                 │                            │
│  ┌──────▼───────┐  ┌──────▼───────┐                   │
│  │   Qdrant     │  │  Frontend    │                   │
│  │ (向量数据库)  │  │   (React)    │                   │
│  └──────────────┘  └──────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         │
                         │ HTTP/API
                         │
┌────────────────────────▼─────────────────────────────────┐
│            三大人格化引擎（外部服务）                      │
├──────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Cognee     │  │   Memobase   │  │     Mem0     │  │
│  │(知识引擎)     │  │ (用户画像)    │  │(会话记忆)     │  │
│  │  :8000       │  │  :8019       │  │  :8888       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  部署在: 192.168.66.11 或其他服务器                      │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 内存
- 至少 20GB 磁盘空间

### 步骤1: 克隆代码

```bash
git clone https://github.com/your-org/CozyChat.git
cd CozyChat
git checkout v1.1.0
```

### 步骤2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.docker.example .env

# 编辑环境变量
vim .env
```

**必须配置的变量**:

```bash
# 数据库密码
POSTGRES_PASSWORD=your_secure_password

# OpenAI API
OPENAI_API_KEY=sk-your-key-here

# 三大引擎URL（修改为实际服务器地址）
COGNEE_API_URL=http://192.168.66.11:8000
MEMOBASE_PROJECT_URL=http://192.168.66.11:8019
MEM0_API_URL=http://192.168.66.11:8888
```

### 步骤3: 构建镜像

```bash
# 方式1: 使用docker-compose构建
docker-compose -f docker-compose.v1.1.yml build

# 方式2: 手动构建后端镜像
cd backend
docker build -f Dockerfile.v1.1 -t cozychat/backend:v1.1.0 .
```

### 步骤4: 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.v1.1.yml up -d

# 查看日志
docker-compose -f docker-compose.v1.1.yml logs -f backend

# 检查服务状态
docker-compose -f docker-compose.v1.1.yml ps
```

### 步骤5: 验证部署

```bash
# 健康检查
curl http://localhost:9800/v1/health

# 三大引擎健康检查
curl http://localhost:9800/v1/health/engines

# 查看版本
curl http://localhost:9800/ | jq .
```

---

## 📦 服务说明

### 1. PostgreSQL（主数据库）

**端口**: 5432（内部）  
**数据卷**: `postgres-data`  
**用途**: 存储用户、会话、消息等业务数据

### 2. Redis（缓存）

**端口**: 6379（内部）  
**数据卷**: `redis-data`  
**用途**: 缓存和会话存储

### 3. Qdrant（向量数据库）

**端口**: 6333（HTTP）、6334（gRPC）  
**数据卷**: `qdrant-data`  
**用途**: 向量存储（通过三大引擎使用）

### 4. Backend（主应用）

**端口**: 9800 → 8000  
**镜像**: `cozychat/backend:v1.1.0`  
**功能**: 
- FastAPI应用服务器
- 三大引擎集成
- API接口提供
- WebSocket支持

---

## 🔧 配置说明

### 环境变量

#### 基础配置

| 变量 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `BACKEND_PORT` | 后端端口 | 9800 | 否 |
| `POSTGRES_PASSWORD` | 数据库密码 | - | 是 |
| `REDIS_PASSWORD` | Redis密码 | - | 是 |
| `OPENAI_API_KEY` | OpenAI密钥 | - | 是 |

#### 三大引擎配置

| 变量 | 说明 | 示例值 | 必需 |
|------|------|--------|------|
| `COGNEE_API_URL` | Cognee API地址 | http://192.168.66.11:8000 | 是 |
| `COGNEE_API_TOKEN` | Cognee认证令牌 | (可选) | 否 |
| `MEMOBASE_PROJECT_URL` | Memobase URL | http://192.168.66.11:8019 | 是 |
| `MEMOBASE_API_KEY` | Memobase密钥 | secret | 是 |
| `MEM0_API_URL` | Mem0 API地址 | http://192.168.66.11:8888 | 是 |
| `MEM0_API_KEY` | Mem0认证密钥 | (可选) | 否 |

---

## 🛠 常用命令

### 启动/停止

```bash
# 启动所有服务
docker-compose -f docker-compose.v1.1.yml up -d

# 停止所有服务
docker-compose -f docker-compose.v1.1.yml down

# 重启某个服务
docker-compose -f docker-compose.v1.1.yml restart backend

# 停止并删除数据卷（⚠️ 会删除所有数据）
docker-compose -f docker-compose.v1.1.yml down -v
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose -f docker-compose.v1.1.yml logs -f

# 查看后端日志
docker-compose -f docker-compose.v1.1.yml logs -f backend

# 查看最近100行日志
docker-compose -f docker-compose.v1.1.yml logs --tail=100 backend
```

### 进入容器

```bash
# 进入后端容器
docker exec -it cozychat-backend bash

# 进入数据库容器
docker exec -it cozychat-postgres psql -U cozychat

# 进入Redis容器
docker exec -it cozychat-redis redis-cli -a your_password
```

### 数据库操作

```bash
# 运行数据库迁移
docker exec cozychat-backend alembic upgrade head

# 创建新迁移
docker exec cozychat-backend alembic revision --autogenerate -m "description"

# 数据库备份
docker exec cozychat-postgres pg_dump -U cozychat cozychat > backup.sql

# 数据库恢复
docker exec -i cozychat-postgres psql -U cozychat cozychat < backup.sql
```

---

## 🔍 故障排查

### 问题1: 后端无法启动

**症状**: 后端容器不断重启

**排查步骤**:
```bash
# 查看日志
docker-compose logs backend

# 常见原因：
# 1. 数据库连接失败
# 2. 环境变量配置错误
# 3. 端口被占用
```

**解决方案**:
1. 检查 `.env` 文件配置
2. 确认数据库已启动: `docker-compose ps postgres`
3. 检查端口占用: `netstat -tunlp | grep 9800`

### 问题2: 三大引擎连接失败

**症状**: `/v1/health/engines` 返回引擎不健康

**排查步骤**:
```bash
# 测试引擎连接
curl http://192.168.66.11:8000/health  # Cognee
curl http://192.168.66.11:8019/health  # Memobase
curl http://192.168.66.11:8888/health  # Mem0
```

**解决方案**:
1. 确认三大引擎服务已启动
2. 检查网络连通性
3. 验证URL配置正确
4. 检查防火墙规则

### 问题3: 数据库连接错误

**症状**: `database connection failed`

**排查步骤**:
```bash
# 检查PostgreSQL状态
docker-compose ps postgres

# 测试连接
docker exec cozychat-postgres pg_isready -U cozychat
```

**解决方案**:
1. 等待数据库完全启动（约10-20秒）
2. 检查密码配置
3. 重启数据库: `docker-compose restart postgres`

### 问题4: Qdrant无法访问

**症状**: `QdrantException: Failed to connect`

**排查步骤**:
```bash
# 检查Qdrant状态
docker-compose ps qdrant

# 测试连接
curl http://localhost:6333/health
```

**解决方案**:
1. 重启Qdrant: `docker-compose restart qdrant`
2. 检查数据卷权限
3. 清理数据并重启: `docker-compose down qdrant && docker-compose up -d qdrant`

---

## 📊 性能优化

### 资源限制

在 `docker-compose.v1.1.yml` 中添加资源限制：

```yaml
services:
  backend:
    # ... 其他配置 ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 数据库优化

```yaml
services:
  postgres:
    environment:
      # ... 其他配置 ...
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_MAX_CONNECTIONS: 100
```

### Redis优化

```yaml
services:
  redis:
    command: >
      redis-server
      --appendonly yes
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
```

---

## 🔐 安全建议

### 1. 密码安全

```bash
# 生成强密码
openssl rand -base64 32
```

### 2. 网络隔离

```yaml
# 只暴露必要的端口
ports:
  - "127.0.0.1:9800:8000"  # 只允许本地访问
```

### 3. 使用secrets

```yaml
secrets:
  postgres_password:
    external: true
    
services:
  postgres:
    secrets:
      - postgres_password
```

### 4. 定期更新

```bash
# 更新镜像
docker-compose pull
docker-compose up -d
```

---

## 📦 生产部署建议

### 1. 使用Docker Swarm或Kubernetes

```bash
# Docker Swarm
docker stack deploy -c docker-compose.v1.1.yml cozychat

# Kubernetes
kubectl apply -f k8s/
```

### 2. 配置反向代理

使用Nginx或Caddy作为反向代理：

```nginx
server {
    listen 80;
    server_name api.cozychat.com;
    
    location / {
        proxy_pass http://localhost:9800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 设置自动备份

```bash
# 创建备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec cozychat-postgres pg_dump -U cozychat cozychat | gzip > backup_$DATE.sql.gz

# 添加到crontab
0 2 * * * /path/to/backup.sh
```

### 4. 监控和日志

- 使用 Prometheus + Grafana 监控
- 使用 ELK Stack 或 Loki 收集日志
- 配置告警规则

---

## 📚 相关文档

- **RELEASE_v1.1.0.md** - 版本发布说明
- **CHANGELOG.md** - 完整变更日志
- **REFACTOR_SUMMARY.md** - 架构重构总结
- **backend/README.md** - 后端文档

---

## ❓ 常见问题

### Q1: 可以不部署三大引擎吗？

A: 可以，但会失去v1.1.0的核心特性。可以设置 `memory.enabled: true` 使用旧配置。

### Q2: 如何本地部署三大引擎？

A: 参考CozyMem0项目的部署文档，或联系技术支持。

### Q3: 支持哪些数据库？

A: v1.1.0支持PostgreSQL。MySQL支持计划在v1.2.0加入。

### Q4: 如何升级到v1.1.0？

A: 参考 `PERSONALITY_CONFIG_MIGRATION.md` 配置迁移指南。

---

**最后更新**: 2024-12-22  
**Docker版本**: 20.10+  
**Docker Compose版本**: 2.0+  
**状态**: ✅ 生产就绪

