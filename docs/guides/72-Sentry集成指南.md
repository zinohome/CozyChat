# Sentry集成指南

## 概述

CozyChat已集成Sentry进行前后端错误追踪和性能监控。本文档说明如何配置和使用Sentry。

---

## 一、后端集成 (已完成 ✅)

### 1.1 安装依赖

```bash
cd backend
pip install sentry-sdk[fastapi]
```

### 1.2 环境变量配置

在 `backend/.env` 中添加：

```bash
# Sentry配置
SENTRY_DSN=your-sentry-dsn-here
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
SENTRY_SEND_DEFAULT_PII=false
SENTRY_ATTACH_STACKTRACE=true
SENTRY_MAX_BREADCRUMBS=50
SENTRY_DEBUG=false
SENTRY_RELEASE=0.1.0
```

### 1.3 代码集成

**初始化（`backend/app/main.py`）**：

```python
from app.utils.monitoring import init_sentry

async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化Sentry
    init_sentry()
    
    yield
```

**异常处理（`backend/app/middleware/exception_handler.py`）**：

```python
from app.utils.monitoring import capture_exception

@app.exception_handler(CozyError)
async def cozy_error_handler(request: Request, exc: CozyError):
    # 上报到Sentry
    capture_exception(exc, {"request_id": request.state.request_id})
    ...
```

### 1.4 集成功能

- ✅ **FastAPI集成** - 自动捕获API错误
- ✅ **SQLAlchemy集成** - 监控数据库查询性能
- ✅ **Redis集成** - 监控缓存操作
- ✅ **日志集成** - 自动收集日志面包屑
- ✅ **性能追踪** - 监控接口响应时间
- ✅ **用户上下文** - 关联错误到具体用户

---

## 二、前端集成 (已完成 ✅)

### 2.1 安装依赖

```bash
cd frontend
pnpm install @sentry/react
```

### 2.2 环境变量配置

在 `frontend/.env` 中添加：

```bash
# Sentry配置
VITE_SENTRY_DSN=your-sentry-dsn-here
VITE_SENTRY_ENVIRONMENT=development
VITE_APP_VERSION=0.1.0

# Sentry采样率配置
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.1
VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=1.0
```

### 2.3 代码集成

**初始化（`frontend/src/main.tsx`）**：

```typescript
import * as Sentry from '@sentry/react';

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT,
    release: import.meta.env.VITE_APP_VERSION,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}
```

**ErrorBoundary（`frontend/src/components/ErrorBoundary.tsx`）**：

```typescript
componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
  Sentry.withScope((scope) => {
    scope.setContext('react_error_info', {
      componentStack: errorInfo.componentStack,
    });
    const eventId = Sentry.captureException(error);
    this.setState({ eventId });
  });
}
```

### 2.4 集成功能

- ✅ **React ErrorBoundary** - 捕获组件树错误
- ✅ **性能追踪** - 监控页面加载和交互性能
- ✅ **Session Replay** - 回放错误发生时的用户会话
- ✅ **用户反馈** - 错误发生时允许用户提交反馈
- ✅ **面包屑** - 记录用户操作路径

---

## 三、Sentry配置说明

### 3.1 DSN获取

1. 登录 [Sentry.io](https://sentry.io)
2. 创建新项目（前端选择React，后端选择FastAPI/Python）
3. 复制DSN（格式：`https://xxx@xxx.ingest.sentry.io/xxx`）
4. 分别配置到前后端 `.env` 文件

### 3.2 环境配置

| 环境 | 说明 | 采样率建议 |
|------|------|----------|
| `development` | 开发环境 | 100% |
| `staging` | 预发布环境 | 50% |
| `production` | 生产环境 | 10% |

### 3.3 采样率说明

**后端**：

- `SENTRY_TRACES_SAMPLE_RATE` - 性能追踪采样率（0.1 = 10%）
- `SENTRY_PROFILES_SAMPLE_RATE` - 性能分析采样率（0.1 = 10%）

**前端**：

- `VITE_SENTRY_TRACES_SAMPLE_RATE` - 性能追踪采样率（0.1 = 10%）
- `VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE` - 正常会话回放采样率（0.1 = 10%）
- `VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE` - 错误会话回放采样率（1.0 = 100%）

**建议**：
- 开发环境：全部设为 `1.0`（100%）
- 生产环境：`0.1`~`0.2`（10%~20%）以控制成本

---

## 四、使用指南

### 4.1 手动捕获错误

**后端**：

```python
from app.utils.monitoring import capture_exception, capture_message

try:
    risky_operation()
except Exception as e:
    capture_exception(e, {"context": "additional info"})
```

**前端**：

```typescript
import * as Sentry from '@sentry/react';

try {
  riskyOperation();
} catch (error) {
  Sentry.captureException(error);
}
```

### 4.2 添加用户上下文

**后端**：

```python
from app.utils.monitoring import set_user_context

set_user_context({
    "id": user.id,
    "username": user.username,
    "email": user.email,
})
```

**前端**：

```typescript
Sentry.setUser({
  id: user.id,
  username: user.username,
  email: user.email,
});
```

### 4.3 添加自定义标签

**后端**：

```python
from app.utils.monitoring import set_tag

set_tag("feature", "chat_completion")
set_tag("ai_provider", "openai")
```

**前端**：

```typescript
Sentry.setTag("feature", "chat");
Sentry.setTag("personality", personalityId);
```

### 4.4 添加面包屑

**后端**：

```python
from app.utils.monitoring import add_breadcrumb

add_breadcrumb(
    category="auth",
    message="User logged in",
    level="info",
    data={"user_id": user.id}
)
```

**前端**：

```typescript
Sentry.addBreadcrumb({
  category: 'user',
  message: 'Clicked send button',
  level: 'info',
  data: { sessionId },
});
```

---

## 五、最佳实践

### 5.1 错误过滤

**排除敏感信息**：

```python
# backend/app/utils/monitoring.py
def init_sentry():
    sentry_sdk.init(
        before_send=filter_sensitive_data,
        ...
    )

def filter_sensitive_data(event, hint):
    # 过滤敏感字段
    if 'request' in event:
        if 'headers' in event['request']:
            event['request']['headers'].pop('Authorization', None)
    return event
```

```typescript
// frontend/src/main.tsx
Sentry.init({
  beforeSend(event) {
    // 过滤敏感信息
    if (event.request?.headers) {
      delete event.request.headers['Authorization'];
    }
    return event;
  },
});
```

### 5.2 性能监控

**关键路径追踪**：

```python
from app.utils.monitoring import trace_performance

@trace_performance("chat.completion")
async def chat_completion(...):
    ...
```

```typescript
const transaction = Sentry.startTransaction({
  name: 'Chat Completion',
  op: 'chat.completion',
});

// ... 业务逻辑

transaction.finish();
```

### 5.3 告警配置

在Sentry控制台配置：

1. **错误告警** - 新错误/错误频率阈值
2. **性能告警** - 响应时间/事务失败率
3. **通知渠道** - Email/Slack/钉钉

---

## 六、故障排查

### 6.1 Sentry未上报错误

**检查清单**：

```bash
# 1. 检查DSN是否正确
echo $SENTRY_DSN  # 后端
echo $VITE_SENTRY_DSN  # 前端

# 2. 检查网络连接
curl https://sentry.io/api/

# 3. 启用调试模式
# 后端: SENTRY_DEBUG=true
# 前端: Sentry.init({ debug: true })

# 4. 检查采样率
# 如果采样率为0，不会上报任何数据
```

### 6.2 性能数据缺失

```bash
# 检查tracesSampleRate是否为0
SENTRY_TRACES_SAMPLE_RATE=0.1  # 后端
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1  # 前端
```

### 6.3 Session Replay不工作

```bash
# 确保配置了回放集成
# 前端: Sentry.replayIntegration()

# 检查采样率
VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.1
VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=1.0
```

---

## 七、参考资料

- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Sentry React SDK](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Sentry FastAPI](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [Session Replay](https://docs.sentry.io/product/session-replay/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)

---

## 附录：快速配置脚本

### 后端配置

```bash
#!/bin/bash
# backend/scripts/setup_sentry.sh

echo "配置后端Sentry..."

# 提示输入DSN
read -p "输入Sentry DSN: " dsn

# 追加到.env
cat >> .env << EOF

# Sentry配置
SENTRY_DSN=$dsn
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0
EOF

echo "✅ 后端Sentry配置完成！"
```

### 前端配置

```bash
#!/bin/bash
# frontend/scripts/setup_sentry.sh

echo "配置前端Sentry..."

# 提示输入DSN
read -p "输入Sentry DSN: " dsn

# 追加到.env
cat >> .env << EOF

# Sentry配置
VITE_SENTRY_DSN=$dsn
VITE_SENTRY_ENVIRONMENT=development
VITE_APP_VERSION=0.1.0
VITE_SENTRY_TRACES_SAMPLE_RATE=1.0
VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE=1.0
VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=1.0
EOF

echo "✅ 前端Sentry配置完成！"
```

---

**更新时间**: 2025-11-20  
**文档版本**: v1.0  
**维护者**: CozyChat团队

