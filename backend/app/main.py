"""
AI闪念笔记 - FastAPI主应用
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.api import api_router
from app.database import db_manager
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.services.cache_service import CacheService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库连接
    print("🚀 正在启动AI闪念笔记后端服务...")
    try:
        await db_manager.init_all()
        print("✅ 数据库连接初始化完成")
        yield
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
    finally:
        # 关闭时清理数据库连接
        print("🔄 正在关闭数据库连接...")
        await db_manager.close_all()
        print("✅ 应用关闭完成")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI闪念笔记后端API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加限流中间件
from app.services.cache_service import get_cache_service
cache_service = get_cache_service()
app.add_middleware(RateLimitMiddleware, cache_service=cache_service)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """根路径健康检查"""
    return JSONResponse(
        content={
            "message": "AI闪念笔记API服务正在运行",
            "version": settings.APP_VERSION,
            "status": "healthy"
        }
    )


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
