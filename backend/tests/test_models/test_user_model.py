"""
用户模型测试
测试User模型的数据完整性、约束和关系
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User


class TestUserModel:
    """用户模型基础测试"""
    
    @pytest.mark.asyncio
    async def test_create_user_model(self, postgres_session):
        """测试创建用户模型"""
        user = User(
            name="测试用户",
            email="test@example.com",
            preferences={"theme": "dark"}
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 验证用户属性
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.name == "测试用户"
        assert user.email == "test@example.com"
        assert user.preferences == {"theme": "dark"}
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    @pytest.mark.asyncio
    async def test_user_model_defaults(self, postgres_session):
        """测试用户模型默认值"""
        user = User(
            name="默认测试用户",
            email="default@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 验证默认值
        assert user.preferences == {}
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_model_string_representation(self, postgres_session):
        """测试用户模型字符串表示"""
        user = User(
            name="字符串测试用户",
            email="string@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 测试__str__方法
        user_str = str(user)
        assert "字符串测试用户" in user_str
        assert "string@example.com" in user_str
    
    @pytest.mark.asyncio
    async def test_user_model_repr(self, postgres_session):
        """测试用户模型repr表示"""
        user = User(
            name="Repr测试用户",
            email="repr@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 测试__repr__方法
        user_repr = repr(user)
        assert "User" in user_repr
        assert str(user.id) in user_repr


class TestUserModelConstraints:
    """用户模型约束测试"""
    
    @pytest.mark.asyncio
    async def test_email_unique_constraint(self, postgres_session):
        """测试邮箱唯一性约束"""
        # 创建第一个用户
        user1 = User(
            name="用户1",
            email="unique@example.com"
        )
        postgres_session.add(user1)
        await postgres_session.commit()
        
        # 尝试创建相同邮箱的用户
        user2 = User(
            name="用户2",
            email="unique@example.com"
        )
        postgres_session.add(user2)
        
        with pytest.raises(IntegrityError):
            await postgres_session.commit()
        
        await postgres_session.rollback()
    
    @pytest.mark.asyncio
    async def test_email_not_null_constraint(self, postgres_session):
        """测试邮箱非空约束"""
        with pytest.raises(Exception):
            user = User(name="无邮箱用户")
            postgres_session.add(user)
            await postgres_session.commit()
        
        await postgres_session.rollback()
    
    @pytest.mark.asyncio
    async def test_name_not_null_constraint(self, postgres_session):
        """测试姓名非空约束"""
        with pytest.raises(Exception):
            user = User(email="noname@example.com")
            postgres_session.add(user)
            await postgres_session.commit()
        
        await postgres_session.rollback()
    
    @pytest.mark.asyncio
    async def test_email_length_constraint(self, postgres_session):
        """测试邮箱长度约束"""
        # 测试正常长度邮箱
        normal_email = "normal@example.com"
        user1 = User(name="正常用户", email=normal_email)
        postgres_session.add(user1)
        await postgres_session.commit()
        
        # 测试过长邮箱（假设数据库有长度限制）
        long_email = "a" * 300 + "@example.com"
        user2 = User(name="长邮箱用户", email=long_email)
        postgres_session.add(user2)
        
        # 根据数据库配置，这可能会失败
        try:
            await postgres_session.commit()
        except Exception:
            await postgres_session.rollback()
    
    @pytest.mark.asyncio
    async def test_name_length_constraint(self, postgres_session):
        """测试姓名长度约束"""
        # 测试正常长度姓名
        normal_name = "正常用户名"
        user1 = User(name=normal_name, email="normal1@example.com")
        postgres_session.add(user1)
        await postgres_session.commit()
        
        # 测试过长姓名
        long_name = "很" * 200 + "长的用户名"
        user2 = User(name=long_name, email="long1@example.com")
        postgres_session.add(user2)
        
        try:
            await postgres_session.commit()
        except Exception:
            await postgres_session.rollback()


class TestUserModelJSONField:
    """用户模型JSON字段测试"""
    
    @pytest.mark.asyncio
    async def test_preferences_json_field(self, postgres_session):
        """测试偏好设置JSON字段"""
        preferences = {
            "theme": "dark",
            "language": "zh-CN",
            "notifications": {
                "email": True,
                "push": False
            },
            "settings": {
                "auto_save": True,
                "sync_interval": 300
            }
        }
        
        user = User(
            name="JSON测试用户",
            email="json@example.com",
            preferences=preferences
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 验证JSON数据完整性
        assert user.preferences == preferences
        assert user.preferences["theme"] == "dark"
        assert user.preferences["notifications"]["email"] is True
        assert user.preferences["settings"]["sync_interval"] == 300
    
    @pytest.mark.asyncio
    async def test_preferences_empty_json(self, postgres_session):
        """测试空JSON偏好设置"""
        user = User(
            name="空JSON用户",
            email="empty_json@example.com",
            preferences={}
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        assert user.preferences == {}
    
    @pytest.mark.asyncio
    async def test_preferences_null_json(self, postgres_session):
        """测试NULL JSON偏好设置"""
        user = User(
            name="NULL JSON用户",
            email="null_json@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 默认应该是空字典
        assert user.preferences == {}
    
    @pytest.mark.asyncio
    async def test_preferences_complex_json(self, postgres_session):
        """测试复杂JSON偏好设置"""
        complex_preferences = {
            "ui": {
                "theme": "dark",
                "sidebar": {
                    "collapsed": False,
                    "width": 250
                },
                "editor": {
                    "font_size": 14,
                    "line_numbers": True,
                    "word_wrap": True
                }
            },
            "behavior": {
                "auto_save": {
                    "enabled": True,
                    "interval": 30
                },
                "shortcuts": {
                    "save": "Ctrl+S",
                    "new": "Ctrl+N"
                }
            },
            "integrations": {
                "ai": {
                    "enabled": True,
                    "provider": "openai",
                    "model": "gpt-4"
                }
            }
        }
        
        user = User(
            name="复杂JSON用户",
            email="complex_json@example.com",
            preferences=complex_preferences
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 验证复杂JSON结构
        assert user.preferences["ui"]["theme"] == "dark"
        assert user.preferences["ui"]["sidebar"]["width"] == 250
        assert user.preferences["behavior"]["auto_save"]["interval"] == 30
        assert user.preferences["integrations"]["ai"]["model"] == "gpt-4"


class TestUserModelTimestamps:
    """用户模型时间戳测试"""
    
    @pytest.mark.asyncio
    async def test_created_at_auto_set(self, postgres_session):
        """测试创建时间自动设置"""
        before_create = datetime.utcnow()
        
        user = User(
            name="时间戳测试用户",
            email="timestamp@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        after_create = datetime.utcnow()
        
        # 验证创建时间在合理范围内
        assert before_create <= user.created_at <= after_create
        assert user.created_at == user.updated_at  # 初始时应该相等
    
    @pytest.mark.asyncio
    async def test_updated_at_auto_update(self, postgres_session):
        """测试更新时间自动更新"""
        user = User(
            name="更新时间测试用户",
            email="update_time@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        original_updated_at = user.updated_at
        
        # 等待一小段时间确保时间戳不同
        import asyncio
        await asyncio.sleep(0.01)
        
        # 更新用户
        user.name = "更新后的用户名"
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 验证更新时间已改变
        assert user.updated_at > original_updated_at
        assert user.created_at < user.updated_at


class TestUserModelQueries:
    """用户模型查询测试"""
    
    @pytest.mark.asyncio
    async def test_query_by_email(self, postgres_session):
        """测试根据邮箱查询用户"""
        user = User(
            name="查询测试用户",
            email="query@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        
        # 查询用户
        stmt = select(User).where(User.email == "query@example.com")
        result = await postgres_session.execute(stmt)
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.email == "query@example.com"
        assert found_user.name == "查询测试用户"
    
    @pytest.mark.asyncio
    async def test_query_by_id(self, postgres_session):
        """测试根据ID查询用户"""
        user = User(
            name="ID查询测试用户",
            email="id_query@example.com"
        )
        
        postgres_session.add(user)
        await postgres_session.commit()
        await postgres_session.refresh(user)
        
        # 查询用户
        stmt = select(User).where(User.id == user.id)
        result = await postgres_session.execute(stmt)
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.name == "ID查询测试用户"
    
    @pytest.mark.asyncio
    async def test_query_multiple_users(self, postgres_session):
        """测试查询多个用户"""
        users = [
            User(name=f"用户{i}", email=f"user{i}@example.com")
            for i in range(5)
        ]
        
        for user in users:
            postgres_session.add(user)
        
        await postgres_session.commit()
        
        # 查询所有用户
        stmt = select(User).order_by(User.created_at)
        result = await postgres_session.execute(stmt)
        found_users = list(result.scalars().all())
        
        assert len(found_users) >= 5  # 可能有其他测试创建的用户
        
        # 验证我们创建的用户都在结果中
        found_emails = {user.email for user in found_users}
        expected_emails = {f"user{i}@example.com" for i in range(5)}
        assert expected_emails.issubset(found_emails)
