"""
测试配置文件
提供测试夹具和配置
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

from app.database import Base, DatabaseManager
from app.core.config import settings
from app.services.cache_service import CacheService
from app.services.user_service import UserService
from app.services.note_service import NoteService


# 测试数据库配置
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_ai_note"
TEST_MONGODB_URL = "mongodb://localhost:27017/test_ai_note"
TEST_REDIS_URL = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def postgres_engine():
    """创建PostgreSQL测试引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def postgres_session(postgres_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建PostgreSQL测试会话"""
    async_session_maker = async_sessionmaker(
        postgres_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="session")
async def mongo_client():
    """创建MongoDB测试客户端"""
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    yield client
    
    # 清理测试数据库
    await client.drop_database("test_ai_note")
    client.close()


@pytest_asyncio.fixture
async def mongo_db(mongo_client):
    """创建MongoDB测试数据库"""
    db = mongo_client.test_ai_note
    yield db
    
    # 清理集合
    collections = await db.list_collection_names()
    for collection_name in collections:
        await db[collection_name].delete_many({})


@pytest_asyncio.fixture(scope="session")
async def redis_client():
    """创建Redis测试客户端"""
    client = redis.from_url(
        TEST_REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    yield client
    
    # 清理
    await client.flushdb()
    await client.close()


@pytest_asyncio.fixture
async def cache_service(redis_client):
    """创建缓存服务实例"""
    service = CacheService(redis_client)
    yield service
    
    # 清理缓存
    await redis_client.flushdb()


@pytest_asyncio.fixture
async def user_service(cache_service):
    """创建用户服务实例"""
    return UserService(cache_service)


@pytest_asyncio.fixture
async def note_service(mongo_db, cache_service):
    """创建笔记服务实例"""
    return NoteService(mongo_db, cache_service)


@pytest_asyncio.fixture
async def test_db_manager():
    """创建测试数据库管理器"""
    manager = DatabaseManager()
    
    # 使用测试数据库URL
    original_urls = (
        settings.DATABASE_URL,
        settings.MONGODB_URL,
        settings.REDIS_URL
    )
    
    settings.DATABASE_URL = TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    settings.MONGODB_URL = TEST_MONGODB_URL
    settings.REDIS_URL = TEST_REDIS_URL
    
    await manager.init_all()
    yield manager
    
    await manager.close_all()
    
    # 恢复原始URL
    settings.DATABASE_URL, settings.MONGODB_URL, settings.REDIS_URL = original_urls


# 测试数据夹具
@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "name": "测试用户",
        "email": "test@example.com",
        "preferences": {"theme": "dark", "language": "zh-CN"}
    }


@pytest.fixture
def sample_note_data():
    """示例笔记数据"""
    return {
        "title": "测试笔记",
        "content": "这是一个测试笔记的内容",
        "tags": ["测试", "笔记"]
    }


@pytest.fixture
def multiple_notes_data():
    """多个笔记数据"""
    return [
        {
            "title": f"测试笔记 {i}",
            "content": f"这是第 {i} 个测试笔记的内容",
            "tags": ["测试", f"标签{i}"]
        }
        for i in range(1, 6)
    ]
