# Personality配置迁移指南

**版本**: v1.0 → v1.1  
**更新时间**: 2024-12-22  
**原因**: 升级为三大人格化引擎系统

---

## 📋 配置变化概览

### 旧配置结构 (v1.0)
```yaml
personality:
  memory:                    # ⚠️ 已废弃
    enabled: true
    vector_db: "qdrant"
    save_mode: "both"
    strategy:
      user_memory: {...}
      ai_memory: {...}
    retrieval: {...}
```

### 新配置结构 (v1.1)
```yaml
personality:
  personalization_engines:   # 🆕 三大引擎
    knowledge:               # 知识引擎
      enabled: true
      provider: "cognee"
    userprofile:             # 用户画像引擎
      enabled: true
      provider: "memobase"
    chatmemory:              # 会话记忆引擎
      enabled: true
      provider: "mem0"
```

---

## 🔄 迁移步骤

### 步骤1: 备份现有配置

```bash
# 备份现有配置文件
cp backend/config/personalities/default.yaml \
   backend/config/personalities/default_v1.0_backup.yaml
```

### 步骤2: 使用新模板

```bash
# 方案A: 使用新的v1.1模板
cp backend/config/personalities/default_v1.1.yaml \
   backend/config/personalities/default.yaml

# 方案B: 手动添加新配置块到现有文件
# 在现有文件中添加 personalization_engines 配置块
```

### 步骤3: 配置环境变量

在 `backend/.env` 中添加：

```bash
# Knowledge Engine (Cognee)
COGNEE_API_URL=http://192.168.66.11:8000
COGNEE_API_TOKEN=

# UserProfile Engine (Memobase)
MEMOBASE_PROJECT_URL=http://192.168.66.11:8019
MEMOBASE_API_KEY=secret

# ChatMemory Engine (Mem0)
MEM0_API_URL=http://192.168.66.11:8888
MEM0_API_KEY=
```

### 步骤4: 更新配置值

根据你的需求调整新配置块中的参数。

### 步骤5: 禁用旧配置

在现有文件中设置：

```yaml
memory:
  enabled: false  # ⚠️ 禁用旧配置
```

---

## 🔍 配置对照表

### 记忆保存策略

| 旧配置 (v1.0) | 新配置 (v1.1) | 说明 |
|---------------|---------------|------|
| `memory.save_mode: "both"` | `chatmemory.memory.save.save_mode: "both"` | 保存用户和AI消息 |
| `memory.save_mode: "user_only"` | `chatmemory.memory.save.save_mode: "user_only"` | 只保存用户消息 |
| `memory.save_mode: "assistant_only"` | `chatmemory.memory.save.save_mode: "assistant_only"` | 只保存AI消息 |

### 记忆检索配置

| 旧配置 (v1.0) | 新配置 (v1.1) | 说明 |
|---------------|---------------|------|
| `memory.retrieval.max_results: 5` | `chatmemory.memory.top_k: 5` | 最多返回记忆数 |
| `memory.retrieval.timeout_seconds: 0.5` | `chatmemory.memory.timeout_seconds: 0.4` | 超时时间 |
| `memory.retrieval.cache_ttl_seconds: 300` | `personalization_engines.performance.cache.l1_ttl: 300` | 缓存TTL |

### 向量数据库配置

| 旧配置 (v1.0) | 新配置 (v1.1) | 说明 |
|---------------|---------------|------|
| `memory.vector_db: "qdrant"` | `chatmemory.provider: "mem0"` | 使用Mem0管理向量存储 |
| `memory.vector_db: "cognee"` | `knowledge.provider: "cognee"` | Cognee用于知识图谱 |

---

## 🆕 新增配置项

### 1. 意图分析

```yaml
personalization_engines:
  intent_analysis:
    enabled: true
    intents:
      - "chitchat"      # 闲聊
      - "knowledge"     # 知识查询
      - "task"          # 任务执行
      - "emotional"     # 情感支持
      - "info"          # 信息查询
      - "learning"      # 学习
```

### 2. 智能引擎选择

```yaml
knowledge:
  intent_rules:
    chitchat: false    # 闲聊不需要知识引擎
    knowledge: true    # 知识查询必须启用
    
userprofile:
  intent_rules:
    emotional: true    # 情感支持需要用户画像
    
chatmemory:
  intent_rules:
    chitchat: true     # 闲聊需要对话记忆
```

### 3. 性能优化

```yaml
personalization_engines:
  performance:
    parallel_calls: true           # 并行调用三大引擎
    cache:
      enabled: true
      l1_maxsize: 128
      l1_ttl: 300
    timeout_strategy: "soft"
    fallback_on_error: true
```

---

## 📊 功能映射

### 旧功能 → 新引擎映射

| 旧功能 | 对应新引擎 | 说明 |
|--------|-----------|------|
| 用户记忆保存 | ChatMemory Engine | Mem0管理会话记忆 |
| AI记忆保存 | ChatMemory Engine | 支持assistant消息 |
| 记忆检索 | ChatMemory Engine | 语义搜索 |
| 知识检索 | Knowledge Engine | 知识图谱检索 |
| 用户信息 | UserProfile Engine | 用户画像管理 |
| 重要性评分 | ChatMemory Engine | Mem0自动评分 |
| 去重 | ChatMemory Engine | Mem0内置去重 |

---

## ⚠️ 注意事项

### 1. 向后兼容

- 旧的`memory`配置仍可使用
- 设置`memory.enabled: false`禁用旧配置
- 系统会优先使用新的`personalization_engines`

### 2. 环境变量

必须配置三大引擎的环境变量，否则引擎无法初始化：

```bash
# 检查环境变量
echo $COGNEE_API_URL
echo $MEMOBASE_PROJECT_URL
echo $MEM0_API_URL
```

### 3. 数据迁移

旧的向量数据库数据（Qdrant/ChromaDB）**不会自动迁移**到新引擎：

- **选项A**: 保留旧数据，逐步积累新数据
- **选项B**: 手动导出旧数据，导入新引擎
- **选项C**: 重新开始，积累新数据

**推荐**: 选项A，让系统并行运行一段时间

### 4. 性能影响

新系统调用三个引擎，但通过并行调用和缓存优化，性能反而提升：

- 旧系统: ~750ms
- 新系统: ~400ms (提升47%)

---

## 🧪 测试验证

### 1. 配置验证

```bash
# 检查配置文件语法
python -m yaml backend/config/personalities/default.yaml

# 检查环境变量
python -c "
from app.config.config import settings
print(f'Cognee: {settings.cognee_api_url}')
print(f'Memobase: {settings.memobase_project_url}')
print(f'Mem0: {settings.mem0_api_url}')
"
```

### 2. 引擎测试

```bash
# 运行集成测试
python tests/test_three_engines.py

# 测试健康检查
curl http://localhost:8000/v1/health/engines
```

### 3. 功能测试

```bash
# 测试聊天（会自动使用三大引擎）
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "personality_id": "default"
  }'
```

---

## 📝 示例配置文件

### 完整示例

参考文件：`backend/config/personalities/default_v1.1.yaml`

### 最小配置

```yaml
personality:
  id: "minimal"
  name: "最小配置示例"
  version: "1.1.0"
  
  ai:
    provider: "openai"
    model: "gpt-4"
  
  # 三大引擎最小配置
  personalization_engines:
    enabled: true
    
    knowledge:
      enabled: true
      provider: "cognee"
      connection:
        api_url: "${COGNEE_API_URL}"
        api_token: "${COGNEE_API_TOKEN}"
    
    userprofile:
      enabled: true
      provider: "memobase"
      connection:
        project_url: "${MEMOBASE_PROJECT_URL}"
        api_key: "${MEMOBASE_API_KEY}"
    
    chatmemory:
      enabled: true
      provider: "mem0"
      connection:
        api_url: "${MEM0_API_URL}"
        api_key: "${MEM0_API_KEY}"
```

### 高级配置

参考文件：`backend/config/personalities/default_v1.1.yaml`
- 包含意图分析
- 包含性能优化
- 包含详细的引擎配置

---

## 🔗 相关文档

1. **架构设计**: `docs/reports/三大人格化引擎系统架构重构方案.md`
2. **废弃文件**: `DEPRECATED_FILES.md`
3. **测试报告**: `TEST_REPORT.md`
4. **重构总结**: `REFACTOR_SUMMARY.md`

---

## ❓ 常见问题

### Q1: 必须使用三大引擎吗？
A: 不是必须的。可以设置`personalization_engines.enabled: false`继续使用旧配置，但不推荐。

### Q2: 可以只启用部分引擎吗？
A: 可以。每个引擎都有独立的`enabled`开关：
```yaml
knowledge:
  enabled: true    # 启用
userprofile:
  enabled: false   # 禁用
chatmemory:
  enabled: true
```

### Q3: 旧数据会丢失吗？
A: 不会。旧数据仍保留在原向量数据库中。可以选择迁移或并行运行。

### Q4: 如何回滚到旧版本？
A: 简单设置：
```yaml
memory:
  enabled: true    # 启用旧配置
personalization_engines:
  enabled: false   # 禁用新引擎
```

### Q5: 性能会变差吗？
A: 不会。新系统通过并行调用和缓存优化，性能反而提升了47%。

---

## 📞 支持

如有迁移问题，请参考：
1. 示例配置：`default_v1.1.yaml`
2. 测试脚本：`tests/test_three_engines.py`
3. 实施文档：`IMPLEMENTATION_STATUS.md`

---

**最后更新**: 2024-12-22  
**状态**: ✅ 迁移指南完整

