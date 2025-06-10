"""
知识关联模型 - PostgreSQL
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Float, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Knowledge(Base):
    """知识关联模型"""
    __tablename__ = "knowledge_relations"
    
    # 主键：UUID类型
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # 源笔记ID：MongoDB ObjectId字符串
    source_note_id: Mapped[str] = mapped_column(
        String(24),  # MongoDB ObjectId长度
        nullable=False,
        index=True
    )
    
    # 相关笔记ID列表：MongoDB ObjectId字符串数组
    related_note_ids: Mapped[List[str]] = mapped_column(
        ARRAY(String(24)),
        nullable=False,
        default=[]
    )
    
    # 关联强度：0.0-1.0之间的浮点数
    relation_strength: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )
    
    # 关联上下文：描述关联的原因或背景
    relation_context: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    
    # 创建时间：自动设置
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # 更新时间：自动更新
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return (f"Knowledge(id={self.id!r}, source_note_id={self.source_note_id!r}, "
                f"relation_strength={self.relation_strength!r})")
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "source_note_id": self.source_note_id,
            "related_note_ids": self.related_note_ids,
            "relation_strength": self.relation_strength,
            "relation_context": self.relation_context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
