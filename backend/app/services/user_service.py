"""
用户服务
处理用户相关的业务逻辑，集成缓存功能
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.cache_service import CacheService, create_cache_service


class UserService:
    """用户服务类，集成缓存功能"""

    def __init__(self, cache_service: CacheService = None):
        self.cache_service = cache_service or create_cache_service()

    async def create_user(self, session: AsyncSession, user_data: UserCreate, password_hash: str) -> User:
        """创建新用户"""
        try:
            # 创建用户实例
            user = User(
                name=user_data.name,
                email=user_data.email,
                password_hash=password_hash,
                preferences=user_data.preferences or {}
            )

            # 添加到会话并提交
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # 缓存用户偏好设置
            if user.preferences:
                await self.cache_service.cache_user_preferences(
                    str(user.id), user.preferences
                )

            return user

        except IntegrityError as e:
            await session.rollback()
            if "email" in str(e.orig):
                raise ValueError(f"邮箱 {user_data.email} 已被使用")
            raise ValueError("创建用户失败：数据完整性错误")
        except Exception as e:
            await session.rollback()
            raise ValueError(f"创建用户失败: {str(e)}")
    
    async def get_user_by_id(self, session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """根据ID获取用户"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"获取用户失败: {str(e)}")

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"获取用户失败: {str(e)}")
    
    async def get_users(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """获取用户列表"""
        try:
            stmt = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise ValueError(f"获取用户列表失败: {str(e)}")

    async def update_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        user_data: UserUpdate
    ) -> Optional[User]:
        """更新用户信息"""
        try:
            # 获取用户
            user = await self.get_user_by_id(session, user_id)
            if not user:
                return None

            # 更新字段
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)

            # 提交更改
            await session.commit()
            await session.refresh(user)

            # 更新缓存
            if 'preferences' in update_data:
                await self.cache_service.cache_user_preferences(
                    str(user.id), user.preferences
                )

            return user

        except IntegrityError as e:
            await session.rollback()
            if "email" in str(e.orig):
                raise ValueError(f"邮箱 {user_data.email} 已被使用")
            raise ValueError("更新用户失败：数据完整性错误")
        except Exception as e:
            await session.rollback()
            raise ValueError(f"更新用户失败: {str(e)}")
    
    async def delete_user(self, session: AsyncSession, user_id: uuid.UUID) -> bool:
        """删除用户"""
        try:
            # 获取用户
            user = await self.get_user_by_id(session, user_id)
            if not user:
                return False

            # 删除用户
            await session.delete(user)
            await session.commit()

            # 清除用户相关缓存
            await self.cache_service.clear_user_cache(str(user_id))

            return True

        except Exception as e:
            await session.rollback()
            raise ValueError(f"删除用户失败: {str(e)}")

    async def user_exists(self, session: AsyncSession, user_id: uuid.UUID) -> bool:
        """检查用户是否存在"""
        user = await self.get_user_by_id(session, user_id)
        return user is not None

    # === 缓存相关方法 ===

    async def get_user_preferences_cached(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的用户偏好设置"""
        return await self.cache_service.get_user_preferences(user_id)

    async def cache_user_stats(self, user_id: str, stats: Dict[str, Any]) -> bool:
        """缓存用户统计信息"""
        return await self.cache_service.cache_user_stats(user_id, stats)

    async def get_user_stats_cached(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的用户统计信息"""
        return await self.cache_service.get_user_stats(user_id)


# 全局用户服务实例（延迟初始化）
def get_user_service() -> UserService:
    """获取用户服务实例"""
    return UserService()
