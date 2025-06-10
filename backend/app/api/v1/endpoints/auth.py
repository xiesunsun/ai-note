"""
认证相关API端点
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_postgres_session
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister, Token, PasswordChange
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService
from app.services.user_service import UserService
from app.middleware import get_current_active_user

router = APIRouter()

# 初始化服务
cache_service = CacheService()
auth_service = AuthService(cache_service)
user_service = UserService(cache_service)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_postgres_session)
):
    """用户注册"""
    try:
        # 检查邮箱是否已存在
        stmt = select(User).where(User.email == user_data.email)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        password_hash = auth_service.hash_password(user_data.password)

        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            is_active=True
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_postgres_session)
):
    """用户登录"""
    try:
        # 用户认证
        user = await auth_service.authenticate_user(
            session,
            form_data.username,  # OAuth2PasswordRequestForm使用username字段
            form_data.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 生成访问令牌
        access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "scopes": []  # 可以根据用户角色设置权限范围
            },
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": auth_service.access_token_expire_minutes * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """用户登出"""
    try:
        # 从请求头获取token
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]

            # 将token加入黑名单
            await auth_service.blacklist_token(token, str(current_user.id))

        return {"message": "登出成功"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """修改密码"""
    try:
        # 验证当前密码
        if not auth_service.verify_password(
            password_data.current_password,
            current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )

        # 更新密码
        current_user.password_hash = auth_service.hash_password(password_data.new_password)
        await session.commit()

        return {"message": "密码修改成功"}

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )
