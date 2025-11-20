#!/bin/bash

# CozyChat Docker镜像一键构建脚本
# 用法: ./build-images.sh [选项]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认配置
BACKEND_IMAGE="cozychat/backend"
FRONTEND_IMAGE="cozychat/frontend"
VERSION="v0.1.0"
NO_CACHE=false
BUILD_BACKEND=true
BUILD_FRONTEND=true

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 项目根目录（deployment的父目录）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --backend-only)
            BUILD_FRONTEND=false
            shift
            ;;
        --frontend-only)
            BUILD_BACKEND=false
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --no-cache          不使用缓存构建（完全重新构建）"
            echo "  --backend-only      只构建后端镜像"
            echo "  --frontend-only     只构建前端镜像"
            echo "  --version VERSION   指定镜像版本（默认: v0.1.0）"
            echo "  --help, -h          显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                  # 构建所有镜像（使用缓存）"
            echo "  $0 --no-cache       # 完全重新构建所有镜像"
            echo "  $0 --backend-only   # 只构建后端镜像"
            echo "  $0 --version v0.2.0 # 构建指定版本的镜像"
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数 $1${NC}"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 构建参数
BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="--no-cache"
    echo -e "${YELLOW}警告: 将使用 --no-cache 构建，这会花费更长时间${NC}"
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker未运行，请先启动Docker${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CozyChat Docker镜像构建脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "项目根目录: $PROJECT_ROOT"
echo "镜像版本: $VERSION"
echo "构建参数: $BUILD_ARGS"
echo ""

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 构建后端镜像
if [ "$BUILD_BACKEND" = true ]; then
    echo -e "${GREEN}[1/2] 构建后端镜像...${NC}"
    echo "镜像名称: ${BACKEND_IMAGE}:${VERSION}"
    echo "Dockerfile: deployment/backend/docker/Dockerfile"
    echo ""
    
    docker build $BUILD_ARGS \
        -t ${BACKEND_IMAGE}:${VERSION} \
        -t ${BACKEND_IMAGE}:latest \
        -f deployment/backend/docker/Dockerfile \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 后端镜像构建成功: ${BACKEND_IMAGE}:${VERSION}${NC}"
    else
        echo -e "${RED}✗ 后端镜像构建失败${NC}"
        exit 1
    fi
    echo ""
fi

# 构建前端镜像
if [ "$BUILD_FRONTEND" = true ]; then
    echo -e "${GREEN}[2/2] 构建前端镜像...${NC}"
    echo "镜像名称: ${FRONTEND_IMAGE}:${VERSION}"
    echo "Dockerfile: deployment/frontend/docker/Dockerfile"
    echo ""
    
    docker build $BUILD_ARGS \
        -t ${FRONTEND_IMAGE}:${VERSION} \
        -t ${FRONTEND_IMAGE}:latest \
        -f deployment/frontend/docker/Dockerfile \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 前端镜像构建成功: ${FRONTEND_IMAGE}:${VERSION}${NC}"
    else
        echo -e "${RED}✗ 前端镜像构建失败${NC}"
        exit 1
    fi
    echo ""
fi

# 显示构建结果
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}构建完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "已构建的镜像:"
if [ "$BUILD_BACKEND" = true ]; then
    echo "  - ${BACKEND_IMAGE}:${VERSION}"
    echo "  - ${BACKEND_IMAGE}:latest"
fi
if [ "$BUILD_FRONTEND" = true ]; then
    echo "  - ${FRONTEND_IMAGE}:${VERSION}"
    echo "  - ${FRONTEND_IMAGE}:latest"
fi
echo ""
echo "查看镜像:"
echo "  docker images | grep cozychat"
echo ""
echo "使用docker-compose启动:"
echo "  cd deployment"
echo "  docker-compose up -d"
echo ""

