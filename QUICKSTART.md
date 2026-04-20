# Offline Agent 快速启动指南

## 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **Ollama**: 本地运行大模型（可选，用于 AI 功能）

## 安装步骤

### 1. 安装 Python 依赖

```bash
# 在项目根目录执行
pip install -r requirements.txt
```

### 2. 安装 Node.js

访问 https://nodejs.org/ 下载并安装 Node.js 16 或更高版本。

验证安装：
```bash
node --version
npm --version
```

### 3. 配置环境变量（可选）

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，配置你的数据库连接等信息
```

### 4. 启动 Ollama（可选）

如果使用本地大模型，需要先启动 Ollama：

```bash
# 安装 Ollama 后，拉取模型
ollama pull qwen2.5:14b

# 启动服务
ollama serve
```

## 启动项目

### 方式1: 一键启动（推荐）

```bash
python run.py
```

这将同时启动：
- FastAPI 后端 (http://localhost:8000)
- Vue 前端 (http://localhost:8080)

### 方式2: 分别启动

**仅启动后端：**
```bash
python run.py --backend-only
```

**仅启动前端：**
```bash
python run.py --frontend-only
```

**启动所有服务（包括 MCP）：**
```bash
python run.py --with-mcp
```

### 方式3: 手动启动

**终端1 - 启动后端：**
```bash
cd webapp/backend
python main.py
```

**终端2 - 启动前端：**
```bash
cd webapp/frontend
npm install  # 首次运行
npm run serve
```

**终端3 - 启动 MCP 服务器（可选）：**
```bash
python start_mcp_server.py
```

## 访问应用

启动成功后，在浏览器中访问：

- **Web 界面**: http://localhost:8080
- **API 文档**: http://localhost:8000/docs
- **MCP 服务**: http://localhost:8001/mcp

## 功能测试

### 1. 测试控制台

打开 http://localhost:8080，你应该能看到：
- 系统状态概览
- 统计卡片
- 快速操作按钮

### 2. 测试对话

点击左侧菜单的"对话"：
- 输入消息并发送
- 尝试选择不同的 Agent 类型
- 测试知识库和数据库关联

### 3. 测试数据库

点击"数据库"菜单：
- 配置数据库连接（需要在 .env 中配置）
- 执行 SQL 查询
- 查看表结构

### 4. 测试知识库

点击"知识库"菜单：
- 创建知识库
- 上传文档
- 进行检索问答

### 5. 测试 MCP

```bash
# 测试 MCP 服务器
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_system_info",
      "arguments": {}
    },
    "id": 1
  }'
```

## 常见问题

### 端口被占用

如果端口被占用，可以修改：

**后端端口** - `webapp/backend/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # 修改这里的端口
```

**前端端口** - `webapp/frontend/vue.config.js`:
```javascript
devServer: {
  port: 8080,  // 修改这里的端口
}
```

### 依赖安装失败

**Python 依赖：**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Node 依赖：**
```bash
cd webapp/frontend

# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### CORS 错误

开发环境已配置代理，如果仍有问题，检查：
1. 后端是否正确启动
2. 前端代理配置是否正确

### Ollama 连接失败

确保 Ollama 服务已启动：
```bash
# 检查 Ollama 状态
ollama list

# 如果没有模型，先拉取
ollama pull qwen2.5:14b
```

## 项目结构

```
offline-agent/
├── config.py                 # 配置文件
├── requirements.txt          # Python 依赖
├── run.py                    # 一键启动脚本
├── main.py                   # 项目入口
│
├── models/                   # 大模型模块
├── database/                 # 数据库模块
├── vectorstore/              # 向量数据库
├── knowledge_base/           # 知识库
├── agent/                    # Agent 模块
├── skills/                   # 技能系统
├── mcp/                      # MCP 协议
│
├── webapp/                   # Web 应用
│   ├── backend/              # FastAPI 后端
│   ├── frontend/             # Vue 前端
│   └── start_webapp.py       # Web 启动脚本
│
├── custom_mcp_server.py      # 自定义 MCP 服务器
├── custom_mcp_client.py      # MCP 客户端示例
├── start_mcp_server.py       # MCP 启动脚本
│
└── examples/                 # 示例代码
    ├── example_basic.py
    ├── example_database.py
    ├── example_rag.py
    ├── example_agent.py
    └── example_mcp.py
```

## 下一步

1. 配置数据库连接（.env 文件）
2. 创建知识库并上传文档
3. 尝试不同的 Agent 类型
4. 开发自定义技能
5. 扩展 MCP 工具

## 获取帮助

- 查看 API 文档: http://localhost:8000/docs
- 查看示例代码: `examples/` 目录
- 查看详细文档: `MCP_README.md`, `WEBAPP_README.md`

## 停止服务

按 `Ctrl+C` 即可停止所有服务。
