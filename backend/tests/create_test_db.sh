#!/bin/bash
# 创建测试数据库脚本
# 使用方法：./create_test_db.sh

set -e

echo "正在创建测试数据库 cozychat_test..."

# 使用psql创建数据库
psql -h 192.168.66.10 -U cozychat -d postgres <<EOF
-- 如果数据库已存在，先删除
DROP DATABASE IF EXISTS cozychat_test;

-- 创建测试数据库
CREATE DATABASE cozychat_test;

-- 验证创建成功
\l cozychat_test
EOF

echo "✅ 测试数据库创建成功！"
echo ""
echo "现在可以运行测试了："
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  pytest tests/ -v"

