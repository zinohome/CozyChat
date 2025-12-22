# 废弃文件清单

**废弃时间**: 2024-12-22  
**移除时间**: 2025-Q1 (v2.0)  
**原因**: 升级为三大人格化引擎系统

---

## 📋 已废弃文件列表

### 🔧 引擎层 (Engines)

#### backend/app/engines/memory/ ⚠️ 已废弃
整个目录已废弃，包含以下文件：

```
memory/
├── __init__.py              ⚠️ 已添加废弃警告
├── manager.py               ⚠️ 已添加废弃警告（核心）
├── base.py                  ⚠️ 废弃
├── qdrant_engine.py         ⚠️ 废弃
├── cognee_engine.py         ⚠️ 废弃（旧版）
├── chromadb_engine.py       ⚠️ 废弃
├── queue.py                 ⚠️ 废弃
├── worker.py                ⚠️ 废弃
├── deduplicator.py          ⚠️ 废弃
├── importance_scorer.py     ⚠️ 废弃
├── eviction_policy.py       ⚠️ 废弃
├── models.py                ⚠️ 废弃
├── jobs.py                  ⚠️ 废弃
└── qdrant_client_manager.py ⚠️ 废弃
```

**替代方案**: 三大人格化引擎
- `backend/app/engines/knowledge/` - Knowledge Engine (Cognee)
- `backend/app/engines/userprofile/` - UserProfile Engine (Memobase)
- `backend/app/engines/chatmemory/` - ChatMemory Engine (Mem0)

---

### 📦 服务层 (Services)

#### backend/app/services/memory_service.py ⚠️ 已废弃
**功能**: 记忆服务，统一处理记忆相关操作  
**状态**: 已添加废弃警告  
**替代**: ContextServiceNew + 三大引擎

#### backend/app/services/context/memory_retriever.py ⚠️ 已废弃
**功能**: 记忆检索器，负责向量数据库检索  
**状态**: 已添加废弃警告  
**替代**: ChatMemory Engine + Knowledge Engine

#### backend/app/services/context/context_service_legacy.py ⚠️ 已废弃
**功能**: 旧版上下文服务  
**状态**: 已重命名为legacy版本  
**替代**: ContextServiceNew (context_service_new.py)

---

### 🌐 API层 (API)

#### backend/app/api/v1/memory.py ⚠️ 已废弃
**功能**: 记忆管理API接口，提供记忆CRUD操作  
**状态**: 已添加废弃警告  
**替代**: 
- 会话记忆通过聊天API自动管理
- 知识管理使用Knowledge Engine API
- 用户画像使用UserProfile Engine API

**注意**: 此API仍可使用，但不推荐，将在v2.0移除

---

### 🔄 核心层 (Core)

#### backend/app/core/context/builder.py ⚠️ 部分废弃
**功能**: 上下文构建器  
**状态**: 保留用于兼容，不推荐使用  
**替代**: ContextServiceNew

**注意**: 此文件暂时保留，因为可能有其他地方依赖

---

## 📊 废弃统计

| 类别 | 废弃文件数 | 状态 |
|------|-----------|------|
| 引擎层 | 14个文件 | ⚠️ 已标记 |
| 服务层 | 3个文件 | ⚠️ 已标记 |
| API层 | 1个文件 | ⚠️ 已标记 |
| 核心层 | 1个文件 | 🔄 保留兼容 |
| **总计** | **19个文件** | ⚠️ **已废弃** |

---

## 🔍 引用检查

### 仍在引用旧Memory代码的文件（需要注意）

通过检查发现以下文件可能仍引用MemoryManager：

```python
# 1. backend/app/api/deps.py
# ✅ 已更新，get_context_service不再依赖memory_manager

# 2. backend/app/services/orchestration/chat_orchestrator.py
# ⚠️ 仍接受memory_manager参数（兼容模式）
# 建议：后续版本移除此参数

# 3. backend/app/core/context/builder.py
# ⚠️ 使用MemoryManager
# 建议：标记为废弃，完全迁移到ContextServiceNew

# 4. backend/app/core/context/summary_generator.py
# ℹ️ 可能使用memory_engine
# 建议：检查是否需要更新

# 5. backend/app/core/personality/orchestrator.py
# ℹ️ 可能引用
# 建议：检查并更新

# 6. backend/app/utils/message_converter.py
# ℹ️ 可能引用
# 建议：检查并更新
```

---

## 🚀 迁移指南

### 从旧Memory引擎迁移到三大引擎

#### 1. 导入变更
```python
# ❌ 旧代码
from app.engines.memory import get_memory_manager
memory_manager = get_memory_manager()

# ✅ 新代码
from app.services.context.context_service_new import ContextServiceNew
context_service = ContextServiceNew.get_instance()
```

#### 2. 记忆保存变更
```python
# ❌ 旧代码
await memory_manager.save_memory(
    content=content,
    user_id=user_id,
    session_id=session_id
)

# ✅ 新代码
await context_service.update_user_data(
    user_id=user_id,
    session_id=session_id,
    messages=[{"role": "user", "content": content}]
)
```

#### 3. 记忆检索变更
```python
# ❌ 旧代码
memories = await memory_manager.retrieve_memories(
    query=query,
    user_id=user_id,
    session_id=session_id,
    top_k=5
)

# ✅ 新代码
context = await context_service.build_personalized_context(
    user_id=user_id,
    session_id=session_id,
    query=query
)
# context包含: knowledge, profile, memories
```

#### 4. 上下文构建变更
```python
# ❌ 旧代码
from app.core.context.builder import ContextBuilder
context_bundle = await context_builder.build_context(...)

# ✅ 新代码
from app.services.context.context_service_new import ContextServiceNew
context_service = ContextServiceNew.get_instance()
context_bundle = await context_service.build_context(...)
```

---

## ⏰ 移除时间表

| 阶段 | 时间 | 操作 |
|------|------|------|
| **阶段1** | 2024-12-22 | ✅ 标记废弃（已完成） |
| **阶段2** | 2025-01-15 | 移除强依赖 |
| **阶段3** | 2025-02-01 | 删除废弃文件 |
| **阶段4** | 2025-Q1 | v2.0发布，完全移除 |

---

## ⚠️ 重要提醒

1. **向后兼容**: 所有废弃代码仍可使用，会显示DeprecationWarning
2. **迁移时间**: 建议在2025-01-15前完成迁移
3. **测试验证**: 迁移后务必运行完整测试
4. **文档参考**: `docs/reports/三大人格化引擎系统架构重构方案.md`

---

## 📝 备份说明

所有废弃的memory引擎代码已备份到：
```
backup/memory_engine_old/
```

如需回滚，可从备份恢复。

---

## 📞 支持

如有迁移问题，请参考：
1. **架构文档**: `docs/reports/三大人格化引擎系统架构重构方案.md`
2. **测试示例**: `tests/test_three_engines.py`
3. **实施状态**: `IMPLEMENTATION_STATUS.md`
4. **重构总结**: `REFACTOR_SUMMARY.md`

---

**最后更新**: 2024-12-22  
**状态**: ✅ 废弃标记完成

