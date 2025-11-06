# CozyChat

一个现代化的AI对话应用，采用Python后端 + React前端架构，提供灵活的模块化设计和强大的扩展能力。

## ✨ 特性

- 🎯 **人格化AI系统** - 支持多个AI人格，每个人格有独立配置
- 🧠 **智能记忆管理** - 向量数据库支持，区分用户和AI记忆
- 🛠️ **统一工具系统** - 内置工具 + MCP协议工具自动发现
- 🎤 **多模态语音支持** - STT、TTS和实时语音对话
- 🤖 **多模型支持** - OpenAI、Ollama、LM Studio
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

#### 前端应用（Week 10开发）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
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

**开发者**: CozyChat Team  
**版本**: v0.1.0  
**最后更新**: 2025-11-06
