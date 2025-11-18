# 微信浏览器聊天问题诊断与修复

## 问题描述

在微信浏览器中无法进行聊天，可能表现为：
- 网络连接失败
- CORS 错误
- 请求被阻止
- 无法建立 WebSocket/WebRTC 连接

## 可能原因分析

### 1. CORS 配置问题 ⚠️ **最可能的原因**

**问题**：
- 生产环境使用配置的 `cors_origins`，如果微信浏览器的域名不在列表中，会被阻止
- 微信浏览器对 CORS 更严格

**当前配置**（`backend/app/main.py`）：
```python
if settings.is_development:
    cors_origins = ["*"]  # 开发环境允许所有来源
    cors_allow_credentials = False
else:
    cors_origins = settings.cors_origins  # 生产环境使用配置的列表
    cors_allow_credentials = True
```

**检查方法**：
1. 查看 `CORS_ORIGINS` 环境变量是否包含微信访问的域名
2. 检查浏览器控制台的 CORS 错误信息

### 2. HTTPS 要求

**问题**：
- 微信浏览器要求 HTTPS 连接
- 如果使用 HTTP，会被阻止

**检查方法**：
- 确认前端访问地址是否为 `https://` 开头
- 检查后端 API 地址是否为 `https://` 开头

### 3. WebSocket/WebRTC 支持问题

**问题**：
- 微信浏览器可能对 WebSocket/WebRTC 有限制
- 某些 Web API 可能不被支持

**检查方法**：
- 检查浏览器控制台的 WebSocket 连接错误
- 检查是否有 `getUserMedia` 权限问题

### 4. 认证问题

**问题**：
- 微信浏览器可能对某些认证方式有限制
- Token 存储可能有问题

**检查方法**：
- 检查 `localStorage` 是否正常工作
- 检查 Token 是否被正确发送

## 解决方案

### 方案1：修复 CORS 配置（推荐）

**步骤1：检查当前 CORS 配置**

查看 `.env` 文件中的 `CORS_ORIGINS` 配置：
```bash
CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]
```

**步骤2：添加微信访问的域名**

确保 `CORS_ORIGINS` 包含：
- 前端访问的域名（HTTPS）
- 所有可能的子域名
- 微信内访问的完整 URL

**步骤3：优化 CORS 配置**

修改 `backend/app/main.py`，添加微信浏览器特殊处理：

```python
# ===== 配置CORS中间件 =====
# 开发环境下允许所有来源，生产环境使用配置的 origins
# 注意：使用 ["*"] 时，allow_credentials 必须为 False
# 微信浏览器需要特殊处理
if settings.is_development:
    cors_origins = ["*"]
    cors_allow_credentials = False
else:
    # 生产环境：使用配置的 origins
    cors_origins = settings.cors_origins
    
    # 微信浏览器特殊处理：如果配置为空或未包含微信域名，添加默认值
    if not cors_origins or len(cors_origins) == 0:
        logger.warning("CORS_ORIGINS 未配置，使用默认值")
        cors_origins = ["*"]
        cors_allow_credentials = False
    else:
        cors_allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRFToken",
        "X-OpenAI-Agents-SDK",  # WebRTC 需要
    ],
    expose_headers=["*"],
    max_age=3600,  # 预检请求缓存时间
)
```

### 方案2：添加微信浏览器检测和日志

**修改 `backend/app/main.py`**，添加中间件检测微信浏览器：

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class WeChatBrowserMiddleware(BaseHTTPMiddleware):
    """微信浏览器检测中间件"""
    
    async def dispatch(self, request: Request, call_next):
        user_agent = request.headers.get("user-agent", "")
        is_wechat = "MicroMessenger" in user_agent
        
        if is_wechat:
            logger.info(
                "WeChat browser detected",
                extra={
                    "user_agent": user_agent,
                    "origin": request.headers.get("origin"),
                    "path": request.url.path
                }
            )
        
        response = await call_next(request)
        
        # 如果是微信浏览器，添加特殊响应头
        if is_wechat:
            response.headers["X-WeChat-Browser"] = "true"
        
        return response

# 在 CORS 中间件之前添加
app.add_middleware(WeChatBrowserMiddleware)
```

### 方案3：前端错误处理优化

**已实现**：前端代码中已有微信浏览器检测和错误处理（`frontend/src/services/api.ts` 和 `frontend/src/utils/errorHandler.ts`）

**建议**：确保错误信息清晰，帮助用户诊断问题。

## 诊断步骤

### 1. 检查后端日志（最重要）

**已添加诊断中间件**，现在后端会自动记录微信浏览器的请求：

```bash
# 查看日志中的微信浏览器请求
tail -f backend/logs/app.log | grep -i "WeChat\|MicroMessenger\|CORS"
```

**关键信息**：
- `WeChat browser request detected` - 微信浏览器请求已到达后端
- `CORS preflight request` - CORS 预检请求
- `CORS response headers for WeChat browser` - CORS 响应头

**如果看不到这些日志**：
- 说明请求没有到达后端（可能是网络问题或前端配置问题）
- 检查前端 API 地址配置是否正确

### 2. 检查浏览器控制台

在微信浏览器中：
1. 尝试打开开发者工具（如果可用）
2. 或者使用微信开发者工具的远程调试功能
3. 检查：
   - 网络请求是否被阻止
   - CORS 错误信息
   - WebSocket 连接错误
   - 具体的错误消息

### 3. 检查前端配置

确认前端 API 地址配置：
```typescript
// frontend/.env 或 vite.config.ts
VITE_API_BASE_URL=https://your-api-domain.com
```

### 4. 测试 CORS 预检请求

使用 curl 测试：
```bash
curl -X OPTIONS \
  -H "Origin: https://your-frontend-domain.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type" \
  https://your-api-domain.com/v1/chat/completions \
  -v
```

应该返回：
```
Access-Control-Allow-Origin: https://your-frontend-domain.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: Authorization, Content-Type, ...
```

### 3. 检查环境变量

确认 `.env` 文件中的配置：
```bash
# CORS 配置
CORS_ORIGINS=["https://your-domain.com"]

# API 地址（必须是 HTTPS）
API_BASE_URL=https://your-api-domain.com
```

### 4. 测试 CORS 配置

使用 curl 测试 CORS 预检请求：
```bash
curl -X OPTIONS \
  -H "Origin: https://your-frontend-domain.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type" \
  https://your-api-domain.com/v1/chat/completions \
  -v
```

应该返回：
```
Access-Control-Allow-Origin: https://your-frontend-domain.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: Authorization, Content-Type, ...
```

## 常见错误信息

### 错误1：CORS policy blocked

**错误信息**：
```
Access to XMLHttpRequest at 'https://api.example.com/v1/chat/completions' 
from origin 'https://frontend.example.com' has been blocked by CORS policy
```

**解决方法**：
1. 检查 `CORS_ORIGINS` 是否包含前端域名
2. 确认后端 CORS 配置正确

### 错误2：Network Error

**错误信息**：
```
Network Error
Failed to fetch
```

**解决方法**：
1. 确认使用 HTTPS
2. 检查网络连接
3. 检查后端服务是否可访问

### 错误3：WebSocket connection failed

**错误信息**：
```
WebSocket connection to 'wss://api.example.com/v1/realtime' failed
```

**解决方法**：
1. 确认 WebSocket 端点支持 CORS
2. 检查 WebSocket 升级请求是否成功
3. 确认代理服务器（如 Caddy）正确配置了 WebSocket 支持

## 快速修复检查清单

### 必须检查项

- [ ] **查看后端日志**：确认是否有 "WeChat browser request detected" 日志
  - 如果有：说明请求到达后端，检查 CORS 响应头
  - 如果没有：说明请求未到达后端，检查前端配置和网络连接

- [ ] **确认前端使用 HTTPS**（微信浏览器要求）
- [ ] **确认后端 API 使用 HTTPS**
- [ ] **检查开发环境**：当前是开发环境，CORS 应该允许所有来源（`["*"]`）
- [ ] **检查后端日志中的 CORS 配置**：应该看到 "CORS configured for development: allow all origins"

### 如果请求到达后端但仍有问题

- [ ] 检查后端日志中的 CORS 响应头是否正确
- [ ] 检查是否有认证错误（401/403）
- [ ] 检查是否有其他中间件阻止了请求

### 如果请求未到达后端

- [ ] 检查前端 API 地址配置（`VITE_API_BASE_URL`）
- [ ] 检查网络连接（微信浏览器可能无法访问内网地址）
- [ ] 检查是否有代理服务器（Caddy/Nginx）配置问题
- [ ] 检查防火墙规则

## 参考文档

- [FastAPI CORS 文档](https://fastapi.tiangolo.com/tutorial/cors/)
- [微信浏览器 WebView 限制](https://developers.weixin.qq.com/doc/oplatform/en/Mobile_App/WeChat_H5_Development_Guide.html)
- [CORS 预检请求说明](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS#预检请求)

---

**最后更新**: 2025-11-18  
**问题状态**: 待修复

