# Week 1 验证文档

## 验证清单

### ✅ 1. 项目结构验证

检查以下目录和文件是否存在：

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── config/
│   ├── core/
│   ├── engines/
│   ├── models/
│   ├── schemas/
│   └── utils/
├── tests/
├── alembic/
├── requirements/
├── scripts/
├── .pre-commit-config.yaml
├── pytest.ini
├── alembic.ini
├── Dockerfile
└── README.md
```

### ✅ 2. 配置文件验证

检查配置加载是否正常：

```bash
cd backend
source venv/bin/activate
python -c "from app.config.config import settings; print(f'App: {settings.app_name}, Env: {settings.app_env}')"
```

预期输出：
```
App: CozyChat, Env: development
```

### ✅ 3. 数据库连接验证

需要先启动PostgreSQL：

```bash
# 启动PostgreSQL和Redis
docker-compose up -d postgres redis

# 等待服务启动
sleep 5

# 测试数据库连接
python -c "
from app.models.base import sync_engine
from sqlalchemy import text
with sync_engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection: OK')
"
```

### ✅ 4. FastAPI应用验证

启动开发服务器：

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

在另一个终端测试：

```bash
# 测试根路径
curl http://localhost:8000/

# 测试健康检查
curl http://localhost:8000/v1/health

# 访问API文档
open http://localhost:8000/docs
```

预期结果：
- 根路径返回欢迎信息
- 健康检查返回 `{"status": "healthy", ...}`
- API文档正常显示

### ✅ 5. 数据库迁移验证

```bash
cd backend
source venv/bin/activate

# 创建初始迁移
alembic revision --autogenerate -m "Initial schema"

# 应用迁移
alembic upgrade head

# 检查迁移状态
alembic current
```

预期结果：
- 迁移文件在 `alembic/versions/` 目录生成
- 迁移成功应用
- current命令显示当前版本

### ✅ 6. 测试验证

注意：测试需要测试数据库，确保环境变量中配置了正确的数据库URL。

```bash
cd backend
source venv/bin/activate

# 运行所有测试
pytest -v

# 查看测试覆盖率
pytest --cov=app --cov-report=term
```

预期结果：
- 所有测试通过
- 配置测试通过
- 健康检查测试通过
- 用户模型测试通过
- 覆盖率 > 80%

### ✅ 7. 代码质量验证

```bash
cd backend
source venv/bin/activate

# 运行Black检查
black app/ tests/ --check

# 运行isort检查
isort app/ tests/ --check-only

# 运行flake8检查
flake8 app/ tests/

# 运行mypy检查
mypy app/ --ignore-missing-imports
```

预期结果：
- 所有检查通过，无错误

### ✅ 8. Pre-commit验证

```bash
cd backend
source venv/bin/activate

# 安装pre-commit hooks
pre-commit install

# 运行所有检查
pre-commit run --all-files
```

预期结果：
- 所有hooks通过

### ✅ 9. Docker验证

```bash
# 从项目根目录
cd CozyChat

# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看后端日志
docker-compose logs backend

# 测试后端健康
curl http://localhost:8000/v1/health
```

预期结果：
- 所有服务状态为 `Up`
- 后端日志无错误
- 健康检查返回成功

## 验证通过标准

以下所有项必须通过才算Week 1完成：

- [x] 项目结构完整
- [x] 配置加载正常
- [x] 数据库连接成功
- [x] FastAPI应用启动成功
- [x] API接口可访问
- [x] 数据库迁移工作正常
- [x] 测试全部通过（覆盖率 > 80%）
- [x] 代码质量检查通过
- [x] Pre-commit hooks配置完成
- [x] Docker环境正常

## 常见问题

### Q1: 数据库连接失败

**解决方法**:
1. 检查PostgreSQL是否运行: `docker-compose ps`
2. 检查`.env`中的`DATABASE_URL`配置
3. 检查数据库用户权限

### Q2: 导入模块错误

**解决方法**:
1. 确保虚拟环境已激活
2. 重新安装依赖: `pip install -r requirements/base.txt`
3. 检查Python版本 >= 3.11

### Q3: 测试失败

**解决方法**:
1. 确保测试数据库存在
2. 检查环境变量配置
3. 查看详细错误信息: `pytest -v --tb=short`

### Q4: Pre-commit检查失败

**解决方法**:
1. 运行 `black app/ tests/` 自动格式化
2. 运行 `isort app/ tests/` 自动排序imports
3. 手动修复flake8和mypy报告的问题

## 下一步

Week 1完成后，继续Week 3的AI引擎系统开发。

参考文档：
- [后端架构设计](../docs/02-后端架构设计.md)
- [实施路线图](../docs/00-实施路线图.md)

