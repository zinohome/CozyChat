# PyTorch 优化说明

## 🔍 问题分析

### 当前问题

构建过程中下载了：
- `torch-2.9.1-cp311-cp311-manylinux_2_28_x86_64.whl` - **~900MB** ⚠️
- `nvidia_cublas_cu12-12.8.4.1-py3-none-manylinux_2_27_x86_64.whl` - **~200-300MB** ⚠️

**总计**：~1.1-1.2GB

### 为什么不需要？

1. **项目只使用 CPU**：
   - `sentence-transformers` 使用 `device='cpu'`
   - 代码中没有 GPU 相关操作
   - 不需要 CUDA 支持

2. **CUDA 库不必要**：
   - `nvidia_cublas_cu12` 是 GPU 加速库
   - 只使用 CPU 时完全不需要

3. **完整版 PyTorch 太大**：
   - 完整版（包含 CUDA）：~900MB
   - CPU 版本：~200-300MB
   - **可以节省 ~600-700MB**

## ✅ 解决方案

### 方案1: 安装 CPU 版本的 PyTorch（推荐）

在 `install.sh` 中，先安装 CPU 版本的 PyTorch：

```bash
# 先安装CPU版本的PyTorch（避免下载CUDA版本）
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 然后安装其他依赖
pip install --no-cache-dir -r requirements/base.txt
```

**优势**：
- 自动选择 CPU 版本
- 不会下载 CUDA 库
- 减少 ~600-700MB

### 方案2: 在 requirements/base.txt 中指定

```txt
# PyTorch CPU版本
torch --index-url https://download.pytorch.org/whl/cpu
```

**注意**：pip 可能不支持在 requirements.txt 中使用 `--index-url`，建议在 `install.sh` 中处理。

### 方案3: 使用环境变量

```bash
export TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
pip install --no-cache-dir torch
```

## 📊 大小对比

| 版本 | 大小 | CUDA 支持 | 适用场景 |
|------|------|-----------|---------|
| **完整版（当前）** | ~900MB | ✅ 是 | GPU 训练/推理 |
| **CPU 版本（推荐）** | ~200-300MB | ❌ 否 | CPU 推理（本项目） |
| **节省空间** | **~600-700MB** | - | - |

## 🔧 实施步骤

### 1. 修改 install.sh

已在 `deployment/backend/docker/bd_build/install.sh` 中添加：

```bash
# 先安装CPU版本的PyTorch（避免下载CUDA版本，减少~700MB）
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
```

### 2. 验证安装

构建后检查：

```bash
# 在容器中检查
docker run --rm cozychat/backend:v0.1.0 python -c "import torch; print(torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

**期望输出**：
```
2.9.1
CUDA available: False  # ✅ 正确，不需要CUDA
```

### 3. 检查包大小

```bash
docker run --rm cozychat/backend:v0.1.0 \
  du -sh /opt/cozychat/backend/.venv/lib/python3.11/site-packages/torch*
```

**期望**：torch 目录应该只有 ~200-300MB（而不是 ~900MB）

## ⚠️ 注意事项

### 1. 确保代码使用 CPU

代码中已经正确使用 CPU：

```python
# backend/app/engines/memory/qdrant_engine.py
model = SentenceTransformer(model_name, device='cpu')  # ✅ 使用CPU
```

### 2. 如果将来需要 GPU

如果将来需要 GPU 支持，可以：
1. 修改 `install.sh`，移除 CPU 版本限制
2. 或使用多阶段构建，根据环境选择版本

### 3. 依赖关系

`sentence-transformers` 依赖 PyTorch，但：
- 可以使用 CPU 版本
- 不需要 CUDA 库
- 不需要 `nvidia_cublas_cu12` 等 CUDA 包

## 📈 预期效果

### 优化前

```
torch (完整版): ~900MB
nvidia_cublas_cu12: ~200-300MB
其他CUDA库: ~100-200MB
总计: ~1.2-1.4GB
```

### 优化后

```
torch (CPU版): ~200-300MB
CUDA库: 0MB
总计: ~200-300MB
```

**节省空间**：~1GB

### 镜像总大小

- **优化前**：9.89GB
- **优化后**：~8.9GB（减少 ~1GB）
- **如果同时优化基础镜像**：~2-3GB（减少 ~7GB）

## 🚀 验证

重新构建后：

```bash
cd deployment
./build-images.sh --no-cache
```

构建过程中应该看到：
- ✅ 下载 `torch` CPU 版本（~200-300MB）
- ❌ 不再下载 `nvidia_cublas_cu12`
- ❌ 不再下载其他 CUDA 库

## 📚 参考

- [PyTorch CPU 版本安装](https://pytorch.org/get-started/locally/)
- [sentence-transformers 文档](https://www.sbert.net/)
- [Docker 镜像优化最佳实践](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

