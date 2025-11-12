# CozyChat Backend

CozyChat后端服务 - 基于FastAPI的AI对话应用后端

## 技术栈

- **FastAPI**: 高性能异步Web框架
- **SQLAlchemy**: ORM框架（异步支持）
- **Alembic**: 数据库迁移工具
- **PostgreSQL**: 主数据库
- **Redis**: 缓存层
- **ChromaDB**: 向量数据库
- **Pydantic**: 数据验证
- **Structlog**: 结构化日志

## 快速开始

### 1. 环境准备

```bash
# 安装Python 3.11+
python --version  # 确保 >= 3.11

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements/base.txt
pip install -r requirements/dev.txt  # 开发环境
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp ../.env.example ../.env

# 编辑.env文件，填入真实配置
# 至少需要配置：
# - DATABASE_URL
# - APP_SECRET_KEY
# - JWT_SECRET_KEY
# - ALLOW_REGISTRATION (可选，默认true，false时禁止开放注册)
```

### 3. 启动数据库（使用Docker）

```bash
# 从项目根目录启动PostgreSQL和Redis
cd ..
docker-compose up -d postgres redis
```

### 4. 数据库迁移

```bash
# 方法1：使用迁移脚本（推荐）
./scripts/migrate.sh upgrade

# 方法2：手动设置PYTHONPATH后运行
export PYTHONPATH="$(pwd)"
alembic upgrade head
```

> **注意**：如果遇到 `ModuleNotFoundError: No module named 'app'` 错误，
> 请使用迁移脚本或手动设置PYTHONPATH。详见 [故障排查文档](../docs/troubleshooting/QUICK_FIX.md)

### 5. 启动开发服务器

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Python直接运行
python -m app.main
```

### 6. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/v1/health

### 7. API认证使用

系统**没有预设的默认用户名和密码**，需要先注册账号，然后登录获取token。

> **注意**：如果 `ALLOW_REGISTRATION=false`，注册功能将被禁用，只能通过管理员手动创建用户。

#### 7.1 注册新用户

```bash
curl -X POST http://localhost:8000/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "email": "your_email@example.com",
    "password": "your_password",
    "display_name": "Your Display Name"
  }'
```

**要求**：
- `username`: 3-50个字符
- `email`: 有效邮箱地址
- `password`: 至少6个字符

#### 7.2 用户登录

```bash
curl -X POST http://localhost:8000/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**响应示例**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 2592000,
  "user": {
    "id": "user-uuid",
    "username": "your_username",
    "email": "your_email@example.com",
    "role": "user"
  }
}
```

#### 7.3 使用Token访问API

在请求头中添加 `Authorization`：

```bash
curl -X GET http://localhost:8000/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 7.4 在Swagger UI中测试

1. 访问 `http://localhost:8000/docs`
2. 找到 `/v1/users/register`，注册账号
3. 找到 `/v1/users/login`，登录获取token
4. 点击右上角 **"Authorize"** 按钮
5. 输入 `Bearer YOUR_ACCESS_TOKEN`
6. 现在可以测试其他需要认证的API

#### 7.5 快速开始示例

```bash
# 1. 注册账号
curl -X POST http://localhost:8000/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "email": "demo@example.com",
    "password": "demo123456"
  }'

# 2. 登录获取token
TOKEN=$(curl -X POST http://localhost:8000/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "demo123456"
  }' | jq -r '.access_token')

# 3. 使用token访问API
curl -X GET http://localhost:8000/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

#### 7.6 注意事项

- ✅ 系统没有默认管理员账号，需要先注册
- ✅ 密码要求至少6个字符
- ✅ Token有效期：30天（可在配置中修改）
- ✅ 支持用户名或邮箱登录
- ✅ 用户状态必须是 `active` 才能登录

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI应用入口
│   ├── api/                     # API路由层
│   │   ├── deps.py              # 依赖注入
│   │   └── v1/                  # API v1
│   │       ├── health.py        # 健康检查
│   │       └── ...              # 其他路由（待开发）
│   ├── config/                  # 配置模块
│   │   └── config.py            # 应用配置
│   ├── core/                    # 核心业务逻辑
│   ├── engines/                 # 引擎层（AI、记忆、工具、语音）
│   ├── models/                  # 数据模型
│   │   ├── base.py              # 基础模型
│   │   └── user.py              # 用户模型
│   └── utils/                   # 工具函数
│       └── logger.py            # 日志配置
├── tests/                       # 测试代码
├── alembic/                     # 数据库迁移
├── requirements/                # 依赖文件
│   ├── base.txt                 # 基础依赖
│   ├── dev.txt                  # 开发依赖
│   └── test.txt                 # 测试依赖
├── .pre-commit-config.yaml      # Pre-commit配置
├── pytest.ini                   # Pytest配置
├── alembic.ini                  # Alembic配置
└── Dockerfile                   # Docker镜像
```

## 开发规范

### 代码风格

遵循项目开发规范（参见 `docs/06-开发规范.md`）：

- 使用 **Black** 格式化代码（行长度88）
- 使用 **isort** 排序import
- 使用 **flake8** 进行代码检查
- 使用 **mypy** 进行类型检查
- 所有函数和类必须有中文docstring
- 使用类型注解

### Pre-commit Hooks

```bash
# 安装pre-commit hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config.py

# 查看覆盖率报告
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## 数据库迁移

```bash
# 使用迁移脚本（推荐）✨
./scripts/migrate.sh upgrade              # 应用迁移
./scripts/migrate.sh downgrade            # 回滚
./scripts/migrate.sh create "描述迁移内容" # 创建新迁移
./scripts/migrate.sh history              # 查看历史
./scripts/migrate.sh current              # 查看当前版本

# 或手动运行（需要先设置PYTHONPATH）
export PYTHONPATH="$(pwd)"
alembic revision --autogenerate -m "描述迁移内容"
alembic upgrade head
alembic downgrade -1
alembic history
alembic current
```

> **⚠️ 重要**：如果遇到 `ModuleNotFoundError: No module named 'app'` 错误，
> 请使用迁移脚本或手动设置PYTHONPATH。详见 [故障排查文档](../docs/troubleshooting/QUICK_FIX.md)

## 常见问题

### Q: 数据库连接失败？

A: 确保PostgreSQL正在运行，并检查`.env`中的`DATABASE_URL`配置是否正确。

### Q: 导入错误？

A: 确保虚拟环境已激活，并且所有依赖已正确安装。

### Q: Pre-commit检查失败？

A: 运行 `pre-commit run --all-files` 查看详细错误，通常是代码格式问题，可以自动修复。

## 开发进度

- [x] Week 1: 后端基础框架
- [ ] Week 3: AI引擎系统
- [ ] Week 4: 记忆管理系统
- [ ] Week 5: 工具系统
- [ ] Week 6: 人格系统
- [ ] Week 7: 语音引擎
- [ ] Week 8: RealTime语音
- [ ] Week 9: 用户认证系统

详见 `docs/00-实施路线图.md`

## 相关文档

- [项目概述](../docs/01-项目概述.md)
- [后端架构设计](../docs/02-后端架构设计.md)
- [API接口设计](../docs/04-API接口设计.md)
- [数据库设计](../docs/05-数据库设计.md)
- [开发规范](../docs/06-开发规范.md)
- [测试规范](../docs/07-测试规范.md)

## License

MIT
