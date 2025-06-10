-- AI闪念笔记 PostgreSQL 初始化脚本
-- 创建开发环境数据库和用户

-- 创建开发数据库（如果不存在）
SELECT 'CREATE DATABASE ai_note_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ai_note_dev')\gexec

-- 创建测试数据库（如果不存在）
SELECT 'CREATE DATABASE ai_note_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ai_note_test')\gexec

-- 连接到开发数据库
\c ai_note_dev;

-- 创建UUID扩展（用于用户ID）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建用户表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    last_login_at TIMESTAMP WITH TIME ZONE,
    locked_until TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 创建更新时间触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建知识关联表（如果不存在）
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_note_id VARCHAR(24) NOT NULL,  -- MongoDB ObjectId
    target_note_id VARCHAR(24) NOT NULL,  -- MongoDB ObjectId
    relation_type VARCHAR(50) NOT NULL DEFAULT 'related',
    strength DECIMAL(3,2) DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建知识关联表索引
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_user_id ON knowledge_relations(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_source ON knowledge_relations(source_note_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_target ON knowledge_relations(target_note_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_type ON knowledge_relations(relation_type);

-- 创建知识关联表更新时间触发器
DROP TRIGGER IF EXISTS update_knowledge_relations_updated_at ON knowledge_relations;
CREATE TRIGGER update_knowledge_relations_updated_at
    BEFORE UPDATE ON knowledge_relations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入测试用户（开发环境）
INSERT INTO users (name, email, password_hash, is_active) 
VALUES 
    ('测试用户', 'test@ai-note.dev', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.O', true),
    ('开发用户', 'dev@ai-note.dev', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.O', true)
ON CONFLICT (email) DO NOTHING;

-- 显示创建结果
\echo '✅ PostgreSQL 数据库初始化完成'
\echo '📊 数据库统计:'
SELECT 
    'users' as table_name, 
    count(*) as record_count 
FROM users
UNION ALL
SELECT 
    'knowledge_relations' as table_name, 
    count(*) as record_count 
FROM knowledge_relations;
