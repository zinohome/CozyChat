# 依赖安装指南

本项目提供了多种依赖安装方式，以解决复杂的依赖冲突问题。

## 方法 1：分步安装（推荐用于解决依赖冲突）

### 步骤 1：安装核心依赖
```bash
cd backend
pip install -r requirements/core.txt
```

### 步骤 2：安装 Cognee（可选）
```bash
pip install -r requirements/cognee.txt
```

**优点**：
- 分步安装可以避免复杂的依赖冲突
- 如果不需要 Cognee，可以跳过步骤 2
- 安装速度更快

**缺点**：
- 需要执行两个命令
- 如果 Cognee 安装失败，需要手动处理

---

## 方法 2：使用 pip-tools 固化依赖（推荐用于生产环境）

### 安装 pip-tools
```bash
pip install pip-tools
```

### 生成锁定文件
```bash
cd backend

# 生成核心依赖的锁定文件
pip-compile requirements/base.txt -o requirements/core-lock.txt

# 或者，如果使用分步安装方式
pip-compile requirements/core.txt -o requirements/core-lock.txt
pip-compile requirements/cognee.txt -o requirements/cognee-lock.txt
```

### 使用锁定文件安装
```bash
# 使用锁定文件安装（所有版本都已确定，不会冲突）
pip install -r requirements/core-lock.txt
pip install -r requirements/cognee-lock.txt
```

**优点**：
- 所有依赖版本都已锁定，确保一致性
- 安装速度快（无需解析依赖）
- 适合生产环境部署
- 可以提交到 Git，确保团队使用相同版本

**缺点**：
- 需要先安装 pip-tools
- 需要定期更新锁定文件

### 更新锁定文件
```bash
# 更新 base.txt 后，重新生成锁定文件
pip-compile --upgrade requirements/base.txt -o requirements/core-lock.txt
```

---

## 方法 3：直接安装（最简单，但可能遇到依赖冲突）

```bash
cd backend
pip install -r requirements/base.txt
```

**优点**：
- 一个命令完成所有安装
- 最简单直接

**缺点**：
- 可能遇到 `resolution-too-deep` 错误
- 安装时间可能很长
- 依赖冲突时需要手动解决

---

## 推荐方案

### 开发环境
使用 **方法 1（分步安装）**：
```bash
pip install -r requirements/core.txt
pip install -r requirements/cognee.txt  # 可选
```

### 生产环境
使用 **方法 2（pip-tools 固化）**：
```bash
# 首次设置
pip install pip-tools
pip-compile requirements/base.txt -o requirements/core-lock.txt

# 后续安装
pip install -r requirements/core-lock.txt
```

---

## 故障排查

### 如果遇到 `resolution-too-deep` 错误

1. **尝试分步安装**（方法 1）
2. **使用 pip-tools**（方法 2）
3. **临时移除 Cognee**：
   ```bash
   # 编辑 requirements/base.txt，注释掉 cognee>=0.4.1
   pip install -r requirements/base.txt
   # 然后单独安装 cognee
   pip install cognee>=0.4.1
   ```

### 如果 Cognee 安装失败

1. 检查数据库连接配置（PostgreSQL、Neo4j、Redis、MinIO）
2. 确认 `backend/config/memory.yaml` 中的配置正确
3. 查看错误日志，根据具体错误信息解决

---

## 文件说明

- `base.txt` - 完整的依赖列表（包含所有依赖）
- `core.txt` - 核心依赖（不包含 Cognee）
- `cognee.txt` - Cognee 相关依赖（需要先安装 core.txt）
- `dev.txt` - 开发环境依赖
- `test.txt` - 测试环境依赖
- `*-lock.txt` - pip-tools 生成的锁定文件（如果使用）

