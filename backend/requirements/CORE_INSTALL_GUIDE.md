# 核心依赖安装指南

## ⚠️ 重要提示：避免安装 CUDA 版本的 PyTorch

`requirements/core.txt` 中包含 `sentence-transformers==2.3.1`，它会自动依赖 `torch`（PyTorch）。

**问题**：
- `pip install torch` 默认安装**完整版**（包含 CUDA 支持），约 900MB
- 完整版会自动拉取所有 CUDA 库（`nvidia_cublas_cu12` 等），约 1.4GB
- **总计：~2.3GB** ⚠️

**实际情况**：
- 项目代码使用 CPU：`SentenceTransformer(model_name, device='cpu')`
- **不需要 CUDA 支持**
- CPU 版本只需 ~200-300MB
- **可以节省 ~2GB 空间**

## ✅ 正确安装方式

### 方法1：分步安装（推荐）

```bash
# 步骤1：先安装CPU版本的PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 步骤2：安装其他核心依赖
pip install -r requirements/core.txt
```

### 方法2：使用环境变量

```bash
# 设置PyTorch索引URL为CPU版本
export TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

# 先安装torch
pip install torch

# 然后安装其他依赖
pip install -r requirements/core.txt
```

### 方法3：使用 pip 的约束文件（高级）

创建 `constraints.txt`：

```txt
--index-url https://download.pytorch.org/whl/cpu
torch>=2.0.0
```

然后安装：

```bash
pip install -c constraints.txt -r requirements/core.txt
```

## 🔍 验证安装

安装完成后，验证是否使用了 CPU 版本：

```bash
python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"
```

**期望输出**：
```
PyTorch版本: 2.x.x
CUDA可用: False  # ✅ 正确，不需要CUDA
```

## 📊 空间对比

| 版本 | PyTorch大小 | CUDA库大小 | 总计 | 适用场景 |
|------|------------|-----------|------|---------|
| **完整版（默认）** | ~900MB | ~1.4GB | **~2.3GB** | GPU训练/推理 |
| **CPU版本（推荐）** | ~200-300MB | 0MB | **~200-300MB** | CPU推理（本项目） |
| **节省空间** | - | - | **~2GB** | - |

## 🚨 如果已经安装了完整版

如果已经安装了完整版的 PyTorch，可以卸载后重新安装 CPU 版本：

```bash
# 卸载完整版
pip uninstall torch torchvision torchaudio -y

# 安装CPU版本
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 验证
python -c "import torch; print('CUDA可用:', torch.cuda.is_available())"
```

## 📚 参考文档

- [PyTorch CPU 版本安装指南](https://pytorch.org/get-started/locally/)
- [项目部署文档：PyTorch优化说明](../docs/deployment/PyTorch优化说明.md)
- [项目部署文档：为什么没有torch却下载了torch](../docs/deployment/为什么没有torch却下载了torch.md)
