# 依赖安装和清理指南

## 🔍 检查当前环境

首先检查您是否使用虚拟环境：

```bash
# 检查是否在虚拟环境中
which python
# 如果在虚拟环境中，会显示类似：/path/to/venv/bin/python
# 如果在系统环境中，会显示类似：/usr/bin/python 或 /Library/Frameworks/...
```

---

## 🧹 清理方案（按推荐顺序）

### 方案 1：使用虚拟环境（强烈推荐）⭐

**优点**：
- 完全隔离，不影响系统 Python
- 可以随时删除重建
- 项目之间互不干扰

#### 步骤：

```bash
cd backend

# 1. 创建新的虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 3. 升级 pip
pip install --upgrade pip

# 4. 安装依赖（使用分步安装）
pip install -r requirements/core.txt
pip install -r requirements/cognee.txt  # 可选
```

**如果已有虚拟环境，想重新开始**：

```bash
cd backend

# 1. 删除旧的虚拟环境
rm -rf venv  # macOS/Linux
# 或
rmdir /s venv  # Windows

# 2. 重新创建虚拟环境
python3 -m venv venv

# 3. 激活并安装
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/core.txt
pip install -r requirements/cognee.txt  # 可选
```

---

### 方案 2：卸载冲突的包（如果使用系统 Python）

**⚠️ 警告**：如果使用系统 Python，卸载包可能影响其他项目。建议先使用方案 1。

```bash
# 卸载可能冲突的包
pip uninstall -y cognee fastapi-users aiohttp yarl tokenizers hf-xet

# 然后重新安装
pip install -r requirements/core.txt
pip install -r requirements/cognee.txt
```

---

### 方案 3：使用 pip 的 --upgrade 和 --force-reinstall

```bash
# 强制重新安装所有依赖
pip install --upgrade --force-reinstall -r requirements/core.txt
pip install --upgrade --force-reinstall -r requirements/cognee.txt
```

---

### 方案 4：完全清理 pip 缓存（如果怀疑缓存问题）

```bash
# 清理 pip 缓存
pip cache purge

# 然后重新安装
pip install -r requirements/core.txt
pip install -r requirements/cognee.txt
```

---

## 📋 推荐安装流程

### 首次安装（推荐）

```bash
cd backend

# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate  # macOS/Linux

# 3. 升级 pip
pip install --upgrade pip

# 4. 安装核心依赖
pip install -r requirements/core.txt

# 5. 安装 Cognee（可选）
pip install -r requirements/cognee.txt
```

### 重新安装（清理后）

```bash
cd backend

# 1. 删除旧的虚拟环境
rm -rf venv

# 2. 创建新的虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 升级 pip
pip install --upgrade pip

# 5. 安装依赖
pip install -r requirements/core.txt
pip install -r requirements/cognee.txt  # 可选
```

---

## 🔧 使用 pip-tools 固化依赖（生产环境推荐）

### 首次设置

```bash
cd backend

# 1. 激活虚拟环境（如果使用）
source venv/bin/activate

# 2. 安装 pip-tools
pip install pip-tools

# 3. 生成锁定文件
pip-compile requirements/base.txt -o requirements/core-lock.txt

# 4. 使用锁定文件安装
pip install -r requirements/core-lock.txt
```

### 更新依赖

```bash
# 更新 base.txt 后，重新生成锁定文件
pip-compile --upgrade requirements/base.txt -o requirements/core-lock.txt

# 安装更新后的依赖
pip install -r requirements/core-lock.txt
```

---

## ❓ 常见问题

### Q: 我应该使用虚拟环境吗？

**A: 强烈建议使用虚拟环境！**

- ✅ 完全隔离，不影响系统 Python
- ✅ 可以随时删除重建
- ✅ 项目之间互不干扰
- ✅ 避免权限问题

### Q: 我已经在系统 Python 中安装了很多包，怎么办？

**A: 建议创建虚拟环境**

系统 Python 中的包不会丢失，虚拟环境是独立的。您可以：
1. 创建虚拟环境用于本项目
2. 系统 Python 继续用于其他项目

### Q: 如何确认虚拟环境已激活？

**A: 检查命令提示符**

激活后，命令提示符前会显示 `(venv)`：
```bash
(venv) zhangjun@MacPro2013 backend %
```

### Q: 安装后如何验证？

**A: 检查关键包**

```bash
# 检查关键包是否安装
pip list | grep -E "cognee|fastapi|qdrant|sentence-transformers"

# 或测试导入
python -c "import cognee; print('Cognee installed:', cognee.__version__)"
python -c "import fastapi; print('FastAPI installed:', fastapi.__version__)"
```

---

## 🚨 故障排查

### 如果遇到权限错误

```bash
# 不要使用 sudo！使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install ...
```

### 如果遇到 "command not found: python3"

```bash
# macOS: 安装 Python
brew install python3

# 或使用 python 命令
python -m venv venv
```

### 如果虚拟环境激活失败

```bash
# macOS/Linux
source venv/bin/activate

# 如果还是失败，检查虚拟环境是否存在
ls -la venv/bin/activate
```

---

## 📝 总结

**最佳实践**：
1. ✅ 使用虚拟环境（方案 1）
2. ✅ 分步安装（先 core.txt，再 cognee.txt）
3. ✅ 生产环境使用 pip-tools 固化依赖

**避免**：
1. ❌ 在系统 Python 中直接安装（除非确定不会影响其他项目）
2. ❌ 使用 sudo pip install
3. ❌ 一次性安装所有依赖（如果遇到冲突）

