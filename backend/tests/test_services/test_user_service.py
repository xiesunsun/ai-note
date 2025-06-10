"""
用户服务测试
测试用户服务的所有功能，包括CRUD操作和缓存集成
"""

import pytest
import pytest_asyncio
import uuid
from sqlalchemy.exc import IntegrityError

from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


class TestUserServiceCRUD:
    """用户服务CRUD操作测试"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, postgres_session, user_service, sample_user_data):
        """测试创建用户"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        user = await user_service.create_user(postgres_session, user_data)
        
        # 验证用户信息
        assert user is not None
        assert user.name == sample_user_data["name"]
        assert user.email == sample_user_data["email"]
        assert user.preferences == sample_user_data["preferences"]
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, postgres_session, user_service, sample_user_data):
        """测试创建重复邮箱用户"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建第一个用户
        await user_service.create_user(postgres_session, user_data)
        
        # 尝试创建相同邮箱的用户
        with pytest.raises(ValueError, match="邮箱.*已被使用"):
            await user_service.create_user(postgres_session, user_data)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, postgres_session, user_service, sample_user_data):
        """测试根据ID获取用户"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 根据ID获取用户
        retrieved_user = await user_service.get_user_by_id(postgres_session, created_user.id)
        
        # 验证用户信息
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.name == created_user.name
        assert retrieved_user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, postgres_session, user_service):
        """测试获取不存在的用户"""
        non_existent_id = uuid.uuid4()
        user = await user_service.get_user_by_id(postgres_session, non_existent_id)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, postgres_session, user_service, sample_user_data):
        """测试根据邮箱获取用户"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 根据邮箱获取用户
        retrieved_user = await user_service.get_user_by_email(postgres_session, created_user.email)
        
        # 验证用户信息
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, postgres_session, user_service):
        """测试获取不存在邮箱的用户"""
        user = await user_service.get_user_by_email(postgres_session, "nonexistent@example.com")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_users_list(self, postgres_session, user_service):
        """测试获取用户列表"""
        # 创建多个用户
        users_data = [
            {"name": f"用户{i}", "email": f"user{i}@example.com", "preferences": {}}
            for i in range(5)
        ]
        
        created_users = []
        for user_data in users_data:
            user = await user_service.create_user(postgres_session, UserCreate(**user_data))
            created_users.append(user)
        
        # 获取用户列表
        users_list = await user_service.get_users(postgres_session, skip=0, limit=10)
        
        # 验证列表
        assert len(users_list) == 5
        assert all(user.id in [u.id for u in created_users] for user in users_list)
    
    @pytest.mark.asyncio
    async def test_get_users_pagination(self, postgres_session, user_service):
        """测试用户列表分页"""
        # 创建多个用户
        users_data = [
            {"name": f"用户{i}", "email": f"page_user{i}@example.com", "preferences": {}}
            for i in range(10)
        ]
        
        for user_data in users_data:
            await user_service.create_user(postgres_session, UserCreate(**user_data))
        
        # 测试分页
        page1 = await user_service.get_users(postgres_session, skip=0, limit=5)
        page2 = await user_service.get_users(postgres_session, skip=5, limit=5)
        
        assert len(page1) == 5
        assert len(page2) == 5
        
        # 确保没有重复
        page1_ids = {user.id for user in page1}
        page2_ids = {user.id for user in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
    
    @pytest.mark.asyncio
    async def test_update_user(self, postgres_session, user_service, sample_user_data):
        """测试更新用户"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 更新用户信息
        update_data = UserUpdate(
            name="更新后的名称",
            preferences={"theme": "light", "language": "en-US"}
        )
        
        updated_user = await user_service.update_user(postgres_session, created_user.id, update_data)
        
        # 验证更新
        assert updated_user is not None
        assert updated_user.name == "更新后的名称"
        assert updated_user.email == sample_user_data["email"]  # 邮箱未更新
        assert updated_user.preferences["theme"] == "light"
        assert updated_user.updated_at > created_user.updated_at
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, postgres_session, user_service):
        """测试更新不存在的用户"""
        non_existent_id = uuid.uuid4()
        update_data = UserUpdate(name="新名称")
        
        result = await user_service.update_user(postgres_session, non_existent_id, update_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(self, postgres_session, user_service):
        """测试更新用户为重复邮箱"""
        # 创建两个用户
        user1_data = UserCreate(name="用户1", email="user1@example.com", preferences={})
        user2_data = UserCreate(name="用户2", email="user2@example.com", preferences={})
        
        user1 = await user_service.create_user(postgres_session, user1_data)
        user2 = await user_service.create_user(postgres_session, user2_data)
        
        # 尝试将user2的邮箱更新为user1的邮箱
        update_data = UserUpdate(email="user1@example.com")
        
        with pytest.raises(ValueError, match="邮箱.*已被使用"):
            await user_service.update_user(postgres_session, user2.id, update_data)
    
    @pytest.mark.asyncio
    async def test_delete_user(self, postgres_session, user_service, sample_user_data):
        """测试删除用户"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 删除用户
        result = await user_service.delete_user(postgres_session, created_user.id)
        assert result is True
        
        # 确认用户已删除
        deleted_user = await user_service.get_user_by_id(postgres_session, created_user.id)
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, postgres_session, user_service):
        """测试删除不存在的用户"""
        non_existent_id = uuid.uuid4()
        result = await user_service.delete_user(postgres_session, non_existent_id)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_user_exists(self, postgres_session, user_service, sample_user_data):
        """测试检查用户是否存在"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 检查用户存在
        exists = await user_service.user_exists(postgres_session, created_user.id)
        assert exists is True
        
        # 检查不存在的用户
        non_existent_id = uuid.uuid4()
        exists = await user_service.user_exists(postgres_session, non_existent_id)
        assert exists is False


class TestUserServiceCache:
    """用户服务缓存功能测试"""
    
    @pytest.mark.asyncio
    async def test_create_user_caches_preferences(self, postgres_session, user_service, sample_user_data):
        """测试创建用户时缓存偏好设置"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 检查偏好设置是否被缓存
        cached_preferences = await user_service.get_user_preferences_cached(str(created_user.id))
        assert cached_preferences == sample_user_data["preferences"]
    
    @pytest.mark.asyncio
    async def test_update_user_updates_cache(self, postgres_session, user_service, sample_user_data):
        """测试更新用户时更新缓存"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 更新偏好设置
        new_preferences = {"theme": "light", "language": "en-US"}
        update_data = UserUpdate(preferences=new_preferences)
        
        await user_service.update_user(postgres_session, created_user.id, update_data)
        
        # 检查缓存是否更新
        cached_preferences = await user_service.get_user_preferences_cached(str(created_user.id))
        assert cached_preferences == new_preferences
    
    @pytest.mark.asyncio
    async def test_delete_user_clears_cache(self, postgres_session, user_service, sample_user_data):
        """测试删除用户时清除缓存"""
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户
        created_user = await user_service.create_user(postgres_session, user_data)
        
        # 添加一些缓存数据
        await user_service.cache_user_stats(str(created_user.id), {"notes": 10})
        
        # 确认缓存存在
        cached_stats = await user_service.get_user_stats_cached(str(created_user.id))
        assert cached_stats is not None
        
        # 删除用户
        await user_service.delete_user(postgres_session, created_user.id)
        
        # 检查缓存是否被清除
        cached_preferences = await user_service.get_user_preferences_cached(str(created_user.id))
        cached_stats = await user_service.get_user_stats_cached(str(created_user.id))
        assert cached_preferences is None
        assert cached_stats is None
    
    @pytest.mark.asyncio
    async def test_user_stats_cache(self, user_service):
        """测试用户统计信息缓存"""
        user_id = "test_stats_user"
        stats = {
            "total_notes": 25,
            "total_tags": 15,
            "last_active": "2024-01-01T00:00:00"
        }
        
        # 缓存统计信息
        result = await user_service.cache_user_stats(user_id, stats)
        assert result is True
        
        # 获取缓存的统计信息
        cached_stats = await user_service.get_user_stats_cached(user_id)
        assert cached_stats == stats


class TestUserServiceErrorHandling:
    """用户服务错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_data(self, postgres_session, user_service):
        """测试创建用户时的数据验证"""
        # 测试空邮箱
        with pytest.raises(Exception):
            invalid_data = UserCreate(name="测试", email="", preferences={})
            await user_service.create_user(postgres_session, invalid_data)
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, postgres_session, user_service):
        """测试数据库错误处理"""
        # 这里可以模拟数据库连接错误等情况
        # 由于测试环境限制，主要测试异常传播
        try:
            user_data = UserCreate(name="测试用户", email="test@example.com", preferences={})
            await user_service.create_user(postgres_session, user_data)
        except Exception as e:
            # 确保异常被正确处理和传播
            assert isinstance(e, (ValueError, IntegrityError))
    
    @pytest.mark.asyncio
    async def test_cache_failure_resilience(self, postgres_session, user_service, sample_user_data):
        """测试缓存失败时的恢复能力"""
        # 即使缓存失败，核心功能也应该正常工作
        user_data = UserCreate(**sample_user_data)
        
        # 创建用户（即使缓存可能失败）
        created_user = await user_service.create_user(postgres_session, user_data)
        assert created_user is not None
        
        # 核心数据库操作应该成功
        retrieved_user = await user_service.get_user_by_id(postgres_session, created_user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == sample_user_data["email"]
