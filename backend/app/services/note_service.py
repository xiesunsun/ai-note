"""
笔记服务
处理笔记相关的业务逻辑
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.note import NoteCreate, NoteUpdate, NoteInDB, NoteResponse


class NoteService:
    """笔记服务类"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.notes
    
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
        """获取用户的笔记列表"""
        try:
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
            
            return [self._document_to_response(note) for note in notes]
            
        except Exception as e:
            raise ValueError(f"获取用户笔记失败: {str(e)}")
    
    async def update_note(self, note_id: str, note_data: NoteUpdate) -> Optional[NoteResponse]:
        """更新笔记"""
        try:
            if not ObjectId.is_valid(note_id):
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
            
            result = await self.collection.delete_one({"_id": ObjectId(note_id)})
            return result.deleted_count > 0
            
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
        """全文搜索笔记"""
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
            return [self._document_to_response(note) for note in notes]
            
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
