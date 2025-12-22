# 旧Memory引擎清理计划

## 清理原则

⚠️ **遵循零风险原则**: 逐步清理，每步都要测试验证

---

## 清理清单

### 阶段1: 标记废弃（保留代码，添加警告）✅ 推荐

**目的**: 标记旧代码为废弃，但保留以备回滚

**操作**:
1. 在旧代码文件顶部添加废弃警告
2. 在导入旧代码处添加警告日志
3. 保持代码可运行

**优点**:
- 零风险，完全可回滚
- 给用户迁移时间
- 保持向后兼容

### 阶段2: 移除依赖（可选，谨慎）⚠️

**目的**: 移除旧代码的强依赖，但保留文件

**操作**:
1. 从deps.py移除get_memory_manager()
2. 从ChatOrchestrator移除memory_manager参数
3. 更新所有导入语句

**风险**: 中等（可能影响某些功能）

### 阶段3: 删除文件（最后，需充分测试）❌ 暂不推荐

**目的**: 彻底删除旧代码文件

**操作**:
1. 删除backend/app/engines/memory/目录
2. 删除相关服务文件

**风险**: 高（不可逆，必须充分测试）

---

## 推荐方案：阶段1（标记废弃）

### 需要标记废弃的文件

```
backend/app/engines/memory/          # 旧memory引擎（已备份）
├── __init__.py
├── manager.py
├── base.py
├── qdrant_engine.py
├── cognee_engine.py
├── chromadb_engine.py
├── queue.py
├── worker.py
├── deduplicator.py
├── importance_scorer.py
├── eviction_policy.py
├── models.py
├── jobs.py
└── qdrant_client_manager.py

backend/app/services/
├── memory_service.py                # 旧记忆服务
└── context/
    ├── context_service.py          # 旧ContextService
    └── memory_retriever.py         # 旧记忆检索器

backend/app/core/context/
├── builder.py                      # 旧ContextBuilder
└── summary_generator.py            # (保留，仍在使用)

backend/app/api/v1/
└── memory.py                       # 旧记忆API（考虑保留）
```

### 需要更新的文件（移除MemoryManager引用）

```
backend/app/api/deps.py              # ✅ 已更新，使用新ContextService
backend/app/services/orchestration/chat_orchestrator.py  # ⚠️ 需要移除memory_manager参数
backend/app/main.py                  # 检查是否有引用
```

---

## 实施步骤

### Step 1: 标记核心废弃文件 ✅

在以下文件顶部添加废弃警告：
- `backend/app/engines/memory/__init__.py`
- `backend/app/engines/memory/manager.py`

```python
# ============================================================================
# ⚠️ DEPRECATED: 旧版Memory引擎（已废弃）
# ============================================================================
# 状态：已废弃，将在 v2.0 移除
# 替代：使用三大引擎系统 (Knowledge + UserProfile + ChatMemory)
#   - backend/app/engines/knowledge/
#   - backend/app/engines/userprofile/
#   - backend/app/engines/chatmemory/
# 移除时间：2025-Q1
# ============================================================================

import warnings
warnings.warn(
    "MemoryManager is deprecated and will be removed in v2.0. "
    "Please use the new three-engine system (Knowledge + UserProfile + ChatMemory).",
    DeprecationWarning,
    stacklevel=2
)
```

### Step 2: 更新ChatOrchestrator（移除memory_manager）⚠️

**当前代码** (chat_orchestrator.py):
```python
def __init__(
    self,
    personality_registry,
    tool_factory,
    engine_pool,
    context_builder,
    memory_manager,  # ← 需要移除
    context_service=None,
):
    self.memory_manager = memory_manager  # ← 需要移除
```

**更新后代码**:
```python
def __init__(
    self,
    personality_registry,
    tool_factory,
    engine_pool,
    context_builder=None,  # ← 标记为可选（兼容）
    context_service=None,  # ← 新的ContextService
):
    # 移除memory_manager，使用context_service
    if context_service is None:
        logger.warning("No context_service provided, some features may be limited")
    self.context_service = context_service
```

### Step 3: 更新deps.py（移除get_memory_manager）⚠️

**当前代码** (deps.py):
```python
def get_memory_manager() -> "MemoryManager":
    from app.engines.memory import get_memory_manager
    return get_memory_manager()

async def get_chat_orchestrator(
    ...
    memory_manager: "MemoryManager" = Depends(get_memory_manager),
    ...
):
    return ChatOrchestrator(
        ...
        memory_manager=memory_manager,
        ...
    )
```

**更新后代码**:
```python
# 移除get_memory_manager

async def get_chat_orchestrator(
    ...
    # 移除memory_manager依赖
    context_service: Optional["ContextService"] = Depends(get_context_service),
    ...
):
    return ChatOrchestrator(
        ...
        # 移除memory_manager参数
        context_service=context_service,
        ...
    )
```

### Step 4: 检查和更新其他引用文件

**需要检查的文件**:
1. `backend/app/main.py` - 检查是否有MemoryManager初始化
2. `backend/app/services/context/context_service.py` - 旧ContextService（标记废弃）
3. `backend/app/api/v1/memory.py` - 旧记忆API（考虑保留或标记废弃）

---

## 测试验证

### 清理前测试
```bash
# 1. 运行集成测试
python tests/test_three_engines.py

# 2. 测试聊天功能
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}], "personality_id": "assistant_001"}'
```

### 清理后测试
- 重复上述所有测试
- 确保没有新的错误
- 检查日志是否有废弃警告

---

## 回滚方案

如果清理后出现问题：

### 方案1: Git回滚（推荐）
```bash
git checkout HEAD~1  # 回滚到清理前
```

### 方案2: 从备份恢复
```bash
# 从备份恢复memory引擎
cp -r backup/memory_engine_old/* backend/app/engines/memory/
```

---

## 时间计划

| 步骤 | 预计时间 | 风险 |
|------|----------|------|
| Step 1: 标记废弃 | 10分钟 | 低 ✅ |
| Step 2: 更新ChatOrchestrator | 20分钟 | 中 ⚠️ |
| Step 3: 更新deps.py | 15分钟 | 中 ⚠️ |
| Step 4: 检查其他文件 | 30分钟 | 低 ✅ |
| 测试验证 | 30分钟 | - |
| **总计** | **约2小时** | - |

---

## 建议

### 立即执行（低风险）✅
- ✅ Step 1: 标记废弃文件
- ✅ Step 4: 检查和记录所有引用

### 谨慎执行（中风险）⚠️
- ⚠️ Step 2: 更新ChatOrchestrator
- ⚠️ Step 3: 更新deps.py
- ⚠️ 需要充分测试

### 暂不执行（高风险）❌
- ❌ 删除memory目录
- ❌ 删除旧服务文件
- ❌ 等待更充分的测试和生产验证

---

## 当前决策

**推荐方案**: 执行 Step 1 + Step 4（标记废弃 + 记录引用）

**理由**:
1. 零风险，完全可回滚
2. 给用户和开发者迁移时间
3. 保持系统稳定性
4. 符合零风险原则

**后续计划**:
- 等待1-2个版本周期（约4-8周）
- 收集生产环境反馈
- 再考虑执行Step 2和Step 3

---

**最后更新**: 2024-12-22

**决策**: 执行低风险清理（标记废弃）✅

