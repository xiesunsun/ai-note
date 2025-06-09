# AI闪念笔记

一款专为信息碎片化时代设计的智能笔记应用，旨在解决现代人获取信息杂乱、缺乏整理时间的痛点。

## 🌟 核心功能

- **即时笔记记录**: 简洁干净的界面，支持Markdown格式和实时渲染
- **AI辅助标签**: 自动为笔记添加标签分类，一键润色功能
- **智能知识关联**: 基于标签自动分类整理，推荐相关知识点
- **知识脉络结构图**: 可视化展示知识间的关联性
- **艾宾浩斯记忆助手**: 根据遗忘曲线智能提醒复习

## 🏗️ 技术架构

### 前端
- **框架**: React 18 + TypeScript
- **样式**: TailwindCSS
- **构建工具**: Create React App
- **代码规范**: ESLint + Prettier

### 后端
- **框架**: Python FastAPI
- **数据库**: PostgreSQL + MongoDB
- **缓存**: Redis
- **任务队列**: Celery
- **AI集成**: OpenAI GPT / Anthropic Claude

### 基础设施
- **容器化**: Docker + Docker Compose
- **开发环境**: VS Code + Remote Development

## 🚀 快速开始

### 环境要求
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### 开发环境设置

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-note
```

2. **启动数据库服务**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

3. **前端开发**
```bash
cd frontend
npm install
npm start
```

4. **后端开发**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 生产环境部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 📁 项目结构

```
ai-note/
├── frontend/                 # React前端应用
│   ├── public/              # 静态资源
│   ├── src/                 # 源代码
│   ├── package.json         # 依赖配置
│   └── Dockerfile           # 前端容器配置
├── backend/                 # FastAPI后端应用
│   ├── app/                 # 应用代码
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   └── main.py         # 应用入口
│   ├── requirements.txt     # Python依赖
│   └── Dockerfile          # 后端容器配置
├── docker-compose.yml       # 生产环境配置
├── docker-compose.dev.yml   # 开发环境配置
└── README.md               # 项目说明
```

## 🔧 开发指南

### 前端开发
- 使用TypeScript进行类型安全开发
- 遵循React Hooks最佳实践
- 使用TailwindCSS进行样式开发
- 运行 `npm run lint` 检查代码规范

### 后端开发
- 使用FastAPI异步框架
- 遵循RESTful API设计原则
- 使用Black进行代码格式化
- 运行 `black .` 和 `isort .` 格式化代码

### 数据库
- PostgreSQL: 存储结构化用户数据
- MongoDB: 存储灵活的笔记内容
- Redis: 缓存和会话管理

## 🧪 测试

### 前端测试
```bash
cd frontend
npm test
```

### 后端测试
```bash
cd backend
pytest
```

## 📝 API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- [项目需求文档](scripts/PRD.txt)
- [开发任务列表](.taskmaster/tasks/)
- [技术文档](docs/)

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论
