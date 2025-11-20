#!/bin/bash
set -e
set -x
apt clean && rm -rf /var/lib/apt/lists/* && \
rm /etc/apt/sources.list.d/passenger.list  && \
apt-get update && DEBIAN_FRONTEND=noninteractive && \
apt install -y --no-install-recommends curl wget procps git && \
# 安装 Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
apt install -y nodejs && \
# 安装 pnpm
npm install -g pnpm && \
cd /opt && \
mkdir -p cozychat && \
cd /opt/cozychat && \
# 如果代码已通过COPY复制，直接使用；否则从Git克隆
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then \
    echo "使用已复制的代码"; \
    cd frontend; \
elif [ -d "frontend" ]; then \
    cd frontend && git pull; \
else \
    git clone https://github.com/your-repo/CozyChat.git . && \
    cd frontend; \
fi && \
pnpm install && \
pnpm build && \
# 配置Nginx服务静态文件
mkdir -p /etc/nginx/sites-enabled && \
echo 'server {' > /etc/nginx/sites-enabled/cozychat && \
echo '    listen 5173;' >> /etc/nginx/sites-enabled/cozychat && \
echo '    server_name _;' >> /etc/nginx/sites-enabled/cozychat && \
echo '    root /opt/cozychat/frontend/dist;' >> /etc/nginx/sites-enabled/cozychat && \
echo '    index index.html;' >> /etc/nginx/sites-enabled/cozychat && \
echo '    location / {' >> /etc/nginx/sites-enabled/cozychat && \
echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/sites-enabled/cozychat && \
echo '    }' >> /etc/nginx/sites-enabled/cozychat && \
echo '}' >> /etc/nginx/sites-enabled/cozychat && \
cp /bd_build/50_start_h.sh /etc/my_init.d/50_start_h.sh && \
chmod 755 /etc/my_init.d/50_start_h.sh

