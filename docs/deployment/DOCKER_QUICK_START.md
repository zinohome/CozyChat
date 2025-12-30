# 🚀 CozyChat v1.1.0 Docker快速部署

**5分钟快速部署指南**

---

## 📋 前置要求

- ✅ Docker 20.10+
- ✅ Docker Compose 2.0+
- ✅ 4GB+ 内存
- ✅ 20GB+ 磁盘

---

## 🏃 5步快速启动

### 步骤1️⃣: 获取代码

```bash
git clone https://github.com/your-org/CozyChat.git
cd CozyChat
git checkout v1.1.0
```

### 步骤2️⃣: 配置环境

```bash
# 复制环境变量模板
cp docker.env.example .env

# 编辑配置（至少修改以下3项）
nano .env
```

**必改配置**:
```bash
POSTGRES_PASSWORD=your_strong_password     # 数据库密码
OPENAI_API_KEY=sk-your-key-here           # OpenAI密钥
COGNEE_API_URL=http://192.168.66.11:8000  # Cognee地址
```

### 步骤3️⃣: 启动服务

```bash
docker-compose -f docker-compose.v1.1.yml up -d
```

### 步骤4️⃣: 验证部署

```bash
# 等待服务启动（约30秒）
sleep 30

# 健康检查
curl http://localhost:9800/v1/health

# 预期输出：
# {"status":"healthy","version":"1.1.0"}
```

### 步骤5️⃣: 测试三大引擎

```bash
curl http://localhost:9800/v1/health/engines

# 预期输出：
# {
#   "knowledge": "healthy",
#   "userprofile": "healthy",
#   "chatmemory": "healthy"
# }
```

---

## ✅ 完成！

访问: http://localhost:9800

API文档: http://localhost:9800/docs

---

## 📊 服务状态检查

```bash
# 查看所有服务
docker-compose -f docker-compose.v1.1.yml ps

# 预期输出：
# NAME                  STATUS    PORTS
# cozychat-backend      Up        0.0.0.0:9800->8000/tcp
# cozychat-postgres     Up        5432/tcp
# cozychat-redis        Up        6379/tcp
# cozychat-qdrant       Up        0.0.0.0:6333-6334->6333-6334/tcp
```

---

## 🛠 常用命令

```bash
# 查看日志
docker-compose -f docker-compose.v1.1.yml logs -f backend

# 重启服务
docker-compose -f docker-compose.v1.1.yml restart backend

# 停止所有服务
docker-compose -f docker-compose.v1.1.yml down

# 停止并删除数据（⚠️ 危险）
docker-compose -f docker-compose.v1.1.yml down -v
```

---

## ⚠️ 注意事项

### 三大引擎服务

三大引擎（Cognee/Memobase/Mem0）需要**单独部署**。

默认配置使用测试服务器: `192.168.66.11`

**修改为你的服务器地址**:
```bash
# 编辑 .env
COGNEE_API_URL=http://your-server:8000
MEMOBASE_PROJECT_URL=http://your-server:8019
MEM0_API_URL=http://your-server:8888
```

### 端口冲突

如果端口9800被占用，修改 `.env`:
```bash
BACKEND_PORT=8800  # 改为其他端口
```

---

## 🐛 故障排查

### 问题1: 容器无法启动

```bash
# 查看日志
docker-compose -f docker-compose.v1.1.yml logs

# 常见原因：
# - 端口被占用
# - 内存不足
# - Docker未启动
```

### 问题2: 数据库连接失败

```bash
# 检查PostgreSQL
docker-compose -f docker-compose.v1.1.yml ps postgres

# 重启数据库
docker-compose -f docker-compose.v1.1.yml restart postgres

# 等待30秒后重试
```

### 问题3: 引擎连接失败

```bash
# 测试引擎连通性
curl http://192.168.66.11:8000/health
curl http://192.168.66.11:8019/health
curl http://192.168.66.11:8888/health

# 如果失败，检查：
# 1. 引擎服务是否启动
# 2. 网络是否连通
# 3. URL配置是否正确
```

---

## 📚 详细文档

- **完整部署指南**: `DOCKER_DEPLOYMENT.md`
- **版本发布说明**: `RELEASE_v1.1.0.md`
- **配置迁移**: `PERSONALITY_CONFIG_MIGRATION.md`

---

## 💬 获取帮助

- 📖 查看文档: `DOCKER_DEPLOYMENT.md`
- 🐛 提交Issue: GitHub Issues
- 💬 技术支持: 联系团队

---

**快速部署成功！享受CozyChat v1.1.0带来的三大人格化引擎系统！** 🎉

