"""
笔记服务
处理笔记相关的业务逻辑，集成缓存功能
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.note import (
    NoteCreate, NoteUpdate, NoteInDB, NoteResponse,
    NoteVersionHistory, NoteWithHistory, MarkdownValidationResult
)
from app.services.cache_service import CacheService, create_cache_service
from app.services.markdown_service import markdown_service


class NoteService:
    """笔记服务类，集成缓存功能"""

    def __init__(self, db: AsyncIOMotorDatabase, cache_service: CacheService = None):
        self.db = db
        self.collection = db.notes
        self.history_collection = db.note_history  # 版本历史集合
        self.cache_service = cache_service or create_cache_service()
    
    async def create_note(self, note_data: NoteCreate) -> NoteResponse:
        """创建新笔记"""
        try:
            # 验证Markdown内容
            validation_result = markdown_service.validate_markdown(note_data.content)
            if not validation_result.is_valid:
                raise ValueError(f"Markdown内容验证失败: {', '.join(validation_result.errors)}")

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
                "review_schedule": [],
                "version": 1  # 初始版本号
            }

            # 插入到MongoDB
            result = await self.collection.insert_one(note_dict)

            # 创建初始版本历史记录
            await self._create_version_history(
                note_id=str(result.inserted_id),
                version=1,
                title=note_data.title,
                content=note_data.content,
                change_summary="创建笔记"
            )

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

            # 获取原笔记信息
            original_note = await self.collection.find_one({"_id": ObjectId(note_id)})
            if not original_note:
                return None

            # 验证Markdown内容（如果有更新）
            if note_data.content is not None:
                validation_result = markdown_service.validate_markdown(note_data.content)
                if not validation_result.is_valid:
                    raise ValueError(f"Markdown内容验证失败: {', '.join(validation_result.errors)}")

            # 准备更新数据
            update_data = note_data.model_dump(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.utcnow()

                # 检查是否有内容或标题变化
                content_changed = (note_data.content is not None and
                                 note_data.content != original_note.get("content"))
                title_changed = (note_data.title is not None and
                               note_data.title != original_note.get("title"))

                # 如果内容或标题有变化，创建新版本
                if content_changed or title_changed:
                    current_version = original_note.get("version", 1)
                    new_version = current_version + 1
                    update_data["version"] = new_version

                    # 创建版本历史记录
                    change_summary = []
                    if title_changed:
                        change_summary.append("修改标题")
                    if content_changed:
                        change_summary.append("修改内容")

                    await self._create_version_history(
                        note_id=note_id,
                        version=new_version,
                        title=note_data.title or original_note.get("title"),
                        content=note_data.content or original_note.get("content"),
                        change_summary=", ".join(change_summary)
                    )

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
        """全文搜索笔记，支持缓存和备用搜索"""
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

            # 首先尝试MongoDB全文搜索
            try:
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

            except Exception as text_search_error:
                print(f"全文搜索失败，使用备用搜索: {text_search_error}")

                # 备用搜索：使用正则表达式搜索标题和内容
                regex_pattern = {"$regex": query, "$options": "i"}
                fallback_query = {
                    "user_id": str(user_id),
                    "$or": [
                        {"title": regex_pattern},
                        {"content": regex_pattern},
                        {"tags": {"$in": [query]}}
                    ]
                }

                cursor = self.collection.find(fallback_query).sort("updated_at", -1).skip(skip).limit(limit)
                notes = await cursor.to_list(length=limit)
                note_responses = [self._document_to_response(note) for note in notes]

                # 缓存备用搜索结果
                if skip == 0:
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
            review_schedule=document.get("review_schedule", []),
            version_count=document.get("version", 1)
        )

    # === 版本历史相关方法 ===

    async def _create_version_history(
        self,
        note_id: str,
        version: int,
        title: str,
        content: str,
        change_summary: str = None
    ) -> bool:
        """创建版本历史记录"""
        try:
            history_record = {
                "note_id": note_id,
                "version": version,
                "title": title,
                "content": content,
                "change_summary": change_summary,
                "created_at": datetime.utcnow()
            }

            await self.history_collection.insert_one(history_record)
            return True

        except Exception as e:
            print(f"创建版本历史失败: {e}")
            return False

    async def get_note_history(self, note_id: str, limit: int = 10) -> List[NoteVersionHistory]:
        """获取笔记的版本历史"""
        try:
            if not ObjectId.is_valid(note_id):
                return []

            cursor = self.history_collection.find(
                {"note_id": note_id}
            ).sort("version", -1).limit(limit)

            history_docs = await cursor.to_list(length=limit)

            return [
                NoteVersionHistory(
                    version=doc["version"],
                    title=doc["title"],
                    content=doc["content"],
                    change_summary=doc.get("change_summary"),
                    created_at=doc["created_at"]
                )
                for doc in history_docs
            ]

        except Exception as e:
            raise ValueError(f"获取版本历史失败: {str(e)}")

    async def get_note_with_history(self, note_id: str) -> Optional[NoteWithHistory]:
        """获取包含历史版本的笔记"""
        try:
            # 获取笔记
            note = await self.get_note_by_id(note_id)
            if not note:
                return None

            # 获取历史版本
            history = await self.get_note_history(note_id)

            # 转换为NoteWithHistory
            note_dict = note.model_dump()
            note_dict["history"] = [h.model_dump() for h in history]

            return NoteWithHistory(**note_dict)

        except Exception as e:
            raise ValueError(f"获取笔记和历史失败: {str(e)}")

    async def restore_note_version(self, note_id: str, version: int) -> Optional[NoteResponse]:
        """恢复笔记到指定版本"""
        try:
            if not ObjectId.is_valid(note_id):
                return None

            # 获取指定版本的历史记录
            history_doc = await self.history_collection.find_one({
                "note_id": note_id,
                "version": version
            })

            if not history_doc:
                raise ValueError(f"版本 {version} 不存在")

            # 获取当前笔记
            current_note = await self.collection.find_one({"_id": ObjectId(note_id)})
            if not current_note:
                raise ValueError("笔记不存在")

            # 创建新版本（回滚版本）
            current_version = current_note.get("version", 1)
            new_version = current_version + 1

            # 更新笔记内容
            update_data = {
                "title": history_doc["title"],
                "content": history_doc["content"],
                "version": new_version,
                "updated_at": datetime.utcnow()
            }

            await self.collection.update_one(
                {"_id": ObjectId(note_id)},
                {"$set": update_data}
            )

            # 创建回滚的版本历史记录
            await self._create_version_history(
                note_id=note_id,
                version=new_version,
                title=history_doc["title"],
                content=history_doc["content"],
                change_summary=f"回滚到版本 {version}"
            )

            # 清除缓存
            await self.cache_service.invalidate_user_notes_cache(current_note["user_id"])

            # 返回更新后的笔记
            updated_note = await self.collection.find_one({"_id": ObjectId(note_id)})
            return self._document_to_response(updated_note)

        except Exception as e:
            raise ValueError(f"恢复版本失败: {str(e)}")

    async def validate_markdown_content(self, content: str) -> MarkdownValidationResult:
        """验证Markdown内容"""
        return markdown_service.validate_markdown(content)

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
