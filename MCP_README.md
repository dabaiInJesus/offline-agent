# 自定义 MCP 服务器使用指南

## 快速开始

### 1. 启动 MCP 服务器

```bash
# 启动完整功能服务器
python start_mcp_server.py

# 启动简化版服务器（不包含数据库和知识库）
python start_mcp_server.py --simple

# 指定端口
python start_mcp_server.py --port 8080
```

服务器将在 `http://localhost:8000/mcp` 提供服务。

### 2. 测试 MCP 客户端

```bash
# 运行客户端演示
python custom_mcp_client.py
```

## MCP 工具列表

### 系统工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_system_info` | 获取系统信息 | 无 |
| `datetime_utils` | 时间日期工具 | `action`, `timezone` |
| `calculate` | 计算器 | `expression` |

### 文件工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `read_file` | 读取文件 | `path`, `encoding` |
| `list_directory` | 列出目录 | `path`, `pattern` |
| `search_in_files` | 文件搜索 | `directory`, `keyword`, `file_pattern` |

### 数据工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `convert_data` | 数据格式转换 | `data`, `from_format`, `to_format` |

### 数据库工具（如果已连接数据库）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `query_database` | 执行 SQL 查询 | `db_name`, `sql` |
| `list_databases` | 列出数据库 | 无 |

### 知识库工具（如果已创建知识库）

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `query_knowledge_base` | 查询知识库 | `kb_name`, `query` |

## MCP 资源列表

| 资源 URI | 描述 |
|----------|------|
| `system://info` | 服务器信息 |
| `system://tools` | 工具列表 |
| `system://env` | 环境变量 |

## API 使用示例

### 使用 curl 调用工具

```bash
# 获取系统信息
curl -X POST http://localhost:8000/mcp \
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

# 计算表达式
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "calculate",
      "arguments": {
        "expression": "2 ** 10 + 100"
      }
    },
    "id": 2
  }'

# 列出目录
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_directory",
      "arguments": {
        "path": ".",
        "pattern": "*.py"
      }
    },
    "id": 3
  }'
```

### 列出工具

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 4
  }'
```

### 读取资源

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "resources/read",
    "params": {
      "uri": "system://info"
    },
    "id": 5
  }'
```

## Python 客户端使用

### 基础用法

```python
import asyncio
from custom_mcp_client import CustomMCPClient

async def main():
    # 创建客户端
    client = CustomMCPClient("http://localhost:8000/mcp")
    
    # 连接服务器
    await client.connect()
    
    # 获取系统信息
    info = await client.get_system_info()
    print(info)
    
    # 计算
    result = await client.calculate("2 ** 10 + 100")
    print(result)
    
    # 读取文件
    content = await client.read_file("config.py")
    print(content)
    
    # 断开连接
    await client.disconnect()

asyncio.run(main())
```

### 与 Agent 集成

```python
import asyncio
from custom_mcp_client import CustomMCPClient
from agent.factory import create_react_agent
from models.ollama_model import get_llm

async def main():
    # 连接 MCP 服务器
    client = CustomMCPClient("http://localhost:8000/mcp")
    await client.connect()
    
    # 创建 Agent
    agent = create_react_agent(name="mcp_agent", llm=get_llm())
    
    # 将 MCP 工具注册到 Agent
    agent.register_tool(
        "get_system_info",
        lambda: asyncio.run(client.get_system_info()),
        "获取系统信息"
    )
    
    agent.register_tool(
        "calculate",
        lambda expr: asyncio.run(client.calculate(expr)),
        "计算表达式"
    )
    
    # 使用 Agent
    result = agent.run("计算 1234 * 5678")
    print(result)
    
    await client.disconnect()

asyncio.run(main())
```

## 扩展自定义工具

在 `custom_mcp_server.py` 中添加新工具：

```python
def my_custom_tool(param1: str, param2: int):
    """我的自定义工具"""
    return {
        "result": f"处理 {param1}，数值 {param2}"
    }

self.server.register_tool(
    "my_custom_tool",
    my_custom_tool,
    "工具描述",
    {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1"},
            "param2": {"type": "integer", "description": "参数2"}
        },
        "required": ["param1", "param2"]
    }
)
```

## 配置文件

在 `.env` 文件中配置数据库连接，MCP 服务器会自动加载：

```env
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=mydb
MYSQL_USER=root
MYSQL_PASSWORD=password

# 其他数据库...
```

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP 客户端                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CustomMCPClient                                      │  │
│  │  • connect()                                          │  │
│  │  • call_tool()                                        │  │
│  │  • get_system_info()                                  │  │
│  │  • calculate()                                        │  │
│  │  • read_file()                                        │  │
│  │  • ...                                                │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/JSON-RPC 2.0
┌───────────────────────────┴─────────────────────────────────┐
│                      MCP 服务器                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CustomMCPServer                                      │  │
│  │                                                       │  │
│  │  工具:                                                │  │
│  │  • get_system_info    • read_file                     │  │
│  │  • list_directory     • search_in_files               │  │
│  │  • convert_data       • calculate                     │  │
│  │  • datetime_utils     • query_database                │  │
│  │  • query_knowledge_base                               │  │
│  │                                                       │  │
│  │  资源:                                                │  │
│  │  • system://info      • system://tools                │  │
│  │  • system://env                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 故障排除

### 端口被占用

```bash
# 查找占用 8000 端口的进程
lsof -i :8000

# 使用其他端口启动
python start_mcp_server.py --port 8080
```

### 连接失败

1. 检查服务器是否已启动
2. 检查防火墙设置
3. 确认 URL 和端口正确

### 工具调用失败

1. 检查工具参数是否正确
2. 查看服务器日志获取详细错误信息
3. 使用 `tools/list` 确认工具存在

## 相关文件

- `custom_mcp_server.py` - MCP 服务器实现
- `custom_mcp_client.py` - MCP 客户端实现
- `start_mcp_server.py` - 服务器启动脚本
- `mcp/` - MCP 协议核心模块
