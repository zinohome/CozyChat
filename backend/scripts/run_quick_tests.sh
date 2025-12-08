#!/bin/bash
# 快速测试脚本 - 避免hang死

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=========================================="
echo "快速测试执行（避免hang死）"
echo "=========================================="

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "虚拟环境已激活: $(which python)"
else
    echo "错误: 找不到虚拟环境 venv/bin/activate"
    exit 1
fi

# 设置测试环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 使用python -m pytest确保使用虚拟环境中的pytest
PYTEST_CMD="python -m pytest"

# 测试参数：快速、不覆盖、最多失败5个、遇到第一个失败就停止
TEST_ARGS="-v --tb=line --no-cov --maxfail=5 -x"

echo ""
echo "1. 运行核心服务测试（快速）..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_message_service.py \
        tests/test_services/test_memory_service.py \
        tests/test_services/test_tool_service.py \
        $TEST_ARGS

echo ""
echo "2. 运行MessageSaver测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_chat/test_message_saver.py \
        $TEST_ARGS

echo ""
echo "3. 运行ContextService测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_context/test_context_service.py \
        $TEST_ARGS

echo ""
echo "4. 运行对比测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_compare/test_new_vs_old.py \
        $TEST_ARGS

echo ""
echo "=========================================="
echo "快速测试完成！"
echo "=========================================="
