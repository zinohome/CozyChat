# Qdrant记忆引擎 - 快速参考

## 🚀 5分钟快速开始

### 1. 启动Qdrant服务

```bash
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

### 2. 安装依赖

```bash
pip install qdrant-client==1.11.3 sentence-transformers==2.3.1
```

### 3. 配置引擎

编辑 `.env`:
```bash
QDRANT_URL=http://localhost:6333
```

编辑 `config/memory.yaml`:
```yaml
memory:
  default_engine: "qdrant"
```

### 4. 运行测试

```bash
pytest tests/test_engines/test_memory/test_qdrant_engine.py -v
```

## 📚 API使用

### 基础操作

```python
from app.engines.memory import MemoryManager, Memory, MemoryType

# 创建管理器
manager = MemoryManager()

# 添加记忆
memory = Memory(
    id="mem-001",
    user_id="user-123",
    session_id="session-456",
    memory_type=MemoryType.USER,
    content="我喜欢Python编程",
    importance=0.8
)
await manager.add_memory_async(memory)

# 搜索记忆
results = await manager.search_memories(
    query="编程",
    user_id="user-123",
    limit=5,
    similarity_threshold=0.7
)

# 删除记忆
await manager.delete_memory("mem-001", "user-123")

# 获取统计
stats = await manager.get_memory_stats("user-123")
```

### 高级功能

```python
# 按会话搜索
results = await manager.search_memories(
    query="Python",
    user_id="user-123",
    session_id="session-456",  # 限定会话
    limit=5
)

# 按类型搜索
results = await manager.search_memories(
    query="Python",
    user_id="user-123",
    memory_type=MemoryType.USER,  # 只搜索用户记忆
    limit=5
)

# 删除会话记忆
count = await manager.delete_session_memories(
    user_id="user-123",
    session_id="session-456"
)

# 自定义向量
memory = Memory(
    id="mem-002",
    user_id="user-123",
    session_id="session-456",
    memory_type=MemoryType.USER,
    content="Test",
    embedding=[0.1] * 384  # 自定义向量
)
await manager.add_memory_async(memory)
```

## 🔧 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `QDRANT_URL` | Qdrant服务地址 | `http://localhost:6333` |
| `QDRANT_API_KEY` | API密钥（可选） | - |

### YAML配置

```yaml
memory:
  default_engine: "qdrant"
  
  qdrant:
    engine: "qdrant"
    url: "http://localhost:6333"
    collection_prefix: "cozychat_"
    embedding:
      model: "all-MiniLM-L6-v2"
      dimension: 384
    performance:
      batch_size: 100
      max_retries: 3
  
  cache:
    enabled: true
    ttl_seconds: 300
    max_size: 100
```

### 代码配置

```python
from app.engines.memory import QdrantMemoryEngine, MemoryManager

# 自定义配置
config = {
    "url": "http://localhost:6333",
    "api_key": "your_key",
    "collection_prefix": "myapp_",
    "embedding": {
        "model": "all-MiniLM-L6-v2",
        "dimension": 384
    }
}

engine = QdrantMemoryEngine(config=config)
manager = MemoryManager(
    engine=engine,
    cache_ttl=600,
    cache_maxsize=200,
    search_timeout=1.0
)
```

## 📊 性能基准

基于1000条记忆的测试结果：

| 操作 | ChromaDB | Qdrant | 提升 |
|------|----------|--------|------|
| 添加单条 | 10ms | 8ms | 20% ↑ |
| 批量添加(100) | 200ms | 150ms | 25% ↑ |
| 搜索(5条) | 50ms | 30ms | 40% ↑ |
| 删除操作 | 15ms | 12ms | 20% ↑ |

**内存占用**:
- ChromaDB: ~150MB
- Qdrant: ~300MB (包含embedding模型)

## 🔍 故障排查

### 连接失败

```bash
# 检查服务
docker ps | grep qdrant
curl http://localhost:6333/health

# 重启服务
docker restart qdrant
```

### 模型下载慢

```bash
# 使用代理
export HTTP_PROXY=http://proxy:port
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### 搜索结果为空

```python
# 降低阈值
results = await manager.search_memories(
    query="...",
    similarity_threshold=0.3  # 降低阈值
)

# 增加返回数量
results = await manager.search_memories(
    query="...",
    limit=10
)
```

### 查看日志

```bash
tail -f logs/app.log | grep -i "qdrant\|memory"
```

## 🔄 引擎切换

### 切换到Qdrant

```yaml
# config/memory.yaml
memory:
  default_engine: "qdrant"
```

或

```python
from app.engines.memory import QdrantMemoryEngine, MemoryManager
engine = QdrantMemoryEngine()
manager = MemoryManager(engine=engine)
```

### 切换回ChromaDB

```yaml
# config/memory.yaml
memory:
  default_engine: "chromadb"
```

或

```python
from app.engines.memory import ChromaDBMemoryEngine, MemoryManager
engine = ChromaDBMemoryEngine()
manager = MemoryManager(engine=engine)
```

## 📖 相关文档

- **完整文档**: `docs/Qdrant记忆引擎实施总结.md`
- **快速开始**: `docs/Qdrant快速开始指南.md`
- **架构设计**: `docs/02-后端架构设计-续.md`
- **开发规范**: `docs/06-开发规范.md`

## 🧪 测试命令

```bash
# 运行Qdrant测试
pytest tests/test_engines/test_memory/test_qdrant_engine.py -v

# 运行所有记忆测试
pytest tests/test_engines/test_memory/ -v

# 查看覆盖率
pytest tests/test_engines/test_memory/ -v --cov=app.engines.memory --cov-report=html

# 性能测试
pytest tests/test_engines/test_memory/ -v --benchmark
```

## 🔗 资源链接

- [Qdrant官方文档](https://qdrant.tech/documentation/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)
- [Sentence Transformers](https://www.sbert.net/)
- [Docker Hub - Qdrant](https://hub.docker.com/r/qdrant/qdrant)

---

**需要帮助？** 查看完整文档或运行测试验证配置。

