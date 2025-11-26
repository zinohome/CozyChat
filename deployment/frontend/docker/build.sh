#!/bin/bash
# 构建前端镜像
# 注意：需要在项目根目录执行此脚本
IMGNAME=cozychat/frontend
IMGVERSION=v0.1.2

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 项目根目录（deployment的父目录）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$PROJECT_ROOT"

# 读取环境变量文件（如果存在）
ENV_FILE="deployment/frontend.env.example"
if [ -f "frontend/.env" ]; then
    ENV_FILE="frontend/.env"
elif [ -f "deployment/frontend.env" ]; then
    ENV_FILE="deployment/frontend.env"
fi

# 构建参数：从环境变量文件读取并传递给 Docker
BUILD_ARGS=""
if [ -f "$ENV_FILE" ]; then
    echo "✓ 从 $ENV_FILE 读取环境变量"
    # 读取以 VITE_ 开头的环境变量
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # 跳过注释和空行
        if [[ $key =~ ^[[:space:]]*# ]] || [[ -z "$key" ]]; then
            continue
        fi
        # 移除前后空格
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        # 只处理以 VITE_ 开头的变量
        if [[ $key == VITE_* ]]; then
            BUILD_ARGS="$BUILD_ARGS --build-arg $key=$value"
        fi
    done < "$ENV_FILE"
else
    echo "⚠ 未找到环境变量文件，将使用默认值"
fi

# 构建镜像
docker build --no-cache $BUILD_ARGS -t $IMGNAME:$IMGVERSION -f deployment/frontend/docker/Dockerfile .

