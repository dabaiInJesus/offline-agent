# Offline Agent Web 应用

基于 FastAPI + Vue 3 + TailwindCSS 的交互式 Web 界面。

## 技术栈

- **后端**: FastAPI (Python)
- **前端**: Vue 3 + Vue Router + Pinia
- **样式**: TailwindCSS
- **图标**: Heroicons

## 目录结构

```
webapp/
├── backend/
│   └── main.py              # FastAPI 后端
├── frontend/
│   ├── public/              # 静态资源
│   ├── src/
│   │   ├── assets/          # 样式文件
│   │   ├── components/      # 组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── views/           # 页面视图
│   │   ├── App.vue          # 根组件
│   │   └── main.js          # 入口文件
│   ├── package.json         # 依赖配置
│   ├── tailwind.config.js   # Tailwind 配置
│   └── vue.config.js        # Vue CLI 配置
├── start_webapp.py          # 启动脚本
└── WEBAPP_README.md         # 本文档
```

## 快速开始

### 方式1: 使用启动脚本（推荐）

```bash
cd webapp
python start_webapp.py
```

这将同时启动后端和前端开发服务器。

### 方式2: 手动启动

**启动后端:**
```bash
cd webapp/backend
python main.py
```

**启动前端:**
```bash
cd webapp/frontend

# 首次运行需要安装依赖
npm install

# 启动开发服务器
npm run serve
```

### 访问应用

- **Web 界面**: http://localhost:8080
- **API 文档**: http://localhost:8000/docs
- **API 端点**: http://localhost:8000

## 功能模块

### 1. 控制台 (Dashboard)
- 系统状态概览
- 统计卡片
- 快速操作入口
- 最近活动

### 2. 对话 (Chat)
- 与 AI 智能体对话
- 支持多种 Agent 类型（ReAct、Tool、Graph）
- 可关联知识库和数据库
- 实时消息展示

### 3. 数据库 (Database)
- 查看数据库连接
- 浏览表结构
- 执行 SQL 查询
- 查询历史记录

### 4. 知识库 (Knowledge Base)
- 管理知识库
- 文档上传
- 智能检索
- 结果展示

### 5. 智能体 (Agent)
- 创建和管理 Agent
- 配置系统提示词
- 查看执行历史

### 6. 技能 (Skills)
- 浏览可用技能
- 执行技能
- 查看执行结果

### 7. 设置 (Settings)
- 主题切换（浅色/深色）
- 系统配置
- 模型管理

## API 接口

### 系统状态
- `GET /api/status` - 获取系统状态

### 对话
- `POST /api/chat` - 发送消息
- `WebSocket /ws/chat` - WebSocket 实时对话

### 数据库
- `GET /api/databases` - 列出数据库
- `GET /api/database/{db_name}/tables` - 获取表列表
- `GET /api/database/{db_name}/schema/{table_name}` - 获取表结构
- `POST /api/database/query` - 执行 SQL 查询

### 知识库
- `GET /api/knowledge-bases` - 列出知识库
- `POST /api/knowledge-base/query` - 查询知识库
- `POST /api/knowledge-base/{kb_name}/documents` - 添加文档

### Agent
- `GET /api/agents/types` - 列出 Agent 类型
- `POST /api/agent/create` - 创建 Agent
- `POST /api/agent/{agent_name}/run` - 运行 Agent

### 技能
- `GET /api/skills` - 列出技能
- `POST /api/skill/execute` - 执行技能

### 模型
- `GET /api/models` - 列出模型
- `POST /api/model/pull` - 拉取模型

## 开发指南

### 添加新页面

1. 在 `src/views/` 创建页面组件
2. 在 `src/router/index.js` 添加路由
3. 在 `src/components/layout/Sidebar.vue` 添加菜单项

### 添加新组件

1. 在 `src/components/` 创建组件
2. 使用 TailwindCSS 进行样式设计
3. 在页面中导入使用

### 状态管理

使用 Pinia 进行状态管理，store 文件放在 `src/stores/` 目录：

- `app.js` - 应用状态
- `chat.js` - 对话状态
- `database.js` - 数据库状态
- `knowledgeBase.js` - 知识库状态

### 样式规范

- 使用 TailwindCSS 工具类
- 支持深色模式（使用 `dark:` 前缀）
- 自定义组件样式在 `tailwind.css` 中定义

## 构建部署

### 构建前端

```bash
cd webapp/frontend
npm run build
```

构建后的文件在 `frontend/dist/` 目录。

### 部署

1. 构建前端
2. 将 `frontend/dist/` 复制到后端目录
3. 启动后端服务
4. 访问 http://localhost:8000

## 常见问题

### 端口冲突

如果端口被占用，可以修改：
- 后端端口: `backend/main.py` 中的 `uvicorn.run(app, host="0.0.0.0", port=8000)`
- 前端端口: `frontend/vue.config.js` 中的 `devServer.port`

### 跨域问题

开发环境已配置代理，生产环境需要配置 CORS：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 依赖安装失败

确保 Node.js 版本 >= 16：

```bash
node -v
npm -v
```

## 截图预览

（此处可以添加应用截图）

## 贡献

欢迎提交 Issue 和 Pull Request！
