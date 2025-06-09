"""
知识关联相关的Pydantic模式
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class KnowledgeBase(BaseModel):
    """知识关联基础模式"""
    source_note_id: str = Field(..., description="源笔记ID")
    related_note_ids: List[str] = Field(..., description="相关笔记ID列表")
    relation_strength: float = Field(..., ge=0.0, le=1.0, description="关联强度（0.0-1.0）")
    relation_context: Optional[str] = Field(None, max_length=1000, description="关联上下文")


class KnowledgeCreate(KnowledgeBase):
    """创建知识关联模式"""
    pass


class KnowledgeUpdate(BaseModel):
    """更新知识关联模式"""
    related_note_ids: Optional[List[str]] = Field(None, description="相关笔记ID列表")
    relation_strength: Optional[float] = Field(None, ge=0.0, le=1.0, description="关联强度")
    relation_context: Optional[str] = Field(None, max_length=1000, description="关联上下文")


class KnowledgeResponse(KnowledgeBase):
    """知识关联响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="关联ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
