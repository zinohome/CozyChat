#!/bin/bash
set -e
set -x
apt clean && rm -rf /var/lib/apt/lists/* && \
rm /etc/apt/sources.list.d/passenger.list  && \
apt-get update && DEBIAN_FRONTEND=noninteractive && \
# 安装运行时依赖（最小化）
apt install -y --no-install-recommends \
    ffmpeg \
    libssl3 \
    libffi8 \
    portaudio19-dev \
    net-tools \
    libsasl2-2 \
    curl \
    wget \
    procps \
    git \
    python3-pip && \
# 安装 Python 3.11（如果不存在）
if ! command -v python3.11 &> /dev/null; then \
    apt install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt install -y --no-install-recommends python3.11 python3.11-venv; \
fi && \
# 安装构建工具（仅用于编译 Python 包，后续会删除）
apt install -y --no-install-recommends build-essential python3.11-dev libpython3.11-dev && \
rm -f /usr/bin/python && ln -s /usr/bin/python3.11 /usr/bin/python && \
python -m pip install --no-cache-dir virtualenv && \
cd /opt && \
mkdir -p cozychat && \
cd /opt/cozychat && \
# 优先从Git克隆代码（避免复制本地venv等文件）
echo "尝试从Git克隆代码..."; \
# 配置Git（禁用交互式认证提示）
export GIT_TERMINAL_PROMPT=0 && \
export GIT_ASKPASS=/bin/echo && \
# 清理目录（如果存在旧文件）
if [ "$(ls -A . 2>/dev/null)" ]; then \
    echo "⚠ 目录不为空，清理中..."; \
    rm -rf * .* 2>/dev/null || true; \
fi && \
# 尝试克隆（支持公开仓库，无需认证）
REPO_URL="${GIT_REPO_URL:-https://github.com/zinohome/CozyChat.git}"; \
echo "正在克隆仓库: $REPO_URL"; \
if git clone "$REPO_URL" . 2>&1; then \
    echo "✓ Git克隆成功"; \
    # 立即删除 Git 历史记录（在切换目录前）
    if [ -d ".git" ]; then \
        echo "清理 Git 历史记录..."; \
        rm -rf .git; \
    fi; \
    if [ -d "backend" ] && [ -f "backend/app/main.py" ]; then \
        cd backend; \
    else \
        echo "✗ 错误: 克隆成功但未找到 backend 目录"; \
        exit 1; \
    fi; \
elif [ -d "backend" ] && [ -f "backend/app/main.py" ]; then \
    echo "⚠ Git克隆失败，使用已复制的代码（备选方案）"; \
    cd backend; \
else \
    echo "✗ 错误: 无法从Git克隆且没有已复制的代码"; \
    echo "提示: 请配置正确的Git仓库地址（公开仓库）或确保Dockerfile中已COPY代码"; \
    exit 1; \
fi && \
virtualenv .venv && \
. .venv/bin/activate && \
pip install --upgrade pip && \
# 设置环境变量，防止自动下载模型
export SENTENCE_TRANSFORMERS_HOME=/tmp && \
export TRANSFORMERS_CACHE=/tmp && \
export HF_HOME=/tmp && \
export TORCH_HOME=/tmp && \
# 先安装CPU版本的PyTorch（避免下载CUDA版本，减少~700MB）
echo "安装CPU版本的PyTorch（避免CUDA依赖）..."; \
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
# 安装其他依赖（不缓存，不自动下载模型）
pip install --no-cache-dir -r requirements/base.txt && \
# 安装腾讯语音SDK（如果存在）
if [ -f "packages/tencent-speech-sdk/setup.py" ]; then \
    pip install --no-cache-dir -e packages/tencent-speech-sdk; \
fi && \
# 清理：删除构建工具和开发依赖（生产环境不需要）
apt-get remove -y --purge build-essential python3.11-dev libpython3.11-dev git && \
apt-get autoremove -y && \
apt-get clean && \
rm -rf /var/lib/apt/lists/* && \
# 清理：删除所有临时文件和缓存（包括模型缓存）
rm -rf /tmp/* /var/tmp/* && \
rm -rf /tmp/.cache && \
rm -rf /tmp/huggingface && \
rm -rf /tmp/transformers && \
rm -rf /tmp/torch && \
# 清理：删除 pip 缓存
rm -rf ~/.cache/pip && \
rm -rf /root/.cache/pip && \
# 清理：删除 Hugging Face 模型缓存（sentence-transformers 可能下载的模型）
rm -rf ~/.cache/huggingface && \
rm -rf /root/.cache/huggingface && \
# 清理：删除 PyTorch 缓存
rm -rf ~/.cache/torch && \
rm -rf /root/.cache/torch && \
# 清理：删除所有缓存目录
rm -rf ~/.cache/* && \
rm -rf /root/.cache/* && \
# 清理：删除 Python 字节码缓存
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && \
find . -type f -name "*.pyc" -delete 2>/dev/null || true && \
find . -type f -name "*.pyo" -delete 2>/dev/null || true && \
# 清理：删除可能的模型下载目录（chromadb 等）
find . -type d -name "models" -path "*/cache/*" -exec rm -r {} + 2>/dev/null || true && \
find . -type d -name ".models" -exec rm -r {} + 2>/dev/null || true && \
cp /bd_build/50_start_h.sh /etc/my_init.d/50_start_h.sh && \
chmod 755 /etc/my_init.d/50_start_h.sh

