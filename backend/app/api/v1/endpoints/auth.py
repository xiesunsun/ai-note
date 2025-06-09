"""
认证相关API端点
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/login")
async def login():
    """用户登录"""
    return JSONResponse(
        content={
            "message": "登录功能开发中",
            "status": "coming_soon"
        }
    )


@router.post("/register")
async def register():
    """用户注册"""
    return JSONResponse(
        content={
            "message": "注册功能开发中",
            "status": "coming_soon"
        }
    )


@router.post("/logout")
async def logout():
    """用户登出"""
    return JSONResponse(
        content={
            "message": "登出功能开发中",
            "status": "coming_soon"
        }
    )
