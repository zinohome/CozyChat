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
# 优先从Git克隆代码（避免复制本地node_modules等文件）
echo "尝试从Git克隆代码..."; \
# 配置Git（禁用交互式认证提示）
export GIT_TERMINAL_PROMPT=0 && \
export GIT_ASKPASS=/bin/echo && \
# 尝试克隆（支持公开仓库，无需认证）
if git clone ${GIT_REPO_URL:-https://github.com/zinohome/CozyChat.git} . 2>/dev/null; then \
    echo "✓ Git克隆成功"; \
    cd frontend; \
elif [ -d "frontend" ] && [ -f "frontend/package.json" ]; then \
    echo "⚠ Git克隆失败，使用已复制的代码（备选方案）"; \
    cd frontend; \
else \
    echo "✗ 错误: 无法从Git克隆且没有已复制的代码"; \
    echo "提示: 请配置正确的Git仓库地址（公开仓库）或确保Dockerfile中已COPY代码"; \
    exit 1; \
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

