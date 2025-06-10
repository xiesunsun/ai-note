"""
笔记相关的Pydantic模式
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
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


class NoteCreate(NoteBase):
    """创建笔记模式"""
    user_id: uuid.UUID = Field(..., description="用户ID")


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
