#!/bin/bash

# Task 001 完成度测试脚本

echo "🧪 Task 001 完成度测试"
echo "=========================="

# 检查项目结构
echo "📁 检查项目结构..."
if [ -d "frontend" ] && [ -d "backend" ]; then
    echo "✅ 前后端分离目录结构存在"
else
    echo "❌ 项目结构不完整"
    exit 1
fi

# 检查前端配置
echo "🎨 检查前端配置..."
if [ -f "frontend/package.json" ] && [ -f "frontend/tsconfig.json" ] && [ -f "frontend/tailwind.config.js" ]; then
    echo "✅ React + TypeScript + TailwindCSS 配置完整"
else
    echo "❌ 前端配置不完整"
    exit 1
fi

# 检查前端代码规范工具
if [ -f "frontend/.eslintrc.json" ] && [ -f "frontend/.prettierrc" ]; then
    echo "✅ ESLint + Prettier 配置存在"
else
    echo "❌ 前端代码规范工具配置缺失"
    exit 1
fi

# 检查后端配置
echo "🐍 检查后端配置..."
if [ -f "backend/requirements.txt" ] && [ -f "backend/app/main.py" ]; then
    echo "✅ Python FastAPI 配置存在"
else
    echo "❌ 后端配置不完整"
    exit 1
fi

# 检查后端依赖
echo "📦 检查后端依赖..."
if grep -q "fastapi" backend/requirements.txt && \
   grep -q "sqlalchemy" backend/requirements.txt && \
   grep -q "pymongo" backend/requirements.txt && \
   grep -q "redis" backend/requirements.txt && \
   grep -q "celery" backend/requirements.txt; then
    echo "✅ 所有必需依赖存在"
else
    echo "❌ 后端依赖不完整"
    exit 1
fi

# 检查后端代码规范工具
if grep -q "black" backend/requirements.txt && grep -q "isort" backend/requirements.txt; then
    echo "✅ Black + isort 配置存在"
else
    echo "❌ 后端代码规范工具配置缺失"
    exit 1
fi

# 检查Docker配置
echo "🐳 检查Docker配置..."
if [ -f "docker-compose.yml" ] && [ -f "frontend/Dockerfile" ] && [ -f "backend/Dockerfile" ]; then
    echo "✅ Docker 配置完整"
else
    echo "❌ Docker 配置不完整"
    exit 1
fi

# 检查Git配置
echo "📝 检查Git配置..."
if [ -f ".gitignore" ]; then
    echo "✅ .gitignore 文件存在"
else
    echo "❌ .gitignore 文件缺失"
    exit 1
fi

# 检查虚拟环境
echo "🔧 检查Python虚拟环境..."
if [ -d "backend/.venv" ]; then
    echo "✅ Python 虚拟环境存在"
else
    echo "❌ Python 虚拟环境缺失"
    exit 1
fi

echo ""
echo "🎉 Task 001 所有要求检查完成！"
echo "✅ 项目基础架构设置完整"
echo ""
echo "📚 下一步测试："
echo "1. 启动后端: cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --reload"
echo "2. 启动前端: cd frontend && npm start"
echo "3. 访问 http://localhost:3000 和 http://localhost:8000"
