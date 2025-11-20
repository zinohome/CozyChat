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
# 安装 pnpm（如果不存在）
if ! command -v pnpm &> /dev/null; then \
    npm install -g pnpm; \
else \
    echo "✓ pnpm 已安装，跳过"; \
fi && \
cd /opt && \
mkdir -p cozychat && \
cd /opt/cozychat && \
# 优先从Git克隆代码（避免复制本地node_modules等文件）
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
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then \
        cd frontend; \
    else \
        echo "✗ 错误: 克隆成功但未找到 frontend 目录"; \
        exit 1; \
    fi; \
elif [ -d "frontend" ] && [ -f "frontend/package.json" ]; then \
    echo "⚠ Git克隆失败，使用已复制的代码（备选方案）"; \
    cd frontend; \
else \
    echo "✗ 错误: 无法从Git克隆且没有已复制的代码"; \
    echo "提示: 请配置正确的Git仓库地址（公开仓库）或确保Dockerfile中已COPY代码"; \
    exit 1; \
fi && \
# 读取环境变量文件（如果存在），用于构建时注入环境变量
# 注意：环境变量文件应该在容器启动时挂载到 /opt/cozychat/frontend/.env
if [ -f "/opt/cozychat/frontend/.env" ]; then \
    echo "✓ 找到 .env 文件，将在构建时使用"; \
    # 导出环境变量供构建使用
    export $(grep -v '^#' /opt/cozychat/frontend/.env | xargs); \
elif [ -f "/data/cozychat/frontend/frontend.env" ]; then \
    echo "✓ 找到 frontend.env 文件，将在构建时使用"; \
    # 导出环境变量供构建使用
    export $(grep -v '^#' /data/cozychat/frontend/frontend.env | grep -v '^$' | xargs); \
else \
    echo "⚠ 未找到 .env 文件，将使用默认值或构建参数"; \
fi && \
pnpm install && \
# 构建时注入环境变量（通过 Docker build args 或环境变量）
# 注意：Vite 的环境变量必须以 VITE_ 开头
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

