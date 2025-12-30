# 混合内容（Mixed Content）错误修复指南

## 问题描述

在 HTTPS 页面中请求 HTTP 资源时，浏览器会阻止这种混合内容请求，导致 API 调用失败。

错误信息：
```
Mixed Content: The page at 'https://chat.naivehero.top/login' was loaded over HTTPS, 
but requested an insecure XMLHttpRequest endpoint 'http://chat.naivehero.top:9800/v1/users/login'. 
This request has been blocked; the content must be served over HTTPS.
```

## 问题原因

1. **前端页面通过 HTTPS 访问**：`https://chat.naivehero.top/login`
2. **API 地址配置为 HTTP**：`http://chat.naivehero.top:9800`
3. **浏览器安全策略**：HTTPS 页面不能请求 HTTP 资源

## 解决方案

### 方案1：使用 HTTPS API 地址（推荐）

前端应该通过 Caddy 反向代理访问 API，而不是直接访问后端端口。

**正确配置**：
```bash
# frontend/.env 或 deployment/frontend.env
VITE_API_BASE_URL=https://chat.naivehero.top
```

**错误配置**：
```bash
# ❌ 错误：使用 HTTP 或直接访问端口
VITE_API_BASE_URL=http://chat.naivehero.top:9800
```

### 方案2：使用相对路径（如果前后端在同一域名）

如果前后端都通过 `chat.naivehero.top` 访问，可以使用相对路径：

```bash
# 使用相对路径（自动使用当前页面的协议和域名）
VITE_API_BASE_URL=
```

这样前端会使用当前页面的协议（HTTPS）和域名。

## 架构说明

根据 Caddyfile 配置：

```
用户浏览器 (HTTPS)
    ↓
https://chat.naivehero.top
    ↓
Caddy 反向代理
    ├─ /v1/* → 后端 9800 端口（HTTP）
    └─ 其他 → 前端 8000 端口（HTTP）
```

**关键点**：
- 用户通过 HTTPS 访问 `chat.naivehero.top`
- Caddy 处理 SSL/TLS，内部转发到后端 HTTP 服务
- 前端应该使用 HTTPS 地址，让 Caddy 处理代理

## 修复步骤

### 1. 更新环境变量

在 `frontend/.env` 或 `deployment/frontend.env` 中：

```bash
# 使用 HTTPS 地址（通过 Caddy 代理）
VITE_API_BASE_URL=https://chat.naivehero.top
```

### 2. 重新构建前端镜像

```bash
cd deployment/frontend/docker
./build.sh
```

### 3. 重新部署

```bash
docker-compose pull frontend
docker-compose up -d frontend
```

## 验证修复

修复后，检查浏览器控制台：
- ✅ 不应该再有混合内容错误
- ✅ API 请求应该使用 HTTPS
- ✅ 请求 URL 应该是 `https://chat.naivehero.top/v1/...`

## 注意事项

1. **必须使用 HTTPS**：生产环境必须使用 HTTPS，不能使用 HTTP
2. **不需要端口号**：通过 Caddy 代理时，使用标准 HTTPS 端口（443）
3. **Caddy 配置**：确保 Caddyfile 正确配置了反向代理规则
4. **环境变量注入**：环境变量必须在构建时注入，运行时无法修改

## 相关文件

- 前端环境变量示例：`deployment/frontend.env.example`
- Caddy 配置：`Caddyfile.prod`
- API 客户端：`frontend/src/services/api.ts`

