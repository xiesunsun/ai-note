"""
笔记相关API端点
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_mongo_db
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse
from app.services.note_service import NoteService

router = APIRouter()


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """创建新笔记"""
    try:
        note_service = NoteService(db)
        note = await note_service.create_note(note_data)
        return note
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建笔记失败")


@router.get("/user/{user_id}", response_model=List[NoteResponse])
async def get_user_notes(
    user_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取用户的笔记列表"""
    try:
        note_service = NoteService(db)
        notes = await note_service.get_user_notes(
            user_id=user_id,
            skip=skip,
            limit=limit,
            tags=tags,
            search=search
        )
        return notes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取笔记列表失败")


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取单个笔记"""
    try:
        note_service = NoteService(db)
        note = await note_service.get_note_by_id(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")

        # 更新最后查看时间
        await note_service.update_last_viewed(note_id)

        return note
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取笔记失败")


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """更新笔记"""
    try:
        note_service = NoteService(db)
        note = await note_service.update_note(note_id, note_data)
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")
        return note
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新笔记失败")


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """删除笔记"""
    try:
        note_service = NoteService(db)
        success = await note_service.delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="笔记不存在")
        return {"message": "笔记删除成功"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除笔记失败")


@router.get("/user/{user_id}/search", response_model=List[NoteResponse])
async def search_notes(
    user_id: uuid.UUID,
    q: str = Query(..., description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """全文搜索笔记"""
    try:
        note_service = NoteService(db)
        notes = await note_service.search_notes(
            user_id=user_id,
            query=q,
            skip=skip,
            limit=limit
        )
        return notes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="搜索笔记失败")


@router.get("/user/{user_id}/count")
async def get_notes_count(
    user_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取用户笔记总数"""
    try:
        note_service = NoteService(db)
        count = await note_service.get_notes_count(user_id)
        return {"count": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取笔记数量失败")
