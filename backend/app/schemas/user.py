"""
用户相关的Pydantic模式
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """用户基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")


class UserCreate(UserBase):
    """创建用户模式"""
    preferences: Optional[Dict[str, Any]] = Field(default={}, description="用户偏好设置")


class UserUpdate(BaseModel):
    """更新用户模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")


class UserResponse(UserBase):
    """用户响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="用户ID")
    preferences: Dict[str, Any] = Field(default={}, description="用户偏好设置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
