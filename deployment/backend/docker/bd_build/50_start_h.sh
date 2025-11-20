#!/bin/bash
cd /opt/cozychat/backend && \
source .venv/bin/activate && \
# 运行数据库迁移
alembic upgrade head && \
# 启动应用
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >> /tmp/cozychat.log 2>&1 &

