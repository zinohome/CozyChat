# Caddy 反向代理 - 快速开始

## 功能

- ✅ 反向代理 OpenAI API，绕过 GFW 限制
- ✅ API Key 替换保护，隐藏真实 OpenAI Key
- ✅ 支持所有 OpenAI API 端点
- ✅ 自动 HTTPS（Let's Encrypt）
- ✅ WebSocket 支持（Realtime API）

## Docker 快速部署

### 1. 配置环境变量

在项目根目录创建或编辑 `.env` 文件：

```bash
# 真实的 OpenAI API Key（必须）
OPENAI_API_KEY=sk-your-real-openai-api-key-here
```

### 2. 创建日志目录

```bash
mkdir -p logs/caddy
```

### 3. 启动服务

```bash
docker-compose -f docker-compose.caddy.yml up -d
```

### 4. 查看日志

```bash
docker-compose -f docker-compose.caddy.yml logs -f caddy
```

### 5. 测试

```bash
# 使用自定义 Key 测试
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"
```

## 在项目中使用

### 后端配置

在 `backend/.env` 中：

```bash
# 使用自定义 Key（Caddy 会自动替换为真实 Key）
OPENAI_API_KEY=sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH
OPENAI_BASE_URL=https://oneapi.naivehero.top/v1
```

## 常用命令

```bash
# 启动
docker-compose -f docker-compose.caddy.yml up -d

# 停止
docker-compose -f docker-compose.caddy.yml down

# 重启
docker-compose -f docker-compose.caddy.yml restart caddy

# 查看日志
docker-compose -f docker-compose.caddy.yml logs -f caddy

# 验证配置
docker-compose -f docker-compose.caddy.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
```

## 文档

- 📖 [Docker 部署指南](docs/setup/CADDY_DOCKER_DEPLOY.md)
- 📖 [完整部署指南](docs/setup/CADDY_PROXY.md)
- 📖 [快速参考](docs/setup/CADDY_API_KEY_QUICK_START.md)

## 工作原理

```
客户端请求
  ↓
使用自定义 Key: sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH
  ↓
Caddy 检测并替换
  ↓
使用真实 Key 请求 OpenAI
  ↓
返回结果给客户端
```

## 安全说明

- ✅ 真实 OpenAI Key 只存储在服务器环境变量中
- ✅ 客户端/后端使用自定义 Key
- ✅ 即使自定义 Key 泄露，也不影响真实 Key
- ✅ 只允许使用自定义 Key 的请求通过

