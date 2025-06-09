"""
用户相关API端点
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """获取当前用户信息"""
    return JSONResponse(
        content={
            "message": "用户信息功能开发中",
            "status": "coming_soon"
        }
    )


@router.put("/me")
async def update_current_user():
    """更新当前用户信息"""
    return JSONResponse(
        content={
            "message": "用户信息更新功能开发中",
            "status": "coming_soon"
        }
    )
