"""
用户相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_postgres_session
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse
from app.services.user_service import UserService
from app.services.cache_service import CacheService
from app.middleware import get_current_active_user

router = APIRouter()

# 初始化服务
cache_service = CacheService()
user_service = UserService(cache_service)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """更新当前用户信息"""
    try:
        updated_user = await user_service.update_user(
            session,
            current_user.id,
            user_data
        )
        return updated_user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )
