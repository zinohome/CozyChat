# Demo模式使用指南

## 概述

Demo模式允许在应用启动时自动创建Demo用户，并在前端登录页面自动填入用户名和密码，方便快速体验应用功能。

## 功能特性

1. **后端自动创建Demo用户**：启动时检查并创建Demo用户（如果不存在）
2. **前端自动填入**：登录页面自动填入Demo账号信息
3. **可配置**：通过环境变量配置Demo用户名、密码和邮箱

## 配置方法

### 后端配置

在 `backend/.env` 文件中添加以下配置：

```bash
# Demo模式配置
DEMO_MODE=true                    # 启用Demo模式
DEMO_USERNAME=demo                # Demo用户名（默认：demo）
DEMO_PASSWORD=demo123             # Demo密码（默认：demo123）
DEMO_EMAIL=demo@cozychat.ai       # Demo邮箱（默认：demo@cozychat.ai）
```

### 前端配置

在 `frontend/.env` 文件中添加以下配置：

```bash
# Demo模式配置
VITE_DEMO_MODE=true               # 启用Demo模式
VITE_DEMO_USERNAME=demo           # Demo用户名（默认：demo）
VITE_DEMO_PASSWORD=demo123        # Demo密码（默认：demo123）
```

## 使用流程

### 1. 启动后端

```bash
cd backend
# 确保 .env 文件中设置了 DEMO_MODE=true
uvicorn app.main:app --reload
```

后端启动时会自动检查并创建Demo用户：

```
[INFO] Demo user created: demo (user_id: xxx-xxx-xxx)
```

如果Demo用户已存在，会跳过创建：

```
[DEBUG] Demo user already exists: demo (user_id: xxx-xxx-xxx)
```

### 2. 启动前端

```bash
cd frontend
# 确保 .env 文件中设置了 VITE_DEMO_MODE=true
pnpm dev
```

### 3. 访问登录页面

打开浏览器访问登录页面，用户名和密码会自动填入：

- **用户名**：demo（或配置的 `VITE_DEMO_USERNAME`）
- **密码**：demo123（或配置的 `VITE_DEMO_PASSWORD`）

直接点击"登录"按钮即可登录。

## 配置说明

### 后端环境变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DEMO_MODE` | bool | `false` | 是否启用Demo模式 |
| `DEMO_USERNAME` | string | `demo` | Demo用户名 |
| `DEMO_PASSWORD` | string | `demo123` | Demo密码 |
| `DEMO_EMAIL` | string | `demo@cozychat.ai` | Demo邮箱 |

### 前端环境变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `VITE_DEMO_MODE` | string | - | 是否启用Demo模式（`true`/`false`） |
| `VITE_DEMO_USERNAME` | string | `demo` | Demo用户名 |
| `VITE_DEMO_PASSWORD` | string | `demo123` | Demo密码 |

## 注意事项

1. **安全性**：Demo模式仅用于演示和开发环境，**不要在生产环境启用**。

2. **用户创建**：Demo用户只在首次启动时创建，后续启动会跳过创建（如果用户已存在）。

3. **密码安全**：Demo密码是明文存储在环境变量中的，请确保 `.env` 文件不被提交到Git仓库。

4. **前端自动填入**：前端自动填入功能仅在Demo模式启用时生效，用户仍可以手动修改用户名和密码。

5. **环境变量同步**：确保后端和前端的环境变量配置一致（用户名和密码）。

## 禁用Demo模式

要禁用Demo模式，只需将环境变量设置为 `false` 或不设置：

```bash
# 后端
DEMO_MODE=false
# 或直接删除该行

# 前端
VITE_DEMO_MODE=false
# 或直接删除该行
```

## 故障排查

### Demo用户未创建

1. 检查 `DEMO_MODE` 是否设置为 `true`
2. 检查数据库连接是否正常
3. 查看后端日志，确认是否有错误信息

### 前端未自动填入

1. 检查 `VITE_DEMO_MODE` 是否设置为 `true`
2. 检查环境变量是否正确加载（需要重启开发服务器）
3. 检查浏览器控制台是否有错误信息

### 登录失败

1. 确认后端Demo用户已创建（查看后端日志）
2. 确认前端填入的用户名和密码与后端配置一致
3. 检查数据库中的用户记录

## 示例配置

### 完整配置示例

**backend/.env**:
```bash
# 应用配置
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/cozychat

# Demo模式配置
DEMO_MODE=true
DEMO_USERNAME=demo
DEMO_PASSWORD=demo123
DEMO_EMAIL=demo@cozychat.ai
```

**frontend/.env**:
```bash
# API配置
VITE_API_BASE_URL=http://localhost:8000

# Demo模式配置
VITE_DEMO_MODE=true
VITE_DEMO_USERNAME=demo
VITE_DEMO_PASSWORD=demo123
```

## 相关文件

- `backend/app/config/config.py` - 后端配置定义
- `backend/app/main.py` - 启动时创建Demo用户逻辑
- `frontend/src/features/auth/components/LoginForm.tsx` - 登录表单自动填入逻辑
- `frontend/src/vite-env.d.ts` - 前端环境变量类型定义

