# CozyChat

一个现代化的AI对话应用，采用Python后端 + React前端架构，提供灵活的模块化设计和强大的扩展能力。

## ✨ 特性

- 🎯 **人格化AI系统** - 支持多个AI人格，每个人格有独立配置
- 🧠 **智能记忆管理** - 向量数据库支持，异步写入，混合存储（user/assistant/mixed）
- 💡 **智能上下文管理** - 分层模型，历史摘要，Token优化20-30%
- 🛠️ **统一工具系统** - 内置工具 + MCP协议工具自动发现
- 🎤 **多模态语音支持** - STT、TTS和实时语音对话
- 🤖 **多模型支持** - OpenAI、Ollama、LM Studio
- ⚡ **高性能** - 应用级单例，多级缓存，批量操作，响应速度提升80%+
- 🔒 **安全可靠** - API限流，XSS防护，JWT认证，数据加密
- 📱 **跨平台** - 支持Web、移动端、微信浏览器

## 🏗️ 架构

```
CozyChat/
├── backend/          # Python后端 (FastAPI)
├── frontend/         # React前端 (开发中)
├── docs/            # 项目文档
├── docker-compose.yml
└── README.md
```

### 技术栈

**后端**
- FastAPI + SQLAlchemy + PostgreSQL
- Redis缓存 + ChromaDB向量数据库
- OpenAI SDK + Ollama Python SDK
- WebSocket实时通信

**前端**
- React 18 + TypeScript + Vite
- TailwindCSS + Ant Design / shadcn/ui
- Zustand状态管理 + TanStack Query
- llm-ui聊天组件

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose（可选）

### 使用Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd CozyChat

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入必要的配置

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f backend

# 访问
# - 后端API: http://localhost:8000
# - API文档: http://localhost:8000/docs
# - 前端: http://localhost:5173 (开发中)
```

### 手动安装

#### 后端服务

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# 配置环境变量
cp ../.env.example ../.env
# 编辑.env文件

# 启动PostgreSQL和Redis（或使用Docker）
docker-compose up -d postgres redis

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload

# 或使用脚本
chmod +x scripts/dev.sh
./scripts/dev.sh
```

#### 前端应用

```bash
cd frontend

# 安装依赖
npm install  # 或使用 pnpm install

# 配置前端环境变量（可选）
# 创建 frontend/.env 文件
cat > .env << EOF
# 前端 API 基础 URL（可选，开发环境使用代理）
VITE_API_BASE_URL=http://localhost:8000

# 高德地图 API Key（用于前端天气工具）
# 获取方式：https://console.amap.com/dev/key/app
VITE_AMAP_MAPS_API_KEY=your_amap_api_key_here
EOF

# 启动开发服务器
npm run dev  # 或使用 pnpm dev
```

## 📚 文档

完整文档位于 `docs/` 目录：

### 设置与配置
- [环境配置指南](docs/setup/CONFIG.md) - 环境变量配置说明（包含OpenAI自定义base_url配置）
- [修复记录](docs/setup/FIXES_SUMMARY.md) - 代码修复总结

### 故障排查
- [alembic问题修复](docs/troubleshooting/QUICK_FIX.md) - ModuleNotFoundError解决方案

### 设计文档
- [实施路线图](docs/00-实施路线图.md)
- [项目概述](docs/01-项目概述.md)
- [后端架构设计](docs/02-后端架构设计.md)
- [前端架构设计](docs/03-前端架构设计.md)
- [API接口设计](docs/04-API接口设计.md)
- [数据库设计](docs/05-数据库设计.md)
- [开发规范](docs/06-开发规范.md)
- [测试规范](docs/07-测试规范.md)
- [开发流程管控](docs/08-开发流程管控.md)

## 🧪 测试

```bash
cd backend

# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html

# 或使用脚本
./scripts/test.sh
```

## 🔐 API认证使用

系统**没有预设的默认用户名和密码**，需要先注册账号，然后登录获取token。

### 注册新用户

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

### 用户登录

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

### 使用Token访问API

在请求头中添加 `Authorization`：

```bash
curl -X GET http://localhost:8000/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 在Swagger UI中测试

1. 访问 `http://localhost:8000/docs`
2. 找到 `/v1/users/register`，注册账号
3. 找到 `/v1/users/login`，登录获取token
4. 点击右上角 **"Authorize"** 按钮
5. 输入 `Bearer YOUR_ACCESS_TOKEN`
6. 现在可以测试其他需要认证的API

### 快速开始示例

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

### 注意事项

- ✅ 系统没有默认管理员账号，需要先注册
- ✅ 密码要求至少6个字符
- ✅ Token有效期：30天（可在配置中修改）
- ✅ 支持用户名或邮箱登录
- ✅ 用户状态必须是 `active` 才能登录

## 🔧 开发

### 代码质量检查

```bash
cd backend

# 安装pre-commit hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files

# 或使用脚本
./scripts/lint.sh
```

### 数据库迁移

```bash
cd backend

# 创建新的迁移
alembic revision --autogenerate -m "描述变更"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 📋 开发进度

- [x] **Week 1**: 后端基础框架
  - [x] 项目结构初始化
  - [x] FastAPI应用配置
  - [x] 数据库设置（SQLAlchemy + Alembic）
  - [x] 开发工具配置（pre-commit, pytest）
  - [x] Docker配置
  - [x] 基础测试

- [ ] **Week 3**: AI引擎系统
  - [ ] AI引擎基类和工厂模式
  - [ ] OpenAI引擎实现
  - [ ] Ollama引擎实现
  - [ ] Chat API接口

- [ ] **Week 4**: 记忆管理系统
- [ ] **Week 5**: 工具系统
- [ ] **Week 6**: 人格系统和核心编排器
- [ ] **Week 7**: 语音引擎基础
- [ ] **Week 8**: RealTime语音对话
- [ ] **Week 9**: 用户认证系统
- [ ] **Week 10**: 前端聊天界面
- [ ] **Week 11**: 性能优化
- [ ] **Week 12**: 测试和部署准备

详见 [实施路线图](docs/00-实施路线图.md)

## 🤝 贡献

本项目遵循[开发规范](docs/06-开发规范.md)和[开发流程管控](docs/08-开发流程管控.md)。

提交代码前请确保：
1. 通过所有测试
2. 通过代码质量检查
3. 更新相关文档
4. 遵循Conventional Commits规范

## 📄 许可

MIT License

## 🔗 相关链接

- 文档: `docs/`
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/v1/health

---

## 🔥 最新更新 (v2.0.0)

### 性能优化完成 (2025-11-18)

- 🚀 **对话响应速度提升80-85%** (1.5-2.0s → 200-300ms)
- 💾 **Token使用优化20-30%** (智能上下文管理)
- 🧠 **记忆系统全面升级** (异步写入 + 混合存储)
- 📝 **智能历史摘要** (自动压缩长对话)
- ⚡ **应用级单例优化** (Personality/Tool/LLM池化)

详见 [项目完整分析报告](docs/45-项目完整分析与整理报告.md) 和 [优化实施总结](docs/42-阶段3记忆系统优化实施报告.md)

---

**开发者**: CozyChat Team  
**版本**: v2.0.0  
**最后更新**: 2025-11-18
