# 测试基础设施设置指南

## 1. 创建测试数据库

连接到PostgreSQL并创建测试数据库：

```sql
-- 连接到PostgreSQL
psql -h 192.168.66.10 -U cozychat -d postgres

-- 创建测试数据库
CREATE DATABASE cozychat_test;

-- 验证创建成功
\l cozychat_test
```

## 2. 验证连接

运行测试配置验证：

```bash
cd backend
source venv/bin/activate
pytest tests/test_config.py -v
```

## 3. 运行基础设施测试

验证所有fixtures是否正常工作：

```bash
pytest tests/test_infrastructure.py -v
```

## 4. 开始编写测试

现在可以开始编写单元测试了！

参考：
- `tests/test_engines/` - 引擎测试示例
- `tests/test_api/` - API测试示例
- `tests/conftest.py` - 可用的fixtures
