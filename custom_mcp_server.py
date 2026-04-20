
"""
自定义 MCP 服务器示例
展示如何创建带有自定义工具和资源的 MCP 服务器
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

from mcp.server import MCPServer, FastAPIMCPServer, create_mcp_server_with_local_tools
from database.db_manager import db_manager
from knowledge_base.knowledge_base import kb_manager


class CustomMCPServer:
    """
    自定义 MCP 服务器
    整合本地数据库、知识库和自定义工具
    """
    
    def __init__(self):
        self.server = MCPServer(
            name="custom-offline-agent",
            version="1.0.0"
        )
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """设置自定义工具"""
        
        # 1. 系统信息工具
        def get_system_info():
            """获取系统信息"""
            import platform
            import psutil
            
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
                "memory_available": f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
                "disk_usage": f"{psutil.disk_usage('/').percent}%",
                "timestamp": datetime.now().isoformat()
            }
        
        self.server.register_tool(
            "get_system_info",
            get_system_info,
            "获取服务器系统信息，包括 CPU、内存、磁盘使用情况",
            {
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        # 2. 文件操作工具
        def read_file(path: str, encoding: str = "utf-8"):
            """读取文件内容"""
            try:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
                return {
                    "success": True,
                    "content": content,
                    "size": len(content),
                    "path": os.path.abspath(path)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        self.server.register_tool(
            "read_file",
            read_file,
            "读取指定路径的文本文件",
            {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "文件编码，默认 utf-8"
                    }
                },
                "required": ["path"]
            }
        )
        
        # 3. 目录列表工具
        def list_directory(path: str = ".", pattern: str = "*"):
            """列出目录内容"""
            try:
                import glob
                from pathlib import Path
                
                target_path = Path(path)
                if not target_path.exists():
                    return {"success": False, "error": "路径不存在"}
                
                items = []
                for item in target_path.glob(pattern):
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                
                return {
                    "success": True,
                    "path": str(target_path.absolute()),
                    "items": items,
                    "total": len(items)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self.server.register_tool(
            "list_directory",
            list_directory,
            "列出指定目录的内容",
            {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径，默认为当前目录"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "文件匹配模式，默认为 *"
                    }
                },
                "required": []
            }
        )
        
        # 4. 文本搜索工具
        def search_in_files(directory: str, keyword: str, file_pattern: str = "*.txt"):
            """在文件中搜索关键词"""
            try:
                from pathlib import Path
                
                results = []
                target_path = Path(directory)
                
                for file_path in target_path.rglob(file_pattern):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if keyword in content:
                                    # 找到关键词上下文
                                    lines = content.split('\n')
                                    matches = []
                                    for i, line in enumerate(lines):
                                        if keyword in line:
                                            matches.append({
                                                "line": i + 1,
                                                "content": line.strip()
                                            })
                                    
                                    results.append({
                                        "file": str(file_path),
                                        "matches": matches,
                                        "match_count": len(matches)
                                    })
                        except:
                            pass
                
                return {
                    "success": True,
                    "keyword": keyword,
                    "directory": str(target_path.absolute()),
                    "results": results,
                    "total_files": len(results)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self.server.register_tool(
            "search_in_files",
            search_in_files,
            "在指定目录的文件中搜索关键词",
            {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "搜索目录"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "文件匹配模式，默认为 *.txt"
                    }
                },
                "required": ["directory", "keyword"]
            }
        )
        
        # 5. 数据转换工具
        def convert_data(data: str, from_format: str, to_format: str):
            """数据格式转换"""
            try:
                # 解析输入
                if from_format == "json":
                    import json
                    parsed = json.loads(data)
                elif from_format == "csv":
                    import csv
                    import io
                    f = io.StringIO(data)
                    reader = csv.DictReader(f)
                    parsed = list(reader)
                elif from_format == "yaml":
                    import yaml
                    parsed = yaml.safe_load(data)
                else:
                    return {"success": False, "error": f"不支持的输入格式: {from_format}"}
                
                # 转换输出
                if to_format == "json":
                    import json
                    result = json.dumps(parsed, ensure_ascii=False, indent=2)
                elif to_format == "yaml":
                    import yaml
                    result = yaml.dump(parsed, allow_unicode=True)
                elif to_format == "csv":
                    import csv
                    import io
                    if isinstance(parsed, list) and len(parsed) > 0:
                        f = io.StringIO()
                        writer = csv.DictWriter(f, fieldnames=parsed[0].keys())
                        writer.writeheader()
                        writer.writerows(parsed)
                        result = f.getvalue()
                    else:
                        result = str(parsed)
                else:
                    return {"success": False, "error": f"不支持的输出格式: {to_format}"}
                
                return {
                    "success": True,
                    "result": result,
                    "from_format": from_format,
                    "to_format": to_format
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self.server.register_tool(
            "convert_data",
            convert_data,
            "在 JSON、CSV、YAML 格式之间转换数据",
            {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "要转换的数据"
                    },
                    "from_format": {
                        "type": "string",
                        "enum": ["json", "csv", "yaml"],
                        "description": "源格式"
                    },
                    "to_format": {
                        "type": "string",
                        "enum": ["json", "csv", "yaml"],
                        "description": "目标格式"
                    }
                },
                "required": ["data", "from_format", "to_format"]
            }
        )
        
        # 6. 计算器工具
        def calculate(expression: str):
            """安全计算数学表达式"""
            try:
                # 安全的计算环境
                allowed_names = {
                    "abs": abs,
                    "max": max,
                    "min": min,
                    "sum": sum,
                    "pow": pow,
                    "round": round,
                    "len": len
                }
                
                # 使用 eval 计算（在安全环境下）
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                
                return {
                    "success": True,
                    "expression": expression,
                    "result": result,
                    "type": type(result).__name__
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        self.server.register_tool(
            "calculate",
            calculate,
            "计算数学表达式，支持基本运算和常用函数",
            {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '1 + 2 * 3' 或 'pow(2, 10)'"
                    }
                },
                "required": ["expression"]
            }
        )
        
        # 7. 时间日期工具
        def datetime_utils(action: str, timezone: str = "UTC"):
            """时间日期工具"""
            from datetime import datetime
            from zoneinfo import ZoneInfo
            
            try:
                tz = ZoneInfo(timezone)
                now = datetime.now(tz)
                
                if action == "now":
                    return {
                        "datetime": now.isoformat(),
                        "date": now.strftime("%Y-%m-%d"),
                        "time": now.strftime("%H:%M:%S"),
                        "timezone": timezone,
                        "timestamp": now.timestamp()
                    }
                elif action == "date":
                    return {"date": now.strftime("%Y-%m-%d")}
                elif action == "time":
                    return {"time": now.strftime("%H:%M:%S")}
                elif action == "weekday":
                    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                    return {
                        "weekday": weekdays[now.weekday()],
                        "weekday_num": now.weekday() + 1
                    }
                else:
                    return {"error": f"未知的操作: {action}"}
            except Exception as e:
                return {"error": str(e)}
        
        self.server.register_tool(
            "datetime_utils",
            datetime_utils,
            "获取时间日期信息",
            {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["now", "date", "time", "weekday"],
                        "description": "操作类型"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "时区，如 'Asia/Shanghai'、'UTC'",
                        "default": "UTC"
                    }
                },
                "required": ["action"]
            }
        )
        
        logger.info("已注册 7 个自定义工具")
    
    def _setup_resources(self):
        """设置资源"""
        
        # 1. 服务器信息资源
        def server_info():
            return {
                "name": "custom-offline-agent",
                "version": "1.0.0",
                "description": "自定义 MCP 服务器，提供系统工具和数据处理能力",
                "tools_count": len(self.server.list_tools()),
                "resources_count": len(self.server.list_resources()),
                "uptime": datetime.now().isoformat()
            }
        
        self.server.register_resource("system://info", server_info)
        
        # 2. 工具列表资源
        def tools_list():
            tools = self.server.list_tools()
            return {
                "count": len(tools),
                "tools": [
                    {
                        "name": t["name"],
                        "description": t["description"]
                    }
                    for t in tools
                ]
            }
        
        self.server.register_resource("system://tools", tools_list)
        
        # 3. 环境变量资源（安全过滤）
        def safe_env():
            """获取安全的环境变量"""
            safe_vars = ["PATH", "HOME", "USER", "SHELL", "LANG", "TZ"]
            return {k: os.environ.get(k, "") for k in safe_vars if k in os.environ}
        
        self.server.register_resource("system://env", safe_env)
        
        logger.info("已注册 3 个资源")
    
    def get_server(self) -> MCPServer:
        """获取 MCP 服务器实例"""
        return self.server
    
    def run_http(self, host: str = "0.0.0.0", port: int = 8000):
        """运行 HTTP 服务"""
        fastapi_server = FastAPIMCPServer(self.server)
        fastapi_server.run(host=host, port=port)


def create_full_featured_mcp_server():
    """
    创建功能完整的 MCP 服务器
    包含本地数据库和知识库工具
    """
    # 先连接数据库和知识库（如果配置了）
    try:
        from config import mysql_config
        if mysql_config.host and mysql_config.database:
            db_manager.quick_connect_mysql("mysql")
            logger.info("已连接 MySQL 数据库")
    except:
        pass
    
    # 创建服务器
    custom_server = CustomMCPServer()
    server = custom_server.get_server()
    
    # 添加本地数据库工具（如果已连接）
    if db_manager.list_databases():
        def query_database(db_name: str, sql: str):
            """查询数据库"""
            db = db_manager.get(db_name)
            if not db:
                return {"error": f"数据库 '{db_name}' 不存在"}
            try:
                result = db.execute(sql)
                return {"success": True, "data": result, "count": len(result)}
            except Exception as e:
                return {"error": str(e)}
        
        server.register_tool(
            "query_database",
            query_database,
            "执行 SQL 查询",
            {
                "type": "object",
                "properties": {
                    "db_name": {"type": "string", "description": "数据库名称"},
                    "sql": {"type": "string", "description": "SQL 查询语句"}
                },
                "required": ["db_name", "sql"]
            }
        )
        
        def list_databases():
            """列出所有数据库"""
            return db_manager.list_databases()
        
        server.register_tool("list_databases", list_databases, "列出所有已连接的数据库")
    
    # 添加知识库工具
    if kb_manager.list_knowledge_bases():
        def query_knowledge_base(kb_name: str, query: str):
            """查询知识库"""
            kb = kb_manager.get(kb_name)
            if not kb:
                return {"error": f"知识库 '{kb_name}' 不存在"}
            try:
                result = kb.query(query)
                return {"success": True, "result": result}
            except Exception as e:
                return {"error": str(e)}
        
        server.register_tool(
            "query_knowledge_base",
            query_knowledge_base,
            "查询知识库",
            {
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "知识库名称"},
                    "query": {"type": "string", "description": "查询问题"}
                },
                "required": ["kb_name", "query"]
            }
        )
    
    return server


# 测试客户端
async def test_client():
    """测试 MCP 客户端"""
    from mcp.client import MCPClient, MCPServerConfig
    
    config = MCPServerConfig(
        name="local",
        url="http://localhost:8000/mcp"
    )
    
    client = MCPClient(config)
    
    if await client.connect():
        print("✓ 连接成功")
        
        # 列出工具
        tools = client.list_tools()
        print(f"\n可用工具 ({len(tools)}个):")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # 测试工具调用
        print("\n测试工具调用:")
        
        # 系统信息
        result = await client.call_tool("get_system_info", {})
        print(f"\n系统信息: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
        
        # 计算器
        result = await client.call_tool("calculate", {"expression": "2 ** 10 + 100"})
        print(f"\n计算结果: {result}")
        
        # 时间
        result = await client.call_tool("datetime_utils", {"action": "now", "timezone": "Asia/Shanghai"})
        print(f"\n当前时间: {result}")
        
        await client.disconnect()
    else:
        print("✗ 连接失败")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "client":
        # 运行测试客户端
        print("启动 MCP 测试客户端...")
        asyncio.run(test_client())
    else:
        # 运行服务器
        print("""
╔══════════════════════════════════════════════════════════════╗
║              自定义 MCP 服务器                               ║
║                                                              ║
║  工具列表:                                                   ║
║    • get_system_info    - 获取系统信息                     ║
║    • read_file          - 读取文件                         ║
║    • list_directory     - 列出目录                         ║
║    • search_in_files    - 文件搜索                         ║
║    • convert_data       - 数据格式转换                     ║
║    • calculate          - 计算器                           ║
║    • datetime_utils     - 时间日期工具                     ║
║    • query_database     - 数据库查询（如果已连接）         ║
║    • query_knowledge_base - 知识库查询（如果已创建）       ║
║                                                              ║
║  资源列表:                                                   ║
║    • system://info      - 服务器信息                       ║
║    • system://tools     - 工具列表                         ║
║    • system://env       - 环境变量                         ║
║                                                              ║
║  启动地址: http://localhost:8000/mcp                        ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        server = create_full_featured_mcp_server()
        custom_server = CustomMCPServer()
        custom_server.run_http(host="0.0.0.0", port=8000)
