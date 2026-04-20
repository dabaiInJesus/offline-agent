"""
MCP (Model Context Protocol) 示例
展示 MCP 客户端和服务器的使用
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()


def example_mcp_client():
    """示例：MCP 客户端"""
    print("\n" + "="*60)
    print("示例1: MCP 客户端连接")
    print("="*60)
    
    print("""
    import asyncio
    from mcp.client import MCPClient, MCPServerConfig
    
    async def use_mcp_client():
        # 配置 MCP 服务器
        config = MCPServerConfig(
            name="my_mcp_server",
            url="http://localhost:3000/mcp",
            api_key="your-api-key"  # 可选
        )
        
        # 创建客户端
        client = MCPClient(config)
        
        # 连接服务器
        success = await client.connect()
        if success:
            print("连接成功！")
            
            # 列出可用工具
            tools = client.list_tools()
            for tool in tools:
                print(f"工具: {tool['name']}")
                print(f"描述: {tool['description']}")
            
            # 调用工具
            result = await client.call_tool(
                "get_weather",
                {"city": "北京"}
            )
            print(f"结果: {result}")
            
            # 列出资源
            resources = await client.list_resources()
            for resource in resources:
                print(f"资源: {resource['uri']}")
            
            # 读取资源
            content = await client.read_resource("file:///data/info.txt")
            print(f"内容: {content}")
            
            # 断开连接
            await client.disconnect()
    
    asyncio.run(use_mcp_client())
    """)


def example_mcp_server():
    """示例：MCP 服务器"""
    print("\n" + "="*60)
    print("示例2: MCP 服务器")
    print("="*60)
    
    print("""
    from mcp.server import MCPServer, FastAPIMCPServer
    
    # 创建 MCP 服务器
    server = MCPServer(name="my_local_server")
    
    # 注册工具
    def calculate_sum(a: int, b: int) -> int:
        \"\"\"计算两个数的和\"\"\"
        return a + b
    
    server.register_tool(
        "calculate_sum",
        calculate_sum,
        "计算两个数的和",
        {
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"}
            },
            "required": ["a", "b"]
        }
    )
    
    # 注册资源
    def get_system_info():
        \"\"\"获取系统信息\"\"\"
        import platform
        return {
            "os": platform.system(),
            "python": platform.python_version()
        }
    
    server.register_resource("system://info", get_system_info)
    
    # 方式1: 使用 FastAPI 提供 HTTP 服务
    fastapi_server = FastAPIMCPServer(server)
    app = fastapi_server.create_app()
    fastapi_server.run(host="0.0.0.0", port=8000)
    你好
    # 方式2: 手动处理请求（用于集成到其他框架）
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "calculate_sum",
            "arguments": {"a": 10, "b": 20}
        },
        "id": 1
    }
    response = server.handle_request(request)
    print(response)
    """)


def example_mcp_with_local_tools():
    """示例：将本地工具暴露为 MCP 服务"""
    print("\n" + "="*60)
    print("示例3: 本地工具 MCP 化")
    print("="*60)
    
    print("""
    from mcp.server import create_mcp_server_with_local_tools
    from database.db_manager import db_manager
    from knowledge_base.knowledge_base import kb_manager
    
    # 先连接一些数据库和知识库
    db_manager.quick_connect_mysql("mysql_db")
    
    # 创建包含本地工具的 MCP 服务器
    server = create_mcp_server_with_local_tools(
        db_manager=db_manager,
        kb_manager=kb_manager
    )
    
    # 现在其他 MCP 客户端可以调用:
    # - query_database: 查询数据库
    # - list_databases: 列出数据库
    # - query_knowledge_base: 查询知识库
    # - list_knowledge_bases: 列出知识库
    
    # 启动 HTTP 服务
    from mcp.server import FastAPIMCPServer
    fastapi_server = FastAPIMCPServer(server)
    fastapi_server.run(port=8000)
    """)


def example_mcp_session():
    """示例：MCP 会话管理"""
    print("\n" + "="*60)
    print("示例4: MCP 会话管理")
    print("="*60)
    
    print("""
    import asyncio
    from mcp.session import create_mcp_session, session_manager
    
    async def use_session():
        # 创建会话
        session = await create_mcp_session(
            server_name="remote_server",
            url="http://localhost:3000/mcp"
        )
        
        print(f"会话 ID: {session.session_id}")
        
        # 调用工具（自动记录到会话历史）
        result = await session.invoke_tool(
            "search",
            {"query": "Python programming"}
        )
        
        # 读取资源
        content = await session.read_resource("doc://guide")
        
        # 获取会话历史
        history = session.get_history()
        for item in history:
            print(f"{item['timestamp']}: {item['type']}")
        
        # 获取统计信息
        stats = session.get_stats()
        print(f"总交互次数: {stats['total_interactions']}")
        print(f"成功调用: {stats['successful_calls']}")
        
        # 关闭会话
        await session.disconnect()
    
    asyncio.run(use_session())
    """)


def example_mcp_agent_integration():
    """示例：MCP 与 Agent 集成"""
    print("\n" + "="*60)
    print("示例5: MCP 与 Agent 集成")
    print("="*60)
    
    print("""
    import asyncio
    from agent.factory import create_react_agent
    from mcp.tools import MCPAgentAdapter
    from models.ollama_model import get_llm
    
    async def integrate_mcp_with_agent():
        # 创建 Agent
        agent = create_react_agent(
            name="mcp_agent",
            llm=get_llm()
        )
        
        # 创建 MCP 适配器
        adapter = MCPAgentAdapter(agent)
        
        # 连接 MCP 服务器并注册工具
        await adapter.connect_mcp_server(
            server_name="remote_tools",
            url="http://localhost:3000/mcp"
        )
        
        # 查看已注册的 MCP 工具
        mcp_tools = adapter.list_mcp_tools()
        for server, tools in mcp_tools.items():
            print(f"服务器 {server} 的工具:")
            for tool in tools:
                print(f"  - {tool}")
        
        # 现在 Agent 可以使用 MCP 工具了
        result = agent.run("请使用远程工具查询天气")
        print(result)
    
    asyncio.run(integrate_mcp_with_agent())
    """)


def example_mcp_manager():
    """示例：MCP 管理器"""
    print("\n" + "="*60)
    print("示例6: MCP 客户端管理器")
    print("="*60)
    
    print("""
    import asyncio
    from mcp.client import mcp_manager, MCPServerConfig
    
    async def use_mcp_manager():
        # 添加多个 MCP 服务器
        configs = [
            MCPServerConfig(name="server1", url="http://localhost:3001/mcp"),
            MCPServerConfig(name="server2", url="http://localhost:3002/mcp"),
            MCPServerConfig(name="server3", url="http://localhost:3003/mcp"),
        ]
        
        for config in configs:
            success = await mcp_manager.add_server(config)
            print(f"连接 {config.name}: {'成功' if success else '失败'}")
        
        # 列出所有服务器
        servers = mcp_manager.list_servers()
        print(f"已连接服务器: {servers}")
        
        # 在指定服务器上调用工具
        result = await mcp_manager.call_tool(
            "server1",
            "some_tool",
            {"param": "value"}
        )
        
        # 获取客户端
        client = mcp_manager.get_client("server1")
        tools = client.list_tools()
        
        # 关闭所有连接
        await mcp_manager.close_all()
    
    asyncio.run(use_mcp_manager())
    """)


def example_mcp_protocol():
    """示例：MCP 协议说明"""
    print("\n" + "="*60)
    print("示例7: MCP 协议说明")
    print("="*60)
    
    print("""
MCP (Model Context Protocol) 是基于 JSON-RPC 2.0 的协议

主要方法:
1. initialize - 初始化连接
   请求: {"jsonrpc": "2.0", "method": "initialize", "params": {...}, "id": 1}
   
2. tools/list - 列出工具
   请求: {"jsonrpc": "2.0", "method": "tools/list", "id": 2}
   
3. tools/call - 调用工具
   请求: {
       "jsonrpc": "2.0",
       "method": "tools/call",
       "params": {
           "name": "tool_name",
           "arguments": {...}
       },
       "id": 3
   }
   
4. resources/list - 列出资源
   请求: {"jsonrpc": "2.0", "method": "resources/list", "id": 4}
   
5. resources/read - 读取资源
   请求: {
       "jsonrpc": "2.0",
       "method": "resources/read",
       "params": {"uri": "resource://uri"},
       "id": 5
   }

错误码:
- -32700: Parse error
- -32600: Invalid Request
- -32601: Method not found
- -32602: Invalid params
- -32603: Internal error
    """)


def main():
    """运行 MCP 示例"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              MCP (Model Context Protocol) 示例               ║
╚══════════════════════════════════════════════════════════════╝

MCP 是一个开放协议，用于标准化 AI 模型与外部工具的交互。
    """)
    
    example_mcp_client()
    example_mcp_server()
    example_mcp_with_local_tools()
    example_mcp_session()
    example_mcp_agent_integration()
    example_mcp_manager()
    example_mcp_protocol()
    
    print("\n" + "="*60)
    print("MCP 示例完成！")
    print("="*60)
    print("""
提示：
1. MCP 需要服务端支持，可以使用示例中的 FastAPIMCPServer
2. 确保网络连接正常，防火墙允许访问
3. 生产环境建议使用 HTTPS 和 API Key 认证
4. 更多 MCP 信息: https://modelcontextprotocol.io/
    """)


if __name__ == "__main__":
    main()
