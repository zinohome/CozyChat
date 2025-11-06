#!/bin/bash
# 测试脚本

set -e

echo "Running CozyChat Backend Tests..."

# 激活虚拟环境
source venv/bin/activate

# 安装测试依赖
pip install -r requirements/test.txt

# 运行测试
pytest -v --cov=app --cov-report=html --cov-report=term

echo "Test completed! Coverage report: htmlcov/index.html"

