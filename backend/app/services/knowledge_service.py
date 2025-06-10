"""
知识关联服务
处理知识关联相关的业务逻辑
"""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError

from app.models.knowledge import Knowledge
from app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate


class KnowledgeService:
    """知识关联服务类"""
    
    @staticmethod
    async def create_knowledge_relation(
        session: AsyncSession, 
        knowledge_data: KnowledgeCreate
    ) -> Knowledge:
        """创建知识关联"""
        try:
            # 创建知识关联实例
            knowledge = Knowledge(
                source_note_id=knowledge_data.source_note_id,
                related_note_ids=knowledge_data.related_note_ids,
                relation_strength=knowledge_data.relation_strength,
                relation_context=knowledge_data.relation_context
            )
            
            # 添加到会话并提交
            session.add(knowledge)
            await session.commit()
            await session.refresh(knowledge)
            
            return knowledge
            
        except Exception as e:
            await session.rollback()
            raise ValueError(f"创建知识关联失败: {str(e)}")
    
    @staticmethod
    async def get_knowledge_by_id(
        session: AsyncSession, 
        knowledge_id: uuid.UUID
    ) -> Optional[Knowledge]:
        """根据ID获取知识关联"""
        try:
            stmt = select(Knowledge).where(Knowledge.id == knowledge_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"获取知识关联失败: {str(e)}")
    
    @staticmethod
    async def get_knowledge_by_source_note(
        session: AsyncSession, 
        source_note_id: str
    ) -> List[Knowledge]:
        """根据源笔记ID获取所有关联"""
        try:
            stmt = select(Knowledge).where(
                Knowledge.source_note_id == source_note_id
            ).order_by(Knowledge.relation_strength.desc())
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise ValueError(f"获取笔记关联失败: {str(e)}")
    
    @staticmethod
    async def get_related_notes(
        session: AsyncSession, 
        note_id: str, 
        min_strength: float = 0.0
    ) -> List[Knowledge]:
        """获取与指定笔记相关的所有关联"""
        try:
            # 查找以该笔记为源的关联
            stmt1 = select(Knowledge).where(
                and_(
                    Knowledge.source_note_id == note_id,
                    Knowledge.relation_strength >= min_strength
                )
            )
            
            # 查找包含该笔记的关联
            stmt2 = select(Knowledge).where(
                and_(
                    Knowledge.related_note_ids.any(note_id),
                    Knowledge.relation_strength >= min_strength
                )
            )
            
            result1 = await session.execute(stmt1)
            result2 = await session.execute(stmt2)
            
            relations = list(result1.scalars().all()) + list(result2.scalars().all())
            
            # 去重并按关联强度排序
            unique_relations = {rel.id: rel for rel in relations}
            return sorted(
                unique_relations.values(), 
                key=lambda x: x.relation_strength, 
                reverse=True
            )
            
        except Exception as e:
            raise ValueError(f"获取相关笔记失败: {str(e)}")
    
    @staticmethod
    async def update_knowledge_relation(
        session: AsyncSession, 
        knowledge_id: uuid.UUID, 
        knowledge_data: KnowledgeUpdate
    ) -> Optional[Knowledge]:
        """更新知识关联"""
        try:
            # 获取知识关联
            knowledge = await KnowledgeService.get_knowledge_by_id(session, knowledge_id)
            if not knowledge:
                return None
            
            # 更新字段
            update_data = knowledge_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(knowledge, field, value)
            
            # 提交更改
            await session.commit()
            await session.refresh(knowledge)
            
            return knowledge
            
        except Exception as e:
            await session.rollback()
            raise ValueError(f"更新知识关联失败: {str(e)}")
    
    @staticmethod
    async def delete_knowledge_relation(
        session: AsyncSession, 
        knowledge_id: uuid.UUID
    ) -> bool:
        """删除知识关联"""
        try:
            # 获取知识关联
            knowledge = await KnowledgeService.get_knowledge_by_id(session, knowledge_id)
            if not knowledge:
                return False
            
            # 删除关联
            await session.delete(knowledge)
            await session.commit()
            
            return True
            
        except Exception as e:
            await session.rollback()
            raise ValueError(f"删除知识关联失败: {str(e)}")
    
    @staticmethod
    async def delete_note_relations(
        session: AsyncSession, 
        note_id: str
    ) -> int:
        """删除与指定笔记相关的所有关联"""
        try:
            # 查找所有相关的关联
            relations = await KnowledgeService.get_related_notes(session, note_id)
            
            deleted_count = 0
            for relation in relations:
                # 如果是源笔记，直接删除整个关联
                if relation.source_note_id == note_id:
                    await session.delete(relation)
                    deleted_count += 1
                # 如果在相关笔记列表中，从列表中移除
                elif note_id in relation.related_note_ids:
                    relation.related_note_ids = [
                        rid for rid in relation.related_note_ids if rid != note_id
                    ]
                    # 如果移除后列表为空，删除整个关联
                    if not relation.related_note_ids:
                        await session.delete(relation)
                        deleted_count += 1
            
            await session.commit()
            return deleted_count
            
        except Exception as e:
            await session.rollback()
            raise ValueError(f"删除笔记关联失败: {str(e)}")
    
    @staticmethod
    async def get_knowledge_statistics(session: AsyncSession) -> dict:
        """获取知识关联统计信息"""
        try:
            # 总关联数
            total_stmt = select(Knowledge)
            total_result = await session.execute(total_stmt)
            total_count = len(list(total_result.scalars().all()))
            
            # 高强度关联数（>0.7）
            high_strength_stmt = select(Knowledge).where(Knowledge.relation_strength > 0.7)
            high_result = await session.execute(high_strength_stmt)
            high_count = len(list(high_result.scalars().all()))
            
            return {
                "total_relations": total_count,
                "high_strength_relations": high_count,
                "average_strength": 0.0 if total_count == 0 else high_count / total_count
            }
            
        except Exception as e:
            raise ValueError(f"获取统计信息失败: {str(e)}")
