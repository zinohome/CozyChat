# Caddy 反向代理配置指南

## 概述

本配置用于将 `oneapi.naivehero.top` 反向代理到 OpenAI API (`https://api.openai.com`)，以绕过 GFW 限制。

**核心安全功能**：配置实现了 API Key 替换机制，保护真实的 OpenAI API Key 不被暴露：
- 对外提供自定义 API Key：`sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH`
- 真实 OpenAI API Key 存储在服务器环境变量中
- 请求时自动将自定义 Key 替换为真实 Key

## 配置文件

项目根目录下的 `Caddyfile` 包含了完整的配置。

## 部署方式

本配置支持两种部署方式：
- **Docker 部署**（推荐）：使用 Docker Compose，简单快速
- **直接安装**：在服务器上直接安装 Caddy

### Docker 部署（推荐）

详细步骤请参考：[Caddy Docker 部署指南](./CADDY_DOCKER_DEPLOY.md)

快速开始：
```bash
# 1. 设置环境变量（在 .env 文件中）
OPENAI_API_KEY=sk-your-real-openai-key

# 2. 创建日志目录
mkdir -p logs/caddy

# 3. 启动服务
docker-compose -f docker-compose.caddy.yml up -d

# 4. 查看日志
docker-compose -f docker-compose.caddy.yml logs -f caddy
```

### 直接安装部署

## 部署步骤

### 1. 安装 Caddy

```bash
# Ubuntu/Debian
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# 或者使用官方安装脚本
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/setup.deb.sh' | sudo -E bash
sudo apt install caddy
```

### 2. 配置 DNS

确保域名 `oneapi.naivehero.top` 的 A 记录指向你的服务器 IP 地址。

```bash
# 验证 DNS 解析
dig oneapi.naivehero.top
# 或
nslookup oneapi.naivehero.top
```

### 3. 配置环境变量

**重要**：必须设置真实的 OpenAI API Key 环境变量：

```bash
# 设置真实的 OpenAI API Key（必须）
export OPENAI_API_KEY="sk-your-real-openai-api-key-here"

# 可选：如果使用环境变量存储自定义Key（默认已在配置文件中硬编码）
export CUSTOM_API_KEY="sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 将环境变量添加到系统环境（持久化）
echo 'export OPENAI_API_KEY="sk-your-real-openai-api-key-here"' | sudo tee -a /etc/environment

# 或者添加到 Caddy 服务环境（推荐）
sudo mkdir -p /etc/systemd/system/caddy.service.d
sudo tee /etc/systemd/system/caddy.service.d/environment.conf <<EOF
[Service]
Environment="OPENAI_API_KEY=sk-your-real-openai-api-key-here"
EOF
```

### 4. 复制配置文件

```bash
# 将 Caddyfile 复制到 Caddy 配置目录
sudo cp Caddyfile /etc/caddy/Caddyfile

# 或者如果 Caddy 安装在用户目录
cp Caddyfile ~/.config/caddy/Caddyfile
```

### 5. 创建日志目录（可选）

```bash
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
```

### 6. 测试配置

```bash
# 验证配置文件语法
sudo caddy validate --config /etc/caddy/Caddyfile

# 或使用相对路径
caddy validate --config ./Caddyfile
```

### 7. 启动 Caddy

**注意**：如果使用 systemd，需要重新加载配置以应用环境变量：

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload
```

```bash
# 使用 systemd（推荐）
sudo systemctl enable caddy
sudo systemctl start caddy
sudo systemctl status caddy

# 或直接运行（用于测试）
sudo caddy run --config /etc/caddy/Caddyfile
```

### 8. 验证代理

```bash
# 测试 API 端点（使用自定义 API Key）
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 应该返回模型列表
# 注意：这里使用的是自定义Key，Caddy会自动替换为真实的OpenAI Key

# 测试使用错误Key（应该返回401）
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer wrong-key"
# 应该返回: Unauthorized: Invalid API Key
```

## 配置说明

### 主要功能

1. **反向代理**: 将所有请求转发到 `https://api.openai.com`
2. **API Key 替换**: 自动将自定义 Key 替换为真实 OpenAI Key，保护真实 Key 不被暴露
3. **请求头转发**: 自动转发 `Authorization`、`Content-Type` 等必要请求头
4. **WebSocket 支持**: 支持 OpenAI Realtime API 的 WebSocket 连接
5. **健康检查**: 自动检查上游服务健康状态
6. **CORS 支持**: 可选的前端直接访问支持
7. **访问控制**: 只允许使用自定义 Key 的请求通过，拒绝其他请求

### API Key 替换机制

配置实现了安全的 API Key 替换：

1. **自定义 Key**（对外暴露）：
   - Key: `sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH`
   - 可以在客户端、前端代码中安全使用
   - 即使泄露也不会影响真实的 OpenAI Key

2. **真实 Key**（服务器端）：
   - 存储在环境变量 `OPENAI_API_KEY` 中
   - 永远不会暴露给客户端
   - 只在服务器内部使用

3. **工作流程**：
   ```
   客户端请求 → 使用自定义Key → Caddy检测并替换 → 使用真实Key请求OpenAI → 返回结果
   ```

### 配置选项

#### 日志记录

```caddy
log {
    output file /var/log/caddy/access.log
    format json
}
```

#### 健康检查

```caddy
health_uri /v1/models
health_interval 30s
health_timeout 5s
```

#### CORS 配置

如果不需要前端直接访问，可以删除 CORS 相关配置。

## 简化配置（无 CORS）

如果你不需要 CORS 支持，可以使用以下简化配置：

```caddy
oneapi.naivehero.top {
    reverse_proxy https://api.openai.com {
        header_up Host {upstream_hostport}
        transport http {
            versions 1.1 2
        }
    }
}
```

## 支持的 OpenAI API 端点

配置支持所有 OpenAI API 端点：

- ✅ `/v1/chat/completions` - 聊天补全
- ✅ `/v1/completions` - 文本补全
- ✅ `/v1/embeddings` - 嵌入向量
- ✅ `/v1/models` - 模型列表
- ✅ `/v1/audio/transcriptions` - 语音转文本
- ✅ `/v1/audio/speech` - 文本转语音
- ✅ `/v1/realtime` - Realtime API (WebSocket)
- ✅ `/v1/realtime/client_secrets` - Realtime 客户端密钥
- ✅ 其他所有 `/v1/*` 端点

## 在项目中使用

### 后端配置

在 `backend/config/models/openai.yaml` 中已经配置：

```yaml
base_url: "https://oneapi.naivehero.top/v1"
```

### 环境变量

#### 后端应用环境变量

在 `backend/.env` 文件中配置：

```bash
# 使用自定义Key（Caddy会自动替换为真实Key）
OPENAI_API_KEY=sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH
OPENAI_BASE_URL=https://oneapi.naivehero.top/v1
```

**重要说明**：
- 后端应用使用自定义 Key，而不是真实的 OpenAI Key
- Caddy 会自动将自定义 Key 替换为真实 Key
- 这样即使后端代码泄露，也不会暴露真实的 OpenAI Key

#### Caddy 服务器环境变量

在 Caddy 服务器上设置（见步骤3）：

```bash
# 真实的 OpenAI API Key（只在服务器上设置）
export OPENAI_API_KEY="sk-your-real-openai-api-key-here"
```

## 故障排查

### 1. 检查 Caddy 状态

```bash
sudo systemctl status caddy
sudo journalctl -u caddy -f
```

### 2. 检查日志

```bash
sudo tail -f /var/log/caddy/access.log
```

### 3. 测试连接

```bash
# 测试基本连接（应该返回401，因为没有提供Key）
curl -I https://oneapi.naivehero.top/v1/models

# 测试使用自定义Key（应该成功）
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 测试使用错误Key（应该返回401）
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer wrong-key"
```

### 4. 检查环境变量

```bash
# 检查 Caddy 是否能读取环境变量
sudo systemctl show caddy --property=Environment

# 或者在 Caddy 日志中查看
sudo journalctl -u caddy | grep -i "api_key\|error"
```

### 5. 检查 DNS

```bash
dig oneapi.naivehero.top
```

### 6. 检查防火墙

```bash
# 确保 80 和 443 端口开放
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## 安全建议

1. **使用 HTTPS**: Caddy 会自动申请 Let's Encrypt 证书
2. **API Key 保护**: 
   - ✅ 真实 OpenAI Key 只存储在服务器环境变量中
   - ✅ 客户端/后端使用自定义 Key
   - ✅ 即使自定义 Key 泄露，也不会影响真实 Key
3. **限制访问**: 如果需要，可以添加 IP 白名单
4. **监控日志**: 定期检查访问日志，监控异常请求
5. **环境变量安全**: 
   - 不要将 `OPENAI_API_KEY` 提交到 Git
   - 使用系统环境变量或密钥管理服务
6. **定期轮换**: 定期更换自定义 Key（修改 Caddyfile 并重启服务）

## 性能优化

1. **启用缓存**: 对于模型列表等静态数据
2. **连接池**: Caddy 自动管理连接池
3. **压缩**: Caddy 自动启用 gzip 压缩

## 相关文档

- [Caddy 官方文档](https://caddyserver.com/docs/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)

