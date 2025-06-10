"""
认证服务 - 处理用户认证、JWT token管理和密码安全
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import TokenData
from app.services.cache_service import CacheService


class AuthService:
    """认证服务类"""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        # 密码加密上下文
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT配置
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # 安全配置
        self.max_login_attempts = settings.MAX_LOGIN_ATTEMPTS
        self.login_timeout_minutes = settings.LOGIN_ATTEMPT_TIMEOUT_MINUTES
    
    # === 密码管理 ===
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    # === JWT Token管理 ===
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        # 生成JWT
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """验证并解析token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查token类型
            token_type = payload.get("type")
            if token_type != "access":
                return None
            
            # 提取用户信息
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            scopes: list = payload.get("scopes", [])
            
            if user_id is None:
                return None
            
            return TokenData(user_id=user_id, email=email, scopes=scopes)
            
        except JWTError:
            return None
    
    # === 用户认证 ===
    
    async def authenticate_user(
        self, 
        session: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """用户认证"""
        try:
            # 检查登录限制
            if await self._is_login_blocked(email):
                return None
            
            # 查找用户
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                await self._record_failed_login(email, "用户不存在")
                return None
            
            # 检查账户状态
            if not user.is_active:
                await self._record_failed_login(email, "账户已禁用")
                return None
            
            if user.is_locked():
                await self._record_failed_login(email, "账户已锁定")
                return None
            
            # 验证密码
            if not self.verify_password(password, user.password_hash):
                await self._increment_failed_attempts(session, user)
                await self._record_failed_login(email, "密码错误")
                return None
            
            # 认证成功，重置失败次数并更新最后登录时间
            await self._reset_failed_attempts(session, user)
            await self._update_last_login(session, user)
            await self._clear_login_blocks(email)
            
            return user
            
        except Exception as e:
            print(f"用户认证失败: {e}")
            return None
    
    # === 登录限制管理 ===
    
    async def _is_login_blocked(self, email: str) -> bool:
        """检查是否被登录限制"""
        block_key = f"login_block:{email}"
        block_info = await self.cache_service.get(block_key)
        return block_info is not None
    
    async def _record_failed_login(self, email: str, reason: str):
        """记录失败的登录尝试"""
        attempt_key = f"login_attempts:{email}"
        
        # 获取当前尝试次数
        attempts = await self.cache_service.get(attempt_key) or 0
        attempts += 1
        
        # 更新尝试次数
        await self.cache_service.set(
            attempt_key, 
            attempts, 
            self.login_timeout_minutes * 60
        )
        
        # 如果超过最大尝试次数，设置登录阻止
        if attempts >= self.max_login_attempts:
            block_key = f"login_block:{email}"
            await self.cache_service.set(
                block_key,
                {
                    "blocked_at": datetime.utcnow().isoformat(),
                    "reason": f"连续{attempts}次登录失败",
                    "attempts": attempts
                },
                self.login_timeout_minutes * 60
            )
    
    async def _clear_login_blocks(self, email: str):
        """清除登录限制"""
        attempt_key = f"login_attempts:{email}"
        block_key = f"login_block:{email}"
        
        await self.cache_service.delete(attempt_key)
        await self.cache_service.delete(block_key)
    
    async def _increment_failed_attempts(self, session: AsyncSession, user: User):
        """增加用户失败登录次数"""
        try:
            user.failed_login_attempts += 1
            
            # 如果失败次数过多，锁定账户
            if user.failed_login_attempts >= self.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.login_timeout_minutes
                )
            
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            print(f"更新失败登录次数失败: {e}")
    
    async def _reset_failed_attempts(self, session: AsyncSession, user: User):
        """重置失败登录次数"""
        try:
            user.failed_login_attempts = 0
            user.locked_until = None
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            print(f"重置失败登录次数失败: {e}")
    
    async def _update_last_login(self, session: AsyncSession, user: User):
        """更新最后登录时间"""
        try:
            user.last_login_at = datetime.utcnow()
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            print(f"更新最后登录时间失败: {e}")
    
    # === Token黑名单管理 ===
    
    async def blacklist_token(self, token: str, user_id: str):
        """将token加入黑名单"""
        try:
            # 解析token获取过期时间
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # 不验证过期时间
            )
            
            exp = payload.get("exp")
            if exp:
                # 计算剩余有效时间
                exp_datetime = datetime.fromtimestamp(exp)
                remaining_time = exp_datetime - datetime.utcnow()
                
                if remaining_time.total_seconds() > 0:
                    blacklist_key = f"blacklist_token:{token}"
                    await self.cache_service.set(
                        blacklist_key,
                        {"user_id": user_id, "blacklisted_at": datetime.utcnow().isoformat()},
                        int(remaining_time.total_seconds())
                    )
                    
        except Exception as e:
            print(f"Token加入黑名单失败: {e}")
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """检查token是否在黑名单中"""
        blacklist_key = f"blacklist_token:{token}"
        return await self.cache_service.get(blacklist_key) is not None
