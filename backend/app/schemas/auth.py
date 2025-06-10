"""
认证相关的Pydantic模式
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    """用户登录模式"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=1, description="密码")


class UserRegister(BaseModel):
    """用户注册模式"""
    name: str = Field(..., min_length=1, max_length=100, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, description="密码")


class Token(BaseModel):
    """Token响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class TokenData(BaseModel):
    """Token数据模式"""
    user_id: Optional[str] = Field(None, description="用户ID")
    email: Optional[str] = Field(None, description="邮箱")
    scopes: List[str] = Field(default=[], description="权限范围")


class RefreshToken(BaseModel):
    """刷新令牌模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordChange(BaseModel):
    """密码修改模式"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")


class PasswordReset(BaseModel):
    """密码重置模式"""
    email: EmailStr = Field(..., description="邮箱地址")


class PasswordResetConfirm(BaseModel):
    """密码重置确认模式"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")


class LoginAttempt(BaseModel):
    """登录尝试记录模式"""
    email: str = Field(..., description="邮箱地址")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str = Field(..., description="用户代理")
    success: bool = Field(..., description="是否成功")
    attempted_at: datetime = Field(..., description="尝试时间")
    failure_reason: Optional[str] = Field(None, description="失败原因")
