"""
笔记服务
处理笔记相关的业务逻辑，集成缓存功能
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.note import NoteCreate, NoteUpdate, NoteInDB, NoteResponse
from app.services.cache_service import CacheService, create_cache_service


class NoteService:
    """笔记服务类，集成缓存功能"""

    def __init__(self, db: AsyncIOMotorDatabase, cache_service: CacheService = None):
        self.db = db
        self.collection = db.notes
        self.cache_service = cache_service or create_cache_service()
    
    async def create_note(self, note_data: NoteCreate) -> NoteResponse:
        """创建新笔记"""
        try:
            # 准备笔记数据
            note_dict = {
                "user_id": str(note_data.user_id),
                "title": note_data.title,
                "content": note_data.content,
                "enhanced_content": None,
                "tags": note_data.tags,
                "ai_tags": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_viewed_at": None,
                "review_schedule": []
            }

            # 插入到MongoDB
            result = await self.collection.insert_one(note_dict)

            # 获取插入的文档
            created_note = await self.collection.find_one({"_id": result.inserted_id})

            # 清除用户笔记列表缓存
            await self.cache_service.invalidate_user_notes_cache(str(note_data.user_id))

            return self._document_to_response(created_note)

        except Exception as e:
            raise ValueError(f"创建笔记失败: {str(e)}")
    
    async def get_note_by_id(self, note_id: str) -> Optional[NoteResponse]:
        """根据ID获取笔记"""
        try:
            if not ObjectId.is_valid(note_id):
                return None
            
            note = await self.collection.find_one({"_id": ObjectId(note_id)})
            if not note:
                return None
            
            return self._document_to_response(note)
            
        except Exception as e:
            raise ValueError(f"获取笔记失败: {str(e)}")
    
    async def get_user_notes(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[NoteResponse]:
        """获取用户的笔记列表，支持缓存"""
        try:
            # 如果没有筛选条件，尝试从缓存获取
            if not tags and not search:
                page = (skip // limit) + 1
                cached_notes = await self.cache_service.get_cached_user_notes(
                    str(user_id), page, limit
                )
                if cached_notes:
                    return [NoteResponse(**note) for note in cached_notes]

            # 构建查询条件
            query = {"user_id": str(user_id)}

            # 添加标签筛选
            if tags:
                query["$or"] = [
                    {"tags": {"$in": tags}},
                    {"ai_tags": {"$in": tags}}
                ]

            # 添加搜索条件
            if search:
                query["$text"] = {"$search": search}

            # 执行查询
            cursor = self.collection.find(query).sort("updated_at", -1).skip(skip).limit(limit)
            notes = await cursor.to_list(length=limit)

            note_responses = [self._document_to_response(note) for note in notes]

            # 缓存结果（仅当没有筛选条件时）
            if not tags and not search:
                page = (skip // limit) + 1
                notes_data = [note.model_dump() for note in note_responses]
                await self.cache_service.cache_user_notes(
                    str(user_id), notes_data, page, limit
                )

            return note_responses

        except Exception as e:
            raise ValueError(f"获取用户笔记失败: {str(e)}")
    
    async def update_note(self, note_id: str, note_data: NoteUpdate) -> Optional[NoteResponse]:
        """更新笔记"""
        try:
            if not ObjectId.is_valid(note_id):
                return None

            # 获取原笔记信息（用于清除缓存）
            original_note = await self.collection.find_one({"_id": ObjectId(note_id)})
            if not original_note:
                return None

            # 准备更新数据
            update_data = note_data.model_dump(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.utcnow()

                # 执行更新
                result = await self.collection.update_one(
                    {"_id": ObjectId(note_id)},
                    {"$set": update_data}
                )

                if result.modified_count == 0:
                    return None

                # 清除用户笔记列表缓存
                await self.cache_service.invalidate_user_notes_cache(original_note["user_id"])

                # 返回更新后的笔记
                updated_note = await self.collection.find_one({"_id": ObjectId(note_id)})
                return self._document_to_response(updated_note)

            return None

        except Exception as e:
            raise ValueError(f"更新笔记失败: {str(e)}")
    
    async def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        try:
            if not ObjectId.is_valid(note_id):
                return False

            # 获取笔记信息（用于清除缓存）
            note = await self.collection.find_one({"_id": ObjectId(note_id)})
            if not note:
                return False

            result = await self.collection.delete_one({"_id": ObjectId(note_id)})

            if result.deleted_count > 0:
                # 清除用户笔记列表缓存
                await self.cache_service.invalidate_user_notes_cache(note["user_id"])
                return True

            return False

        except Exception as e:
            raise ValueError(f"删除笔记失败: {str(e)}")
    
    async def update_last_viewed(self, note_id: str) -> bool:
        """更新笔记的最后查看时间"""
        try:
            if not ObjectId.is_valid(note_id):
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(note_id)},
                {"$set": {"last_viewed_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise ValueError(f"更新查看时间失败: {str(e)}")
    
    async def get_notes_count(self, user_id: uuid.UUID) -> int:
        """获取用户笔记总数"""
        try:
            count = await self.collection.count_documents({"user_id": str(user_id)})
            return count
        except Exception as e:
            raise ValueError(f"获取笔记数量失败: {str(e)}")
    
    async def search_notes(
        self,
        user_id: uuid.UUID,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[NoteResponse]:
        """全文搜索笔记，支持缓存"""
        try:
            # 尝试从缓存获取搜索结果
            cached_results = await self.cache_service.get_cached_search_results(
                query, str(user_id)
            )
            if cached_results:
                # 应用分页
                start = skip
                end = skip + limit
                paginated_results = cached_results[start:end]
                return [NoteResponse(**note) for note in paginated_results]

            search_query = {
                "user_id": str(user_id),
                "$text": {"$search": query}
            }

            cursor = self.collection.find(
                search_query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(limit)

            notes = await cursor.to_list(length=limit)
            note_responses = [self._document_to_response(note) for note in notes]

            # 缓存搜索结果
            if skip == 0:  # 只缓存第一页的完整结果
                results_data = [note.model_dump() for note in note_responses]
                await self.cache_service.cache_search_results(
                    query, results_data, str(user_id)
                )

            return note_responses

        except Exception as e:
            raise ValueError(f"搜索笔记失败: {str(e)}")
    
    def _document_to_response(self, document: Dict[str, Any]) -> NoteResponse:
        """将MongoDB文档转换为响应模型"""
        return NoteResponse(
            id=str(document["_id"]),
            user_id=document["user_id"],
            title=document["title"],
            content=document["content"],
            enhanced_content=document.get("enhanced_content"),
            tags=document.get("tags", []),
            ai_tags=document.get("ai_tags", []),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            last_viewed_at=document.get("last_viewed_at"),
            review_schedule=document.get("review_schedule", [])
        )

    # === 缓存相关方法 ===

    async def cache_hot_notes(self, limit: int = 10) -> bool:
        """缓存热门笔记"""
        try:
            # 获取最近更新的笔记作为热门笔记
            cursor = self.collection.find().sort("updated_at", -1).limit(limit)
            notes = await cursor.to_list(length=limit)

            hot_notes_data = [self._document_to_response(note).model_dump() for note in notes]
            return await self.cache_service.cache_hot_notes(hot_notes_data)

        except Exception as e:
            print(f"缓存热门笔记失败: {e}")
            return False

    async def get_hot_notes_cached(self) -> Optional[List[NoteResponse]]:
        """获取缓存的热门笔记"""
        cached_notes = await self.cache_service.get_hot_notes()
        if cached_notes:
            return [NoteResponse(**note) for note in cached_notes]
        return None

    async def invalidate_user_cache(self, user_id: str) -> bool:
        """清除用户相关的笔记缓存"""
        return await self.cache_service.invalidate_user_notes_cache(user_id)
