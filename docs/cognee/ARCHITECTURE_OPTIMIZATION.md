# 架构优化方案：分离 Cognee API 和 Agent API

## 一、架构设计思路

### 1.1 核心概念

**两种使用 Cognee 的方式**：

1. **Python SDK 方式**（Agent API 使用）
   - 直接导入 `cognee` 库
   - 在代码中直接调用函数
   - **不需要启动 HTTP API 服务**
   - 性能更好，延迟更低

2. **HTTP API 方式**（Cognee UI 使用）
   - 启动独立的 Cognee API 服务
   - 通过 HTTP 请求调用
   - 适合 Web 界面和远程调用

### 1.2 优化后的架构

```
┌─────────────────────────────────────────────────────────┐
│                    客户端层                               │
│  ┌──────────────┐              ┌──────────────┐          │
│  │  Cognee UI  │              │  Agent API   │          │
│  │  (Web界面)  │              │  (用户对话)  │          │
│  └──────┬───────┘              └──────┬───────┘          │
└─────────┼────────────────────────────┼──────────────────┘
          │                            │
          │ HTTP API                   │ Python SDK
          │                            │ (直接调用)
          ▼                            ▼
┌──────────────────┐          ┌──────────────────┐
│  Cognee API      │          │  Agent API       │
│  (独立服务)       │          │  (直接使用库)     │
│  端口: 8000      │          │  端口: 8001      │
│                  │          │                  │
│  用途:           │          │  用途:           │
│  - UI 管理       │          │  - 处理对话      │
│  - 专业数据集维护 │          │  - 搜索知识库    │
│  - 可视化         │          │  - 保存会话记忆   │
└────────┬─────────┘          └────────┬─────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
         ┌──────────▼──────────┐
         │   数据存储层          │
         │  PostgreSQL/Neo4j   │
         └──────────────────────┘
```

---

## 二、架构优势

### 2.1 性能优势

| 对比项 | HTTP API 方式 | Python SDK 方式 |
|--------|--------------|----------------|
| **延迟** | 网络延迟 + 处理时间 | 仅处理时间 |
| **吞吐量** | 受 HTTP 限制 | 更高 |
| **资源消耗** | 需要 HTTP 服务器 | 直接调用 |
| **适用场景** | Web 界面、远程调用 | 内部服务调用 |

### 2.2 职责分离

- **Cognee API 服务**：
  - ✅ 专门为 Cognee UI 提供 HTTP 接口
  - ✅ 管理专业数据集（医学、心理学等）
  - ✅ 可视化知识图谱
  - ✅ 文档上传和管理

- **Agent API**：
  - ✅ 直接使用 cognee Python SDK
  - ✅ 处理用户对话
  - ✅ 搜索知识库（直接调用，无 HTTP 开销）
  - ✅ 管理用户会话记忆

---

## 三、实现方案

### 3.1 Agent API 使用 Python SDK

```python
# agent_api.py
"""
Agent API - 直接使用 Cognee Python SDK
不需要启动 Cognee HTTP API
"""
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import cognee  # 直接导入库
from cognee.modules.users.models import User
from cognee.modules.users.methods import get_authenticated_user
from cognee.modules.search.types import SearchType

app = FastAPI(title="Agent API")

# 初始化 Cognee（不启动 API 服务）
@app.on_event("startup")
async def startup():
    """启动时初始化 Cognee SDK"""
    await cognee.setup()  # 只初始化，不启动 HTTP 服务
    print("✅ Cognee SDK 已初始化（无 HTTP API）")


class ChatRequest(BaseModel):
    message: str
    user_id: str


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(get_authenticated_user)
):
    """处理用户对话 - 直接使用 Cognee SDK"""
    try:
        # 直接调用 cognee.search，无需 HTTP 请求
        professional_results = await cognee.search(
            query_text=request.message,
            datasets=["medical_knowledge", "psychology_knowledge"],
            query_type=SearchType.GRAPH_COMPLETION,
            top_k=5
        )
        
        # 搜索用户会话记忆
        conversation_dataset = f"conversation_{request.user_id}"
        conversation_results = await cognee.search(
            query_text=request.message,
            datasets=[conversation_dataset],
            user=user,
            query_type=SearchType.GRAPH_COMPLETION,
            top_k=3
        )
        
        # 生成响应（简化示例）
        response = f"基于专业知识：{professional_results}\n基于对话历史：{conversation_results}"
        
        # 保存对话 - 直接调用 SDK
        await cognee.add(
            data=f"用户: {request.message}\n助手: {response}",
            dataset_name=conversation_dataset,
            user=user
        )
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # 只启动 Agent API，不启动 Cognee API
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 3.2 独立的 Cognee API 服务

```python
# cognee_api_service.py
"""
独立的 Cognee API 服务
专门为 Cognee UI 提供 HTTP 接口
"""
import uvicorn
from cognee.api.client import app  # 使用 Cognee 官方的 API

if __name__ == "__main__":
    # 启动独立的 Cognee API 服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
```

或者使用命令行：

```bash
# 启动独立的 Cognee API 服务
python -m uvicorn cognee.api.client:app --host 0.0.0.0 --port 8000
```

---

## 四、Docker Compose 配置

### 4.1 优化后的配置

```yaml
version: '3.8'

services:
  # ==================== 数据库服务 ====================
  postgres:
    image: pgvector/pgvector:pg15
    container_name: cognee-postgres
    environment:
      POSTGRES_USER: cognee
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cognee123}
      POSTGRES_DB: cognee
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - cognee-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cognee"]
      interval: 10s
      timeout: 5s
      retries: 5

  neo4j:
    image: neo4j:5.15.0
    container_name: cognee-neo4j
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-neo4j123}
      NEO4J_dbms_memory_heap_max__size: 2G
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
    networks:
      - cognee-network
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD:-neo4j123}", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: cognee-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin123}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - cognee-network

  redis:
    image: redis:7-alpine
    container_name: cognee-redis
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - cognee-network

  # ==================== 应用服务 ====================

  # Cognee API 服务 - 专门为 UI 提供接口
  cognee-api:
    build:
      context: .
      dockerfile: Dockerfile.cognee-api
    container_name: cognee-api
    environment:
      # 数据库配置
      DATABASE_URL: postgresql://cognee:${POSTGRES_PASSWORD:-cognee123}@postgres:5432/cognee
      VECTOR_DB_PROVIDER: pgvector
      GRAPH_DATABASE_PROVIDER: neo4j
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD:-neo4j123}
      
      # MinIO 配置
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minioadmin123}
      
      # LLM 配置
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_PROVIDER: ${LLM_PROVIDER:-openai}
      LLM_MODEL: ${LLM_MODEL:-gpt-4}
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./system:/app/system
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_healthy
    networks:
      - cognee-network
    restart: unless-stopped
    # 用途：专门为 Cognee UI 提供 HTTP API，管理专业数据集

  # Agent API - 直接使用 Cognee SDK，不启动 HTTP API
  agent-api:
    build:
      context: .
      dockerfile: Dockerfile.agent-api
    container_name: agent-api
    environment:
      # 数据库配置（直接连接，不通过 HTTP）
      DATABASE_URL: postgresql://cognee:${POSTGRES_PASSWORD:-cognee123}@postgres:5432/cognee
      VECTOR_DB_PROVIDER: pgvector
      GRAPH_DATABASE_PROVIDER: neo4j
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD:-neo4j123}
      
      # MinIO 配置
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minioadmin123}
      
      # Redis 配置
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_DB: 1
      
      # LLM 配置
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_PROVIDER: ${LLM_PROVIDER:-openai}
      LLM_MODEL: ${LLM_MODEL:-gpt-4}
      
      # 重要：不需要 COGNEE_API_URL，因为直接使用 SDK
    ports:
      - "8001:8001"
    volumes:
      - ./data:/app/data
      - ./system:/app/system
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - cognee-network
    restart: unless-stopped
    # 用途：处理用户对话，直接使用 Cognee SDK，性能更好

  # Cognee UI - 连接到独立的 Cognee API
  cognee-ui:
    build:
      context: .
      dockerfile: Dockerfile.cognee-ui
    container_name: cognee-ui
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      COGNEE_API_URL: http://cognee-api:8000
    ports:
      - "3000:3000"
    depends_on:
      - cognee-api  # 依赖独立的 Cognee API 服务
    networks:
      - cognee-network
    restart: unless-stopped

volumes:
  postgres_data:
  neo4j_data:
  minio_data:
  redis_data:

networks:
  cognee-network:
    driver: bridge
```

---

## 五、Dockerfile 配置

### 5.1 Dockerfile.cognee-api

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc g++ postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements-cognee.txt .
RUN pip install --no-cache-dir -r requirements-cognee.txt

# 启动 Cognee API 服务
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "cognee.api.client:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 Dockerfile.agent-api

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（包含 cognee）
COPY requirements-agent.txt .
RUN pip install --no-cache-dir -r requirements-agent.txt

# 复制 Agent API 代码
COPY agent_api.py .

# 启动 Agent API（不启动 Cognee API）
EXPOSE 8001

CMD ["python", "-m", "uvicorn", "agent_api:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 六、启动方式

### 6.1 开发环境

```bash
# 终端1：启动独立的 Cognee API（供 UI 使用）
python -m uvicorn cognee.api.client:app --host 0.0.0.0 --port 8000

# 终端2：启动 Agent API（直接使用 SDK）
python agent_api.py

# 终端3：启动 Cognee UI（可选）
cognee start-ui
```

### 6.2 生产环境

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f agent-api
docker-compose logs -f cognee-api
```

---

## 七、数据共享

### 7.1 共享数据存储

两个服务共享同一个数据存储：

```
┌─────────────────────────────────┐
│     数据存储层（共享）            │
│  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │  Neo4j   │   │
│  └──────────┘  └──────────┘   │
└─────────────────────────────────┘
         ▲                ▲
         │                │
    ┌────┴────┐      ┌────┴────┐
    │Cognee   │      │ Agent   │
    │API      │      │ API     │
    │(UI管理) │      │(SDK调用)│
    └─────────┘      └─────────┘
```

### 7.2 数据集访问

- **专业数据集**（medical_knowledge, psychology_knowledge）：
  - Cognee API：通过 UI 管理（添加、删除、更新）
  - Agent API：通过 SDK 读取和搜索

- **用户会话数据集**（conversation_{user_id}）：
  - Agent API：通过 SDK 创建和管理
  - Cognee API：通常不需要访问

---

## 八、优势总结

### 8.1 性能优势

✅ **Agent API 性能提升**：
- 无 HTTP 网络延迟
- 直接函数调用，速度更快
- 减少序列化/反序列化开销

✅ **资源优化**：
- Agent API 不需要运行 HTTP 服务器
- 减少内存和 CPU 占用

### 8.2 架构优势

✅ **职责清晰**：
- Cognee API：专门为 UI 服务
- Agent API：专门处理业务逻辑

✅ **易于维护**：
- 服务独立，互不干扰
- 可以独立升级和扩展

✅ **灵活性**：
- UI 可以通过 HTTP 远程访问
- Agent API 可以部署在任意位置

---

## 九、注意事项

### 9.1 数据库连接

两个服务需要连接**同一个数据库**：
- 确保 `DATABASE_URL` 相同
- 确保 `NEO4J_URI` 相同
- 确保数据目录共享（如果使用文件存储）

### 9.2 初始化顺序

建议启动顺序：
1. 数据库服务（PostgreSQL, Neo4j, MinIO, Redis）
2. Cognee API 服务（初始化数据库结构）
3. Agent API 服务
4. Cognee UI

### 9.3 权限管理

两个服务使用**相同的用户和权限系统**：
- 共享用户数据库
- 共享权限配置
- 确保一致性

---

## 十、总结

这种架构设计的核心思想：

1. **Cognee API**：独立的 HTTP 服务，专门为 UI 提供接口
2. **Agent API**：直接使用 Cognee Python SDK，无需 HTTP 开销
3. **数据共享**：两个服务共享同一个数据存储层
4. **职责分离**：UI 管理专业数据集，Agent 处理用户对话

**优势**：
- ✅ 性能更好（Agent API 无 HTTP 延迟）
- ✅ 架构更清晰（职责分离）
- ✅ 易于维护（服务独立）
- ✅ 资源利用更高效

**适用场景**：
- ✅ 生产环境部署
- ✅ 需要高性能的场景
- ✅ 需要 UI 管理专业数据集的场景

