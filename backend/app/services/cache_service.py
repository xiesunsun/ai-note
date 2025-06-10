"""
Redis缓存服务
提供会话管理、数据缓存和缓存策略实现
"""

import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.database import get_redis_client


class CacheService:
    """Redis缓存服务类"""

    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        
        # 缓存键前缀
        self.KEY_PREFIX = "ai_note"
        self.SESSION_PREFIX = f"{self.KEY_PREFIX}:session"
        self.USER_PREFIX = f"{self.KEY_PREFIX}:user"
        self.NOTE_PREFIX = f"{self.KEY_PREFIX}:note"
        self.SEARCH_PREFIX = f"{self.KEY_PREFIX}:search"
        
        # 默认过期时间（秒）
        self.DEFAULT_TTL = 3600  # 1小时
        self.SESSION_TTL = 86400 * 7  # 7天
        self.SEARCH_TTL = 1800  # 30分钟
        self.NOTE_LIST_TTL = 3600  # 1小时
    
    def _generate_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    def _serialize_data(self, data: Any) -> str:
        """序列化数据"""
        if isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False, default=str)
        return str(data)
    
    def _deserialize_data(self, data: str) -> Any:
        """反序列化数据"""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if not self.redis_client:
            return None
        try:
            data = await self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize_data(data)
        except Exception as e:
            print(f"缓存获取失败 {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存数据"""
        if not self.redis_client:
            return False
        try:
            serialized_value = self._serialize_data(value)
            ttl = ttl or self.DEFAULT_TTL
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"缓存设置失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存数据"""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"缓存删除失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            print(f"缓存检查失败 {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.expire(key, ttl)
            return result
        except Exception as e:
            print(f"设置过期时间失败 {key}: {e}")
            return False
    
    # === 会话管理功能 ===
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """创建用户会话"""
        session_id = hashlib.md5(f"{user_id}:{datetime.now().isoformat()}".encode()).hexdigest()
        session_key = self._generate_key(self.SESSION_PREFIX, session_id)
        
        session_info = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            **session_data
        }
        
        success = await self.set(session_key, session_info, self.SESSION_TTL)
        return session_id if success else None
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        session_key = self._generate_key(self.SESSION_PREFIX, session_id)
        session_data = await self.get(session_key)
        
        if session_data:
            # 更新最后访问时间
            session_data["last_accessed"] = datetime.now().isoformat()
            await self.set(session_key, session_data, self.SESSION_TTL)
        
        return session_data
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session_key = self._generate_key(self.SESSION_PREFIX, session_id)
        return await self.delete(session_key)
    
    async def refresh_session(self, session_id: str) -> bool:
        """刷新会话过期时间"""
        session_key = self._generate_key(self.SESSION_PREFIX, session_id)
        return await self.expire(session_key, self.SESSION_TTL)
    
    # === 用户数据缓存 ===
    
    async def cache_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """缓存用户偏好设置"""
        key = self._generate_key(self.USER_PREFIX, user_id, "preferences")
        return await self.set(key, preferences, self.DEFAULT_TTL * 24)  # 24小时
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置"""
        key = self._generate_key(self.USER_PREFIX, user_id, "preferences")
        return await self.get(key)
    
    async def cache_user_stats(self, user_id: str, stats: Dict[str, Any]) -> bool:
        """缓存用户统计信息"""
        key = self._generate_key(self.USER_PREFIX, user_id, "stats")
        return await self.set(key, stats, self.DEFAULT_TTL)
    
    async def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户统计信息"""
        key = self._generate_key(self.USER_PREFIX, user_id, "stats")
        return await self.get(key)
    
    # === 笔记数据缓存 ===
    
    async def cache_user_notes(self, user_id: str, notes: List[Dict[str, Any]], 
                              page: int = 1, limit: int = 20) -> bool:
        """缓存用户笔记列表"""
        key = self._generate_key(self.NOTE_PREFIX, "list", user_id, f"p{page}_l{limit}")
        cache_data = {
            "notes": notes,
            "cached_at": datetime.now().isoformat(),
            "page": page,
            "limit": limit
        }
        return await self.set(key, cache_data, self.NOTE_LIST_TTL)
    
    async def get_cached_user_notes(self, user_id: str, page: int = 1, 
                                   limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的用户笔记列表"""
        key = self._generate_key(self.NOTE_PREFIX, "list", user_id, f"p{page}_l{limit}")
        cache_data = await self.get(key)
        return cache_data.get("notes") if cache_data else None
    
    async def cache_hot_notes(self, notes: List[Dict[str, Any]]) -> bool:
        """缓存热门笔记"""
        key = self._generate_key(self.NOTE_PREFIX, "hot")
        return await self.set(key, notes, self.DEFAULT_TTL * 2)  # 2小时
    
    async def get_hot_notes(self) -> Optional[List[Dict[str, Any]]]:
        """获取热门笔记"""
        key = self._generate_key(self.NOTE_PREFIX, "hot")
        return await self.get(key)
    
    async def invalidate_user_notes_cache(self, user_id: str) -> bool:
        """清除用户笔记缓存"""
        pattern = self._generate_key(self.NOTE_PREFIX, "list", user_id, "*")
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"清除用户笔记缓存失败 {user_id}: {e}")
            return False
    
    # === 搜索结果缓存 ===
    
    def _generate_search_key(self, query: str, user_id: str = None, 
                           filters: Dict[str, Any] = None) -> str:
        """生成搜索缓存键"""
        search_params = {
            "query": query,
            "user_id": user_id,
            "filters": filters or {}
        }
        search_hash = hashlib.md5(
            json.dumps(search_params, sort_keys=True).encode()
        ).hexdigest()
        return self._generate_key(self.SEARCH_PREFIX, search_hash)
    
    async def cache_search_results(self, query: str, results: List[Dict[str, Any]], 
                                  user_id: str = None, filters: Dict[str, Any] = None) -> bool:
        """缓存搜索结果"""
        key = self._generate_search_key(query, user_id, filters)
        cache_data = {
            "results": results,
            "query": query,
            "user_id": user_id,
            "filters": filters,
            "cached_at": datetime.now().isoformat()
        }
        return await self.set(key, cache_data, self.SEARCH_TTL)
    
    async def get_cached_search_results(self, query: str, user_id: str = None, 
                                       filters: Dict[str, Any] = None) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的搜索结果"""
        key = self._generate_search_key(query, user_id, filters)
        cache_data = await self.get(key)
        return cache_data.get("results") if cache_data else None
    
    # === 缓存管理功能 ===
    
    async def clear_user_cache(self, user_id: str) -> bool:
        """清除用户相关的所有缓存"""
        patterns = [
            self._generate_key(self.USER_PREFIX, user_id, "*"),
            self._generate_key(self.NOTE_PREFIX, "list", user_id, "*"),
        ]
        
        try:
            for pattern in patterns:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"清除用户缓存失败 {user_id}: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            print(f"获取缓存统计失败: {e}")
            return {}


# 全局缓存服务实例（延迟初始化）
_cache_service = None


def get_cache_service() -> CacheService:
    """获取缓存服务实例（FastAPI依赖注入）"""
    global _cache_service
    if _cache_service is None:
        try:
            from app.database import get_redis_client
            redis_client = get_redis_client()
            _cache_service = CacheService(redis_client)
        except Exception:
            # 如果Redis未初始化，返回无Redis客户端的实例
            _cache_service = CacheService(None)
    return _cache_service


def create_cache_service(redis_client=None) -> CacheService:
    """创建缓存服务实例"""
    return CacheService(redis_client)
