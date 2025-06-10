"""
限流中间件 - API请求频率限制
"""

import time
from typing import Dict, Optional
from fastapi import HTTPException, status, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.cache_service import CacheService


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, cache_service: Optional[CacheService] = None):
        super().__init__(app)
        self.cache_service = cache_service or CacheService()
        
        # 限流配置：路径 -> (请求数, 时间窗口秒数)
        self.rate_limits = {
            "/api/v1/auth/login": (5, 300),      # 登录：5次/5分钟
            "/api/v1/auth/register": (3, 3600),  # 注册：3次/小时
            "/api/v1/auth/logout": (10, 60),     # 登出：10次/分钟
            "default": (100, 60)                 # 默认：100次/分钟
        }
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 获取请求路径
        path = request.url.path
        
        # 检查是否需要限流
        if await self._should_rate_limit(client_ip, path):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试",
                headers={"Retry-After": "60"}
            )
        
        # 记录请求
        await self._record_request(client_ip, path)
        
        # 继续处理请求
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 使用客户端IP
        return request.client.host if request.client else "unknown"
    
    async def _should_rate_limit(self, client_ip: str, path: str) -> bool:
        """检查是否应该限流"""
        try:
            # 获取限流配置
            max_requests, window_seconds = self._get_rate_limit_config(path)
            
            # 生成缓存键
            cache_key = f"rate_limit:{client_ip}:{path}"
            
            # 获取当前请求记录
            request_data = await self.cache_service.get(cache_key)
            
            current_time = int(time.time())
            
            if not request_data:
                # 首次请求
                return False
            
            # 检查时间窗口
            first_request_time = request_data.get("first_request", current_time)
            request_count = request_data.get("count", 0)
            
            # 如果超出时间窗口，重置计数
            if current_time - first_request_time >= window_seconds:
                return False
            
            # 检查是否超过限制
            return request_count >= max_requests
            
        except Exception as e:
            print(f"限流检查失败: {e}")
            return False
    
    async def _record_request(self, client_ip: str, path: str):
        """记录请求"""
        try:
            # 获取限流配置
            max_requests, window_seconds = self._get_rate_limit_config(path)
            
            # 生成缓存键
            cache_key = f"rate_limit:{client_ip}:{path}"
            
            # 获取当前请求记录
            request_data = await self.cache_service.get(cache_key)
            
            current_time = int(time.time())
            
            if not request_data:
                # 首次请求
                request_data = {
                    "first_request": current_time,
                    "count": 1,
                    "last_request": current_time
                }
            else:
                first_request_time = request_data.get("first_request", current_time)
                
                # 如果超出时间窗口，重置计数
                if current_time - first_request_time >= window_seconds:
                    request_data = {
                        "first_request": current_time,
                        "count": 1,
                        "last_request": current_time
                    }
                else:
                    # 增加计数
                    request_data["count"] += 1
                    request_data["last_request"] = current_time
            
            # 保存到缓存
            await self.cache_service.set(
                cache_key,
                request_data,
                window_seconds
            )
            
        except Exception as e:
            print(f"记录请求失败: {e}")
    
    def _get_rate_limit_config(self, path: str) -> tuple:
        """获取路径的限流配置"""
        # 精确匹配
        if path in self.rate_limits:
            return self.rate_limits[path]
        
        # 模式匹配
        for pattern, config in self.rate_limits.items():
            if pattern != "default" and path.startswith(pattern):
                return config
        
        # 默认配置
        return self.rate_limits["default"]


class APIRateLimit:
    """API限流装饰器"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cache_service = CacheService()
    
    def __call__(self, func):
        """装饰器实现"""
        async def wrapper(*args, **kwargs):
            # 从参数中获取request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # 如果没有request对象，直接执行
                return await func(*args, **kwargs)
            
            # 获取客户端IP
            client_ip = self._get_client_ip(request)
            
            # 检查限流
            if await self._check_rate_limit(client_ip, func.__name__):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，请{self.window_seconds}秒后再试"
                )
            
            # 记录请求
            await self._record_request(client_ip, func.__name__)
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        """检查是否超过限流"""
        cache_key = f"api_rate_limit:{client_ip}:{endpoint}"
        
        request_data = await self.cache_service.get(cache_key)
        current_time = int(time.time())
        
        if not request_data:
            return False
        
        first_request_time = request_data.get("first_request", current_time)
        request_count = request_data.get("count", 0)
        
        # 检查时间窗口
        if current_time - first_request_time >= self.window_seconds:
            return False
        
        return request_count >= self.max_requests
    
    async def _record_request(self, client_ip: str, endpoint: str):
        """记录请求"""
        cache_key = f"api_rate_limit:{client_ip}:{endpoint}"
        
        request_data = await self.cache_service.get(cache_key)
        current_time = int(time.time())
        
        if not request_data:
            request_data = {
                "first_request": current_time,
                "count": 1
            }
        else:
            first_request_time = request_data.get("first_request", current_time)
            
            if current_time - first_request_time >= self.window_seconds:
                request_data = {
                    "first_request": current_time,
                    "count": 1
                }
            else:
                request_data["count"] += 1
        
        await self.cache_service.set(
            cache_key,
            request_data,
            self.window_seconds
        )
