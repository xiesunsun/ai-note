#!/bin/bash

# AI闪念笔记 - 数据库启动脚本

set -e

echo "🚀 启动AI闪念笔记数据库服务..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    echo "安装命令："
    echo "  Ubuntu: sudo apt install docker.io"
    echo "  或访问: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker未运行，请启动Docker服务"
    echo "启动命令: sudo systemctl start docker"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose未找到，尝试使用docker compose..."
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "📋 使用配置文件: docker-compose.dev.yml"

# 创建必要的目录
mkdir -p backend/scripts

# 停止可能存在的容器
echo "🛑 停止现有容器..."
$DOCKER_COMPOSE -f docker-compose.dev.yml down --remove-orphans

# 清理旧的卷（可选，谨慎使用）
read -p "是否清理旧的数据库数据？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  清理旧数据..."
    docker volume rm ai-note_postgres_dev_data ai-note_mongo_dev_data ai-note_redis_dev_data 2>/dev/null || true
fi

# 拉取最新镜像
echo "📥 拉取Docker镜像..."
$DOCKER_COMPOSE -f docker-compose.dev.yml pull

# 启动数据库服务
echo "🚀 启动数据库服务..."
$DOCKER_COMPOSE -f docker-compose.dev.yml up -d postgres-dev mongo-dev redis-dev

# 等待服务启动
echo "⏳ 等待数据库服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
$DOCKER_COMPOSE -f docker-compose.dev.yml ps

# 等待健康检查通过
echo "🏥 等待健康检查..."
for i in {1..30}; do
    if $DOCKER_COMPOSE -f docker-compose.dev.yml ps | grep -q "healthy"; then
        echo "✅ 数据库服务健康检查通过"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 2
done

# 启动管理工具（可选）
read -p "是否启动数据库管理工具？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🛠️  启动管理工具..."
    $DOCKER_COMPOSE -f docker-compose.dev.yml up -d pgadmin-dev mongo-express-dev
    echo "📊 管理工具访问地址："
    echo "  - PostgreSQL (pgAdmin): http://localhost:5050"
    echo "    用户名: admin@ai-note.dev"
    echo "    密码: admin123"
    echo "  - MongoDB (Mongo Express): http://localhost:8081"
    echo "    用户名: admin"
    echo "    密码: admin123"
fi

echo ""
echo "🎉 数据库服务启动完成！"
echo ""
echo "📋 连接信息："
echo "  PostgreSQL:"
echo "    主机: localhost:5432"
echo "    数据库: ai_note_dev"
echo "    用户名: postgres"
echo "    密码: dev_password_123"
echo ""
echo "  MongoDB:"
echo "    连接字符串: mongodb://localhost:27017/ai_note_dev"
echo ""
echo "  Redis:"
echo "    连接字符串: redis://localhost:6379/0"
echo ""
echo "🔧 管理命令："
echo "  查看日志: $DOCKER_COMPOSE -f docker-compose.dev.yml logs -f"
echo "  停止服务: $DOCKER_COMPOSE -f docker-compose.dev.yml down"
echo "  重启服务: $DOCKER_COMPOSE -f docker-compose.dev.yml restart"
echo ""
echo "📝 下一步："
echo "  1. 复制 .env.dev 到 backend/.env"
echo "  2. 运行数据库迁移: cd backend && alembic upgrade head"
echo "  3. 启动后端服务: cd backend && uvicorn app.main:app --reload"
