"""
笔记相关API端点
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def get_notes():
    """获取笔记列表"""
    return JSONResponse(
        content={
            "message": "笔记列表功能开发中",
            "status": "coming_soon",
            "data": []
        }
    )


@router.post("/")
async def create_note():
    """创建新笔记"""
    return JSONResponse(
        content={
            "message": "创建笔记功能开发中",
            "status": "coming_soon"
        }
    )


@router.get("/{note_id}")
async def get_note(note_id: str):
    """获取单个笔记"""
    return JSONResponse(
        content={
            "message": f"获取笔记 {note_id} 功能开发中",
            "status": "coming_soon"
        }
    )


@router.put("/{note_id}")
async def update_note(note_id: str):
    """更新笔记"""
    return JSONResponse(
        content={
            "message": f"更新笔记 {note_id} 功能开发中",
            "status": "coming_soon"
        }
    )


@router.delete("/{note_id}")
async def delete_note(note_id: str):
    """删除笔记"""
    return JSONResponse(
        content={
            "message": f"删除笔记 {note_id} 功能开发中",
            "status": "coming_soon"
        }
    )
