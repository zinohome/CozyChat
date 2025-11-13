# Caddy Docker 部署指南

## 概述

本指南介绍如何使用 Docker 部署 Caddy 反向代理服务，实现 OpenAI API 的代理和 API Key 保护。

## 前置要求

- Docker 和 Docker Compose 已安装
- 域名 `oneapi.naivehero.top` 已解析到服务器 IP
- 服务器开放 80 和 443 端口

## 快速开始

### 1. 准备环境变量

创建或编辑 `.env` 文件（在项目根目录）：

```bash
# 真实的 OpenAI API Key（必须设置）
OPENAI_API_KEY=sk-your-real-openai-api-key-here

# 可选：自定义 API Key（默认已在 Caddyfile 中硬编码）
CUSTOM_API_KEY=sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH
```

### 2. 创建日志目录

```bash
mkdir -p logs/caddy
```

### 3. 启动 Caddy 服务

```bash
# 使用独立的 docker-compose.caddy.yml
docker-compose -f docker-compose.caddy.yml up -d

# 查看日志
docker-compose -f docker-compose.caddy.yml logs -f caddy

# 查看状态
docker-compose -f docker-compose.caddy.yml ps
```

### 4. 验证部署

```bash
# 测试 API 端点（使用自定义 Key）
curl https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 应该返回模型列表
```

## 配置说明

### Docker Compose 配置

`docker-compose.caddy.yml` 包含以下配置：

- **镜像**: `caddy:2-alpine`（轻量级 Alpine 版本）
- **端口映射**: 
  - `80:80` - HTTP
  - `443:443` - HTTPS
  - `443:443/udp` - HTTP/3 (QUIC)
- **卷挂载**:
  - `./Caddyfile:/etc/caddy/Caddyfile:ro` - 配置文件（只读）
  - `caddy_data:/data` - Caddy 数据（证书、缓存等）
  - `caddy_config:/config` - Caddy 配置
  - `./logs/caddy:/var/log/caddy` - 日志目录
- **环境变量**: 从 `.env` 文件读取 `OPENAI_API_KEY`

### 环境变量

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | 真实的 OpenAI API Key | ✅ 是 | - |
| `CUSTOM_API_KEY` | 自定义 API Key | ❌ 否 | `sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH` |

## 常用命令

### 启动和停止

```bash
# 启动服务
docker-compose -f docker-compose.caddy.yml up -d

# 停止服务
docker-compose -f docker-compose.caddy.yml down

# 重启服务
docker-compose -f docker-compose.caddy.yml restart caddy

# 停止并删除卷（清理数据）
docker-compose -f docker-compose.caddy.yml down -v
```

### 查看日志

```bash
# 实时查看日志
docker-compose -f docker-compose.caddy.yml logs -f caddy

# 查看最近 100 行日志
docker-compose -f docker-compose.caddy.yml logs --tail=100 caddy

# 查看访问日志
tail -f logs/caddy/access.log
```

### 验证配置

```bash
# 进入容器验证配置
docker-compose -f docker-compose.caddy.yml exec caddy caddy validate --config /etc/caddy/Caddyfile

# 查看容器环境变量
docker-compose -f docker-compose.caddy.yml exec caddy env | grep OPENAI
```

### 更新配置

```bash
# 修改 Caddyfile 后，重新加载配置
docker-compose -f docker-compose.caddy.yml exec caddy caddy reload --config /etc/caddy/Caddyfile

# 或者重启容器
docker-compose -f docker-compose.caddy.yml restart caddy
```

## 与主项目集成

### 方式1：独立部署（推荐）

Caddy 作为独立服务运行，不依赖其他服务：

```bash
# 只启动 Caddy
docker-compose -f docker-compose.caddy.yml up -d
```

### 方式2：合并到主 docker-compose.yml

如果需要，可以将 Caddy 添加到主 `docker-compose.yml`：

```yaml
services:
  # ... 其他服务 ...
  
  caddy:
    image: caddy:2-alpine
    container_name: cozychat_caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
      - ./logs/caddy:/var/log/caddy
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CUSTOM_API_KEY=${CUSTOM_API_KEY:-sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH}
    networks:
      - default

volumes:
  # ... 其他卷 ...
  caddy_data:
  caddy_config:
```

然后使用：

```bash
# 启动所有服务（包括 Caddy）
docker-compose up -d

# 只启动 Caddy
docker-compose up -d caddy
```

## 故障排查

### 1. 容器无法启动

```bash
# 查看容器日志
docker-compose -f docker-compose.caddy.yml logs caddy

# 检查配置文件语法
docker-compose -f docker-compose.caddy.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
```

### 2. 环境变量未生效

```bash
# 检查环境变量
docker-compose -f docker-compose.caddy.yml exec caddy env | grep OPENAI

# 确认 .env 文件存在且包含 OPENAI_API_KEY
cat .env | grep OPENAI_API_KEY
```

### 3. 证书申请失败

```bash
# 检查端口是否开放
sudo netstat -tlnp | grep -E ':(80|443)'

# 检查 DNS 解析
dig oneapi.naivehero.top

# 查看 Caddy 日志
docker-compose -f docker-compose.caddy.yml logs caddy | grep -i cert
```

### 4. API Key 替换不工作

```bash
# 测试请求
curl -v https://oneapi.naivehero.top/v1/models \
  -H "Authorization: Bearer sk-1s98FFGBvUwEs0uH5yKQDxsxLuv9qNa4P1WadrANek8hh8TH"

# 检查访问日志
tail -f logs/caddy/access.log
```

### 5. 权限问题

```bash
# 确保日志目录权限正确
sudo chown -R $USER:$USER logs/caddy
chmod 755 logs/caddy
```

## 安全建议

1. **保护 .env 文件**：
   ```bash
   chmod 600 .env
   ```

2. **不要提交 .env 到 Git**：
   ```bash
   # 确保 .env 在 .gitignore 中
   echo ".env" >> .gitignore
   ```

3. **定期更新 Caddy 镜像**：
   ```bash
   docker-compose -f docker-compose.caddy.yml pull caddy
   docker-compose -f docker-compose.caddy.yml up -d caddy
   ```

4. **监控日志**：
   ```bash
   # 设置日志轮转
   # 在 docker-compose.caddy.yml 中已配置 max-size 和 max-file
   ```

## 性能优化

1. **使用 HTTP/3 (QUIC)**：配置已包含 UDP 端口映射
2. **启用缓存**：Caddy 自动缓存证书和配置
3. **连接复用**：Caddy 自动管理连接池

## 备份和恢复

### 备份 Caddy 数据

```bash
# 备份卷数据
docker run --rm -v cozychat_caddy_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/caddy_data_backup.tar.gz -C /data .

# 备份配置
cp Caddyfile Caddyfile.backup
```

### 恢复数据

```bash
# 恢复卷数据
docker run --rm -v cozychat_caddy_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/caddy_data_backup.tar.gz -C /data
```

## 相关文档

- 完整部署指南：`docs/setup/CADDY_PROXY.md`
- 快速参考：`docs/setup/CADDY_API_KEY_QUICK_START.md`
- Caddy 配置文件：`Caddyfile`
- Docker Compose 配置：`docker-compose.caddy.yml`

