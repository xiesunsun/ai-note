"""
用户模型 - PostgreSQL
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    # 主键：UUID类型
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # 用户名：唯一，不能为空
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    # 邮箱：唯一，不能为空
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    # 用户偏好设置：JSON格式
    preferences: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default={}
    )
    
    # 创建时间：自动设置
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # 更新时间：自动更新
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, email={self.email!r})"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "preferences": self.preferences or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
