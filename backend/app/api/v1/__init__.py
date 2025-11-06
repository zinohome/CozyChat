"""API v1版本路由"""
from fastapi import APIRouter

from . import chat, health, memory, users

api_router = APIRouter()

# 注册子路由
api_router.include_router(health.router, tags=["health"])

# Week 3: Chat路由
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# Week 4: Memory路由
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])

# Week 7: 添加audio路由
# api_router.include_router(audio.router, prefix="/audio", tags=["audio"])

# Week 9: 用户管理路由
api_router.include_router(users.router, tags=["users"])


