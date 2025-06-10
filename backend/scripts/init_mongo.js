// AI闪念笔记 MongoDB 初始化脚本
// 创建开发环境集合和索引

// 切换到开发数据库
db = db.getSiblingDB('ai_note_dev');

print('🚀 开始初始化 MongoDB 数据库...');

// 创建笔记集合
db.createCollection('notes', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "title", "content", "created_at", "updated_at"],
            properties: {
                user_id: {
                    bsonType: "string",
                    description: "用户ID，必须是有效的UUID字符串"
                },
                title: {
                    bsonType: "string",
                    minLength: 1,
                    maxLength: 200,
                    description: "笔记标题，1-200字符"
                },
                content: {
                    bsonType: "string",
                    description: "笔记内容，Markdown格式"
                },
                enhanced_content: {
                    bsonType: ["string", "null"],
                    description: "AI润色后的内容"
                },
                tags: {
                    bsonType: "array",
                    items: {
                        bsonType: "string"
                    },
                    description: "手动标签数组"
                },
                ai_tags: {
                    bsonType: "array",
                    items: {
                        bsonType: "string"
                    },
                    description: "AI生成的标签数组"
                },
                created_at: {
                    bsonType: "date",
                    description: "创建时间"
                },
                updated_at: {
                    bsonType: "date",
                    description: "更新时间"
                },
                last_viewed_at: {
                    bsonType: ["date", "null"],
                    description: "最后查看时间"
                },
                review_schedule: {
                    bsonType: "array",
                    items: {
                        bsonType: "date"
                    },
                    description: "复习计划时间数组"
                }
            }
        }
    }
});

print('✅ 创建 notes 集合完成');

// 创建索引
print('📊 创建索引...');

// 用户ID索引（最重要）
db.notes.createIndex({ "user_id": 1 }, { name: "idx_user_id" });

// 复合索引：用户ID + 创建时间（用于分页查询）
db.notes.createIndex({ "user_id": 1, "created_at": -1 }, { name: "idx_user_created" });

// 复合索引：用户ID + 更新时间（用于最近更新查询）
db.notes.createIndex({ "user_id": 1, "updated_at": -1 }, { name: "idx_user_updated" });

// 标签索引（用于标签筛选）
db.notes.createIndex({ "user_id": 1, "tags": 1 }, { name: "idx_user_tags" });
db.notes.createIndex({ "user_id": 1, "ai_tags": 1 }, { name: "idx_user_ai_tags" });

// 文本搜索索引
db.notes.createIndex(
    { 
        "title": "text", 
        "content": "text",
        "enhanced_content": "text"
    }, 
    { 
        name: "idx_text_search",
        default_language: "none",  // 支持中文搜索
        weights: {
            "title": 10,
            "content": 5,
            "enhanced_content": 3
        }
    }
);

// 最后查看时间索引（用于查找需要复习的笔记）
db.notes.createIndex({ "user_id": 1, "last_viewed_at": 1 }, { name: "idx_user_last_viewed" });

// 复习计划索引
db.notes.createIndex({ "user_id": 1, "review_schedule": 1 }, { name: "idx_user_review" });

print('✅ 索引创建完成');

// 插入测试数据
print('📝 插入测试数据...');

// 测试用户的UUID（与PostgreSQL中的测试用户对应）
const testUserId1 = "550e8400-e29b-41d4-a716-446655440000";  // 模拟UUID
const testUserId2 = "550e8400-e29b-41d4-a716-446655440001";  // 模拟UUID

const testNotes = [
    {
        user_id: testUserId1,
        title: "欢迎使用AI闪念笔记",
        content: "# 欢迎使用AI闪念笔记\n\n这是您的第一条笔记！\n\n## 功能特点\n- 支持Markdown格式\n- AI智能标签\n- 知识关联\n- 复习提醒",
        enhanced_content: null,
        tags: ["欢迎", "教程"],
        ai_tags: ["入门", "指南", "功能介绍"],
        created_at: new Date(),
        updated_at: new Date(),
        last_viewed_at: new Date(),
        review_schedule: []
    },
    {
        user_id: testUserId1,
        title: "学习笔记：JavaScript异步编程",
        content: "# JavaScript异步编程\n\n## Promise\n- 解决回调地狱问题\n- 三种状态：pending、fulfilled、rejected\n\n## async/await\n- 基于Promise的语法糖\n- 使异步代码看起来像同步代码",
        enhanced_content: null,
        tags: ["JavaScript", "编程", "学习"],
        ai_tags: ["前端开发", "异步", "Promise"],
        created_at: new Date(Date.now() - 86400000), // 1天前
        updated_at: new Date(Date.now() - 86400000),
        last_viewed_at: new Date(Date.now() - 3600000), // 1小时前
        review_schedule: [new Date(Date.now() + 86400000)] // 明天复习
    },
    {
        user_id: testUserId2,
        title: "项目想法：AI助手应用",
        content: "# AI助手应用构想\n\n## 核心功能\n1. 智能对话\n2. 任务管理\n3. 知识库\n\n## 技术栈\n- 前端：React + TypeScript\n- 后端：Python + FastAPI\n- AI：OpenAI API",
        enhanced_content: null,
        tags: ["项目", "AI", "想法"],
        ai_tags: ["人工智能", "应用开发", "创意"],
        created_at: new Date(Date.now() - 172800000), // 2天前
        updated_at: new Date(Date.now() - 172800000),
        last_viewed_at: null,
        review_schedule: []
    }
];

// 插入测试笔记
db.notes.insertMany(testNotes);

print('✅ 测试数据插入完成');

// 显示统计信息
print('📊 数据库统计:');
print('笔记总数:', db.notes.countDocuments());
print('索引列表:');
db.notes.getIndexes().forEach(index => {
    print('- ' + index.name + ': ' + JSON.stringify(index.key));
});

// 创建测试数据库
db = db.getSiblingDB('ai_note_test');
db.createCollection('notes');
print('✅ 测试数据库创建完成');

print('🎉 MongoDB 初始化完成！');
print('');
print('📋 访问信息:');
print('- 开发数据库: ai_note_dev');
print('- 测试数据库: ai_note_test');
print('- 管理界面: http://localhost:8081 (用户名: admin, 密码: admin123)');
