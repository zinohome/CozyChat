#!/bin/bash
# 构建前端镜像
# 注意：需要在项目根目录执行此脚本
IMGNAME=cozychat/frontend
IMGVERSION=v0.1.0

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 项目根目录（deployment的父目录）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$PROJECT_ROOT"
docker build --no-cache -t $IMGNAME:$IMGVERSION -f deployment/frontend/docker/Dockerfile .

