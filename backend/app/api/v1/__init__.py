"""API v1版本路由"""
from fastapi import APIRouter

from . import audio, auth, chat, config, health, memory, models, personalities, sessions, tools, users

api_router = APIRouter()

# 注册子路由
api_router.include_router(health.router, tags=["health"])

# Week 3: Chat路由
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# Week 4: Memory路由
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])

# Week 7: Audio路由（STT、TTS）
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])

# 配置API
api_router.include_router(config.router)

# Week 9: 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 认证相关
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Models API（OpenAI兼容）
api_router.include_router(models.router, prefix="/models", tags=["models"])

# 人格管理API
api_router.include_router(personalities.router, tags=["personalities"])

# 会话管理API
api_router.include_router(sessions.router, tags=["sessions"])

# 工具管理API
api_router.include_router(tools.router, tags=["tools"])


