#!/bin/bash
# 代码质量检查脚本

set -e

echo "Running code quality checks..."

# 激活虚拟环境
source venv/bin/activate

echo "1. Running Black (code formatting)..."
black app/ tests/ --check

echo "2. Running isort (import sorting)..."
isort app/ tests/ --check-only

echo "3. Running flake8 (style guide)..."
flake8 app/ tests/

echo "4. Running mypy (type checking)..."
mypy app/ --ignore-missing-imports

echo "All checks passed!"

