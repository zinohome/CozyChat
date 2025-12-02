# Cognee 配置指南

> **版本**: v1.0  
> **创建日期**: 2025-01-XX  
> **状态**: 📋 配置说明

---

## 📋 配置概述

Cognee 的所有配置都在 `backend/config/memory.yaml` 中，代码只读取配置，不硬编码任何值。

---

## 🔧 数据库连接配置

### 重要说明

**开发环境 vs 生产环境**：

- **开发环境**（本地开发）：
  - 使用 **IP 地址**（如 `192.168.66.11`）
  - 因为 CozyChat 项目可能不在 Docker 网络中运行

- **生产环境**（Docker 内部）：
  - 可以使用 **服务名**（如 `postgres`、`neo4j`）
  - 因为所有服务都在同一个 Docker 网络中

### 配置示例

```yaml
# backend/config/memory.yaml
memory:
  cognee:
    # ==================== 数据库配置 ====================
    # 开发环境：使用 IP 地址
    database_url: "postgresql://cognee_user:cognee_password@192.168.66.11:5432/cognee_db"
    
    # 生产环境（Docker 内部）：可使用服务名
    # database_url: "postgresql://cognee_user:cognee_password@postgres:5432/cognee_db"
    
    # ==================== 图数据库配置 ====================
    # 开发环境：使用 IP 地址
    graph_database_url: "bolt://192.168.66.11:7687"
    
    # 生产环境（Docker 内部）：可使用服务名
    # graph_database_url: "bolt://neo4j:7687"
    
    # ==================== Redis 配置 ====================
    # 开发环境：使用 IP 地址
    redis_url: "redis://:cognee_redis_password@192.168.66.11:6379/0"
    
    # 生产环境（Docker 内部）：可使用服务名
    # redis_url: "redis://:cognee_redis_password@redis:6379/0"
    
    # ==================== MinIO 配置 ====================
    # 开发环境：使用 IP 地址
    s3_endpoint: "http://192.168.66.11:9000"
    
    # 生产环境（Docker 内部）：可使用服务名
    # s3_endpoint: "http://minio:9000"
```

---

## 📝 完整配置说明

### 1. 数据库配置

```yaml
cognee:
  # PostgreSQL 关系数据库
  database_url: "postgresql://cognee_user:cognee_password@192.168.66.11:5432/cognee_db"
  vector_db_provider: "pgvector"
```

**说明**：
- `database_url`: PostgreSQL 连接 URL
  - 开发环境：`postgresql://cognee_user:cognee_password@192.168.66.11:5432/cognee_db`
  - 生产环境：`postgresql://cognee_user:cognee_password@postgres:5432/cognee_db`
- `vector_db_provider`: 向量数据库提供商，使用 `pgvector`（向量数据存储在 PostgreSQL 中）

### 2. 图数据库配置

```yaml
cognee:
  graph_database_provider: "neo4j"
  graph_database_url: "bolt://192.168.66.11:7687"
  graph_database_username: "neo4j"
  graph_database_password: "pleaseletmein"
```

**说明**：
- `graph_database_url`: Neo4j 连接 URL
  - 开发环境：`bolt://192.168.66.11:7687`
  - 生产环境：`bolt://neo4j:7687`

### 3. Redis 配置

```yaml
cognee:
  redis_url: "redis://:cognee_redis_password@192.168.66.11:6379/0"
```

**说明**：
- `redis_url`: Redis 连接 URL（用于异步队列）
  - 开发环境：`redis://:cognee_redis_password@192.168.66.11:6379/0`
  - 生产环境：`redis://:cognee_redis_password@redis:6379/0`

### 4. MinIO/S3 配置

```yaml
cognee:
  s3_endpoint: "http://192.168.66.11:9000"
  s3_access_key: "minioadmin"
  s3_secret_key: "minioadmin"
  s3_bucket_name: "cognee-storage"
  s3_use_ssl: false
```

**说明**：
- `s3_endpoint`: MinIO 服务地址
  - 开发环境：`http://192.168.66.11:9000`
  - 生产环境：`http://minio:9000`

---

## 🔄 环境切换

### 开发环境配置

```yaml
cognee:
  database_url: "postgresql://cognee_user:cognee_password@192.168.66.11:5432/cognee_db"
  graph_database_url: "bolt://192.168.66.11:7687"
  redis_url: "redis://:cognee_redis_password@192.168.66.11:6379/0"
  s3_endpoint: "http://192.168.66.11:9000"
```

### 生产环境配置（Docker 内部）

```yaml
cognee:
  database_url: "postgresql://cognee_user:cognee_password@postgres:5432/cognee_db"
  graph_database_url: "bolt://neo4j:7687"
  redis_url: "redis://:cognee_redis_password@redis:6379/0"
  s3_endpoint: "http://minio:9000"
```

---

## ⚙️ 环境变量支持（可选）

虽然配置主要在 YAML 中，但某些敏感信息（如 API Key）支持环境变量覆盖：

```bash
# LLM API Key
export LLM_API_KEY=sk-xxx

# Embedding API Key
export EMBEDDING_API_KEY=sk-xxx

# LLM Endpoint（可选）
export LLM_ENDPOINT=https://oneapi.naivehero.top/v1

# Embedding Endpoint（可选）
export EMBEDDING_ENDPOINT=https://oneapi.naivehero.top/v1
```

代码会优先使用环境变量，如果没有则使用 YAML 配置中的值。

---

## ✅ 配置验证

配置加载后，代码会验证所有必需的配置项：

```python
# 必需的配置项
required_configs = [
    "database_url",
    "redis_url",
    "s3_endpoint"
]

for key in required_configs:
    if not config.get(key):
        raise ValueError(f"Cognee {key} is required in config")
```

---

## 📌 注意事项

1. **独立数据库**：Cognee 使用独立的数据库，不能复用项目数据库
2. **IP vs 服务名**：开发环境使用 IP，生产环境可使用服务名
3. **网络连通性**：确保 CozyChat 能够访问 192.168.66.11 上的服务
4. **端口映射**：确保端口已正确映射（5432、7687、6379、9000）

---

**文档版本**: v1.0  
**最后更新**: 2025-01-XX  
**维护者**: CozyChat Team

