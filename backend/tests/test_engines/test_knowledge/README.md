# Cognee知识引擎单元测试

## 测试概述

本目录包含Cognee知识引擎（`CogneeKnowledgeEngine`）的完整单元测试，覆盖所有公共和私有方法。

## 测试覆盖率

**目标覆盖率：≥85%**

### 测试方法覆盖

| 方法 | 测试用例数 | 覆盖场景 |
|------|-----------|---------|
| `__init__` | 3 | 有配置、无token、默认值 |
| `initialize` | 4 | 成功、已初始化、健康检查失败、异常 |
| `health_check` | 5 | 成功(ok/ready)、失败、无客户端、异常 |
| `search_knowledge` | 10 | CHUNKS成功、降级、异常、GRAPH_COMPLETION、边界条件 |
| `_parse_search_results` | 8 | 字符串、对象、字典、混合格式、无法解析 |
| `add_knowledge` | 5 | 成功、无元数据、额外参数、异常、自动初始化 |
| `shutdown` | 2 | 有客户端、无客户端 |
| 指标更新 | 2 | 成功、失败 |

**总计：38个测试用例**

## 运行测试

### 运行所有测试

```bash
cd backend
pytest tests/test_engines/test_knowledge/test_cognee_engine.py -v
```

### 运行特定测试类

```bash
pytest tests/test_engines/test_knowledge/test_cognee_engine.py::TestCogneeKnowledgeEngine -v
```

### 运行特定测试方法

```bash
pytest tests/test_engines/test_knowledge/test_cognee_engine.py::TestCogneeKnowledgeEngine::test_search_knowledge_chunks_success -v
```

### 生成覆盖率报告

```bash
pytest tests/test_engines/test_knowledge/test_cognee_engine.py \
    --cov=app.engines.knowledge.cognee_engine \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=85
```

覆盖率报告将生成在 `htmlcov/index.html`

## 测试场景说明

### 1. 引擎初始化测试

- ✅ 使用配置初始化
- ✅ 无token初始化
- ✅ 默认值初始化
- ✅ 初始化成功流程
- ✅ 重复初始化（已初始化）
- ✅ 健康检查失败
- ✅ 初始化异常处理

### 2. 健康检查测试

- ✅ 健康检查成功（status=ok）
- ✅ 健康检查成功（status=ready）
- ✅ 健康检查失败（status不为ok/ready）
- ✅ 无客户端情况
- ✅ 健康检查异常处理

### 3. 知识搜索测试

**正常流程：**
- ✅ CHUNKS模式成功
- ✅ GRAPH_COMPLETION模式成功
- ✅ 多数据集搜索

**降级策略：**
- ✅ CHUNKS返回空，降级到GRAPH_COMPLETION
- ✅ CHUNKS异常，降级到GRAPH_COMPLETION

**异常流程：**
- ✅ 数据集不存在错误
- ✅ 一般异常处理

**边界条件：**
- ✅ 无数据集名称
- ✅ 空数据集列表
- ✅ 自动初始化

### 4. 搜索结果解析测试

- ✅ 字符串格式结果
- ✅ 对象格式（text属性）
- ✅ 对象格式（content属性）
- ✅ 字典格式结果
- ✅ 混合格式结果
- ✅ 无法解析的结果
- ✅ 空结果列表
- ✅ 无数据集名称

### 5. 知识添加测试

- ✅ 添加成功
- ✅ 无元数据
- ✅ 带额外参数
- ✅ 异常处理
- ✅ 自动初始化

### 6. 引擎关闭测试

- ✅ 有客户端关闭
- ✅ 无客户端关闭

### 7. 指标更新测试

- ✅ 成功操作更新指标
- ✅ 失败操作更新指标

## Mock策略

所有测试使用Mock避免外部依赖：

1. **CogneeClient Mock**：使用`unittest.mock.patch`模拟`CogneeClient`类
2. **异步方法Mock**：使用`AsyncMock`模拟异步方法
3. **返回值Mock**：使用`MagicMock`创建模拟返回值对象

## 测试数据

测试使用以下Mock数据：

- **健康检查响应**：`status="ok"` 或 `status="ready"`
- **搜索结果（CHUNKS）**：包含`text`和`score`属性的对象列表
- **搜索结果（GRAPH_COMPLETION）**：字符串列表
- **添加结果**：包含`data_id`属性的对象

## 注意事项

1. **异步测试**：所有异步方法测试使用`@pytest.mark.asyncio`装饰器
2. **Mock隔离**：每个测试用例独立Mock，避免相互影响
3. **边界条件**：测试覆盖了所有边界条件和异常情况
4. **覆盖率要求**：确保覆盖率≥85%

## 持续集成

测试应在以下场景运行：

- ✅ 代码提交前（pre-commit hook）
- ✅ Pull Request合并前
- ✅ 发布前验证

## 维护

当`CogneeKnowledgeEngine`代码变更时：

1. 更新相关测试用例
2. 添加新功能的测试
3. 确保覆盖率≥85%
4. 更新本文档
