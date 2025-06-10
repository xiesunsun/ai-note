"""
缓存服务测试
测试Redis缓存服务的所有功能
"""

import pytest
import pytest_asyncio
import json
from datetime import datetime, timedelta
from app.services.cache_service import CacheService


class TestCacheServiceBasic:
    """缓存服务基础功能测试"""
    
    @pytest.mark.asyncio
    async def test_cache_service_initialization(self, redis_client):
        """测试缓存服务初始化"""
        cache_service = CacheService(redis_client)
        assert cache_service.redis_client is not None
        assert cache_service.KEY_PREFIX == "ai_note"
    
    @pytest.mark.asyncio
    async def test_basic_cache_operations(self, cache_service):
        """测试基础缓存操作"""
        key = "test_key"
        value = "test_value"
        
        # 设置缓存
        result = await cache_service.set(key, value)
        assert result is True
        
        # 获取缓存
        cached_value = await cache_service.get(key)
        assert cached_value == value
        
        # 检查存在性
        exists = await cache_service.exists(key)
        assert exists is True
        
        # 删除缓存
        deleted = await cache_service.delete(key)
        assert deleted is True
        
        # 确认删除
        cached_value = await cache_service.get(key)
        assert cached_value is None
    
    @pytest.mark.asyncio
    async def test_cache_with_ttl(self, cache_service):
        """测试带过期时间的缓存"""
        key = "ttl_test_key"
        value = "ttl_test_value"
        ttl = 2  # 2秒
        
        # 设置带TTL的缓存
        result = await cache_service.set(key, value, ttl)
        assert result is True
        
        # 立即获取应该成功
        cached_value = await cache_service.get(key)
        assert cached_value == value
        
        # 等待过期（在实际测试中可能需要调整）
        import asyncio
        await asyncio.sleep(3)
        
        # 过期后应该获取不到
        cached_value = await cache_service.get(key)
        assert cached_value is None
    
    @pytest.mark.asyncio
    async def test_cache_data_types(self, cache_service):
        """测试不同数据类型的缓存"""
        # 字符串
        await cache_service.set("string_key", "string_value")
        assert await cache_service.get("string_key") == "string_value"
        
        # 字典
        dict_data = {"name": "test", "value": 123}
        await cache_service.set("dict_key", dict_data)
        cached_dict = await cache_service.get("dict_key")
        assert cached_dict == dict_data
        
        # 列表
        list_data = [1, 2, 3, "test"]
        await cache_service.set("list_key", list_data)
        cached_list = await cache_service.get("list_key")
        assert cached_list == list_data
        
        # 数字
        await cache_service.set("number_key", 42)
        assert await cache_service.get("number_key") == 42


class TestSessionManagement:
    """会话管理测试"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, cache_service):
        """测试创建会话"""
        user_id = "test_user_123"
        session_data = {"role": "user", "permissions": ["read", "write"]}
        
        session_id = await cache_service.create_session(user_id, session_data)
        assert session_id is not None
        assert len(session_id) == 32  # MD5 hash length
    
    @pytest.mark.asyncio
    async def test_get_session(self, cache_service):
        """测试获取会话"""
        user_id = "test_user_456"
        session_data = {"role": "admin", "permissions": ["read", "write", "delete"]}
        
        # 创建会话
        session_id = await cache_service.create_session(user_id, session_data)
        
        # 获取会话
        retrieved_session = await cache_service.get_session(session_id)
        assert retrieved_session is not None
        assert retrieved_session["user_id"] == user_id
        assert retrieved_session["role"] == "admin"
        assert "created_at" in retrieved_session
        assert "last_accessed" in retrieved_session
    
    @pytest.mark.asyncio
    async def test_delete_session(self, cache_service):
        """测试删除会话"""
        user_id = "test_user_789"
        session_data = {"role": "user"}
        
        # 创建会话
        session_id = await cache_service.create_session(user_id, session_data)
        
        # 确认会话存在
        session = await cache_service.get_session(session_id)
        assert session is not None
        
        # 删除会话
        deleted = await cache_service.delete_session(session_id)
        assert deleted is True
        
        # 确认会话已删除
        session = await cache_service.get_session(session_id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_refresh_session(self, cache_service):
        """测试刷新会话"""
        user_id = "test_user_refresh"
        session_data = {"role": "user"}
        
        # 创建会话
        session_id = await cache_service.create_session(user_id, session_data)
        
        # 刷新会话
        refreshed = await cache_service.refresh_session(session_id)
        assert refreshed is True


class TestUserDataCache:
    """用户数据缓存测试"""
    
    @pytest.mark.asyncio
    async def test_user_preferences_cache(self, cache_service):
        """测试用户偏好设置缓存"""
        user_id = "user_123"
        preferences = {
            "theme": "dark",
            "language": "zh-CN",
            "notifications": True
        }
        
        # 缓存用户偏好
        result = await cache_service.cache_user_preferences(user_id, preferences)
        assert result is True
        
        # 获取用户偏好
        cached_preferences = await cache_service.get_user_preferences(user_id)
        assert cached_preferences == preferences
    
    @pytest.mark.asyncio
    async def test_user_stats_cache(self, cache_service):
        """测试用户统计信息缓存"""
        user_id = "user_456"
        stats = {
            "total_notes": 25,
            "total_tags": 15,
            "last_login": datetime.now().isoformat()
        }
        
        # 缓存用户统计
        result = await cache_service.cache_user_stats(user_id, stats)
        assert result is True
        
        # 获取用户统计
        cached_stats = await cache_service.get_user_stats(user_id)
        assert cached_stats["total_notes"] == 25
        assert cached_stats["total_tags"] == 15


class TestNoteDataCache:
    """笔记数据缓存测试"""
    
    @pytest.mark.asyncio
    async def test_user_notes_cache(self, cache_service):
        """测试用户笔记列表缓存"""
        user_id = "user_notes_test"
        notes = [
            {"id": "1", "title": "笔记1", "content": "内容1"},
            {"id": "2", "title": "笔记2", "content": "内容2"}
        ]
        page = 1
        limit = 20
        
        # 缓存笔记列表
        result = await cache_service.cache_user_notes(user_id, notes, page, limit)
        assert result is True
        
        # 获取缓存的笔记列表
        cached_notes = await cache_service.get_cached_user_notes(user_id, page, limit)
        assert cached_notes == notes
    
    @pytest.mark.asyncio
    async def test_hot_notes_cache(self, cache_service):
        """测试热门笔记缓存"""
        hot_notes = [
            {"id": "hot1", "title": "热门笔记1", "views": 100},
            {"id": "hot2", "title": "热门笔记2", "views": 95}
        ]
        
        # 缓存热门笔记
        result = await cache_service.cache_hot_notes(hot_notes)
        assert result is True
        
        # 获取热门笔记
        cached_hot_notes = await cache_service.get_hot_notes()
        assert cached_hot_notes == hot_notes
    
    @pytest.mark.asyncio
    async def test_invalidate_user_notes_cache(self, cache_service):
        """测试清除用户笔记缓存"""
        user_id = "user_invalidate_test"
        notes = [{"id": "1", "title": "测试笔记"}]
        
        # 缓存多个页面的笔记
        await cache_service.cache_user_notes(user_id, notes, 1, 20)
        await cache_service.cache_user_notes(user_id, notes, 2, 20)
        
        # 确认缓存存在
        cached_notes_p1 = await cache_service.get_cached_user_notes(user_id, 1, 20)
        cached_notes_p2 = await cache_service.get_cached_user_notes(user_id, 2, 20)
        assert cached_notes_p1 is not None
        assert cached_notes_p2 is not None
        
        # 清除缓存
        result = await cache_service.invalidate_user_notes_cache(user_id)
        assert result is True
        
        # 确认缓存已清除
        cached_notes_p1 = await cache_service.get_cached_user_notes(user_id, 1, 20)
        cached_notes_p2 = await cache_service.get_cached_user_notes(user_id, 2, 20)
        assert cached_notes_p1 is None
        assert cached_notes_p2 is None


class TestSearchCache:
    """搜索结果缓存测试"""
    
    @pytest.mark.asyncio
    async def test_search_results_cache(self, cache_service):
        """测试搜索结果缓存"""
        query = "测试搜索"
        user_id = "search_user"
        results = [
            {"id": "1", "title": "搜索结果1", "relevance": 0.9},
            {"id": "2", "title": "搜索结果2", "relevance": 0.8}
        ]
        filters = {"tags": ["测试"]}
        
        # 缓存搜索结果
        result = await cache_service.cache_search_results(query, results, user_id, filters)
        assert result is True
        
        # 获取搜索结果
        cached_results = await cache_service.get_cached_search_results(query, user_id, filters)
        assert cached_results == results
    
    @pytest.mark.asyncio
    async def test_search_cache_key_generation(self, cache_service):
        """测试搜索缓存键生成"""
        query1 = "测试"
        query2 = "测试"
        user_id = "same_user"
        
        # 相同查询应该生成相同的缓存键
        key1 = cache_service._generate_search_key(query1, user_id)
        key2 = cache_service._generate_search_key(query2, user_id)
        assert key1 == key2
        
        # 不同用户应该生成不同的缓存键
        key3 = cache_service._generate_search_key(query1, "different_user")
        assert key1 != key3


class TestCacheManagement:
    """缓存管理测试"""
    
    @pytest.mark.asyncio
    async def test_clear_user_cache(self, cache_service):
        """测试清除用户缓存"""
        user_id = "clear_test_user"
        
        # 创建各种用户相关缓存
        await cache_service.cache_user_preferences(user_id, {"theme": "dark"})
        await cache_service.cache_user_stats(user_id, {"notes": 10})
        await cache_service.cache_user_notes(user_id, [{"id": "1"}], 1, 20)
        
        # 确认缓存存在
        assert await cache_service.get_user_preferences(user_id) is not None
        assert await cache_service.get_user_stats(user_id) is not None
        assert await cache_service.get_cached_user_notes(user_id, 1, 20) is not None
        
        # 清除用户缓存
        result = await cache_service.clear_user_cache(user_id)
        assert result is True
        
        # 确认缓存已清除
        assert await cache_service.get_user_preferences(user_id) is None
        assert await cache_service.get_user_stats(user_id) is None
        assert await cache_service.get_cached_user_notes(user_id, 1, 20) is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service):
        """测试缓存统计信息"""
        stats = await cache_service.get_cache_stats()
        assert isinstance(stats, dict)
        # 基本统计信息应该存在
        expected_keys = ["connected_clients", "used_memory", "keyspace_hits", "keyspace_misses"]
        for key in expected_keys:
            assert key in stats
