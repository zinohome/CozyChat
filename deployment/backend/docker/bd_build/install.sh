#!/bin/bash
set -e
set -x
apt clean && rm -rf /var/lib/apt/lists/* && \
rm /etc/apt/sources.list.d/passenger.list  && \
apt-get update && DEBIAN_FRONTEND=noninteractive && \
apt install -y --no-install-recommends build-essential ffmpeg libssl-dev libffi-dev portaudio19-dev net-tools libsasl2-dev curl wget procps git libnss3-tools python3-pip && \
apt install -y software-properties-common  && add-apt-repository -y ppa:deadsnakes/ppa && apt install -y python3.11 && \
apt install -y python3.11-dev libpython3.11-dev && \
rm /usr/bin/python && ln -s /usr/bin/python3.11 /usr/bin/python && \
python -m pip install virtualenv && \
cd /opt && \
mkdir -p cozychat && \
cd /opt/cozychat && \
# 优先从Git克隆代码（避免复制本地venv等文件）
echo "尝试从Git克隆代码..."; \
# 配置Git（禁用交互式认证提示）
export GIT_TERMINAL_PROMPT=0 && \
export GIT_ASKPASS=/bin/echo && \
# 尝试克隆（支持公开仓库，无需认证）
if git clone ${GIT_REPO_URL:-https://github.com/zinohome/CozyChat.git} . 2>/dev/null; then \
    echo "✓ Git克隆成功"; \
    cd backend; \
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
pip install -r requirements/base.txt && \
# 安装腾讯语音SDK（如果存在）
if [ -f "packages/tencent-speech-sdk/setup.py" ]; then \
    pip install -e packages/tencent-speech-sdk; \
fi && \
cp /bd_build/50_start_h.sh /etc/my_init.d/50_start_h.sh && \
chmod 755 /etc/my_init.d/50_start_h.sh

