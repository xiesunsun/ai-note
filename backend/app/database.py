"""
数据库连接管理器
支持PostgreSQL、MongoDB和Redis连接
"""

import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import motor.motor_asyncio
import redis.asyncio as redis
from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy声明式基类"""
    pass


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        # PostgreSQL异步引擎
        self.postgres_engine = None
        self.async_session_maker = None
        
        # MongoDB异步客户端
        self.mongo_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.mongo_db = None
        
        # Redis异步客户端
        self.redis_client: Optional[redis.Redis] = None
    
    async def init_postgres(self):
        """初始化PostgreSQL连接"""
        try:
            # 创建异步引擎
            self.postgres_engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                echo=settings.DEBUG,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            # 创建会话工厂
            self.async_session_maker = async_sessionmaker(
                self.postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            print("✅ PostgreSQL连接初始化成功")
            
        except Exception as e:
            print(f"❌ PostgreSQL连接初始化失败: {e}")
            raise
    
    async def init_mongodb(self):
        """初始化MongoDB连接"""
        try:
            # 创建MongoDB客户端
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
            )
            
            # 获取数据库引用
            self.mongo_db = self.mongo_client.ai_note
            
            # 测试连接
            await self.mongo_client.admin.command('ping')
            print("✅ MongoDB连接初始化成功")
            
        except Exception as e:
            print(f"❌ MongoDB连接初始化失败: {e}")
            raise
    
    async def init_redis(self):
        """初始化Redis连接"""
        try:
            # 创建Redis客户端
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
            )
            
            # 测试连接
            await self.redis_client.ping()
            print("✅ Redis连接初始化成功")
            
        except Exception as e:
            print(f"❌ Redis连接初始化失败: {e}")
            raise
    
    async def init_all(self):
        """初始化所有数据库连接"""
        await asyncio.gather(
            self.init_postgres(),
            self.init_mongodb(),
            self.init_redis(),
        )
    
    async def close_all(self):
        """关闭所有数据库连接"""
        tasks = []
        
        if self.postgres_engine:
            tasks.append(self.postgres_engine.dispose())
        
        if self.mongo_client:
            self.mongo_client.close()
        
        if self.redis_client:
            tasks.append(self.redis_client.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        print("✅ 所有数据库连接已关闭")
    
    async def get_postgres_session(self) -> AsyncSession:
        """获取PostgreSQL会话"""
        if not self.async_session_maker:
            raise RuntimeError("PostgreSQL未初始化")
        return self.async_session_maker()
    
    def get_mongo_db(self):
        """获取MongoDB数据库引用"""
        if self.mongo_db is None:
            raise RuntimeError("MongoDB未初始化")
        return self.mongo_db
    
    def get_redis_client(self):
        """获取Redis客户端"""
        if not self.redis_client:
            raise RuntimeError("Redis未初始化")
        return self.redis_client


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 依赖注入函数
async def get_postgres_session():
    """FastAPI依赖：获取PostgreSQL会话"""
    async with db_manager.async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_mongo_db():
    """FastAPI依赖：获取MongoDB数据库"""
    return db_manager.get_mongo_db()


def get_redis_client():
    """FastAPI依赖：获取Redis客户端"""
    return db_manager.get_redis_client()
