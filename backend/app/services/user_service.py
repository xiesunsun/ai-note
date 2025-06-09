"""
用户服务
处理用户相关的业务逻辑
"""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """用户服务类"""
    
    @staticmethod
    async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
        """创建新用户"""
        try:
            # 创建用户实例
            user = User(
                name=user_data.name,
                email=user_data.email,
                preferences=user_data.preferences or {}
            )
            
            # 添加到会话并提交
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            return user
            
        except IntegrityError as e:
            await session.rollback()
            if "email" in str(e.orig):
                raise ValueError(f"邮箱 {user_data.email} 已被使用")
            raise ValueError("创建用户失败：数据完整性错误")
        except Exception as e:
            await session.rollback()
            raise ValueError(f"创建用户失败: {str(e)}")
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """根据ID获取用户"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"获取用户失败: {str(e)}")
    
    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"获取用户失败: {str(e)}")
    
    @staticmethod
    async def get_users(
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
    
    @staticmethod
    async def update_user(
        session: AsyncSession, 
        user_id: uuid.UUID, 
        user_data: UserUpdate
    ) -> Optional[User]:
        """更新用户信息"""
        try:
            # 获取用户
            user = await UserService.get_user_by_id(session, user_id)
            if not user:
                return None
            
            # 更新字段
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            # 提交更改
            await session.commit()
            await session.refresh(user)
            
            return user
            
        except IntegrityError as e:
            await session.rollback()
            if "email" in str(e.orig):
                raise ValueError(f"邮箱 {user_data.email} 已被使用")
            raise ValueError("更新用户失败：数据完整性错误")
        except Exception as e:
            await session.rollback()
            raise ValueError(f"更新用户失败: {str(e)}")
    
    @staticmethod
    async def delete_user(session: AsyncSession, user_id: uuid.UUID) -> bool:
        """删除用户"""
        try:
            # 获取用户
            user = await UserService.get_user_by_id(session, user_id)
            if not user:
                return False
            
            # 删除用户
            await session.delete(user)
            await session.commit()
            
            return True
            
        except Exception as e:
            await session.rollback()
            raise ValueError(f"删除用户失败: {str(e)}")
    
    @staticmethod
    async def user_exists(session: AsyncSession, user_id: uuid.UUID) -> bool:
        """检查用户是否存在"""
        user = await UserService.get_user_by_id(session, user_id)
        return user is not None
