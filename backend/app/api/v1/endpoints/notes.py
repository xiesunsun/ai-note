"""
笔记相关API端点
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_mongo_db
from app.schemas.note import (
    NoteCreate, NoteUpdate, NoteResponse,
    NoteVersionHistory, NoteWithHistory, MarkdownValidationResult
)
from app.services.note_service import NoteService
from app.middleware import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """创建新笔记"""
    try:
        # 设置笔记的用户ID
        note_data.user_id = current_user.id

        note_service = NoteService(db)
        note = await note_service.create_note(note_data)
        return note
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建笔记失败")


@router.get("/", response_model=List[NoteResponse])
async def get_user_notes(
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取当前用户的笔记列表"""
    try:
        note_service = NoteService(db)
        notes = await note_service.get_user_notes(
            user_id=current_user.id,
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


@router.get("/search", response_model=List[NoteResponse])
async def search_notes(
    current_user: User = Depends(get_current_active_user),
    q: str = Query(..., description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """全文搜索当前用户的笔记"""
    try:
        note_service = NoteService(db)
        notes = await note_service.search_notes(
            user_id=current_user.id,
            query=q,
            skip=skip,
            limit=limit
        )
        return notes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="搜索笔记失败")


@router.get("/count")
async def get_notes_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取当前用户笔记总数"""
    try:
        note_service = NoteService(db)
        count = await note_service.get_notes_count(current_user.id)
        return {"count": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取笔记数量失败")


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取单个笔记"""
    try:
        note_service = NoteService(db)
        note = await note_service.get_note_by_id(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")

        # 检查笔记所有权
        if str(note.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权访问此笔记")

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
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """更新笔记"""
    try:
        note_service = NoteService(db)

        # 先检查笔记是否存在和权限
        existing_note = await note_service.get_note_by_id(note_id)
        if not existing_note:
            raise HTTPException(status_code=404, detail="笔记不存在")

        if str(existing_note.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权修改此笔记")

        note = await note_service.update_note(note_id, note_data)
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
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """删除笔记"""
    try:
        note_service = NoteService(db)

        # 先检查笔记是否存在和权限
        existing_note = await note_service.get_note_by_id(note_id)
        if not existing_note:
            raise HTTPException(status_code=404, detail="笔记不存在")

        if str(existing_note.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权删除此笔记")

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





@router.get("/{note_id}/history", response_model=List[NoteVersionHistory])
async def get_note_history(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=50, description="返回的版本数量"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取笔记的版本历史"""
    try:
        note_service = NoteService(db)

        # 先检查笔记是否存在和权限
        note = await note_service.get_note_by_id(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")

        if str(note.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权访问此笔记")

        history = await note_service.get_note_history(note_id, limit)
        return history
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取版本历史失败")


@router.get("/{note_id}/with-history", response_model=NoteWithHistory)
async def get_note_with_history(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """获取包含历史版本的笔记"""
    try:
        note_service = NoteService(db)

        # 先检查笔记是否存在和权限
        note = await note_service.get_note_by_id(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")

        if str(note.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权访问此笔记")

        note_with_history = await note_service.get_note_with_history(note_id)
        return note_with_history
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取笔记和历史失败")


@router.post("/{note_id}/restore/{version}", response_model=NoteResponse)
async def restore_note_version(
    note_id: str,
    version: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """恢复笔记到指定版本"""
    try:
        note_service = NoteService(db)

        # 先检查笔记是否存在和权限
        note = await note_service.get_note_by_id(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")

        if str(note.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权修改此笔记")

        restored_note = await note_service.restore_note_version(note_id, version)
        if not restored_note:
            raise HTTPException(status_code=400, detail="版本恢复失败")

        return restored_note
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="恢复版本失败")


@router.post("/validate-markdown", response_model=MarkdownValidationResult)
async def validate_markdown(
    request: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """验证Markdown内容"""
    try:
        content = request.get("content") if isinstance(request, dict) else request
        if not content:
            raise HTTPException(status_code=400, detail="内容不能为空")

        note_service = NoteService(db)
        result = await note_service.validate_markdown_content(content)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Markdown验证失败")
