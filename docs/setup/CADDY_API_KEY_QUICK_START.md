# Caddy API Key 替换功能快速指南

## 功能概述

Caddy 配置实现了 API Key 替换机制，保护真实的 OpenAI API Key：

- **自定义 Key**（对外使用）：`sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH`
- **真实 Key**（服务器端）：存储在环境变量 `OPENAI_API_KEY` 中

## 部署方式

### Docker 部署（推荐）

```bash
# 1. 在 .env 文件中设置环境变量
OPENAI_API_KEY=sk-your-real-openai-key

# 2. 创建日志目录
mkdir -p logs/caddy

# 3. 启动服务
docker-compose -f docker-compose.caddy.yml up -d

# 4. 测试
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"
```

详细步骤请参考：[Caddy Docker 部署指南](../setup/CADDY_DOCKER_DEPLOY.md)

### 直接安装部署

## 快速部署

### 1. 设置环境变量

```bash
# 在 Caddy 服务器上设置真实的 OpenAI API Key
export OPENAI_API_KEY="sk-your-real-openai-key"

# 持久化到 systemd（推荐）
sudo mkdir -p /etc/systemd/system/caddy.service.d
sudo tee /etc/systemd/system/caddy.service.d/environment.conf <<EOF
[Service]
Environment="OPENAI_API_KEY=sk-your-real-openai-key"
EOF

sudo systemctl daemon-reload
```

### 2. 部署配置

```bash
# 复制配置文件
sudo cp Caddyfile /etc/caddy/Caddyfile

# 验证配置
sudo caddy validate --config /etc/caddy/Caddyfile

# 重启 Caddy
sudo systemctl restart caddy
```

### 3. 测试

```bash
# 使用自定义Key测试（应该成功）
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 使用错误Key测试（应该返回401）
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer wrong-key"
```

## 在项目中使用

### 后端配置

在 `backend/.env` 中：

```bash
# 使用自定义Key（不是真实的OpenAI Key）
OPENAI_API_KEY=sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH
OPENAI_BASE_URL=https://oneapi.naivehero.top/v1
```

### 前端配置（如果需要）

```typescript
// 使用自定义Key
const API_KEY = 'sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH';
const BASE_URL = 'https://oneapi.naivehero.top/v1';
```

## 工作原理

```
┌─────────┐                    ┌─────────┐                    ┌──────────┐
│ 客户端  │                    │ Caddy   │                    │ OpenAI   │
│         │                    │ 代理    │                    │ API      │
└────┬────┘                    └────┬────┘                    └────┬─────┘
     │                              │                              │
     │ 请求 + 自定义Key              │                              │
     ├─────────────────────────────>│                              │
     │                              │ 检测到自定义Key              │
     │                              │ 替换为真实Key                │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │ 响应                         │
     │                              │<─────────────────────────────┤
     │ 响应                         │                              │
     │<─────────────────────────────┤                              │
     │                              │                              │
```

## 安全优势

1. ✅ **真实 Key 不暴露**：只在服务器环境变量中
2. ✅ **自定义 Key 可泄露**：即使泄露也不影响真实 Key
3. ✅ **访问控制**：只允许使用自定义 Key 的请求
4. ✅ **易于轮换**：更换自定义 Key 只需修改配置

## 更换自定义 Key

如果需要更换自定义 Key：

1. 修改 `Caddyfile` 中的 Key
2. 重启 Caddy：`sudo systemctl restart caddy`
3. 更新项目中的 Key 配置

## 故障排查

### Key 替换不工作

```bash
# 检查环境变量是否设置
sudo systemctl show caddy --property=Environment

# 检查 Caddy 日志
sudo journalctl -u caddy -f
```

### 401 错误

- 确认使用的是正确的自定义 Key
- 检查 Caddyfile 中的 Key 配置是否正确
- 确认 Caddy 服务已重启

## 相关文档

- 完整部署指南：`docs/setup/CADDY_PROXY.md`
- Caddy 配置文件：`Caddyfile`

