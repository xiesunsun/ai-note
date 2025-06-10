# AI闪念笔记 - 开发环境配置指南

## 🚀 快速开始

### 方式一：一键启动（推荐）

```bash
# 启动完整开发环境
./start-dev.sh

# 或者分步启动
./start-dev.sh db-only      # 仅启动数据库
./start-dev.sh backend-only # 仅启动后端
./start-dev.sh test         # 测试数据库连接
```

### 方式二：手动配置

#### 1. 启动数据库服务

```bash
# 启动数据库容器
./start-databases.sh

# 或使用docker-compose
docker-compose -f docker-compose.dev.yml up -d postgres-dev mongo-dev redis-dev
```

#### 2. 配置后端环境

```bash
cd backend

# 复制环境变量文件
cp ../.env.dev .env

# 激活虚拟环境（如果使用）
source venv/bin/activate  # 或 source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 测试数据库连接
python test_db_connection.py

# 运行数据库迁移（如果需要）
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 测试API功能

```bash
# 在新终端中运行API测试
python test-api.py
```

## 📋 环境要求

### 必需软件
- **Docker**: 用于运行数据库服务
- **Python 3.11+**: 后端开发环境
- **Node.js 18+**: 前端开发环境（如果有前端）

### 可选工具
- **Docker Compose**: 容器编排
- **pyenv**: Python版本管理
- **uv**: Python包管理器

## 🗄️ 数据库配置

### 连接信息

| 数据库 | 地址 | 端口 | 用户名 | 密码 | 数据库名 |
|--------|------|------|--------|------|----------|
| PostgreSQL | localhost | 5432 | postgres | dev_password_123 | ai_note_dev |
| MongoDB | localhost | 27017 | - | - | ai_note_dev |
| Redis | localhost | 6379 | - | - | 0 |

### 管理工具

启动数据库管理工具：
```bash
docker-compose -f docker-compose.dev.yml up -d pgadmin-dev mongo-express-dev
```

访问地址：
- **pgAdmin**: http://localhost:5050 (admin@ai-note.dev / admin123)
- **Mongo Express**: http://localhost:8081 (admin / admin123)

## 🔧 开发配置

### 环境变量

主要配置项（`.env`文件）：

```env
# 数据库连接
DATABASE_URL=postgresql://postgres:dev_password_123@localhost:5432/ai_note_dev
MONGODB_URL=mongodb://localhost:27017/ai_note_dev
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 安全配置
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### API端点

| 功能 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 健康检查 | GET | `/` | 服务状态检查 |
| 用户注册 | POST | `/api/v1/auth/register` | 新用户注册 |
| 用户登录 | POST | `/api/v1/auth/login` | 用户登录获取token |
| 用户信息 | GET | `/api/v1/auth/me` | 获取当前用户信息 |
| 用户登出 | POST | `/api/v1/auth/logout` | 用户登出 |
| 创建笔记 | POST | `/api/v1/notes/` | 创建新笔记 |
| 获取笔记 | GET | `/api/v1/notes/` | 获取用户笔记列表 |
| API文档 | GET | `/docs` | Swagger UI |
| API文档 | GET | `/redoc` | ReDoc |

## 🧪 测试指南

### 数据库连接测试

```bash
cd backend
python test_db_connection.py
```

### API功能测试

```bash
python test-api.py
```

### 认证系统测试

```bash
cd backend
python test_auth.py
python simple_test.py
```

## 🔍 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查容器状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs postgres-dev
docker-compose -f docker-compose.dev.yml logs mongo-dev
docker-compose -f docker-compose.dev.yml logs redis-dev

# 重启服务
docker-compose -f docker-compose.dev.yml restart
```

#### 2. 端口被占用
```bash
# 查看端口占用
lsof -i :8000  # 后端端口
lsof -i :5432  # PostgreSQL端口
lsof -i :27017 # MongoDB端口
lsof -i :6379  # Redis端口

# 终止进程
kill -9 <PID>
```

#### 3. 权限问题
```bash
# 给脚本执行权限
chmod +x start-dev.sh
chmod +x start-databases.sh
chmod +x test-api.py

# Docker权限问题
sudo usermod -aG docker $USER
# 然后重新登录
```

#### 4. Python依赖问题
```bash
# 重新安装依赖
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# 或使用uv
uv pip install -r requirements.txt
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs -f postgres-dev
docker-compose -f docker-compose.dev.yml logs -f mongo-dev
docker-compose -f docker-compose.dev.yml logs -f redis-dev

# 后端服务日志
cd backend
uvicorn app.main:app --reload --log-level debug
```

## 🎯 前后端联调

### 后端准备
1. 确保所有数据库服务正常运行
2. 后端API服务在 http://localhost:8000 运行
3. 运行 `python test-api.py` 确保API功能正常

### 前端配置
1. 设置API基础URL为 `http://localhost:8000`
2. 配置CORS允许的源地址
3. 实现JWT token管理

### 测试流程
1. 用户注册/登录
2. 获取用户信息
3. 创建/编辑/删除笔记
4. 笔记搜索和筛选
5. 用户登出

## 📚 开发资源

### API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 数据库Schema
- **PostgreSQL**: 用户信息、知识关联
- **MongoDB**: 笔记内容、标签
- **Redis**: 缓存、会话、限流

### 认证流程
1. 用户注册 → 密码哈希存储
2. 用户登录 → JWT token生成
3. API请求 → token验证
4. 用户登出 → token加入黑名单

## 🚀 部署准备

开发完成后，可以参考以下步骤准备生产部署：

1. 更新生产环境配置
2. 配置HTTPS和域名
3. 设置生产数据库
4. 配置监控和日志
5. 设置CI/CD流程

---

**💡 提示**: 如果遇到问题，请查看相关日志文件或联系开发团队。
