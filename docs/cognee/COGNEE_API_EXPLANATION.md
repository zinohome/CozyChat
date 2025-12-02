# Cognee API 服务层详解

## 一、什么是 Cognee API 服务层？

**Cognee API 服务层**是 **Cognee 框架自带的 FastAPI Web 服务**，它提供了完整的 RESTful API 接口，用于操作和管理知识图谱系统。

### 核心特点

1. **Cognee 官方提供**：Cognee 框架内置的 API 服务
2. **FastAPI 实现**：基于 FastAPI 框架构建
3. **完整功能**：涵盖知识图谱的所有核心操作
4. **标准 REST API**：提供标准的 HTTP REST 接口

---

## 二、Cognee API 服务层的定位

### 在架构中的位置

```
┌─────────────────────────────────────────┐
│         客户端层                         │
│  ┌──────────┐  ┌──────────┐           │
│  │ Cognee UI│  │ Agent API│           │
│  └────┬─────┘  └────┬─────┘           │
└───────┼─────────────┼──────────────────┘
        │             │
        └──────┬──────┘
               │
    ┌──────────▼──────────┐
    │   Cognee API 服务层  │  ← 核心知识图谱 API
    │   (端口: 8000)      │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   数据存储层         │
    │ (PostgreSQL/Neo4j)  │
    └─────────────────────┘
```

### 与其他服务的关系

| 服务 | 作用 | 关系 |
|------|------|------|
| **Cognee API** | 提供知识图谱核心操作 API | **基础服务** |
| **Agent API** | 处理用户对话，调用 Cognee API | **依赖 Cognee API** |
| **Cognee UI** | Web 界面，调用 Cognee API | **依赖 Cognee API** |

**关键点**：
- Cognee API 是**底层基础服务**
- Agent API 和 Cognee UI 都**依赖** Cognee API
- Cognee API **不依赖** Agent API

---

## 三、Cognee API 提供的功能

### 3.1 核心操作 API

#### 1. 数据添加 (Add)
```
POST /api/v1/add
```
- 功能：添加文档、文本、文件到数据集
- 用途：导入专业文档、用户对话内容

#### 2. 认知化 (Cognify)
```
POST /api/v1/cognify
```
- 功能：将数据转换为知识图谱
- 用途：创建实体、关系、节点集

#### 3. 记忆化 (Memify)
```
POST /api/v1/memify
```
- 功能：语义增强知识图谱
- 用途：提升理解能力（可选）

#### 4. 搜索 (Search)
```
POST /api/v1/search
```
- 功能：搜索知识图谱
- 用途：语义搜索、图遍历、混合搜索

### 3.2 数据集管理 API

#### 数据集操作
```
GET    /api/v1/datasets          # 获取所有数据集
POST   /api/v1/datasets          # 创建数据集
GET    /api/v1/datasets/{id}     # 获取特定数据集
DELETE /api/v1/datasets/{id}     # 删除数据集
```

### 3.3 用户和权限管理 API

#### 用户认证
```
POST /api/v1/auth/login          # 登录
POST /api/v1/auth/register       # 注册
POST /api/v1/auth/logout         # 登出
```

#### 权限管理
```
GET  /api/v1/permissions         # 获取权限
POST /api/v1/permissions         # 授予权限
```

### 3.4 其他功能 API

```
GET  /api/v1/visualize          # 可视化知识图谱
POST /api/v1/delete             # 删除数据
POST /api/v1/update             # 更新数据
GET  /api/v1/settings           # 系统设置
GET  /health                    # 健康检查
```

---

## 四、Cognee API 服务层的启动方式

### 4.1 命令行启动

```bash
# 方式1：使用 Cognee CLI
cognee start-api

# 方式2：使用 Python 模块
python -m uvicorn cognee.api.client:app --host 0.0.0.0 --port 8000

# 方式3：使用 Cognee UI（会自动启动 API）
cognee start-ui --start-backend
```

### 4.2 Docker 容器启动

```yaml
# docker-compose.yml
cognee-api:
  image: cognee/cognee:latest
  ports:
    - "8000:8000"
  environment:
    DATABASE_URL: postgresql://...
    NEO4J_URI: bolt://neo4j:7687
  command: python -m uvicorn cognee.api.client:app --host 0.0.0.0 --port 8000
```

---

## 五、Cognee API 与 Agent API 的区别

### 5.1 功能对比

| 特性 | Cognee API | Agent API |
|------|-----------|-----------|
| **定位** | 知识图谱核心操作 | 用户对话处理 |
| **功能** | 数据管理、搜索、图谱操作 | 对话管理、响应生成 |
| **端口** | 8000 | 8001 |
| **依赖** | 无（基础服务） | 依赖 Cognee API |
| **使用者** | Cognee UI、Agent API | 最终用户 |

### 5.2 使用场景

#### Cognee API 使用场景：
- ✅ 通过 Cognee UI 维护专业数据集
- ✅ 管理员上传和管理文档
- ✅ 直接调用知识图谱操作
- ✅ 系统集成和自动化

#### Agent API 使用场景：
- ✅ 处理用户对话
- ✅ 管理用户会话记忆
- ✅ 生成对话响应
- ✅ 业务逻辑处理

### 5.3 调用关系

```python
# Agent API 内部调用 Cognee API
class AgentAPI:
    async def process_message(self, message: str):
        # 1. 调用 Cognee API 搜索专业记忆
        professional_results = await cognee.search(
            query=message,
            datasets=["medical_knowledge"]
        )
        
        # 2. 调用 Cognee API 搜索会话记忆
        conversation_results = await cognee.search(
            query=message,
            datasets=[f"conversation_{user_id}"]
        )
        
        # 3. 生成响应
        response = generate_response(professional_results, conversation_results)
        
        # 4. 调用 Cognee API 保存对话
        await cognee.add(
            data=response,
            dataset_name=f"conversation_{user_id}"
        )
```

---

## 六、在部署架构中的作用

### 6.1 服务配置

```yaml
# docker-compose.yml 中的配置
cognee-api:
  container_name: cognee-api
  environment:
    # 数据库连接
    DATABASE_URL: postgresql://cognee:password@postgres:5432/cognee
    VECTOR_DB_PROVIDER: pgvector
    GRAPH_DATABASE_PROVIDER: neo4j
    
    # Neo4j 配置
    NEO4J_URI: bolt://neo4j:7687
    NEO4J_USER: neo4j
    NEO4J_PASSWORD: neo4j123
    
    # MinIO 配置
    MINIO_ENDPOINT: minio:9000
    MINIO_ACCESS_KEY: minioadmin
    MINIO_SECRET_KEY: minioadmin123
    
    # LLM 配置
    LLM_API_KEY: your_key
    LLM_PROVIDER: openai
  ports:
    - "8000:8000"
```

### 6.2 服务依赖关系

```
PostgreSQL ──┐
             ├──> Cognee API ──┐
Neo4j ───────┤                 ├──> Agent API
             │                 │
MinIO ───────┘                 │
                               │
Redis ─────────────────────────┘
```

### 6.3 访问方式

#### 1. 直接访问（开发/测试）
```bash
curl http://localhost:8000/api/v1/datasets
```

#### 2. 通过 Nginx 网关（生产环境）
```bash
curl https://yourdomain.com/api/v1/datasets
```

#### 3. 通过 Cognee UI
- UI 自动调用 `http://localhost:8000/api/v1/*`

#### 4. 通过 Agent API
- Agent API 内部调用 Cognee API

---

## 七、API 文档和测试

### 7.1 API 文档

启动服务后，访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 7.2 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细健康检查
curl http://localhost:8000/health/detailed
```

---

## 八、总结

### Cognee API 服务层的核心价值

1. **标准化接口**：提供统一的知识图谱操作接口
2. **功能完整**：涵盖所有核心操作（Add、Cognify、Search 等）
3. **易于集成**：RESTful API，易于与其他系统集成
4. **官方支持**：Cognee 官方维护，稳定可靠

### 在您的架构中的角色

- **基础服务**：为 Agent API 和 Cognee UI 提供底层支持
- **数据管理**：通过 UI 维护专业数据集
- **知识图谱操作**：所有知识图谱操作都通过它完成

### 关键要点

✅ **Cognee API 是必须的**：它是整个系统的核心服务  
✅ **独立运行**：可以独立部署和运行  
✅ **被其他服务调用**：Agent API 和 Cognee UI 都依赖它  
✅ **提供完整功能**：包含知识图谱的所有操作接口

---

## 九、常见问题

### Q1: Cognee API 和 Agent API 必须分开部署吗？

**A**: 不是必须的，但建议分开：
- **分开部署**：服务解耦，易于扩展和维护
- **合并部署**：可以，但会增加服务复杂度

### Q2: Cognee UI 可以直接使用吗？

**A**: 可以，但需要 Cognee API 运行：
```bash
# 启动 Cognee API
cognee start-api

# 启动 Cognee UI（会自动连接到 API）
cognee start-ui
```

### Q3: 如何验证 Cognee API 是否正常工作？

**A**: 
```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 查看 API 文档
浏览器打开 http://localhost:8000/docs

# 3. 测试 API
curl -X GET http://localhost:8000/api/v1/datasets
```

