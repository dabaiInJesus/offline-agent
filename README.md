# Offline Agent - 本地 AI 智能体平台

> 🤖 基于 LangChain + LangGraph 的本地/云端 AI 智能体平台，支持 Ollama 和 DeepSeek 双模型切换，多数据库、知识库 RAG、MCP 协议

## 功能特性

- 🔮 **本地大模型** - 通过 Ollama 连接 qwen2.5/llama 等开源模型，完全离线运行
- ☁️ **云端模型** - 支持 DeepSeek API，在线学习更方便
- 🧠 **多种 Agent** - 支持 ReAct、Tool、PlanExecute、Graph 等多种 Agent 架构
- 📚 **知识库 RAG** - 支持 PDF/Word/Excel 等文档的向量检索增强生成
- 💾 **多数据库** - 支持 Oracle、MySQL、PostgreSQL、Hive 等数据库的 SQL 执行
- 🔗 **MCP 协议** - 支持 Model Context Protocol，可扩展工具集
- 🎯 **技能系统** - 可注册的 AgentSkill 技能体系
- 🌐 **Web 界面** - FastAPI + Vue 构建的现代化管理界面

## 系统要求

- **OS**: Linux (Ubuntu 20.04+) / macOS / Windows
- **Python**: 3.10+
- **Node.js**: 16+ (前端需要)
- **RAM**: 16GB+ (推荐 32GB，用于运行大模型)
- **GPU**: NVIDIA GPU with CUDA (可选，提升推理速度)

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/dabaiInJesus/offline-agent.git
cd offline-agent

# 启动所有服务
docker-compose up -d

# 访问 Web 界面
open http://localhost:8080
```

### 方式二：手动安装

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装 Node.js
# https://nodejs.org/

# 3. 配置模型（二选一）

# 方式 A: 使用 Ollama 本地模型（离线）
# 安装 Ollama: https://ollama.ai/
ollama pull qwen2.5:32b
ollama serve

# 方式 B: 使用 DeepSeek 云端模型（联网）
# 申请 API: https://platform.deepseek.com/
# 设置环境变量: export DEEPSEEK_API_KEY=your-key

# 4. 启动服务
python run.py
```

## 配置说明

复制配置文件并修改：

```bash
cp .env.example .env
```

主要配置项：

```env
# 模型切换（ollama 或 deepseek）
ACTIVE_PROVIDER=ollama  # 或 deepseek

# Ollama 配置（离线）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b

# DeepSeek 配置（联网）
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_MODEL=deepseek-chat  # 或 deepseek-coder

# 向量数据库路径
VECTOR_DB_PATH=./vector_db

# 知识库路径
KNOWLEDGE_BASE_PATH=./knowledge_base
```

## 使用指南

### 启动服务

```bash
# 一键启动所有服务
python run.py

# 仅启动后端
python run.py --backend-only

# 仅启动前端
python run.py --frontend-only

# 启动所有服务（包括 MCP）
python run.py --with-mcp
```

### Web 界面

启动后访问 http://localhost:8080

功能模块：
- **对话** - 与 AI 智能体对话
- **数据库** - 执行 SQL 查询
- **知识库** - 上传文档进行 RAG 问答
- **MCP** - 调用 MCP 工具

### API 调用

```bash
# 获取系统信息
curl http://localhost:8000/api/system/info

# 对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "agent_type": "react"}'
```

## 项目结构

```
offline-agent/
├── agent/              # Agent 相关代码
│   ├── base.py         # Agent 基类
│   ├── factory.py      # Agent 工厂
│   ├── react_agent.py  # ReAct Agent
│   ├── tool_agent.py   # Tool Agent
│   └── graph_agent.py  # Graph Agent
├── models/              # 大模型封装
│   └── ollama_model.py # Ollama 模型接口
├── database/            # 数据库连接
├── vectorstore/        # 向量数据库
├── knowledge_base/      # 知识库 RAG
├── skills/              # 技能系统
├── mcp/                 # MCP 协议实现
├── webapp/              # Web 应用
│   ├── backend/        # FastAPI 后端
│   └── frontend/       # Vue 前端
├── config.py           # 配置文件
├── main.py             # 主程序
└── run.py              # 启动脚本
```

## 支持的模型

推荐使用以下 Ollama 模型：

| 模型 | 参数量 | 内存需求 | 适用场景 |
|------|--------|----------|----------|
| qwen2.5:32b | 32B | ~20GB | 通用对话、代码 |
| deepseek-chat | V3 | - | 最新一代，性能超越 GPT-4o |
| deepseek-coder | V3 | - | 代码专用
| qwen2.5-coder:32b | 32B | ~20GB | 代码生成 |
| llama3.1:70b | 70B | ~40GB | 复杂推理 |
| phi3:14b | 14B | ~8GB | 轻量对话 |

## 常见问题

### 1. 内存不足
确保系统有足够内存运行模型。32B 模型建议 16GB+ RAM。

### 2. Ollama 连接失败
```bash
# 确保 Ollama 服务运行
ollama serve

# 测试 API
curl http://localhost:11434/api/generate \
  -d '{"model": "qwen2.5:32b", "prompt": "你好"}'
```

### 3. 向量库加载失败
安装 FAISS 或 ChromaDB：
```bash
pip install faiss-cpu  # 或 faiss-gpu (有 GPU)
pip install chromadb
```

## 开发指南

```bash
# 克隆并进入目录
git clone https://github.com/dabaiInJesus/offline-agent.git
cd offline-agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
pytest tests/

# 代码格式
black .
```

## 许可证

MIT License

## 联系方式

- GitHub Issues: https://github.com/dabaiInJesus/offline-agent/issues
