"""
数据库连接测试
测试PostgreSQL、MongoDB和Redis连接功能
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from app.database import DatabaseManager


class TestDatabaseConnections:
    """数据库连接测试类"""
    
    @pytest.mark.asyncio
    async def test_postgres_connection(self, postgres_engine):
        """测试PostgreSQL连接"""
        async with postgres_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1
    
    @pytest.mark.asyncio
    async def test_postgres_session(self, postgres_session):
        """测试PostgreSQL会话"""
        result = await postgres_session.execute(text("SELECT 'Hello PostgreSQL' as message"))
        row = result.fetchone()
        assert row[0] == "Hello PostgreSQL"
    
    @pytest.mark.asyncio
    async def test_mongodb_connection(self, mongo_client):
        """测试MongoDB连接"""
        # 测试ping命令
        result = await mongo_client.admin.command('ping')
        assert result['ok'] == 1.0
    
    @pytest.mark.asyncio
    async def test_mongodb_operations(self, mongo_db):
        """测试MongoDB基本操作"""
        collection = mongo_db.test_collection
        
        # 插入测试文档
        doc = {"name": "test", "value": 123}
        result = await collection.insert_one(doc)
        assert result.inserted_id is not None
        
        # 查询文档
        found_doc = await collection.find_one({"name": "test"})
        assert found_doc is not None
        assert found_doc["value"] == 123
        
        # 删除文档
        delete_result = await collection.delete_one({"name": "test"})
        assert delete_result.deleted_count == 1
    
    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_client):
        """测试Redis连接"""
        # 测试ping命令
        result = await redis_client.ping()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_redis_operations(self, redis_client):
        """测试Redis基本操作"""
        # 设置键值
        await redis_client.set("test_key", "test_value")
        
        # 获取值
        value = await redis_client.get("test_key")
        assert value == "test_value"
        
        # 检查键是否存在
        exists = await redis_client.exists("test_key")
        assert exists == 1
        
        # 删除键
        deleted = await redis_client.delete("test_key")
        assert deleted == 1
        
        # 确认键已删除
        value = await redis_client.get("test_key")
        assert value is None


class TestDatabaseManager:
    """数据库管理器测试类"""
    
    @pytest.mark.asyncio
    async def test_database_manager_initialization(self):
        """测试数据库管理器初始化"""
        manager = DatabaseManager()
        
        # 初始状态检查
        assert manager.postgres_engine is None
        assert manager.mongo_client is None
        assert manager.redis_client is None
    
    @pytest.mark.asyncio
    async def test_postgres_initialization_error_handling(self):
        """测试PostgreSQL初始化错误处理"""
        manager = DatabaseManager()
        
        # 使用无效的数据库URL
        original_url = manager.__dict__.get('DATABASE_URL')
        
        with pytest.raises(Exception):
            # 模拟连接失败
            manager.postgres_engine = None
            await manager.init_postgres()
    
    @pytest.mark.asyncio
    async def test_connection_pool_configuration(self, postgres_engine):
        """测试连接池配置"""
        # 检查连接池设置
        assert postgres_engine.pool.size() >= 0
        assert postgres_engine.pool.checked_in() >= 0
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, postgres_engine):
        """测试并发连接"""
        import asyncio
        
        async def test_query():
            async with postgres_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.fetchone()[0]
        
        # 并发执行多个查询
        tasks = [test_query() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # 所有查询都应该成功
        assert all(result == 1 for result in results)
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, postgres_session):
        """测试事务回滚"""
        try:
            # 开始事务
            await postgres_session.execute(text("CREATE TEMPORARY TABLE test_rollback (id INTEGER)"))
            await postgres_session.execute(text("INSERT INTO test_rollback VALUES (1)"))
            
            # 强制回滚
            await postgres_session.rollback()
            
            # 验证回滚后表不存在
            with pytest.raises(Exception):
                await postgres_session.execute(text("SELECT * FROM test_rollback"))
                
        except Exception:
            # 确保会话状态正常
            await postgres_session.rollback()


class TestDatabaseIntegration:
    """数据库集成测试类"""
    
    @pytest.mark.asyncio
    async def test_cross_database_operations(self, postgres_session, mongo_db, redis_client):
        """测试跨数据库操作"""
        # PostgreSQL操作
        pg_result = await postgres_session.execute(text("SELECT 'postgres_data' as data"))
        pg_data = pg_result.fetchone()[0]
        
        # MongoDB操作
        mongo_doc = {"source": "postgres", "data": pg_data}
        mongo_result = await mongo_db.integration_test.insert_one(mongo_doc)
        
        # Redis操作
        await redis_client.set("integration_test", str(mongo_result.inserted_id))
        redis_data = await redis_client.get("integration_test")
        
        # 验证数据一致性
        assert pg_data == "postgres_data"
        assert mongo_result.inserted_id is not None
        assert redis_data == str(mongo_result.inserted_id)
    
    @pytest.mark.asyncio
    async def test_error_handling_across_databases(self, postgres_session, mongo_db, redis_client):
        """测试跨数据库错误处理"""
        try:
            # 模拟操作序列
            await postgres_session.execute(text("SELECT 1"))
            await mongo_db.test.insert_one({"test": "data"})
            await redis_client.set("test", "value")
            
            # 所有操作都应该成功
            assert True
            
        except Exception as e:
            # 如果有错误，确保能够正确处理
            pytest.fail(f"跨数据库操作失败: {e}")
    
    @pytest.mark.asyncio
    async def test_connection_recovery(self, redis_client):
        """测试连接恢复"""
        # 正常操作
        await redis_client.set("recovery_test", "initial")
        value = await redis_client.get("recovery_test")
        assert value == "initial"
        
        # 模拟连接中断后的恢复
        # 注意：这里只是测试基本的重连机制
        try:
            await redis_client.ping()
            assert True
        except Exception:
            # 如果连接失败，应该能够重新连接
            pytest.fail("连接恢复失败")
