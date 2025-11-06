# 🔧 快速修复：alembic ModuleNotFoundError

## 问题描述

运行 `alembic upgrade head` 时出现：
```
ModuleNotFoundError: No module named 'app'
```

## 原因

alembic 无法找到 `app` 模块，需要设置 PYTHONPATH。

## 🚀 解决方案（3种方法）

### 方法1：使用迁移脚本（推荐）✨

我们已经为您创建了专用的迁移脚本：

```bash
cd backend

# 运行数据库升级
./scripts/migrate.sh upgrade

# 其他命令
./scripts/migrate.sh downgrade    # 回滚
./scripts/migrate.sh history      # 查看历史
./scripts/migrate.sh current      # 查看当前版本
./scripts/migrate.sh create "消息" # 创建新迁移
```

### 方法2：手动设置PYTHONPATH

在 backend 目录下运行：

```bash
cd backend

# 设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 然后运行alembic命令
alembic upgrade head
```

### 方法3：使用开发脚本

开发脚本会自动处理迁移：

```bash
cd backend
./scripts/dev.sh
```

这个脚本会：
1. 激活虚拟环境
2. 安装依赖
3. 设置PYTHONPATH ✨
4. 运行数据库迁移
5. 启动开发服务器

## 💡 验证修复

运行以下命令验证：

```bash
cd backend
export PYTHONPATH="$(pwd)"
source venv/bin/activate
alembic current
```

如果看到类似输出说明成功：
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
c01c55832e12 (head)
```

## 📝 永久解决方案

在您的 `~/.zshrc` 或 `~/.bashrc` 中添加（可选）：

```bash
# 添加别名简化操作
alias cozychat-migrate='cd /path/to/CozyChat/backend && export PYTHONPATH=$(pwd) && alembic'
```

然后：
```bash
source ~/.zshrc  # 或 source ~/.bashrc
cozychat-migrate upgrade head
```

## ⚡ 现在就试试

立即运行：

```bash
cd /Users/zhangjun/CursorProjects/CozyChat/backend
./scripts/migrate.sh upgrade
```

✅ 问题应该解决了！
