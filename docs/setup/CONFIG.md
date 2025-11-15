# CozyChat 配置指南

## 环境变量配置

CozyChat使用环境变量进行配置管理。所有敏感信息都应通过环境变量设置，而不是硬编码在代码中。

### 快速开始

1. **复制环境变量模板**

```bash
cp .env.example .env
```

2. **编辑 `.env` 文件**

使用文本编辑器打开 `.env` 文件，根据您的实际情况修改配置。

### 必需配置项

以下配置项是必需的，应用启动前必须设置：

#### 1. 应用密钥

```bash
# 生成安全的密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 在.env中设置
APP_SECRET_KEY=生成的密钥
JWT_SECRET_KEY=生成的密钥
```

#### 2. 数据库配置

```bash
# PostgreSQL连接URL
DATABASE_URL=postgresql://用户名:密码@主机:端口/数据库名

# 示例
DATABASE_URL=postgresql://cozychat_user:cozychat_password@localhost:5432/cozychat_dev
```

### OpenAI 自定义配置 ⭐

CozyChat完整支持OpenAI自定义base_url，可以使用：
- 官方OpenAI API
- 国内代理服务
- Azure OpenAI
- 其他OpenAI兼容的API服务

#### 配置方法

```bash
# OpenAI API密钥
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API基础URL（支持自定义）
# 默认值（官方API）
OPENAI_BASE_URL=https://api.openai.com/v1

# OpenAI Realtime API 模型名称（语音通话功能）
# 默认值（推荐）
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2025-06-03
# 其他可用模型
# OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-10-01

# 国内代理示例
OPENAI_BASE_URL=https://api.openai-proxy.com/v1

# Azure OpenAI示例
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment

# 其他兼容API示例
OPENAI_BASE_URL=https://your-custom-api.com/v1
```

#### 代码中的实现

配置文件 `backend/app/config/config.py`:
- `OPENAI_API_KEY`: OpenAI API密钥（可选，如果不使用OpenAI可以留空）
- `OPENAI_BASE_URL`: OpenAI API基础URL（默认为官方API）
- `OPENAI_REALTIME_MODEL`: OpenAI Realtime API使用的模型（默认：`gpt-4o-realtime-preview-2025-06-03`）

OpenAI引擎 `backend/app/engines/ai/openai_engine.py`:
- 自动使用配置中的 `base_url`
- 支持任何OpenAI兼容的API端点

语音通话功能 `backend/app/api/v1/config.py`:
- 使用 `OPENAI_REALTIME_MODEL` 配置项
- 在创建 ephemeral token 时自动应用正确的模型名称

### 可选配置项

#### Redis配置

```bash
REDIS_URL=redis://localhost:6379/0
# 如果Redis设置了密码
REDIS_PASSWORD=your_redis_password
```

#### Ollama配置（本地模型）

```bash
OLLAMA_BASE_URL=http://localhost:11434
```

#### 向量数据库配置

```bash
# ChromaDB持久化目录
CHROMA_PERSIST_DIRECTORY=./data/chroma

# Qdrant配置（可选，未来支持）
# QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY=your_api_key
```

#### CORS配置

```bash
# 允许的前端域名（多个用逗号分隔）
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

#### 日志配置

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log
```

## 完整配置示例

查看 `.env.example` 文件获取完整的配置模板，包含所有可用选项的详细说明。

## 配置验证

启动应用后，配置会自动加载和验证。如果有必需的配置项缺失或格式错误，应用会报错并提示具体问题。

```bash
cd backend
uvicorn app.main:app --reload
```

如果配置正确，您会看到：

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Docker Compose 配置

使用 Docker Compose 时，可以通过以下方式设置环境变量：

1. 在项目根目录创建 `.env` 文件
2. Docker Compose 会自动读取 `.env` 文件
3. 查看 `docker-compose.yml` 了解如何引用环境变量

## 生产环境注意事项

1. **永远不要提交 `.env` 文件到Git**
   - `.env` 文件已在 `.gitignore` 中排除
   - 只提交 `.env.example` 模板

2. **使用强密钥**
   - 生产环境必须使用安全的随机密钥
   - 定期轮换密钥

3. **数据库安全**
   - 使用强密码
   - 限制数据库访问权限
   - 启用SSL连接

4. **API密钥管理**
   - 使用环境变量或密钥管理服务
   - 不要在日志中输出密钥
   - 设置API密钥的使用限额

## 故障排查

### 问题：应用启动时提示缺少配置

**解决方法**：
1. 检查 `.env` 文件是否存在
2. 确认所有必需字段都已设置
3. 检查配置值的格式是否正确

### 问题：OpenAI API调用失败

**解决方法**：
1. 检查 `OPENAI_API_KEY` 是否正确
2. 检查 `OPENAI_BASE_URL` 是否可访问
3. 如果使用代理，确认代理服务正常
4. 检查网络连接

### 问题：数据库连接失败

**解决方法**：
1. 确认PostgreSQL服务正在运行
2. 检查 `DATABASE_URL` 格式是否正确
3. 确认数据库用户权限
4. 检查防火墙设置

## 更多帮助

- [项目README](README.md)
- [后端架构文档](docs/02-后端架构设计.md)
- [API文档](http://localhost:8000/docs)

