# CozyChat 一体化部署指南

**一条命令，拉起所有服务。**

包含：前端 Nginx、后端 FastAPI、PostgreSQL、Redis、Qdrant。

---

## 快速开始

### 前提条件
- Docker + Docker Compose v2（`docker compose` 命令可用）
- 服务器上已克隆本仓库

### 第一步：创建配置文件

```bash
cd CozyChat/deployment
cp simple.env.example .env
```

打开 `.env`，**只需修改以下 4 项**：

| 变量 | 说明 |
|------|------|
| `POSTGRES_PASSWORD` | PostgreSQL 密码（任意强密码） |
| `JWT_SECRET_KEY` | JWT 签名密钥（32位以上随机字符串） |
| `APP_SECRET_KEY` | 应用密钥（32位以上随机字符串） |
| `OPENAI_API_KEY` | 你的 OpenAI API Key |

> 生成随机密钥：`openssl rand -hex 32`

### 第二步：启动所有服务

**在项目根目录** 执行：

```bash
cd CozyChat  # 项目根目录

docker compose \
  -f deployment/docker-compose.simple.yml \
  --env-file deployment/.env \
  up -d --build
```

首次构建约需 **5-15 分钟**（下载依赖和 PyTorch CPU 版本）。

### 第三步：访问

```
http://服务器IP
```

---

## 服务管理

```bash
# 查看所有服务状态
docker compose -f deployment/docker-compose.simple.yml ps

# 查看后端日志
docker logs cozychat-backend --tail 50 -f

# 查看前端 Nginx 日志
docker logs cozychat-frontend --tail 20 -f

# 重启某个服务
docker compose -f deployment/docker-compose.simple.yml restart backend

# 停止所有服务
docker compose -f deployment/docker-compose.simple.yml down

# 停止并清除数据（⚠️ 会删除数据库）
docker compose -f deployment/docker-compose.simple.yml down -v
```

---

## HTTPS 配置（可选）

如果需要 HTTPS，在服务器的 Caddy 中添加：

```
chat.yourdomain.com {
    reverse_proxy 127.0.0.1:80
}
```

**无需任何 CORS 配置**——前端 Nginx 已经在内部代理 API，所有请求同源。

---

## 架构说明

```
用户请求
   │
   ▼
前端 Nginx :80（唯一对外端口）
   ├── GET /v1/* ──► 代理到 backend:8000
   ├── WS  /ws/*  ──► 代理到 backend:8000
   └── 其他       ──► 服务 /usr/share/nginx/html (Vue SPA)

内部网络 (cozychat-network):
  backend  ←→  postgres:5432
  backend  ←→  redis:6379
  backend  ←→  qdrant:6333
```

前端 JS 使用**相对路径**（`/v1/...`）调用 API，由 Nginx 转发，完全同源，**无 CORS 问题**。

---

## 常见问题

**Q：后端启动失败怎么办？**
```bash
docker logs cozychat-backend --tail 100
```
通常是 PostgreSQL 还没就绪，等 30 秒后 Docker 会自动重启。

**Q：如何修改配置？**
编辑 `deployment/.env`，然后：
```bash
docker compose -f deployment/docker-compose.simple.yml --env-file deployment/.env up -d
```

**Q：如何迁移旧数据库数据？**
```bash
# 从旧 PG 导出
pg_dump -h 旧PG地址 -U cozychat cozychat > backup.sql

# 导入到新 PG
docker exec -i cozychat-postgres psql -U cozychat -d cozychat < backup.sql
```

**Q：前端构建参数如何自定义？**
在 `deployment/.env` 中设置 `VITE_AMAP_MAPS_API_KEY` 等变量，重新 `--build` 即可。
