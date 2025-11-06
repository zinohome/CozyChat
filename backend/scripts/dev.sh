#!/bin/bash
# 开发服务器启动脚本

set -e

# 切换到backend目录
cd "$(dirname "$0")/.."

echo "🚀 Starting CozyChat Backend Development Server..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# 安装依赖
echo "📥 Installing dependencies..."
pip install -q -r requirements/base.txt
pip install -q -r requirements/dev.txt

# 检查环境变量
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# 设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "✅ PYTHONPATH set to: $(pwd)"

# 运行数据库迁移
echo "🔄 Running database migrations..."
alembic upgrade head

# 启动开发服务器
echo "✨ Starting server on http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

