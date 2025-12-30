# Agent 部署架构设计

## 一、架构问题分析与解决方案

### 1.1 混合搜索性能优化

#### 问题分析
混合搜索同时查询多个数据集（专业记忆 + 用户会话记忆），可能导致：
- 搜索时间过长
- 数据库负载高
- 用户体验差

#### 解决方案

**策略1：并行搜索 + 结果合并**
```python
# 并行执行多个搜索，而不是串行
async def optimized_hybrid_search(user_id: str, query: str, user: User):
    # 并行搜索专业记忆和会话记忆
    professional_task = cognee.search(
        query_text=query,
        datasets=["medical_knowledge", "psychology_knowledge"],
        top_k=5
    )
    
    conversation_task = cognee.search(
        query_text=query,
        datasets=[f"conversation_{user_id}"],
        user=user,
        top_k=3
    )
    
    # 并行执行
    professional_results, conversation_results = await asyncio.gather(
        professional_task,
        conversation_task
    )
    
    return merge_results(professional_results, conversation_results)
```

**策略2：Redis 缓存层**
- 缓存常见查询的专业记忆结果（TTL: 1小时）
- 缓存用户会话记忆的最近查询（TTL: 15分钟）
- 使用查询哈希作为缓存键

**策略3：智能路由**
- 根据查询类型决定搜索范围
- 专业问题 → 只搜索专业记忆
- 个人问题 → 只搜索会话记忆
- 混合问题 → 并行搜索

**策略4：分阶段搜索**
- 第一阶段：快速向量搜索（top_k=20）
- 第二阶段：图遍历和关系推理（top_k=5）
- 第三阶段：LLM 生成最终答案

---

### 1.2 Cognee UI 集成

Cognee UI 需要：
- 后端 API 服务运行在指定端口（默认 8000）
- 前端 UI 服务运行在指定端口（默认 3000）
- 通过 API 访问数据集进行维护

**部署方案**：
- Cognee API 作为独立服务运行
- UI 通过 API 访问专业数据集
- 管理员通过 UI 维护专业记忆

---

## 二、完整部署架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Web UI      │  │  Agent API   │  │  Cognee UI   │          │
│  │  (Next.js)   │  │  (FastAPI)   │  │  (Cognee)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼─────────────────┼──────────────────┘
          │                  │                 │
          └──────────────────┴─────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │         API Gateway / Nginx         │
          │      (负载均衡、SSL终止、路由)        │
          └──────────────────┬──────────────────┘
                             │
┌────────────────────────────┼────────────────────────────┐
│                            │                            │
│  ┌─────────────────────────▼─────────────────────────┐ │
│  │            Cognee API 服务层                        │ │
│  │  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │  Agent API   │  │  Cognee API   │              │ │
│  │  │  Service     │  │  Service      │              │ │
│  │  └──────┬───────┘  └──────┬───────┘              │ │
│  └─────────┼──────────────────┼──────────────────────┘ │
│            │                  │                           │
│  ┌─────────▼──────────────────▼──────────────────────┐  │
│  │              Redis 缓存层                          │  │
│  │  - 查询结果缓存                                     │  │
│  │  - 会话状态缓存                                     │  │
│  │  - 用户权限缓存                                     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │              数据存储层                              │  │
│  │                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │  PostgreSQL  │  │   pgvector    │              │  │
│  │  │  (关系数据)  │  │  (向量数据)   │              │  │
│  │  └──────┬───────┘  └──────┬───────┘              │  │
│  │         │                  │                        │  │
│  │         └────────┬─────────┘                        │  │
│  │                  │                                  │  │
│  │         ┌─────────▼─────────┐                       │  │
│  │         │   PostgreSQL      │                       │  │
│  │         │   (主数据库)      │                       │  │
│  │         └───────────────────┘                       │  │
│  │                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │   Neo4j      │  │    MinIO      │              │  │
│  │  │  (图数据库)  │  │  (文件存储)   │              │  │
│  │  └──────────────┘  └──────────────┘              │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## 三、组件详细设计

### 3.1 服务组件

#### Agent API Service
- **功能**：处理用户对话、管理会话记忆
- **技术栈**：FastAPI + Python
- **端口**：8001
- **职责**：
  - 用户对话处理
  - 会话记忆管理
  - 混合搜索协调
  - 响应生成

#### Cognee API Service
- **功能**：Cognee 核心 API，处理知识图谱操作
- **技术栈**：Cognee + FastAPI
- **端口**：8000
- **职责**：
  - 数据集管理
  - 数据添加和认知化
  - 知识图谱查询
  - UI 数据维护接口

#### Cognee UI
- **功能**：Web 界面，维护专业数据集
- **技术栈**：Next.js (Cognee 自带)
- **端口**：3000
- **职责**：
  - 专业数据集可视化
  - 文档上传和管理
  - 知识图谱浏览
  - 数据集配置

---

### 3.2 数据存储组件

#### PostgreSQL (主数据库)
- **用途**：关系型数据存储
- **存储内容**：
  - 用户信息
  - 数据集元数据
  - 权限信息
  - 文档元数据
- **配置**：
  ```yaml
  version: '15'
  extensions:
    - uuid-ossp
    - pg_trgm  # 文本搜索
  ```

#### pgvector (向量数据库)
- **用途**：存储嵌入向量
- **存储内容**：
  - 文档块嵌入
  - 查询嵌入
  - 语义相似度搜索
- **配置**：
  ```sql
  CREATE EXTENSION vector;
  -- 在 PostgreSQL 中创建向量表
  ```

#### Neo4j (图数据库)
- **用途**：知识图谱存储
- **存储内容**：
  - 实体节点
  - 关系边
  - 节点集
  - 图遍历查询
- **配置**：
  ```yaml
  version: '5'
  memory: '2g'
  ```

#### MinIO (对象存储)
- **用途**：文件存储
- **存储内容**：
  - 原始文档文件
  - 处理后的文件
  - 临时文件
- **配置**：
  ```yaml
  buckets:
    - cognee-documents
    - cognee-processed
    - cognee-temp
  ```

#### Redis (缓存)
- **用途**：缓存层
- **存储内容**：
  - 查询结果缓存
  - 用户会话状态
  - 权限信息缓存
  - 热点数据
- **配置**：
  ```yaml
  maxmemory: 2gb
  maxmemory-policy: allkeys-lru
  ```

---

## 四、Docker Compose 部署配置

### 4.1 完整 docker-compose.yml

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
      POSTGRES_INITDB_ARGS: "-E UTF8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts/init-pgvector.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cognee"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cognee-network

  neo4j:
    image: neo4j:5.15.0
    container_name: cognee-neo4j
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-neo4j123}
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_dbms_memory_heap_max__size: 2G
      NEO4J_dbms_memory_pagecache_size: 1G
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - neo4j_plugins:/plugins
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD:-neo4j123}", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cognee-network

  minio:
    image: minio/minio:latest
    container_name: cognee-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin123}
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
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
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - cognee-network

  # ==================== 应用服务 ====================

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
      
      # Neo4j 配置
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD:-neo4j123}
      
      # MinIO 配置
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minioadmin123}
      MINIO_BUCKET: cognee-documents
      MINIO_USE_SSL: "false"
      
      # Redis 配置
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_DB: 0
      
      # LLM 配置
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_PROVIDER: ${LLM_PROVIDER:-openai}
      LLM_MODEL: ${LLM_MODEL:-gpt-4}
      
      # 其他配置
      COGNEE_DATA_ROOT: /app/data
      COGNEE_SYSTEM_ROOT: /app/system
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
      minio:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - cognee-network
    restart: unless-stopped

  agent-api:
    build:
      context: .
      dockerfile: Dockerfile.agent-api
    container_name: agent-api
    environment:
      # Cognee API 地址
      COGNEE_API_URL: http://cognee-api:8000
      
      # Redis 配置（用于缓存）
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_DB: 1
      
      # LLM 配置
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_PROVIDER: ${LLM_PROVIDER:-openai}
      LLM_MODEL: ${LLM_MODEL:-gpt-4}
    ports:
      - "8001:8001"
    depends_on:
      - cognee-api
      - redis
    networks:
      - cognee-network
    restart: unless-stopped

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
      - cognee-api
    networks:
      - cognee-network
    restart: unless-stopped

  # ==================== 网关服务 ====================

  nginx:
    image: nginx:alpine
    container_name: cognee-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - cognee-api
      - agent-api
      - cognee-ui
    networks:
      - cognee-network
    restart: unless-stopped

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  neo4j_plugins:
  minio_data:
  redis_data:

networks:
  cognee-network:
    driver: bridge
```

---

## 五、配置文件

### 5.1 PostgreSQL 初始化脚本 (init-pgvector.sql)

```sql
-- 创建 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建文本搜索扩展
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 创建 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 验证扩展
SELECT * FROM pg_extension WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp');
```

### 5.2 Nginx 配置 (nginx/nginx.conf)

```nginx
upstream cognee_api {
    server cognee-api:8000;
}

upstream agent_api {
    server agent-api:8001;
}

upstream cognee_ui {
    server cognee-ui:3000;
}

server {
    listen 80;
    server_name localhost;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name localhost;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Cognee API
    location /api/v1/ {
        proxy_pass http://cognee_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Agent API
    location /agent/ {
        proxy_pass http://agent_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cognee UI
    location / {
        proxy_pass http://cognee_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5.3 环境变量文件 (.env)

```env
# 数据库密码
POSTGRES_PASSWORD=cognee123
NEO4J_PASSWORD=neo4j123

# MinIO 配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# LLM 配置
LLM_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# 其他配置
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## 六、Dockerfile

### 6.1 Dockerfile.cognee-api

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-cognee.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements-cognee.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/system

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "cognee.api.client:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 Dockerfile.agent-api

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-agent.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements-agent.txt

# 复制应用代码
COPY agent_implementation_example.py .
COPY agent_api.py .

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["python", "-m", "uvicorn", "agent_api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 6.3 Dockerfile.cognee-ui

```dockerfile
FROM node:18-alpine

WORKDIR /app

# 安装 Cognee（包含 UI）
RUN npm install -g cognee

# 或者从源码构建
# COPY cognee-frontend/ .
# RUN npm install && npm run build

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["cognee", "start-ui", "--port", "3000", "--start-backend", "false"]
```

---

## 七、性能优化策略

### 7.1 搜索性能优化

#### 缓存策略
```python
# Redis 缓存配置
CACHE_CONFIG = {
    "professional_knowledge": {
        "ttl": 3600,  # 1小时
        "key_prefix": "pro_knowledge:"
    },
    "user_conversation": {
        "ttl": 900,  # 15分钟
        "key_prefix": "user_conv:"
    },
    "search_results": {
        "ttl": 1800,  # 30分钟
        "key_prefix": "search:"
    }
}
```

#### 并行搜索实现
```python
import asyncio
import redis
import json
import hashlib

redis_client = redis.Redis(host='redis', port=6379, db=0)

async def cached_hybrid_search(user_id: str, query: str, user: User):
    # 生成缓存键
    query_hash = hashlib.md5(query.encode()).hexdigest()
    cache_key = f"search:{user_id}:{query_hash}"
    
    # 检查缓存
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # 并行搜索
    professional_task = search_professional_knowledge(query, top_k=5)
    conversation_task = search_user_conversation(user_id, query, user, top_k=3)
    
    professional_results, conversation_results = await asyncio.gather(
        professional_task,
        conversation_task
    )
    
    # 合并结果
    results = {
        "professional": professional_results,
        "conversation": conversation_results
    }
    
    # 缓存结果（30分钟）
    redis_client.setex(
        cache_key,
        1800,
        json.dumps(results)
    )
    
    return results
```

### 7.2 数据库连接池

```python
# PostgreSQL 连接池配置
DATABASE_POOL_CONFIG = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}

# Neo4j 连接池配置
NEO4J_POOL_CONFIG = {
    "max_connection_lifetime": 3600,
    "max_connection_pool_size": 50
}
```

---

## 八、监控与日志

### 8.1 健康检查端点

```python
# Agent API 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "postgres": await check_postgres(),
            "neo4j": await check_neo4j(),
            "redis": await check_redis(),
            "minio": await check_minio(),
            "cognee_api": await check_cognee_api()
        }
    }
```

### 8.2 日志配置

```python
# 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/agent.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "console": {
            "class": "logging.StreamHandler"
        }
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "INFO"
    }
}
```

---

## 九、部署步骤

### 9.1 初始化步骤

```bash
# 1. 克隆项目
git clone <your-repo>
cd usecognee

# 2. 创建环境变量文件
cp .env.example .env
# 编辑 .env 文件，填入配置

# 3. 创建必要的目录
mkdir -p data system logs nginx/ssl

# 4. 启动服务
docker-compose up -d

# 5. 等待服务就绪
docker-compose ps

# 6. 初始化数据库
docker-compose exec postgres psql -U cognee -d cognee -f /docker-entrypoint-initdb.d/init.sql

# 7. 初始化 MinIO buckets
docker-compose exec minio mc mb /data/cognee-documents
docker-compose exec minio mc mb /data/cognee-processed
docker-compose exec minio mc mb /data/cognee-temp

# 8. 初始化专业数据集（通过 API 或脚本）
python initialize_professional_datasets.py
```

### 9.2 访问服务

- **Cognee UI**: http://localhost:3000
- **Cognee API**: http://localhost:8000
- **Agent API**: http://localhost:8001
- **Nginx Gateway**: http://localhost (通过 Nginx 路由)
- **Neo4j Browser**: http://localhost:7474
- **MinIO Console**: http://localhost:9001

---

## 十、总结

### 10.1 架构优势

1. **性能优化**：
   - Redis 缓存减少数据库查询
   - 并行搜索提高响应速度
   - 连接池优化数据库性能

2. **可扩展性**：
   - 服务分离，易于横向扩展
   - 数据库独立，可按需扩容
   - 缓存层支持高并发

3. **可维护性**：
   - Cognee UI 可视化维护专业数据集
   - 服务容器化，易于部署
   - 配置集中管理

4. **高可用性**：
   - 健康检查确保服务可用
   - 数据持久化存储
   - 服务自动重启

### 10.2 关键配置要点

1. **数据库连接**：确保所有服务能正确连接到数据库
2. **缓存策略**：合理设置 TTL，平衡性能和一致性
3. **权限管理**：通过 Cognee 权限系统控制数据集访问
4. **监控告警**：设置监控和告警，及时发现问题

