"""
笔记相关的Pydantic模式
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """自定义ObjectId类型，用于Pydantic验证"""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string", format="objectid")


class NoteBase(BaseModel):
    """笔记基础模式"""
    title: str = Field(..., min_length=1, max_length=200, description="笔记标题")
    content: str = Field(..., description="笔记内容（Markdown格式）")
    tags: List[str] = Field(default=[], description="手动标签")

    @validator('content')
    def validate_markdown_content(cls, v):
        """验证Markdown内容格式"""
        if not v or not v.strip():
            raise ValueError('笔记内容不能为空')

        # 基本长度检查
        if len(v) > 100000:  # 100KB限制
            raise ValueError('笔记内容过长，请控制在100KB以内')

        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        """验证标签格式"""
        if not v:
            return []

        # 检查标签数量
        if len(v) > 20:
            raise ValueError('标签数量不能超过20个')

        # 检查每个标签
        validated_tags = []
        for tag in v:
            if not isinstance(tag, str):
                continue
            tag = tag.strip()
            if not tag:
                continue
            if len(tag) > 50:
                raise ValueError('单个标签长度不能超过50个字符')
            validated_tags.append(tag)

        return validated_tags


class NoteCreate(NoteBase):
    """创建笔记模式"""
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")


class NoteUpdate(BaseModel):
    """更新笔记模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="笔记标题")
    content: Optional[str] = Field(None, description="笔记内容（Markdown格式）")
    tags: Optional[List[str]] = Field(None, description="手动标签")
    enhanced_content: Optional[str] = Field(None, description="AI润色后的内容")
    ai_tags: Optional[List[str]] = Field(None, description="AI生成的标签")


class NoteInDB(NoteBase):
    """数据库中的笔记模式"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: uuid.UUID = Field(..., description="用户ID")
    enhanced_content: Optional[str] = Field(None, description="AI润色后的内容")
    ai_tags: List[str] = Field(default=[], description="AI生成的标签")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    last_viewed_at: Optional[datetime] = Field(None, description="最后查看时间")
    review_schedule: List[datetime] = Field(default=[], description="复习计划")


class NoteVersionHistory(BaseModel):
    """笔记版本历史模式"""
    version: int = Field(..., description="版本号")
    title: str = Field(..., description="历史版本标题")
    content: str = Field(..., description="历史版本内容")
    change_summary: Optional[str] = Field(None, description="变更摘要")
    created_at: datetime = Field(..., description="版本创建时间")


class MarkdownValidationResult(BaseModel):
    """Markdown验证结果"""
    is_valid: bool = Field(..., description="是否有效")
    html_content: Optional[str] = Field(None, description="转换后的HTML内容")
    errors: List[str] = Field(default=[], description="验证错误列表")
    warnings: List[str] = Field(default=[], description="验证警告列表")


class NoteResponse(BaseModel):
    """笔记响应模式"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: str = Field(..., description="笔记ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记内容")
    enhanced_content: Optional[str] = Field(None, description="AI润色后的内容")
    tags: List[str] = Field(default=[], description="手动标签")
    ai_tags: List[str] = Field(default=[], description="AI生成的标签")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_viewed_at: Optional[datetime] = Field(None, description="最后查看时间")
    review_schedule: List[datetime] = Field(default=[], description="复习计划")
    version_count: Optional[int] = Field(None, description="版本总数")


class NoteWithHistory(NoteResponse):
    """包含历史版本的笔记响应模式"""
    history: List[NoteVersionHistory] = Field(default=[], description="版本历史列表")
