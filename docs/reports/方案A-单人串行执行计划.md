# 方案A：单人串行执行计划

**执行模式**: 单人串行执行（安全、可控）  
**预计总时间**: 10-12天  
**开始日期**: 待定  
**状态**: 📋 待开始

---

## 📊 总体时间表

| 周 | 阶段 | 任务数 | 预计时间 | 状态 |
|---|------|--------|----------|------|
| 第1周 | 测试验证 | 14个 | 5-6天 | ⏳ 待开始 |
| 第2周 | 清理旧代码 | 8个 | 2-3天 | ⏳ 待开始 |
| 第2周 | 文档更新 | 6个 | 1-2天 | ⏳ 待开始 |
| **总计** | - | **28个** | **8-11天** | ⏳ **待开始** |

---

## 📅 第一周：测试验证（5-6天）

### Day 1: Knowledge Engine单元测试

**日期**: Day 1  
**任务**: T-501  
**预计时间**: 0.5天（4小时）  
**优先级**: P0

#### 具体任务

1. **创建测试目录结构** (30分钟)
   ```bash
   mkdir -p backend/tests/test_engines/test_knowledge
   touch backend/tests/test_engines/test_knowledge/__init__.py
   touch backend/tests/test_engines/test_knowledge/test_cognee_engine.py
   touch backend/tests/test_engines/test_knowledge/test_knowledge_factory.py
   touch backend/tests/test_engines/test_knowledge/test_knowledge_base.py
   ```

2. **编写Cognee引擎测试** (2小时)
   - 测试 `search()` 方法（正常搜索、异常处理、超时）
   - 测试 `health_check()` 方法
   - 使用Mock避免真实Cognee服务调用
   - 测试边界条件

3. **编写工厂类测试** (30分钟)
   - 测试 `KnowledgeEngineFactory.create_engine()`
   - 测试不同provider的创建

4. **编写基类测试** (30分钟)
   - 测试 `KnowledgeEngineBase` 抽象方法

5. **运行测试并验证覆盖率** (30分钟)
   ```bash
   pytest backend/tests/test_engines/test_knowledge/ -v --cov=app.engines.knowledge --cov-report=html
   # 目标：覆盖率≥85%
   ```

#### 完成标准

- [ ] 所有测试通过
- [ ] 覆盖率≥85%
- [ ] 测试代码质量良好（有注释、清晰）

#### 检查点

- ✅ 测试文件已创建
- ✅ 所有测试用例已编写
- ✅ 测试通过且覆盖率达标

---

### Day 2: UserProfile和ChatMemory Engine单元测试

**日期**: Day 2  
**任务**: T-502, T-503  
**预计时间**: 1天（8小时）  
**优先级**: P0

#### 上午：UserProfile Engine测试 (4小时)

1. **创建测试目录** (15分钟)
   ```bash
   mkdir -p backend/tests/test_engines/test_userprofile
   ```

2. **编写Memobase引擎测试** (2.5小时)
   - 测试 `get_profile()` 方法
   - 测试 `update_profile()` 方法
   - 测试UUID转换逻辑
   - 测试用户不存在场景

3. **编写工厂和基类测试** (1小时)

4. **运行测试验证** (15分钟)

#### 下午：ChatMemory Engine测试 (4小时)

1. **创建测试目录** (15分钟)
   ```bash
   mkdir -p backend/tests/test_engines/test_chatmemory
   ```

2. **编写Mem0引擎测试** (2.5小时)
   - 测试 `search_memories()` 方法
   - 测试 `add_memory()` 方法
   - 测试并发搜索场景

3. **编写工厂和基类测试** (1小时)

4. **运行测试验证** (15分钟)

#### 完成标准

- [ ] T-502: UserProfile Engine测试通过，覆盖率≥85%
- [ ] T-503: ChatMemory Engine测试通过，覆盖率≥85%

---

### Day 3: ContextServiceNew和IntentAnalyzer单元测试

**日期**: Day 3  
**任务**: T-504, T-505  
**预计时间**: 1天（8小时）  
**优先级**: P0

#### 上午：ContextServiceNew测试 (4小时)

1. **创建测试文件** (15分钟)
   ```bash
   touch backend/tests/test_services/test_context/test_context_service_new.py
   ```

2. **编写测试** (3小时)
   - 测试 `build_personalized_context()` 方法
   - 测试 `update_user_data()` 方法
   - 测试 `initialize()` 方法
   - Mock三大引擎
   - 测试超时控制和降级策略
   - 测试各种意图场景

3. **运行测试验证** (45分钟)

#### 下午：IntentAnalyzer测试 (4小时)

1. **创建测试文件** (15分钟)
   ```bash
   touch backend/tests/test_services/test_context/test_intent_analyzer.py
   ```

2. **编写测试** (3小时)
   - 测试6种意图识别
   - 测试引擎配置生成
   - 测试各种查询场景

3. **运行测试验证** (45分钟)

#### 完成标准

- [ ] T-504: ContextServiceNew测试通过
- [ ] T-505: IntentAnalyzer测试通过

---

### Day 4: 集成测试

**日期**: Day 4  
**任务**: T-511, T-512, T-513, T-514  
**预计时间**: 1天（8小时）  
**优先级**: P0

#### 前提条件

- ✅ 所有单元测试已完成（T-501到T-505）

#### 具体任务

1. **端到端聊天流程测试** (T-511, 2小时)
   - 创建 `backend/tests/integration/test_chat_flow.py`
   - 测试完整的聊天流程
   - 验证三大引擎在真实场景中的集成

2. **三大引擎并发调用测试** (T-512, 1.5小时)
   - 测试ContextServiceNew中三大引擎的并发调用
   - 验证并行执行和结果合并
   - 确保并发安全

3. **超时和降级策略测试** (T-513, 2小时)
   - 测试引擎超时时的降级策略
   - 测试各种超时场景
   - 验证系统稳定性

4. **意图分析器集成测试** (T-514, 1.5小时)
   - 测试意图分析器与ContextServiceNew的集成
   - 验证意图识别和引擎配置的正确性

5. **运行所有集成测试** (1小时)
   ```bash
   pytest backend/tests/integration/ -v
   ```

#### 完成标准

- [ ] 所有集成测试通过
- [ ] 端到端流程正常
- [ ] 并发调用安全
- [ ] 超时和降级策略正常

---

### Day 5: 性能和回归测试

**日期**: Day 5  
**任务**: T-521, T-522, T-523, T-531, T-532  
**预计时间**: 1天（8小时）  
**优先级**: P0

#### 前提条件

- ✅ 所有集成测试已完成（T-511到T-514）

#### 具体任务

1. **QPS测试** (T-521, 1.5小时)
   - 创建性能测试脚本
   - 使用压力测试工具
   - 目标：QPS≥20

2. **延迟测试** (T-522, 1.5小时)
   - 测试P50和P95延迟
   - 使用性能监控工具
   - 目标：P50<200ms, P95<500ms

3. **缓存命中率测试** (T-523, 1小时)
   - 测试缓存命中率
   - 验证多级缓存系统
   - 目标：命中率≥60%

4. **现有功能回归测试** (T-531, 2小时)
   - 运行所有现有测试
   - 确保没有功能退化
   ```bash
   pytest backend/tests/ -v
   ```

5. **新实现vs旧实现对比测试** (T-532, 2小时)
   - 对比新实现和旧实现的输出结果
   - 验证功能等价性
   - 确保一致性

#### 完成标准

- [ ] QPS≥20
- [ ] P50延迟<200ms, P95延迟<500ms
- [ ] 缓存命中率≥60%
- [ ] 所有回归测试通过
- [ ] 对比测试结果一致

#### 检查点

- ✅ 性能指标达标
- ✅ 没有功能退化
- ✅ 新实现与旧实现结果一致

---

### Day 6: 测试验证总结和准备

**日期**: Day 6（如果需要）  
**任务**: 测试验证总结  
**预计时间**: 0.5-1天

#### 具体任务

1. **测试报告整理** (2小时)
   - 整理所有测试结果
   - 生成测试覆盖率报告
   - 记录性能测试数据

2. **问题修复** (4-6小时)
   - 修复测试中发现的问题
   - 重新运行测试验证

3. **最终验证** (1小时)
   - 运行完整测试套件
   - 确保所有测试通过

#### 完成标准

- [ ] 所有测试通过
- [ ] 测试报告完整
- [ ] 准备进入下一阶段

---

## 📅 第二周：清理旧代码和文档更新（3-4天）

### Day 7: 代码迁移

**日期**: Day 7  
**任务**: T-601, T-602, T-603  
**预计时间**: 0.5天（4小时）  
**优先级**: P0

#### 前提条件

- ✅ 所有测试通过（阶段一完成）

#### 具体任务

1. **更新ContextBuilder** (T-601, 1.5小时)
   - 打开 `backend/app/core/context/builder.py`
   - 移除 `MemoryManager` 导入
   - 移除 `memory_manager` 参数
   - 添加废弃警告注释
   - 运行测试验证

2. **更新ChatOrchestrator** (T-602, 1.5小时)
   - 打开 `backend/app/services/orchestration/chat_orchestrator.py`
   - 移除 `MemoryManager` 导入
   - 移除 `memory_manager` 参数
   - 确保只使用ContextService
   - 运行测试验证

3. **更新API依赖** (T-603, 1小时)
   - 打开 `backend/app/api/deps.py`
   - 移除 `get_memory_manager` 依赖（如果不再需要）
   - 更新类型注解
   - 运行测试验证

#### 完成标准

- [ ] 所有MemoryManager引用已移除
- [ ] 所有测试通过
- [ ] 代码可以正常运行

#### 检查点

- ✅ 没有编译错误
- ✅ 没有类型检查错误
- ✅ 所有测试通过

---

### Day 8: 删除废弃文件（顺序执行）

**日期**: Day 8  
**任务**: T-611, T-612, T-613, T-614, T-621  
**预计时间**: 1天（8小时）  
**优先级**: P0

#### ⚠️ 重要：必须顺序执行，每步后测试

#### 步骤1: 删除memory引擎目录 (T-611, 1.5小时)

1. **创建Git备份** (15分钟)
   ```bash
   git tag backup-before-delete-memory-engine
   git add .
   git commit -m "backup: before deleting memory engine"
   ```

2. **检查引用** (30分钟)
   ```bash
   # 检查是否还有其他文件引用memory引擎
   grep -r "from app.engines.memory" backend/app/
   grep -r "import.*memory" backend/app/
   ```

3. **删除目录** (15分钟)
   ```bash
   rm -rf backend/app/engines/memory/
   ```

4. **运行测试验证** (30分钟)
   ```bash
   pytest backend/tests/ -v
   # 确保所有测试通过
   ```

#### 步骤2: 删除memory_service.py (T-612, 1小时)

1. **检查引用** (20分钟)
   ```bash
   grep -r "memory_service" backend/app/
   ```

2. **删除文件** (10分钟)
   ```bash
   rm backend/app/services/memory_service.py
   ```

3. **运行测试验证** (30分钟)

#### 步骤3: 删除memory_retriever.py (T-613, 1小时)

1. **检查引用** (20分钟)
   ```bash
   grep -r "memory_retriever" backend/app/
   ```

2. **删除文件** (10分钟)
   ```bash
   rm backend/app/services/context/memory_retriever.py
   ```

3. **运行测试验证** (30分钟)

#### 步骤4: 标记memory API为废弃 (T-614, 1小时)

1. **添加废弃标记** (30分钟)
   - 打开 `backend/app/api/v1/memory.py`
   - 添加废弃警告注释
   - 添加 `@deprecated` 装饰器

2. **运行测试验证** (30分钟)

#### 步骤5: 删除废弃测试文件 (T-621, 1.5小时)

1. **检查引用** (30分钟)
   ```bash
   grep -r "test_memory" backend/tests/
   ```

2. **删除测试文件** (30分钟)
   ```bash
   rm backend/tests/deprecated/test_memory.py
   rm -rf backend/tests/deprecated/test_memory_old/
   rm backend/tests/deprecated/test_memory_service.py
   ```

3. **运行测试验证** (30分钟)

#### 完成标准

- [ ] 所有废弃文件已删除或标记
- [ ] 所有测试通过
- [ ] Git备份已创建
- [ ] 没有破坏性变更

#### 检查点

- ✅ 每删除一个文件后测试通过
- ✅ 没有编译错误
- ✅ 功能正常

---

### Day 9-10: 文档更新

**日期**: Day 9-10  
**任务**: T-701, T-702, T-711, T-721, T-722, T-723  
**预计时间**: 1-2天（8-16小时）  
**优先级**: P1-P2

#### Day 9: 架构和API文档更新 (4小时)

1. **更新后端架构设计文档** (T-701, 1.5小时)
   - 打开 `docs/core/02-后端架构设计-续.md`
   - 添加三大引擎详细说明
   - 移除旧memory引擎说明

2. **更新架构重构方案文档** (T-702, 1小时)
   - 打开 `docs/reports/三大人格化引擎系统架构重构方案.md`
   - 更新迁移状态
   - 添加清理步骤说明

3. **更新API接口设计文档** (T-711, 1.5小时)
   - 打开 `docs/core/04-API接口设计.md`
   - 标记废弃的API端点
   - 说明替代方案

#### Day 10: README和配置文档更新 (4小时)

1. **更新backend README** (T-721, 1小时)
   - 打开 `backend/README.md`
   - 添加三大引擎说明
   - 更新环境变量说明

2. **更新环境变量文档** (T-722, 1.5小时)
   - 更新 `.env.example`
   - 更新 `docs/setup/CONFIG.md`
   - 添加三大引擎配置说明

3. **更新Docker配置文档** (T-723, 1.5小时)
   - 更新 `docker-compose.yml`
   - 更新部署文档
   - 确保包含三大引擎服务

#### 完成标准

- [ ] 所有文档已更新
- [ ] 文档内容准确
- [ ] 文档格式正确

---

## 📋 每日检查清单

### 每日开始前

- [ ] 检查Git状态（确保工作区干净）
- [ ] 拉取最新代码
- [ ] 运行基础测试确保环境正常

### 每日结束时

- [ ] 提交代码（如果有变更）
- [ ] 更新任务状态（在VibeKanban中）
- [ ] 记录遇到的问题和解决方案
- [ ] 准备第二天的工作

### 每周结束时

- [ ] 运行完整测试套件
- [ ] 生成测试报告
- [ ] 更新进度文档
- [ ] 总结本周工作

---

## 🎯 关键里程碑

### 里程碑1: 单元测试完成（Day 3结束）

**标准**:
- ✅ 所有单元测试通过
- ✅ 覆盖率≥85%
- ✅ 测试代码质量良好

**验证**:
```bash
pytest backend/tests/test_engines/ -v --cov=app.engines --cov-report=html
```

### 里程碑2: 集成测试完成（Day 4结束）

**标准**:
- ✅ 所有集成测试通过
- ✅ 端到端流程正常
- ✅ 并发调用安全

**验证**:
```bash
pytest backend/tests/integration/ -v
```

### 里程碑3: 测试验证完成（Day 5结束）

**标准**:
- ✅ 所有测试通过
- ✅ 性能指标达标
- ✅ 没有功能退化

**验证**:
```bash
pytest backend/tests/ -v
# 运行性能测试
# 运行对比测试
```

### 里程碑4: 代码清理完成（Day 8结束）

**标准**:
- ✅ 所有废弃文件已删除
- ✅ 所有测试通过
- ✅ 没有破坏性变更

**验证**:
```bash
pytest backend/tests/ -v
# 检查没有memory引擎引用
```

### 里程碑5: 项目完成（Day 10结束）

**标准**:
- ✅ 所有任务完成
- ✅ 所有文档更新
- ✅ 代码审查通过

---

## ⚠️ 风险控制措施

### 删除文件前的检查清单

每次删除文件前必须：

1. **创建Git备份**
   ```bash
   git tag backup-before-delete-<filename>
   git commit -m "backup: before deleting <filename>"
   ```

2. **检查引用**
   ```bash
   grep -r "<filename>" backend/app/
   ```

3. **运行测试**
   ```bash
   pytest backend/tests/ -v
   ```

4. **删除文件**

5. **再次运行测试**
   ```bash
   pytest backend/tests/ -v
   ```

### 如果出现问题

1. **立即停止**
2. **回滚到Git备份**
   ```bash
   git checkout backup-before-delete-<filename>
   ```
3. **分析问题**
4. **修复后继续**

---

## 📊 进度跟踪

### 每日进度记录

建议每天记录：

```markdown
## Day X - [日期]

### 完成的任务
- [x] T-XXX: 任务名称

### 遇到的问题
- 问题1: 描述
  - 解决方案: 描述

### 明天的计划
- T-XXX: 任务名称

### 备注
- 其他说明
```

### 周报模板

```markdown
## Week X 进度报告

### 完成情况
- 已完成: X个任务
- 进行中: X个任务
- 待开始: X个任务

### 关键成果
- 成果1
- 成果2

### 遇到的问题
- 问题1及解决方案
- 问题2及解决方案

### 下周计划
- 计划1
- 计划2
```

---

## 🚀 快速参考

### 常用命令

```bash
# 运行所有测试
pytest backend/tests/ -v

# 运行特定测试
pytest backend/tests/test_engines/test_knowledge/ -v

# 检查覆盖率
pytest backend/tests/ --cov=app --cov-report=html

# 检查类型
mypy backend/app/

# 检查代码风格
flake8 backend/app/
black --check backend/app/

# 创建Git备份
git tag backup-<description>
git commit -m "backup: <description>"
```

### 重要文件路径

- 测试目录: `backend/tests/test_engines/`
- 引擎代码: `backend/app/engines/`
- 服务代码: `backend/app/services/`
- 文档目录: `docs/`

---

## 📝 执行日志模板

建议创建 `docs/reports/执行日志.md` 记录每日执行情况。

---

**最后更新**: 2026-01-02  
**状态**: 📋 待开始  
**预计开始日期**: 待定  
**预计完成日期**: 待定
