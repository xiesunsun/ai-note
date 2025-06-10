"""
认证中间件 - JWT验证和用户认证
"""

from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_postgres_session
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService
from app.schemas.auth import TokenData


# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """认证中间件类"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.auth_service = AuthService(self.cache_service)
    
    async def get_current_user(
        self,
        request: Request,
        session: AsyncSession = Depends(get_postgres_session),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[User]:
        """获取当前用户（可选认证）"""
        if not credentials:
            return None
        
        return await self._authenticate_token(credentials.credentials, session)
    
    async def get_current_user_required(
        self,
        request: Request,
        session: AsyncSession = Depends(get_postgres_session),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> User:
        """获取当前用户（必须认证）"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await self._authenticate_token(credentials.credentials, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证令牌无效",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    async def get_current_active_user(
        self,
        request: Request,
        session: AsyncSession = Depends(get_postgres_session),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> User:
        """获取当前活跃用户"""
        # 先获取当前用户
        current_user = await self.get_current_user_required(request, session, credentials)

        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已禁用"
            )

        if current_user.is_locked():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="用户账户已锁定"
            )

        return current_user
    
    async def _authenticate_token(
        self, 
        token: str, 
        session: AsyncSession
    ) -> Optional[User]:
        """验证token并返回用户"""
        try:
            # 检查token是否在黑名单中
            if await self.auth_service.is_token_blacklisted(token):
                return None
            
            # 验证token
            token_data = self.auth_service.verify_token(token)
            if not token_data or not token_data.user_id:
                return None
            
            # 查找用户
            stmt = select(User).where(User.id == token_data.user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # 检查用户状态
            if not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            print(f"Token认证失败: {e}")
            return None


# 创建全局中间件实例
auth_middleware = AuthMiddleware()

# 导出依赖函数
get_current_user = auth_middleware.get_current_user
get_current_user_required = auth_middleware.get_current_user_required  
get_current_active_user = auth_middleware.get_current_active_user
