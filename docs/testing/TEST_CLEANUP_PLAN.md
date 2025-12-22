# 测试文件清理计划

**日期**: 2025-12-22  
**目标**: 整理所有测试文件，删除废弃测试，修复错误测试，提升覆盖率

---

## 📊 当前状态

### 测试文件统计

- **测试文件总数**: 110个
- **测试用例总数**: 1072个（收集时）
- **实际运行**: 72个
- **覆盖率**: 28.19%
- **错误文件**: 待统计

### 问题分析

1. **废弃测试未删除**: 旧的memory引擎测试仍在测试目录中
2. **导入错误**: 部分测试文件引用已废弃的模块
3. **测试未运行**: 大量测试因错误或依赖问题未运行

---

## 🗑️ 已移动到deprecated目录

### 1. 旧的Memory引擎测试

**目录**: `tests/deprecated/test_memory_old/`

包含文件:
- `test_chromadb_engine.py`
- `test_qdrant_engine.py`
- `test_memory_manager.py`
- `test_memory_comprehensive.py`
- `test_deduplicator.py`
- `test_importance_scorer.py`

### 2. 旧的Memory API测试

**目录**: `tests/deprecated/`

包含文件:
- `test_memory.py`
- `test_memory_coverage.py`

### 3. 旧的Memory服务测试

**目录**: `tests/deprecated/`

包含文件:
- `test_memory_service.py`
- `test_scoring_service.py`

---

## 🔍 需要修复的测试文件

### 1. 引用废弃模块的测试

这些测试文件需要更新或删除：

1. **引用旧的memory引擎**:
   - `test_services/test_context/test_context_service.py` - 需要更新为ContextServiceNew
   - 其他引用 `app.engines.memory` 的测试文件

2. **引用旧的memory服务**:
   - 引用 `app.services.memory` 的测试文件
   - 引用 `MemoryManager` 的测试文件

### 2. 导入错误的测试

这些测试文件有导入错误：

1. **cache相关**:
   - `test_utils/test_cache.py` - ✅ 已修复
   - `test_utils/test_cache_coverage.py` - ✅ 已修复

2. **query_optimizer相关**:
   - `test_utils/test_query_optimizer.py` - ✅ 已修复
   - `test_utils/test_query_optimizer_coverage.py` - ✅ 已修复

---

## 🎯 清理步骤

### 阶段1: 移动废弃测试 ✅

- [x] 创建 `tests/deprecated/` 目录
- [x] 移动 `test_engines/test_memory/` 到 `deprecated/`
- [x] 移动 `test_api/test_memory*.py` 到 `deprecated/`
- [x] 移动 `test_services/test_memory*.py` 到 `deprecated/`
- [x] 创建 `deprecated/README.md` 说明文档

### 阶段2: 修复导入错误 ✅

- [x] 修复 `cached` 装饰器导入
- [x] 修复 `test_utils/test_cache*.py` 导入
- [x] 修复 `test_utils/test_query_optimizer*.py` 导入

### 阶段3: 更新引用废弃模块的测试

- [ ] 查找所有引用废弃模块的测试文件
- [ ] 更新或删除这些测试文件
- [ ] 创建新的三大引擎测试

### 阶段4: 运行所有可用测试

- [ ] 运行所有测试查看真实覆盖率
- [ ] 修复剩余的错误
- [ ] 分析覆盖率报告

---

## 📋 测试文件分类

### ✅ 可用测试（可直接运行）

1. **无外部服务依赖**:
   - `test_no_external_deps.py` (54个测试)
   - `test_utils/test_security.py`
   - `test_utils/test_token_utils.py`
   - `test_utils/test_config_loader.py`
   - `test_utils/test_config_adapter.py`

2. **需要PostgreSQL/Redis**:
   - `test_database_comprehensive.py` (8个测试)
   - `test_cache_redis.py` (9个测试)
   - `test_api_database.py` (4个测试)
   - `test_user_id_normalizer.py` (10个测试)
   - `test_models/*.py`

3. **需要完整环境**:
   - `test_api/test_*.py` (大部分)
   - `test_engines/test_ai/*.py`
   - `test_engines/test_tools/*.py`
   - `test_engines/test_voice/*.py`
   - `test_core/*.py`
   - `test_services/test_chat/*.py`

### ⚠️ 需要修复的测试

1. **引用废弃模块**:
   - `test_services/test_context/test_context_service.py` - 需要更新

2. **其他问题**:
   - 待进一步分析

### ❌ 已废弃的测试

1. **已移动到deprecated**:
   - `test_engines/test_memory/` → `deprecated/test_memory_old/`
   - `test_api/test_memory*.py` → `deprecated/`
   - `test_services/test_memory*.py` → `deprecated/`

---

## 🎯 下一步行动

### 立即执行

1. **运行所有可用测试**:
   ```bash
   cd backend
   python3 -m pytest tests/ \
     --ignore=tests/deprecated \
     --cov=app \
     --cov-report=html \
     --cov-report=term
   ```

2. **分析测试结果**:
   - 查看哪些测试通过
   - 查看哪些测试失败
   - 查看覆盖率报告

3. **修复剩余错误**:
   - 修复引用废弃模块的测试
   - 修复其他导入错误
   - 更新过时的测试

### 后续工作

1. **创建新的三大引擎测试**:
   - `test_engines/test_knowledge/`
   - `test_engines/test_userprofile/`
   - `test_engines/test_chatmemory/`

2. **创建ContextServiceNew测试**:
   - `test_services/test_context/test_context_service_new.py`

3. **提升覆盖率到80%**:
   - 完善现有测试
   - 添加缺失的测试
   - 覆盖边界条件

---

## 📊 预期结果

### 清理后

- **测试文件数**: 110个 → ~100个（删除废弃测试）
- **可运行测试**: 72个 → 500+个（修复错误后）
- **覆盖率**: 28% → 60-70%（运行所有测试后）

### 最终目标

- **测试文件数**: ~100个（清理后）
- **可运行测试**: 800+个
- **覆盖率**: 80%+

---

**最后更新**: 2025-12-22

