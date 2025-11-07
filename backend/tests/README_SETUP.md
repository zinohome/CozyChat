# 测试环境设置指南

## 问题1：创建测试数据库

### 方法1：使用SQL脚本（推荐）

```bash
cd backend/tests
psql -h 192.168.66.10 -U cozychat -d postgres -f create_test_db.sql
```

### 方法2：使用Shell脚本

```bash
cd backend/tests
./create_test_db.sh
```

### 方法3：手动创建

连接到PostgreSQL并执行：

```sql
-- 连接到PostgreSQL
psql -h 192.168.66.10 -U cozychat -d postgres

-- 创建测试数据库
CREATE DATABASE cozychat_test;

-- 验证创建成功
\l cozychat_test
```

### 验证数据库创建成功

```bash
cd backend
source venv/bin/activate
pytest tests/test_infrastructure.py::test_database_connection -v
```

## 问题2：修复pytest-asyncio支持

### 当前状态

pytest-asyncio已经在`pytest.ini`中配置了`asyncio_mode = auto`，但需要确保：

1. **已安装pytest-asyncio**：
   ```bash
   pip install pytest-asyncio
   ```

2. **测试文件正确使用装饰器**：
   - 异步测试函数使用`@pytest.mark.asyncio`
   - 异步fixture使用`@pytest_asyncio.fixture`

### 验证异步测试支持

```bash
cd backend
source venv/bin/activate
pytest tests/test_engines/test_ai/test_openai_engine.py -v
```

### 如果遇到问题

如果仍然遇到`AttributeError: 'Package' object has no attribute 'obj'`错误，可以：

1. **临时禁用asyncio模式**（仅用于同步测试）：
   ```bash
   pytest tests/ -v -p no:asyncio
   ```

2. **只运行异步测试**：
   ```bash
   pytest tests/ -v -m asyncio
   ```

## 完整设置步骤

1. **创建测试数据库**：
   ```bash
   cd backend/tests
   ./create_test_db.sh
   ```

2. **验证测试基础设施**：
   ```bash
   cd backend
   source venv/bin/activate
   pytest tests/test_infrastructure.py -v
   ```

3. **运行所有P0测试**：
   ```bash
   pytest tests/test_utils/test_security.py \
          tests/test_core/test_user/test_auth.py \
          tests/test_engines/test_ai/test_openai_engine.py \
          tests/test_engines/test_ai/test_ai_factory.py \
          tests/test_core/test_personality/test_orchestrator.py \
          tests/test_api/test_chat.py \
          tests/test_api/test_auth.py \
          -v
   ```

## 常见问题

### Q: 测试数据库连接失败

**A**: 检查：
- PostgreSQL服务是否运行
- 网络连接是否正常（192.168.66.10）
- 用户名和密码是否正确
- 数据库`cozychat_test`是否已创建

### Q: 异步测试无法运行

**A**: 检查：
- `pytest-asyncio`是否已安装：`pip list | grep pytest-asyncio`
- `pytest.ini`中`asyncio_mode = auto`是否设置
- 测试函数是否使用`@pytest.mark.asyncio`装饰器

### Q: 测试数据库已存在错误

**A**: 可以删除后重新创建：
```sql
DROP DATABASE IF EXISTS cozychat_test;
CREATE DATABASE cozychat_test;
```

## 下一步

设置完成后，可以：
1. 运行完整的P0测试套件
2. 继续编写P1测试（记忆、工具、人格管理）
3. 提高测试覆盖率到目标值（≥80%）

