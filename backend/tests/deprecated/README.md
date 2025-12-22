# 废弃测试文件目录

此目录包含已废弃的测试文件，这些测试不再适用于当前架构。

## 废弃原因

### 旧的Memory引擎测试

这些测试针对旧的单一Memory引擎系统，已在v1.1.0中被三大引擎系统替代：

- **Knowledge Engine** (Cognee) - 替代了部分知识检索功能
- **UserProfile Engine** (Memobase) - 替代了部分用户画像功能  
- **ChatMemory Engine** (Mem0) - 替代了部分会话记忆功能

### 废弃的测试文件

1. `test_memory_old/` - 旧的memory引擎测试目录
   - `test_chromadb_engine.py`
   - `test_qdrant_engine.py`
   - `test_memory_manager.py`
   - `test_memory_comprehensive.py`
   - `test_deduplicator.py`
   - `test_importance_scorer.py`

2. `test_memory*.py` - 旧的memory API测试
   - `test_memory.py`
   - `test_memory_coverage.py`

3. `test_memory*.py` - 旧的memory服务测试
   - `test_memory_service.py`
   - `test_scoring_service.py`

## 替代方案

新的测试应该针对三大引擎系统：

- `test_engines/test_knowledge/` - Cognee引擎测试
- `test_engines/test_userprofile/` - Memobase引擎测试
- `test_engines/test_chatmemory/` - Mem0引擎测试
- `test_services/test_context/test_context_service_new.py` - ContextServiceNew测试

## 删除计划

这些文件将在v2.0版本中完全删除。

---

**最后更新**: 2025-12-22
