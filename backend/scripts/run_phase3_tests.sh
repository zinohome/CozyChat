#!/bin/bash
# 阶段三测试运行脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=========================================="
echo "阶段三测试执行"
echo "=========================================="

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "虚拟环境已激活: $(which python)"
else
    echo "错误: 找不到虚拟环境 venv/bin/activate"
    echo "请确保在backend目录下运行此脚本"
    exit 1
fi

# 检查pytest是否安装
if ! python -m pytest --version &> /dev/null; then
    echo "警告: pytest未安装，正在安装..."
    pip install -r requirements/test.txt
fi

# 设置测试环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 使用python -m pytest确保使用虚拟环境中的pytest
PYTEST_CMD="python -m pytest"

echo ""
echo "1. 运行单元测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_orchestration/ \
        tests/test_services/test_context/ \
        tests/test_services/test_message_service.py \
        tests/test_services/test_tool_service.py \
        tests/test_services/test_memory_service.py \
        tests/test_api/test_chat_simplified.py \
        -v --tb=short -x

echo ""
echo "2. 运行集成测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_integration/ \
        -v --tb=short -x

echo ""
echo "3. 运行回归测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_regression/ \
        -v --tb=short -x

echo ""
echo "4. 运行对比测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_compare/ \
        -v --tb=short -x

echo ""
echo "5. 检查测试覆盖率..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_orchestration/ \
        tests/test_services/test_context/ \
        tests/test_services/test_message_service.py \
        tests/test_services/test_tool_service.py \
        tests/test_services/test_memory_service.py \
        --cov=app.services.orchestration \
        --cov=app.services.context \
        --cov=app.services.message_service \
        --cov=app.services.tool_service \
        --cov=app.services.memory_service \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/phase3

echo ""
echo "=========================================="
echo "阶段三测试完成！"
echo "=========================================="
echo ""
echo "覆盖率报告已生成: htmlcov/phase3/index.html"
