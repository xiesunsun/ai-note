#!/usr/bin/env python3
"""
MongoDB索引创建脚本
为笔记集合创建必要的索引以优化查询性能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from pymongo import ASCENDING, DESCENDING, TEXT


async def create_notes_indexes():
    """为notes集合创建索引"""
    try:
        # 初始化MongoDB连接
        await db_manager.init_mongodb()
        db = db_manager.get_mongo_db()
        notes_collection = db.notes
        
        print("开始创建MongoDB索引...")
        
        # 1. 用户ID索引 - 用于查询用户的所有笔记
        await notes_collection.create_index([("user_id", ASCENDING)])
        print("✅ 创建user_id索引")
        
        # 2. 创建时间索引 - 用于按时间排序
        await notes_collection.create_index([("created_at", DESCENDING)])
        print("✅ 创建created_at索引")
        
        # 3. 更新时间索引 - 用于按更新时间排序
        await notes_collection.create_index([("updated_at", DESCENDING)])
        print("✅ 创建updated_at索引")
        
        # 4. 标签索引 - 用于按标签筛选
        await notes_collection.create_index([("tags", ASCENDING)])
        print("✅ 创建tags索引")
        
        # 5. AI标签索引 - 用于按AI标签筛选
        await notes_collection.create_index([("ai_tags", ASCENDING)])
        print("✅ 创建ai_tags索引")
        
        # 6. 复合索引：用户ID + 创建时间 - 用于用户笔记的时间排序
        await notes_collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        print("✅ 创建user_id + created_at复合索引")
        
        # 7. 复合索引：用户ID + 标签 - 用于用户按标签筛选
        await notes_collection.create_index([
            ("user_id", ASCENDING),
            ("tags", ASCENDING)
        ])
        print("✅ 创建user_id + tags复合索引")
        
        # 8. 文本搜索索引 - 用于全文搜索标题和内容
        await notes_collection.create_index([
            ("title", TEXT),
            ("content", TEXT)
        ], default_language='none')  # 设置为none以支持中文搜索
        print("✅ 创建全文搜索索引")
        
        # 9. 最后查看时间索引 - 用于记忆系统
        await notes_collection.create_index([("last_viewed_at", DESCENDING)])
        print("✅ 创建last_viewed_at索引")
        
        # 10. 复习计划索引 - 用于艾宾浩斯记忆系统
        await notes_collection.create_index([("review_schedule", ASCENDING)])
        print("✅ 创建review_schedule索引")

        # 11. 版本索引 - 用于版本管理
        await notes_collection.create_index([("version", ASCENDING)])
        print("✅ 创建version索引")

        # 创建笔记历史集合的索引
        print("\n📝 创建笔记历史集合索引...")
        history_collection = db.note_history

        # 1. 笔记ID索引 - 用于查询特定笔记的历史
        await history_collection.create_index([("note_id", ASCENDING)])
        print("✅ 创建note_id索引")

        # 2. 版本索引 - 用于查询特定版本
        await history_collection.create_index([("version", ASCENDING)])
        print("✅ 创建version索引")

        # 3. 复合索引：笔记ID + 版本 - 用于查询特定笔记的特定版本
        await history_collection.create_index([
            ("note_id", ASCENDING),
            ("version", DESCENDING)
        ])
        print("✅ 创建note_id + version复合索引")

        # 4. 创建时间索引 - 用于按时间排序历史记录
        await history_collection.create_index([("created_at", DESCENDING)])
        print("✅ 创建历史记录created_at索引")

        # 列出所有索引
        notes_indexes = await notes_collection.list_indexes().to_list(length=None)
        history_indexes = await history_collection.list_indexes().to_list(length=None)

        print(f"\n📋 notes集合当前索引列表:")
        for idx in notes_indexes:
            print(f"  - {idx['name']}: {idx.get('key', {})}")

        print(f"\n📋 note_history集合当前索引列表:")
        for idx in history_indexes:
            print(f"  - {idx['name']}: {idx.get('key', {})}")

        total_indexes = len(notes_indexes) + len(history_indexes)
        print(f"\n🎉 MongoDB索引创建完成！共创建了 {total_indexes} 个索引")
        
    except Exception as e:
        print(f"❌ 创建MongoDB索引失败: {e}")
        raise
    finally:
        await db_manager.close_all()


async def main():
    """主函数"""
    print("🚀 开始创建MongoDB索引...")
    await create_notes_indexes()
    print("✅ 索引创建任务完成")


if __name__ == "__main__":
    asyncio.run(main())
