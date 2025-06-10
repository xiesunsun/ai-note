# AI笔记项目结构文档

## 项目概述

AI闪念笔记是一个现代化的全栈Web应用，采用前后端分离架构，支持智能笔记管理、AI增强和多数据库存储。

## 技术栈

### 后端技术栈
- **Python 3.11.9** (pyenv管理)
- **FastAPI 0.104.1** - 现代高性能Web框架
- **SQLAlchemy 2.0.23** - PostgreSQL ORM
- **Motor 3.3.2** - MongoDB异步驱动
- **Redis 5.0.1** - 缓存和会话管理
- **Alembic 1.12.1** - 数据库迁移
- **pytest 7.4.3** - 测试框架
- **uv** - 包管理器

### 前端技术栈
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Vite** - 构建工具

### 数据存储
- **PostgreSQL** - 用户数据、关系数据
- **MongoDB** - 笔记内容、文档数据
- **Redis** - 缓存、会话管理

## 项目结构

```
ai-note/
├── .venv/                    # Python虚拟环境 (uv管理)
├── .env                      # 环境变量配置
├── .gitignore               # Git忽略文件
├── README.md                # 项目说明
├── docker-compose.yml       # Docker编排配置
├── LICENSE                  # 开源许可证
│
├── docs/                    # 项目文档
│   ├── project_structure.md # 项目结构文档 (本文件)
│   ├── test_report.md       # 测试报告
│   └── task_002_work_record.md # 任务二工作记录
│
├── scripts/                 # 项目脚本和文档
│   └── PRD.txt             # 产品需求文档
│
├── frontend/                # 前端React应用
│   ├── src/                # 源代码
│   ├── public/             # 静态资源
│   ├── package.json        # 前端依赖
│   ├── tsconfig.json       # TypeScript配置
│   ├── tailwind.config.js  # Tailwind配置
│   ├── Dockerfile          # 前端Docker配置
│   └── nginx.conf          # Nginx配置
│
└── backend/                 # 后端Python应用
    ├── app/                # 主应用代码
    │   ├── __init__.py
    │   ├── main.py         # FastAPI应用入口
    │   ├── database.py     # 数据库连接管理器
    │   │
    │   ├── core/           # 核心配置
    │   │   ├── __init__.py
    │   │   ├── config.py   # 应用配置 (Pydantic)
    │   │   └── celery.py   # Celery配置
    │   │
    │   ├── models/         # SQLAlchemy数据模型
    │   │   ├── __init__.py
    │   │   ├── user.py     # 用户模型 (PostgreSQL)
    │   │   └── knowledge.py # 知识关联模型
    │   │
    │   ├── schemas/        # Pydantic数据模式
    │   │   ├── __init__.py
    │   │   ├── user.py     # 用户API模式
    │   │   ├── note.py     # 笔记API模式
    │   │   └── knowledge.py # 知识关联API模式
    │   │
    │   ├── services/       # 业务逻辑服务层 ⭐ 核心实现
    │   │   ├── __init__.py
    │   │   ├── cache_service.py    # Redis缓存服务
    │   │   ├── user_service.py     # 用户CRUD服务
    │   │   ├── note_service.py     # 笔记CRUD服务
    │   │   └── knowledge_service.py # 知识关联服务
    │   │
    │   └── api/            # API路由
    │       ├── __init__.py
    │       └── v1/         # API版本1
    │           ├── __init__.py
    │           ├── api.py  # 路由聚合
    │           └── endpoints/ # 具体端点
    │               ├── __init__.py
    │               ├── auth.py    # 认证端点
    │               ├── users.py   # 用户端点
    │               └── notes.py   # 笔记端点
    │
    ├── alembic/            # 数据库迁移
    │   ├── env.py          # 迁移环境配置
    │   ├── alembic.ini     # Alembic配置
    │   └── versions/       # 迁移脚本版本
    │
    ├── tests/              # 测试套件 ⭐ 完整实现
    │   ├── __init__.py
    │   ├── conftest.py     # pytest配置和夹具
    │   ├── test_database.py # 数据库连接测试
    │   ├── test_models/    # 模型测试
    │   │   └── test_user_model.py # 用户模型测试
    │   └── test_services/  # 服务层测试
    │       ├── test_cache_service.py # 缓存服务测试
    │       └── test_user_service.py  # 用户服务测试
    │
    ├── scripts/            # 工具脚本
    │   ├── __init__.py
    │   └── create_mongodb_indexes.py # MongoDB索引创建
    │
    ├── requirements.txt    # Python依赖
    ├── pytest.ini         # pytest配置
    ├── run_tests.py       # 测试运行脚本
    ├── pyproject.toml     # Python项目配置
    └── Dockerfile         # 后端Docker配置
```

## 核心组件说明

### 数据库层 (database.py)
- **DatabaseManager**: 统一数据库连接管理器
- **PostgreSQL**: 用户数据、关系数据存储
- **MongoDB**: 笔记内容、文档数据存储
- **Redis**: 缓存和会话管理

### 服务层 (services/)
- **CacheService**: Redis缓存服务，支持会话管理、数据缓存
- **UserService**: 用户CRUD服务，集成缓存功能
- **NoteService**: 笔记CRUD服务，支持全文搜索
- **KnowledgeService**: 知识关联服务

### 模型层 (models/ & schemas/)
- **SQLAlchemy模型**: PostgreSQL表结构定义
- **Pydantic模式**: API数据验证和序列化

### API层 (api/)
- **FastAPI路由**: RESTful API端点
- **版本控制**: 支持API版本管理
- **自动文档**: Swagger/OpenAPI文档

### 测试层 (tests/)
- **单元测试**: 70个测试用例
- **集成测试**: 数据库连接测试
- **服务测试**: 业务逻辑测试
- **模型测试**: 数据模型测试

## 开发工作流

### 环境设置
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv pip install -r backend/requirements.txt

# 运行测试
cd backend && python run_tests.py
```

### 数据库迁移
```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

### 启动服务
```bash
# 启动后端
cd backend && uvicorn app.main:app --reload

# 启动前端
cd frontend && npm run dev

# Docker启动
docker-compose up -d
```

## 项目特色

### 架构优势
- **分层架构**: 清晰的模型、服务、API分层
- **依赖注入**: 松耦合的服务设计
- **缓存策略**: 多层缓存提升性能
- **错误处理**: 完善的异常处理机制

### 技术亮点
- **现代化技术栈**: FastAPI + SQLAlchemy 2.0 + Motor
- **异步编程**: 全异步架构，高并发支持
- **类型安全**: TypeScript前端 + Pydantic后端
- **容器化部署**: Docker + docker-compose

### 质量保证
- **测试覆盖**: 70个测试用例，覆盖核心逻辑
- **代码质量**: Black + isort代码格式化
- **文档完善**: 自动API文档 + 项目文档
- **版本控制**: Git + 语义化版本管理

## 部署说明

### 开发环境
- 本地开发服务器
- 热重载支持
- 调试模式

### 生产环境
- Docker容器化部署
- Nginx反向代理
- 数据库集群
- Redis集群

## 维护指南

### 代码规范
- Python: Black + isort格式化
- TypeScript: ESLint + Prettier
- 提交信息: Conventional Commits

### 测试策略
- 单元测试: 业务逻辑测试
- 集成测试: 数据库操作测试
- 端到端测试: API功能测试

### 监控日志
- 应用日志: 结构化日志记录
- 性能监控: 响应时间、错误率
- 缓存监控: 命中率、内存使用
