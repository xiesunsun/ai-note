"""
API v1 路由汇总
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, notes, users

# 创建API路由器
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(notes.router, prefix="/notes", tags=["笔记"])
