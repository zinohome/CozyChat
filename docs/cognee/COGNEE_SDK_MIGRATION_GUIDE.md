# Cognee SDK 迁移指南

## 一、迁移概述

本指南说明如何从 `cognee` 库迁移到 `cognee-sdk`。

**前提条件**：
- ✅ Cognee API 服务器已部署并运行（端口 8000）
- ✅ API 服务器健康检查通过：`curl http://localhost:8000/health`

---

## 二、迁移步骤

### 步骤 1：更新依赖

```bash
# 卸载旧库
pip uninstall -y cognee

# 安装新 SDK
pip install cognee-sdk>=0.1.1

# 或从 requirements 文件安装
pip install -r requirements/cognee.txt
```

### 步骤 2：更新配置文件

在 `backend/config/memory.yaml` 中添加 API 配置：

```yaml
cognee:
  engine: "cognee"
  
  # ==================== API 服务器配置 ====================
  api_url: "http://localhost:8000"  # Cognee API 服务器地址
  api_token: ""  # 可选，如果启用了认证
  
  # 其他配置保持不变...
```

**环境变量支持**：
```bash
# 可以通过环境变量覆盖配置
export COGNEE_API_URL="http://localhost:8000"
export COGNEE_API_TOKEN="your-token"  # 可选
```

### 步骤 3：验证迁移

```bash
# 1. 检查 SDK 是否安装
python -c "from cognee_sdk import CogneeClient; print('SDK installed')"

# 2. 测试 API 服务器连接
curl http://localhost:8000/health

# 3. 运行应用测试
pytest tests/test_engines/test_memory/test_cognee_engine.py
```

---

## 三、代码变更说明

### 3.1 主要变更

| 变更项 | 旧方式（cognee 库） | 新方式（cognee-sdk） |
|--------|-------------------|---------------------|
| **导入** | `import cognee` | `from cognee_sdk import CogneeClient, SearchType` |
| **初始化** | `await cognee.setup()` | `client = CogneeClient(api_url="...")` |
| **添加数据** | `await cognee.add(...)` | `await client.add(...)` |
| **搜索** | `await cognee.search(...)` | `await client.search(...)` |
| **删除** | `await cognee.delete(...)` | `await client.delete(...)` |
| **错误处理** | `except Exception` | `except ValidationError, ServerError` |

### 3.2 配置变更

**旧配置**（环境变量）：
```python
os.environ["DATABASE_URL"] = "..."
os.environ["LLM_API_KEY"] = "..."
# ... 大量环境变量
await cognee.setup()
```

**新配置**（API URL）：
```python
client = CogneeClient(
    api_url="http://localhost:8000",
    api_token="..."  # 可选
)
```

**优势**：
- ✅ 配置简化：只需要 API URL
- ✅ 配置集中：数据库、LLM 等配置在 API 服务器端管理
- ✅ 易于维护：不需要在多个地方管理配置

---

## 四、API 差异说明

### 4.1 方法签名差异

#### add() 方法

**旧方式**：
```python
await cognee.add(
    data=memory.content,
    dataset_name=dataset_name,
    node_set=node_set,
    metadata=metadata  # 直接支持
)
```

**新方式**：
```python
result = await client.add(
    data=memory.content,
    dataset_name=dataset_name,
    node_set=node_set
    # 注意：metadata 需要通过其他方式存储（如更新操作）
)
# result.data_id 包含创建的数据 ID
```

#### search() 方法

**旧方式**：
```python
results = await cognee.search(
    query_text=query,
    datasets=[dataset_name],
    query_type=SearchType.CHUNKS,
    top_k=top_k,
    use_combined_context=True
)
```

**新方式**：
```python
results = await client.search(
    query=query,  # 参数名从 query_text 改为 query
    search_type=SearchType.CHUNKS,  # 参数名从 query_type 改为 search_type
    datasets=[dataset_name],
    top_k=top_k,
    use_combined_context=True
)
```

#### delete() 方法

**旧方式**：
```python
await cognee.delete(
    dataset_name=dataset_name,
    data_ids=[memory_id]
)
```

**新方式**：
```python
# 需要先获取数据集 ID
datasets = await client.list_datasets()
dataset = [ds for ds in datasets if ds.name == dataset_name][0]

await client.delete(
    data_id=UUID(memory_id),  # 需要 UUID 类型
    dataset_id=dataset.id,  # 需要数据集 ID
    mode="soft"  # 或 "hard"
)
```

### 4.2 返回值差异

**旧方式**：返回原始对象或字典

**新方式**：返回类型化的 Pydantic 模型
- `AddResult` - 添加操作结果
- `SearchResult` - 搜索结果
- `DeleteResult` - 删除操作结果
- `Dataset` - 数据集对象

---

## 五、错误处理

### 5.1 异常类型

SDK 提供明确的异常类型：

```python
from cognee_sdk.exceptions import (
    AuthenticationError,  # 401/403
    NotFoundError,        # 404
    ValidationError,      # 400
    ServerError,          # 5xx
    TimeoutError,         # 超时
    CogneeAPIError,       # 其他 API 错误
    CogneeSDKError,       # SDK 内部错误
)
```

### 5.2 错误处理示例

```python
try:
    result = await client.add(data="...", dataset_name="test")
except ValidationError as e:
    logger.error(f"Validation error: {e.message}")
    # 处理验证错误
except ServerError as e:
    logger.error(f"Server error: {e.message}")
    # 处理服务器错误
except TimeoutError as e:
    logger.error(f"Timeout: {e.message}")
    # 处理超时
except CogneeAPIError as e:
    logger.error(f"API error: {e.message}")
    # 处理其他 API 错误
```

---

## 六、性能优化建议

### 6.1 连接池

SDK 自动管理 HTTP 连接池，无需手动配置。

### 6.2 批量操作

```python
# 使用 SDK 的批量方法
results = await client.add_batch(
    data_list=[m.content for m in memories],
    dataset_name=dataset_name
)
```

### 6.3 异步上下文管理器

```python
async with CogneeClient(api_url="...") as client:
    # 使用 client
    result = await client.add(...)
# 自动关闭连接
```

---

## 七、常见问题

### Q1: API 服务器未启动

**错误**：
```
ConnectionError: Failed to connect to http://localhost:8000
```

**解决**：
1. 检查 API 服务器是否运行：`curl http://localhost:8000/health`
2. 检查 `api_url` 配置是否正确
3. 检查防火墙和网络连接

### Q2: 认证失败

**错误**：
```
AuthenticationError: Invalid token
```

**解决**：
1. 检查 `api_token` 配置
2. 确认 API 服务器是否启用了认证
3. 使用 `client.login()` 获取新 token

### Q3: 数据集不存在

**错误**：
```
NotFoundError: Dataset not found
```

**解决**：
1. 使用 `client.create_dataset()` 创建数据集
2. 或使用 `client.list_datasets()` 查看现有数据集

### Q4: 搜索返回空结果

**可能原因**：
1. 数据集为空
2. 搜索类型不匹配
3. 相似度阈值过高

**解决**：
1. 先添加数据：`await client.add(...)`
2. 尝试不同的 `search_type`
3. 降低 `similarity_threshold`

---

## 八、回滚方案

如果迁移后出现问题，可以回滚：

```bash
# 1. 卸载 SDK
pip uninstall cognee-sdk

# 2. 重新安装旧库
pip install cognee>=0.4.1

# 3. 恢复配置文件
git checkout backend/config/memory.yaml

# 4. 恢复代码
git checkout backend/app/engines/memory/cognee_engine.py
```

---

## 九、测试清单

迁移完成后，请验证以下功能：

- [ ] 引擎初始化成功
- [ ] 健康检查通过
- [ ] 添加记忆功能正常
- [ ] 搜索记忆功能正常
- [ ] 删除记忆功能正常
- [ ] 批量操作功能正常
- [ ] 错误处理正确
- [ ] 性能满足要求

---

## 十、总结

**迁移优势**：
- ✅ 轻量级（5-10MB vs 500MB-2GB）
- ✅ 类型安全
- ✅ 更好的错误处理
- ✅ 配置简化

**注意事项**：
- ⚠️ 需要独立的 API 服务器
- ⚠️ 有网络延迟开销
- ⚠️ 需要维护 API 服务器

**推荐场景**：
- ✅ 已部署 Cognee API 服务器
- ✅ 需要分布式部署
- ✅ 需要多语言集成
- ✅ 需要轻量级部署

---

**文档版本**：1.0  
**最后更新**：2025-12-07  
**维护者**：CozyChat Team

