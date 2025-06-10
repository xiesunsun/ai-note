"""
用户相关的Pydantic模式
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator


class UserBase(BaseModel):
    """用户基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")


class UserCreate(UserBase):
    """创建用户模式"""
    password: str = Field(..., min_length=8, description="密码")
    preferences: Optional[Dict[str, Any]] = Field(default={}, description="用户偏好设置")

    @validator('password')
    def validate_password(cls, v):
        """密码强度验证"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含至少一个字母')
        return v


class UserUpdate(BaseModel):
    """更新用户模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")


class UserResponse(UserBase):
    """用户响应模式"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="用户ID")
    is_active: bool = Field(..., description="用户状态")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    preferences: Dict[str, Any] = Field(default={}, description="用户偏好设置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
