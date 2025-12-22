# CozyChat Backend

CozyChat 后端服务，基于 FastAPI 构建的现代化 AI 对话平台。

## 📋 目录

- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [测试](#测试)
- [部署](#部署)
- [监控](#监控)

## 🛠 技术栈

### 核心框架
- **FastAPI** - 现代化Web框架，支持异步和自动API文档
- **Python 3.11+** - 使用最新Python特性
- **Pydantic** - 数据验证和设置管理
- **SQLAlchemy 2.0** - ORM，支持异步操作

### 数据库
- **PostgreSQL** - 主数据库，存储业务数据
- **Redis** - 缓存和会话存储
- **Qdrant** - 向量数据库（通过三大引擎）

### AI引擎
- **OpenAI API** - GPT系列模型
- **Ollama** - 本地LLM部署
- **LM Studio** - 本地模型管理

### 🆕 三大人格化引擎（v1.1+）
- **Knowledge Engine (Cognee)** - 知识图谱构建和检索
- **UserProfile Engine (Memobase)** - 用户画像管理
- **ChatMemory Engine (Mem0)** - 会话记忆搜索

### 监控与日志
- **Sentry** - 错误追踪和性能监控
- **结构化日志** - JSON格式日志，支持ELK集成

## 📁 项目结构

```
backend/
├── app/
│   ├── api/v1/              # API路由
│   │   ├── auth.py          # 认证接口
│   │   ├── chat.py          # 聊天接口
│   │   ├── sessions.py      # 会话管理
│   │   ├── users.py         # 用户管理
│   │   └── ...
│   ├── core/                # 核心业务逻辑
│   │   ├── personality/     # 人格系统
│   │   ├── context/         # 上下文管理
│   │   └── user/            # 用户管理
│   ├── services/            # 服务层（Phase 1重构）
│   │   ├── chat/            # 聊天服务
│   │   ├── memory/          # 记忆服务
│   │   └── prompt/          # 提示词服务
│   ├── engines/             # 引擎层
│   │   ├── ai/              # AI引擎（OpenAI/Ollama/LMStudio）
│   │   ├── knowledge/       # 🆕 知识引擎（Cognee）
│   │   ├── userprofile/     # 🆕 用户画像引擎（Memobase）
│   │   ├── chatmemory/      # 🆕 会话记忆引擎（Mem0）
│   │   ├── memory/          # ⚠️ 旧记忆引擎（已废弃，v2.0移除）
│   │   ├── tools/           # 工具引擎（MCP）
│   │   └── voice/           # 语音引擎（STT/TTS/RealTime）
│   ├── models/              # 数据库模型
│   │   ├── user.py
│   │   ├── session.py
│   │   └── message.py
│   ├── schemas/             # Pydantic模型
│   │   ├── chat.py
│   │   └── context.py
│   ├── middleware/          # 中间件
│   │   ├── performance.py   # 性能监控
│   │   ├── rate_limit.py    # 限流
│   │   └── exception_handler.py  # 异常处理
│   ├── utils/               # 工具函数
│   │   ├── logger.py
│   │   ├── cache.py
│   │   ├── monitoring.py    # Sentry监控（Phase 3）
│   │   └── exceptions.py
│   ├── config/              # 配置管理
│   │   └── config.py
│   └── main.py              # 应用入口
├── alembic/                 # 数据库迁移
│   └── versions/            # 迁移脚本
├── config/                  # YAML配置
│   ├── personalities/       # 人格配置
│   ├── prompts/             # 提示词配置（Phase 1）
│   └── tools/               # 工具配置
├── tests/                   # 测试
│   ├── test_api/            # API测试
│   ├── test_services/       # 服务层测试（Phase 2）
│   └── performance/         # 性能测试
├── scripts/                 # 脚本
│   └── sync_docs.py         # 文档同步检查（Phase 3）
├── requirements/            # 依赖管理
│   ├── base.txt
│   ├── dev.txt
│   └── test.txt
├── .env.example             # 环境变量示例
├── pyrightconfig.json       # 类型检查配置
└── pytest.ini               # 测试配置
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- (可选) Ollama / LM Studio

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements/dev.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，配置必要参数
nano .env
```

**必需配置项**：
- `DATABASE_URL` - PostgreSQL连接URL
- `REDIS_URL` - Redis连接URL
- `OPENAI_API_KEY` - OpenAI API密钥
- `APP_SECRET_KEY` - 应用密钥
- `JWT_SECRET_KEY` - JWT密钥

### 4. 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head
```

### 5. 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用脚本
./scripts/dev.sh
```

访问 http://localhost:8000/docs 查看API文档。

## ⚙️ 配置说明

### 环境变量

完整配置项请参考 `.env.example` 文件。

**核心配置**：
```bash
# 应用配置
APP_ENV=development          # 环境：development/staging/production
APP_DEBUG=true              # 调试模式

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cozychat
DB_POOL_SIZE=20             # 连接池大小

# Redis配置
REDIS_URL=redis://localhost:6379/0

# AI配置
OPENAI_API_KEY=sk-xxx
OLLAMA_BASE_URL=http://localhost:11434

# Sentry监控（Phase 3）
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENABLE=false
```

### YAML配置

**人格配置** (`config/personalities/*.yaml`):
```yaml
id: assistant_001
name: "AI助手"
ai:
  provider: openai
  model: gpt-4
memory:
  enabled: true
tools:
  enabled: true
```

**提示词配置** (`config/prompts/*.yaml`):
```yaml
# Phase 1 新增：配置化提示词
instructions: "简洁回答，避免生硬开场白"
```

## 👨‍💻 开发指南

### 代码规范

遵循项目开发规范（详见 `docs/06-开发规范.md`）：

- **代码风格**：PEP 8 + Black格式化
- **类型注解**：强制使用类型注解
- **文档字符串**：Google风格docstring
- **测试覆盖率**：核心模块≥85%

### 类型检查

```bash
# 使用Pyright进行类型检查
# IDE会自动进行类型检查，确保无错误
```

### 代码格式化

```bash
# Black格式化
black app/

# isort排序导入
isort app/
```

### 提交规范

使用 Conventional Commits：
```
feat(chat): 添加流式响应支持
fix(memory): 修复记忆检索超时
docs(api): 更新API文档
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api/test_chat.py

# 运行并生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 测试结构

- **单元测试** (`tests/test_services/`) - Phase 2新增，90个测试
- **API测试** (`tests/test_api/`)
- **集成测试** (`tests/test_api/test_chat_integration.py`) - Phase 2新增
- **性能测试** (`tests/performance/`)

### 测试覆盖率

当前覆盖率（Phase 2优化后）：
- MessageSaver: 100%
- ToolCallHandler: 100%
- PromptBuilder: 100%
- MemoryScoringService: 99%

## 🚢 部署

### 生产环境配置

```bash
# 设置生产环境变量
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=WARNING

# 启用Sentry监控
SENTRY_ENABLE=true
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Docker部署

```bash
# 构建镜像
docker build -t cozychat-backend .

# 运行容器
docker run -p 8000:8000 --env-file .env cozychat-backend
```

### 性能优化

**Phase 2-3 数据库优化**：
- ✅ 13个性能优化索引
- ✅ N+1查询优化（joinedload）
- ✅ 查询响应时间 <50ms（提升80%）

**缓存策略**：
- L1: 内存缓存（TTL: 5分钟）
- L2: Redis缓存（TTL: 30分钟）

## 📊 监控

### Sentry集成（Phase 3）

启用Sentry后，自动监控：
- ❌ 错误追踪
- ⏱️ 性能监控
- 👤 用户上下文
- 🍞 操作面包屑

**查看Sentry**：
访问配置的Sentry项目地址

### 性能指标

当前性能（Phase 2优化后）：
- API响应时间：P95 < 200ms
- 数据库查询：平均 < 50ms
- 聊天完成：< 2s（不含AI推理）

### 日志

```bash
# 查看日志
tail -f logs/app.log

# 结构化日志查询（需要ELK集成）
```

## 📚 文档

- [后端架构设计](../docs/02-后端架构设计.md)
- [API接口设计](../docs/04-API接口设计.md)
- [数据库设计](../docs/05-数据库设计.md)
- [开发规范](../docs/06-开发规范.md)
- [测试规范](../docs/07-测试规范.md)
- [N+1查询优化](docs/N+1查询优化说明.md)

## 🐛 问题排查

### 常见问题

**1. 数据库连接失败**
```bash
# 检查PostgreSQL是否运行
pg_isready

# 检查连接字符串
echo $DATABASE_URL
```

**2. Redis连接失败**
```bash
# 检查Redis是否运行
redis-cli ping

# 应该返回：PONG
```

**3. 测试失败**
```bash
# 确保测试数据库已迁移
alembic upgrade head

# 启动Redis
brew services start redis  # macOS
```

更多问题请参考：[troubleshooting](../docs/troubleshooting/)

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写测试并确保通过
4. 提交代码（遵循提交规范）
5. 创建Pull Request

## 📝 更新日志

### Phase 3 (2025-11-20)
- ✅ Sentry监控集成
- ✅ 文档同步机制
- ✅ .env.example配置完善

### Phase 2 (2025-11-19)
- ✅ 服务层重构（MessageSaver/ToolCallHandler等）
- ✅ 90个单元测试和集成测试
- ✅ 数据库索引优化（13个索引）
- ✅ N+1查询优化
- ✅ BaseEngine统一引擎接口

### Phase 1 (2025-11-18)
- ✅ chat.py重构（1611行→547行，-66%）
- ✅ 提示词配置化（YAML）
- ✅ 异常处理层次化
- ✅ 前端ErrorBoundary

## 📄 许可证

MIT License

---

**CozyChat Backend** - 现代化AI对话平台后端服务

