#!/bin/bash

# Docker 镜像大小分析脚本
# 用法: ./analyze-image-size.sh <镜像名称:标签>

IMAGE_NAME="${1:-cozychat/backend:v0.1.0}"

echo "=========================================="
echo "Docker 镜像大小分析工具"
echo "=========================================="
echo "镜像: $IMAGE_NAME"
echo ""

# 检查镜像是否存在
if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "❌ 错误: 镜像 $IMAGE_NAME 不存在"
    echo ""
    echo "可用的镜像:"
    docker images | grep -E "REPOSITORY|cozychat"
    exit 1
fi

echo "1️⃣ 镜像基本信息"
echo "----------------------------------------"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

echo "2️⃣ 镜像各层大小（从大到小）"
echo "----------------------------------------"
docker history "$IMAGE_NAME" --human --format "{{.Size}}\t{{.CreatedBy}}" | head -20
echo ""

echo "3️⃣ 启动临时容器分析文件大小"
echo "----------------------------------------"
CONTAINER_ID=$(docker create "$IMAGE_NAME" /bin/bash)
echo "临时容器 ID: $CONTAINER_ID"
echo ""

echo "📊 目录大小分析（Top 20）"
echo "----------------------------------------"
docker exec "$CONTAINER_ID" du -h --max-depth=1 / 2>/dev/null | sort -rh | head -20
echo ""

echo "📦 Python 包大小分析"
echo "----------------------------------------"
if docker exec "$CONTAINER_ID" test -d /opt/cozychat/backend/.venv 2>/dev/null; then
    echo "虚拟环境位置: /opt/cozychat/backend/.venv"
    echo ""
    echo "Top 20 最大的 Python 包:"
    docker exec "$CONTAINER_ID" du -h /opt/cozychat/backend/.venv/lib/python3.11/site-packages/* 2>/dev/null | sort -rh | head -20
    echo ""
    echo "虚拟环境总大小:"
    docker exec "$CONTAINER_ID" du -sh /opt/cozychat/backend/.venv 2>/dev/null
else
    echo "⚠️  未找到虚拟环境"
fi
echo ""

echo "🗂️  项目代码大小"
echo "----------------------------------------"
if docker exec "$CONTAINER_ID" test -d /opt/cozychat/backend 2>/dev/null; then
    echo "项目目录大小:"
    docker exec "$CONTAINER_ID" du -sh /opt/cozychat/backend 2>/dev/null
    echo ""
    echo "各子目录大小:"
    docker exec "$CONTAINER_ID" du -h --max-depth=1 /opt/cozychat/backend 2>/dev/null | sort -rh | head -10
else
    echo "⚠️  未找到项目目录"
fi
echo ""

echo "📚 系统包大小分析"
echo "----------------------------------------"
echo "已安装的 Python 相关包:"
docker exec "$CONTAINER_ID" dpkg -l | grep -E "python|pip" 2>/dev/null | awk '{print $2, $3}'
echo ""

echo "已安装的大型包（>100MB）:"
docker exec "$CONTAINER_ID" dpkg-query -Wf '${Installed-Size}\t${Package}\n' 2>/dev/null | sort -rn | head -20 | awk '{printf "%.2f MB\t%s\n", $1/1024, $2}'
echo ""

echo "🔍 查找大文件（>100MB）"
echo "----------------------------------------"
docker exec "$CONTAINER_ID" find / -type f -size +100M 2>/dev/null | head -20
echo ""

echo "🧹 检查缓存和临时文件"
echo "----------------------------------------"
echo "apt 缓存:"
docker exec "$CONTAINER_ID" du -sh /var/lib/apt/lists 2>/dev/null || echo "已清理"
echo "pip 缓存:"
docker exec "$CONTAINER_ID" du -sh /root/.cache/pip 2>/dev/null || echo "已清理"
echo "临时文件:"
docker exec "$CONTAINER_ID" du -sh /tmp /var/tmp 2>/dev/null
echo ""

echo "📋 检查 Git 历史"
echo "----------------------------------------"
if docker exec "$CONTAINER_ID" test -d /opt/cozychat/.git 2>/dev/null; then
    echo "⚠️  警告: 发现 .git 目录！"
    docker exec "$CONTAINER_ID" du -sh /opt/cozychat/.git 2>/dev/null
else
    echo "✓ Git 历史已清理"
fi
echo ""

echo "🔧 检查构建工具"
echo "----------------------------------------"
if docker exec "$CONTAINER_ID" command -v gcc &>/dev/null; then
    echo "⚠️  警告: 发现构建工具 gcc"
    docker exec "$CONTAINER_ID" dpkg -l | grep -E "build-essential|gcc|g\+\+" 2>/dev/null
else
    echo "✓ 构建工具已清理"
fi
echo ""

echo "📊 总结"
echo "----------------------------------------"
TOTAL_SIZE=$(docker images "$IMAGE_NAME" --format "{{.Size}}")
echo "镜像总大小: $TOTAL_SIZE"
echo ""
echo "💡 优化建议:"
echo "1. 检查最大的 Python 包，看是否可以优化"
echo "2. 确认没有 .git 目录"
echo "3. 确认构建工具已删除"
echo "4. 确认所有缓存已清理"
echo "5. 考虑使用多阶段构建"
echo ""

# 清理临时容器
docker rm "$CONTAINER_ID" &>/dev/null

echo "=========================================="
echo "分析完成！"
echo "=========================================="

