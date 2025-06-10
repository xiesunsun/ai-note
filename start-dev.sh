#!/bin/bash

# AI闪念笔记 - 开发环境快速启动脚本

set -e

echo "🚀 启动AI闪念笔记开发环境..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查必要的工具
check_requirements() {
    echo -e "${BLUE}📋 检查环境要求...${NC}"
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安装${NC}"
        echo "请安装Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3未安装${NC}"
        exit 1
    fi
    
    # 检查Node.js (如果有前端)
    if [ -d "frontend" ] && ! command -v node &> /dev/null; then
        echo -e "${YELLOW}⚠️  Node.js未安装，前端将无法启动${NC}"
    fi
    
    echo -e "${GREEN}✅ 环境检查通过${NC}"
}

# 启动数据库
start_databases() {
    echo -e "${BLUE}🗄️  启动数据库服务...${NC}"
    
    if [ ! -f "docker-compose.dev.yml" ]; then
        echo -e "${RED}❌ docker-compose.dev.yml 文件不存在${NC}"
        exit 1
    fi
    
    # 检查docker-compose命令
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    # 启动数据库服务
    $DOCKER_COMPOSE -f docker-compose.dev.yml up -d postgres-dev mongo-dev redis-dev
    
    echo -e "${YELLOW}⏳ 等待数据库服务启动...${NC}"
    sleep 15
    
    # 检查服务状态
    if $DOCKER_COMPOSE -f docker-compose.dev.yml ps | grep -q "Up"; then
        echo -e "${GREEN}✅ 数据库服务启动成功${NC}"
    else
        echo -e "${RED}❌ 数据库服务启动失败${NC}"
        $DOCKER_COMPOSE -f docker-compose.dev.yml logs
        exit 1
    fi
}

# 配置后端环境
setup_backend() {
    echo -e "${BLUE}🐍 配置后端环境...${NC}"
    
    cd backend
    
    # 复制环境变量文件
    if [ ! -f ".env" ]; then
        if [ -f "../.env.dev" ]; then
            cp ../.env.dev .env
            echo -e "${GREEN}✅ 环境变量文件已复制${NC}"
        else
            echo -e "${YELLOW}⚠️  .env.dev 文件不存在，请手动创建 .env 文件${NC}"
        fi
    fi
    
    # 检查虚拟环境
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        echo -e "${YELLOW}⚠️  未找到虚拟环境，请确保已激活Python虚拟环境${NC}"
    fi
    
    # 安装依赖
    echo -e "${BLUE}📦 安装Python依赖...${NC}"
    pip install -r requirements.txt
    
    cd ..
}

# 测试数据库连接
test_database() {
    echo -e "${BLUE}🧪 测试数据库连接...${NC}"
    
    cd backend
    
    if python test_db_connection.py; then
        echo -e "${GREEN}✅ 数据库连接测试通过${NC}"
    else
        echo -e "${RED}❌ 数据库连接测试失败${NC}"
        echo -e "${YELLOW}请检查数据库服务状态和配置${NC}"
        exit 1
    fi
    
    cd ..
}

# 运行数据库迁移
run_migrations() {
    echo -e "${BLUE}🔄 运行数据库迁移...${NC}"
    
    cd backend
    
    # 检查alembic是否存在
    if [ ! -f "alembic.ini" ]; then
        echo -e "${YELLOW}⚠️  alembic.ini 不存在，跳过迁移${NC}"
        cd ..
        return
    fi
    
    # 运行迁移
    if alembic upgrade head; then
        echo -e "${GREEN}✅ 数据库迁移完成${NC}"
    else
        echo -e "${YELLOW}⚠️  数据库迁移失败，可能是首次运行${NC}"
    fi
    
    cd ..
}

# 启动后端服务
start_backend() {
    echo -e "${BLUE}🚀 启动后端服务...${NC}"
    
    cd backend
    
    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  端口8000已被占用${NC}"
        read -p "是否终止占用进程并继续？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill -9 $(lsof -Pi :8000 -sTCP:LISTEN -t)
        else
            echo -e "${RED}❌ 后端启动取消${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}🎯 后端服务启动中...${NC}"
    echo -e "${BLUE}访问地址: http://localhost:8000${NC}"
    echo -e "${BLUE}API文档: http://localhost:8000/docs${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
    echo ""
    
    # 启动FastAPI服务
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# 启动前端服务 (如果存在)
start_frontend() {
    if [ -d "frontend" ]; then
        echo -e "${BLUE}🎨 启动前端服务...${NC}"
        
        cd frontend
        
        # 安装依赖
        if [ ! -d "node_modules" ]; then
            echo -e "${BLUE}📦 安装前端依赖...${NC}"
            npm install
        fi
        
        # 启动开发服务器
        echo -e "${GREEN}🎯 前端服务启动中...${NC}"
        echo -e "${BLUE}访问地址: http://localhost:3000${NC}"
        
        npm run dev &
        FRONTEND_PID=$!
        
        cd ..
    else
        echo -e "${YELLOW}⚠️  未找到frontend目录，跳过前端启动${NC}"
    fi
}

# 显示服务信息
show_services() {
    echo ""
    echo -e "${GREEN}🎉 开发环境启动完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 服务访问地址:${NC}"
    echo -e "  🔗 后端API: http://localhost:8000"
    echo -e "  📚 API文档: http://localhost:8000/docs"
    echo -e "  🔍 交互式API: http://localhost:8000/redoc"
    
    if [ -d "frontend" ]; then
        echo -e "  🎨 前端应用: http://localhost:3000"
    fi
    
    echo ""
    echo -e "${BLUE}🗄️  数据库管理:${NC}"
    echo -e "  🐘 PostgreSQL: localhost:5432 (用户: postgres, 密码: dev_password_123)"
    echo -e "  🍃 MongoDB: mongodb://localhost:27017/ai_note_dev"
    echo -e "  🔴 Redis: redis://localhost:6379/0"
    echo ""
    echo -e "${YELLOW}💡 提示:${NC}"
    echo -e "  - 使用 Ctrl+C 停止后端服务"
    echo -e "  - 数据库管理工具可通过 docker-compose -f docker-compose.dev.yml up -d pgadmin-dev mongo-express-dev 启动"
    echo -e "  - 查看日志: docker-compose -f docker-compose.dev.yml logs -f"
}

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 正在停止服务...${NC}"
    
    # 停止前端服务
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 设置信号处理
trap cleanup EXIT INT TERM

# 主流程
main() {
    echo -e "${GREEN}🚀 AI闪念笔记 - 开发环境启动脚本${NC}"
    echo -e "${BLUE}⏰ $(date)${NC}"
    echo ""
    
    # 检查参数
    case "${1:-all}" in
        "db-only")
            check_requirements
            start_databases
            echo -e "${GREEN}✅ 仅数据库服务已启动${NC}"
            ;;
        "backend-only")
            setup_backend
            test_database
            run_migrations
            start_backend
            ;;
        "test")
            setup_backend
            test_database
            echo -e "${GREEN}✅ 数据库测试完成${NC}"
            ;;
        "all"|*)
            check_requirements
            start_databases
            setup_backend
            test_database
            run_migrations
            show_services
            start_backend
            ;;
    esac
}

# 显示帮助
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "AI闪念笔记开发环境启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  all         启动完整开发环境 (默认)"
    echo "  db-only     仅启动数据库服务"
    echo "  backend-only 仅启动后端服务"
    echo "  test        测试数据库连接"
    echo "  --help, -h  显示此帮助信息"
    echo ""
    exit 0
fi

# 运行主流程
main "$1"
