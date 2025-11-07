-- 创建测试数据库脚本
-- 使用方法：psql -h 192.168.66.10 -U cozychat -d postgres -f create_test_db.sql

-- 创建测试数据库
CREATE DATABASE cozychat_test;

-- 验证创建成功
\l cozychat_test

