# 需要外部服务的测试清单

**创建时间**: 2024-12-22  
**状态**: 待部署服务

---

## 📋 服务部署清单

### 1. PostgreSQL 数据库 ⚠️ 必需

**用途**: 存储业务数据（用户、会话、消息等）

**配置要求**:
```bash
# 数据库配置
数据库名: cozychat_test
用户名: cozychat
密码: passw0rd
主机: 192.168.66.10
端口: 5432
```

**部署命令**:
```sql
-- 创建测试数据库
CREATE DATABASE cozychat_test;
GRANT ALL PRIVILEGES ON DATABASE cozychat_test TO cozychat;

-- 验证
\c cozychat_test
```

**需要的测试**:
- ✅ 数据库模型测试（User, Session, Message等）
- ✅ MessageSaver测试
- ✅ MessageService测试
- ✅ Session API测试
- ✅ User API测试
- ✅ Chat API测试（需要保存消息）

**预计提升覆盖率**: +3-5%

---

### 2. Redis 缓存 ⚠️ 必需

**用途**: 缓存和会话存储

**配置要求**:
```bash
# Redis配置
主机: 192.168.66.10
端口: 6379
密码: redis_passw0rd
数据库: 0
```

**部署命令**:
```bash
# 启动Redis（如果使用Docker）
docker run -d \
  --name redis-test \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --requirepass redis_passw0rd
```

**需要的测试**:
- ✅ CacheManager完整测试（219行，0% → 80%）
- ✅ 缓存装饰器测试
- ✅ 多级缓存L2测试
- ✅ 会话存储测试

**预计提升覆盖率**: +2-3%

---

### ~~3. Qdrant 向量数据库~~ ❌ **已废弃，不需要**

**状态**: ⚠️ **已废弃** - 旧的Memory引擎将在v2.0移除

**说明**: 
- Qdrant是旧Memory引擎的一部分（`backend/app/engines/memory/qdrant_engine.py`）
- 旧Memory引擎已标记为deprecated（见`DEPRECATED_FILES.md`）
- 新的三大引擎系统不使用Qdrant：
  - Knowledge Engine → 使用Cognee ✅
  - ChatMemory Engine → 使用Mem0 ✅
  - UserProfile Engine → 使用Memobase ✅
- **不需要部署Qdrant进行测试**

**替代方案**: 使用新的三大引擎系统

---

### 3. Cognee 知识引擎 🆕 必需

**用途**: 知识图谱检索

**配置要求**:
```bash
# Cognee配置
API URL: http://192.168.66.11:8000
API Token: (可选)
```

**部署状态**: ✅ 已部署（192.168.66.11:8000）

**需要的测试**:
- ✅ CogneeKnowledgeEngine完整测试
- ✅ 知识检索测试（CHUNKS模式）
- ✅ 知识检索测试（GRAPH_COMPLETION模式）
- ✅ 降级策略测试
- ✅ 健康检查测试

**预计提升覆盖率**: +0.5-1%

---

### 4. Memobase 用户画像引擎 🆕 必需

**用途**: 用户画像管理

**配置要求**:
```bash
# Memobase配置
Project URL: http://192.168.66.11:8019
API Key: secret
```

**部署状态**: ✅ 已部署（192.168.66.11:8019）

**需要的测试**:
- ✅ MemobaseUserProfileEngine完整测试
- ✅ 获取用户画像测试
- ✅ 更新用户画像测试
- ✅ UUID转换测试
- ✅ 健康检查测试

**预计提升覆盖率**: +0.5-1%

---

### 5. Mem0 会话记忆引擎 🆕 必需

**用途**: 会话记忆管理

**配置要求**:
```bash
# Mem0配置
API URL: http://192.168.66.11:8888
API Key: (可选)
```

**部署状态**: ✅ 已部署（192.168.66.11:8888）

**需要的测试**:
- ✅ Mem0ChatMemoryEngine完整测试
- ✅ 检索当前会话记忆测试
- ✅ 检索跨会话记忆测试
- ✅ 添加记忆测试
- ✅ 健康检查测试

**预计提升覆盖率**: +0.5-1%

---

## 📊 测试分类

### ✅ 已完成（无外部服务依赖）

**测试文件**: `test_no_external_deps.py`

**测试数量**: 50+个测试

**覆盖模块**:
- ✅ TokenUtils（纯函数）
- ✅ Security（纯函数）
- ✅ TextConverter（纯函数）
- ✅ Exceptions（纯类定义）
- ✅ PerformanceMonitor（纯内存操作）
- ✅ MultiLevelCache L1（纯内存操作）
- ✅ IntentAnalyzer（纯函数）
- ✅ Logger（无外部依赖）
- ✅ MessageUtils部分（纯函数）
- ✅ ConfigLoader（只需要文件系统）
- ✅ ConfigAdapter（纯函数）
- ✅ Monitoring（使用Mock）

**当前覆盖率**: 27%

---

### ⏳ 待部署服务后测试

#### 数据库相关测试

**需要**: PostgreSQL

**测试文件**: 
- `test_models_comprehensive.py` (待创建)
- `test_services_database.py` (待创建)
- `test_api_database.py` (待创建)

**测试内容**:
```python
# 模型测试
- User模型CRUD
- Session模型CRUD
- Message模型CRUD
- UserProfile模型CRUD

# 服务测试
- MessageSaver完整测试
- MessageService完整测试
- SessionService测试

# API测试
- POST /v1/sessions
- GET /v1/sessions
- POST /v1/chat/completions
- GET /v1/users/me
```

**预计提升**: +3-5%

---

#### Redis缓存测试

**需要**: Redis

**测试文件**: `test_cache_redis.py` (待创建)

**测试内容**:
```python
# CacheManager完整测试
- CacheManager初始化
- get/set/delete操作
- TTL过期测试
- 缓存装饰器测试
- 多级缓存L2测试
```

**预计提升**: +2-3%

---

#### ~~Qdrant向量数据库测试~~ ❌ **已废弃**

**状态**: ⚠️ **已废弃** - 不需要测试

**说明**: 
- QdrantMemoryEngine已废弃
- 将在v2.0移除
- 不需要创建Qdrant测试

---

#### 三大引擎完整测试

**需要**: Cognee + Memobase + Mem0

**测试文件**: `test_three_engines_full.py` (已部分创建)

**测试内容**:
```python
# Knowledge Engine
- 知识检索（各种模式）
- 知识添加
- 错误处理

# UserProfile Engine
- 画像获取
- 画像更新
- 用户创建

# ChatMemory Engine
- 记忆检索
- 记忆添加
- 跨会话检索
```

**预计提升**: +1.5-3%

---

#### ContextService集成测试

**需要**: 三大引擎 + 数据库

**测试文件**: `test_context_service_integration.py` (待创建)

**测试内容**:
```python
# ContextService完整测试
- 构建上下文（所有引擎）
- 构建上下文（部分引擎）
- 并行调用测试
- 超时处理测试
- 降级策略测试
```

**预计提升**: +1-2%

---

#### ChatOrchestrator测试

**需要**: 数据库 + AI引擎（可用Mock）

**测试文件**: `test_chat_orchestrator.py` (待创建)

**测试内容**:
```python
# ChatOrchestrator完整测试
- 初始化测试
- prepare_request测试
- process_request测试
- 流式和非流式测试
```

**预计提升**: +1-1.5%

---

## 🚀 部署优先级

### P0 - 立即部署（核心功能）

1. **PostgreSQL** - 必需，影响大量测试
2. **Redis** - 必需，影响CacheManager测试
3. **三大引擎** - 已部署 ✅，只需验证连接

### ~~P1 - 短期部署（已废弃）~~

~~4. **Qdrant** - 影响旧Memory引擎测试~~  
**注意**: Qdrant已废弃，旧的Memory引擎将在v2.0移除，**不需要部署Qdrant进行测试**

### P2 - 可选部署（兼容性测试）

5. **其他服务** - 根据测试需求

---

## 📝 部署验证

### 验证脚本

```bash
#!/bin/bash
# verify_services.sh

echo "验证外部服务连接..."

# PostgreSQL
echo -n "PostgreSQL: "
psql -h 192.168.66.10 -U cozychat -d cozychat_test -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 连接成功"
else
    echo "❌ 连接失败"
fi

# Redis
echo -n "Redis: "
redis-cli -h 192.168.66.10 -p 6379 -a redis_passw0rd ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 连接成功"
else
    echo "❌ 连接失败"
fi

# Qdrant (已废弃，不需要验证)
# echo -n "Qdrant: "
# echo "❌ 已废弃，不需要"

# Cognee
echo -n "Cognee: "
curl -s http://192.168.66.11:8000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 连接成功"
else
    echo "❌ 连接失败"
fi

# Memobase
echo -n "Memobase: "
curl -s http://192.168.66.11:8019/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 连接成功"
else
    echo "❌ 连接失败"
fi

# Mem0
echo -n "Mem0: "
curl -s http://192.168.66.11:8888/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 连接成功"
else
    echo "❌ 连接失败"
fi
```

---

## 📈 覆盖率提升预期

### 当前状态

- **覆盖率**: 27%
- **无外部服务测试**: 50+个测试 ✅
- **需要外部服务测试**: ~100+个测试 ⏳

### 部署服务后预期

| 服务 | 测试数量 | 预计提升 |
|------|----------|----------|
| PostgreSQL | ~40个 | +3-5% |
| Redis | ~20个 | +2-3% |
| ~~Qdrant~~ | ~~~10个~~ | ~~+1-2%~~ ❌ **已废弃** |
| 三大引擎 | ~30个 | +1.5-3% |
| **总计** | **~90个** | **+7-11%** |

**最终预期**: 27% → **34-38%** (移除Qdrant后)

**要达到80%**: 还需要更多测试和优化

---

## 🔧 测试运行命令

### 只运行无外部服务测试

```bash
cd backend
pytest tests/test_no_external_deps.py -v
```

### 运行所有测试（需要服务）

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### 运行特定服务测试

```bash
# 数据库测试
pytest tests/test_models_comprehensive.py -v

# Redis测试
pytest tests/test_cache_redis.py -v

# 三大引擎测试
pytest tests/test_three_engines_full.py -v
```

---

## ✅ 检查清单

### 部署前检查

- [ ] PostgreSQL已部署并创建测试数据库
- [ ] Redis已部署并配置密码
- [ ] Qdrant已部署
- [ ] 三大引擎服务已部署（✅ 已确认）
- [ ] 网络连通性测试通过

### 部署后验证

- [ ] 所有服务健康检查通过
- [ ] 测试数据库连接成功
- [ ] Redis连接成功
- [ ] Qdrant连接成功
- [ ] 三大引擎连接成功

### 测试运行

- [ ] 无外部服务测试全部通过（✅ 已完成）
- [ ] 数据库测试运行成功
- [ ] Redis测试运行成功
- [ ] 三大引擎测试运行成功
- [ ] 集成测试运行成功

---

## 📞 服务信息汇总

### 已部署服务 ✅

| 服务 | 地址 | 状态 |
|------|------|------|
| Cognee | http://192.168.66.11:8000 | ✅ 已部署 |
| Memobase | http://192.168.66.11:8019 | ✅ 已部署 |
| Mem0 | http://192.168.66.11:8888 | ✅ 已部署 |

### 待部署服务 ⏳

| 服务 | 地址 | 优先级 | 状态 |
|------|------|--------|------|
| PostgreSQL | 192.168.66.10:5432 | P0 | ⏳ 待部署 |
| Redis | 192.168.66.10:6379 | P0 | ⏳ 待部署 |
| ~~Qdrant~~ | ~~192.168.66.10:6333~~ | ~~P1~~ | ❌ **已废弃，不需要** |

---

## 🎯 下一步行动

1. **部署PostgreSQL测试数据库**
   ```sql
   CREATE DATABASE cozychat_test;
   GRANT ALL PRIVILEGES ON DATABASE cozychat_test TO cozychat;
   ```

2. **部署Redis测试实例**
   ```bash
   docker run -d --name redis-test -p 6379:6379 redis:7-alpine redis-server --requirepass redis_passw0rd
   ```

3. ~~**部署Qdrant测试实例**~~ ❌ **已废弃，不需要**

4. **验证服务连接**
   ```bash
   bash verify_services.sh
   ```

5. **运行完整测试**
   ```bash
   pytest tests/ --cov=app --cov-report=html
   ```

---

**状态**: 🟡 无外部服务测试已完成，等待服务部署  
**当前覆盖率**: 27%  
**预期覆盖率**: 35-40%（部署服务后）

