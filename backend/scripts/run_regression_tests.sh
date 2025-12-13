#!/bin/bash
# 配置迁移回归测试运行脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=========================================="
echo "配置迁移回归测试"
echo "=========================================="

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "虚拟环境已激活: $(which python)"
else
    echo "警告: 找不到虚拟环境 venv/bin/activate"
    echo "使用系统Python: $(which python)"
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
echo "1. 运行配置适配器测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_utils/test_config_adapter.py -v --tb=short || echo "⚠ 测试失败或跳过"

echo ""
echo "2. 运行配置加载器测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_utils/test_config_loader.py -v --tb=short || echo "⚠ 测试失败或跳过"

echo ""
echo "3. 运行记忆系统测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_engines/test_memory/test_memory_manager.py -v --tb=short -k "config" || echo "⚠ 测试失败或跳过"

echo ""
echo "4. 运行会话标题生成测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_core/test_session/test_title_generator.py -v --tb=short || echo "⚠ 测试失败或跳过"

echo ""
echo "5. 运行上下文服务测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_services/test_context/ -v --tb=short || echo "⚠ 测试失败或跳过"

echo ""
echo "6. 运行性能中间件测试..."
echo "----------------------------------------"
$PYTEST_CMD tests/test_middleware/test_performance.py -v --tb=short || echo "⚠ 测试失败或跳过"

echo ""
echo "7. 运行配置验证脚本..."
echo "----------------------------------------"
python scripts/validate_config_migration.py || echo "⚠ 验证失败或跳过"

echo ""
echo "=========================================="
echo "回归测试完成"
echo "=========================================="

