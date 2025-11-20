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
# 如果代码已通过COPY复制，直接使用；否则从Git克隆
if [ -d "backend" ] && [ -f "backend/app/main.py" ]; then \
    echo "使用已复制的代码"; \
    cd backend; \
elif [ -d "backend" ]; then \
    cd backend && git pull; \
else \
    git clone https://github.com/your-repo/CozyChat.git . && \
    cd backend; \
fi && \
virtualenv .venv && \
. .venv/bin/activate && \
pip install --upgrade pip && \
pip install -r requirements/base.txt && \
if [ -f "../packages/tencent-speech-sdk/setup.py" ]; then \
    pip install -e ../packages/tencent-speech-sdk; \
fi && \
cp /bd_build/50_start_h.sh /etc/my_init.d/50_start_h.sh && \
chmod 755 /etc/my_init.d/50_start_h.sh

