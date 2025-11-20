# 为什么 requirements/base.txt 中没有 torch 却下载了 torch？

## 🔍 问题分析

### 关键发现

`requirements/base.txt` 中确实**没有直接列出 `torch`**，但是：

```txt
sentence-transformers==2.3.1  # 第35行
```

### 依赖链分析

```
sentence-transformers==2.3.1
  └── 依赖 torch (PyTorch)
       └── 默认安装完整版（包含 CUDA）
            └── 自动拉取所有 CUDA 依赖
                 ├── nvidia_cublas_cu12 (594 MB)
                 ├── nvidia_cudnn_cu12 (707 MB)
                 ├── nvidia_cuda_nvrtc_cu12 (88 MB)
                 ├── nvidia_cuda_cupti_cu12 (10 MB)
                 └── nvidia_cuda_runtime_cu12 (1 MB)
```

### 为什么会自动下载？

1. **pip 的依赖解析机制**：
   - 当安装 `sentence-transformers` 时，pip 会检查它的依赖
   - `sentence-transformers` 的依赖包括 `torch`
   - pip 会自动安装所有未满足的依赖

2. **PyTorch 的默认行为**：
   - `pip install torch` 默认安装**完整版**（包含 CUDA 支持）
   - 完整版大小：~900 MB
   - CPU 版本大小：~200-300 MB

3. **CUDA 依赖的自动拉取**：
   - 一旦安装了完整版 PyTorch，会自动拉取所有 CUDA 库
   - 总计 ~1.4 GB 的 CUDA 库

## 📊 验证方法

### 方法1: 查看 sentence-transformers 的依赖

```bash
# 查看 sentence-transformers 的依赖
pip show sentence-transformers

# 或
pip install sentence-transformers --dry-run
```

**预期输出**：
```
Requires: torch, transformers, sentencepiece, ...
```

### 方法2: 查看 pip 的依赖解析

```bash
# 查看安装 sentence-transformers 时会安装哪些包
pip install sentence-transformers --dry-run --report report.json
cat report.json | grep -i torch
```

## ✅ 解决方案

### 方案1: 先安装 CPU 版本的 torch（推荐）

**原理**：
- 在安装 `sentence-transformers` 之前，先安装 CPU 版本的 `torch`
- 当 pip 解析 `sentence-transformers` 的依赖时，会发现 `torch` 已经安装
- 不会再次安装完整版的 `torch`
- 不会拉取任何 CUDA 依赖

**实施**（在 `install.sh` 中）：

```bash
# 先安装CPU版本的PyTorch（避免下载CUDA版本）
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 然后安装其他依赖（包括 sentence-transformers）
pip install --no-cache-dir -r requirements/base.txt
```

**优势**：
- 简单直接
- 确保只安装 CPU 版本
- 节省 ~2 GB 空间

---

### 方案2: 在 requirements/base.txt 中明确指定

**问题**：pip 的 requirements.txt 格式不支持 `--index-url` 参数。

**替代方案**：
```txt
# requirements/base.txt

# 注意：torch 需要在 install.sh 中单独安装 CPU 版本
# 不要在这里直接写 torch，否则会安装完整版

sentence-transformers==2.3.1
```

然后在 `install.sh` 中先安装 CPU 版本的 torch。

---

### 方案3: 使用环境变量

```bash
# 设置环境变量，强制使用 CPU 版本
export TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
pip install --no-cache-dir -r requirements/base.txt
```

**注意**：这种方法可能不够可靠，因为某些 pip 版本可能不遵循这个环境变量。

---

## 🎯 推荐方案

### 最佳实践：在 install.sh 中先安装 CPU 版本的 torch

```bash
# 在 install.sh 中
virtualenv .venv && \
. .venv/bin/activate && \
pip install --upgrade pip && \

# 关键：先安装CPU版本的PyTorch
echo "安装CPU版本的PyTorch（避免CUDA依赖）..."; \
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \

# 然后安装其他依赖
pip install --no-cache-dir -r requirements/base.txt && \
```

### 为什么这样有效？

1. **依赖已满足**：
   - `torch` 已经安装（CPU 版本）
   - pip 检测到依赖已满足，不会再次安装

2. **版本锁定**：
   - 已安装的 `torch` 版本会被使用
   - 不会触发 CUDA 依赖的安装

3. **避免依赖冲突**：
   - 如果先安装完整版，后续无法降级到 CPU 版本
   - 先安装 CPU 版本，可以避免这个问题

---

## 📊 优化效果

### 当前行为

```
pip install -r requirements/base.txt
  └── 检测到 sentence-transformers
       └── 解析依赖：需要 torch
            └── 安装完整版 torch (900 MB)
                 └── 自动拉取 CUDA 库 (1.4 GB)
                      └── 总计：~2.3 GB
```

### 优化后行为

```
pip install torch --index-url .../cpu  # 先安装 CPU 版本 (200-300 MB)
  └── torch (CPU) 已安装

pip install -r requirements/base.txt
  └── 检测到 sentence-transformers
       └── 解析依赖：需要 torch
            └── 检测到 torch 已安装 ✅
                 └── 跳过安装
                      └── 总计：~200-300 MB
```

**节省空间**：~2 GB

---

## ⚠️ 注意事项

### 1. 安装顺序很重要

**错误顺序**：
```bash
pip install -r requirements/base.txt  # 先安装，会下载完整版 torch
pip install torch --index-url .../cpu  # 后安装，可能冲突
```

**正确顺序**：
```bash
pip install torch --index-url .../cpu  # 先安装 CPU 版本
pip install -r requirements/base.txt  # 后安装，使用已安装的 torch
```

### 2. 验证安装

构建后验证：

```bash
docker run --rm cozychat/backend:v0.1.0 python -c "import torch; print('Version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

**期望输出**：
```
Version: 2.9.1
CUDA available: False  # ✅ 正确
```

### 3. 如果将来需要 GPU

如果将来需要 GPU 支持：
1. 修改 `install.sh`，移除 CPU 版本限制
2. 或使用多阶段构建，根据环境选择版本

---

## 📝 总结

### 问题

- `requirements/base.txt` 中没有 `torch`
- 但 `sentence-transformers` 依赖 `torch`
- pip 自动安装完整版 `torch`（包含 CUDA）
- 自动拉取所有 CUDA 库（~1.4 GB）

### 解决方案

在 `install.sh` 中，**先安装 CPU 版本的 torch**，然后再安装其他依赖。

### 效果

- 节省空间：~2 GB
- 镜像大小：从 9.89 GB 降至 ~7.9 GB
- 构建时间：减少（下载时间减少）

---

## 🔗 相关文档

- `deployment/pip安装日志分析.md` - 详细的包分析
- `deployment/PyTorch优化说明.md` - PyTorch 优化方案

