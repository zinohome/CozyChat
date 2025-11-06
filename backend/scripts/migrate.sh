#!/bin/bash
# 数据库迁移脚本

set -e

# 切换到backend目录
cd "$(dirname "$0")/.."

echo "📦 CozyChat Database Migration Tool"
echo "===================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# 检查环境变量
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# 设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "✅ PYTHONPATH set to: $(pwd)"

# 执行迁移命令
case "${1:-upgrade}" in
    upgrade)
        echo "⬆️  Running database upgrade..."
        alembic upgrade head
        echo "✅ Database migration completed!"
        ;;
    downgrade)
        echo "⬇️  Running database downgrade..."
        alembic downgrade -1
        echo "✅ Database downgrade completed!"
        ;;
    create)
        if [ -z "$2" ]; then
            echo "❌ Error: Please provide migration message"
            echo "Usage: ./migrate.sh create 'your migration message'"
            exit 1
        fi
        echo "📝 Creating new migration: $2"
        alembic revision --autogenerate -m "$2"
        echo "✅ Migration file created!"
        ;;
    history)
        echo "📋 Migration history:"
        alembic history
        ;;
    current)
        echo "📍 Current migration version:"
        alembic current
        ;;
    *)
        echo "Usage: ./migrate.sh [upgrade|downgrade|create|history|current]"
        echo ""
        echo "Commands:"
        echo "  upgrade    - Apply all pending migrations (default)"
        echo "  downgrade  - Rollback last migration"
        echo "  create     - Create new migration file"
        echo "  history    - Show migration history"
        echo "  current    - Show current migration version"
        exit 1
        ;;
esac

