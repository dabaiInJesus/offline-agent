"""
自定义 MCP 客户端示例
展示如何连接自定义 MCP 服务器并使用其工具
"""
import asyncio
import json
from typing import Dict, Any, Optional
from loguru import logger

from mcp.client import MCPClient, MCPServerConfig, mcp_manager
from mcp.tools import MCPToolAdapter
from agent.factory import create_react_agent
from models.ollama_model import get_llm


class CustomMCPClient:
    """
    自定义 MCP 客户端
    封装与 MCP 服务器的交互
    """
    
    def __init__(self, server_url: str = "http://localhost:8000/mcp", api_key: str = None):
        self.server_url = server_url
        self.api_key = api_key
        self.client: Optional[MCPClient] = None
        self._tools_cache: Dict[str, Any] = {}
    
    async def connect(self) -> bool:
        """连接到 MCP 服务器"""
        config = MCPServerConfig(
            name="custom_server",
            url=self.server_url,
            api_key=self.api_key
        )
        
        self.client = MCPClient(config)
        success = await self.client.connect()
        
        if success:
            # 缓存工具列表
            tools = self.client.list_tools()
            for tool in tools:
                self._tools_cache[tool["name"]] = tool
            
            logger.info(f"已连接到 MCP 服务器，发现 {len(tools)} 个工具")
        
        return success
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.disconnect()
            self.client = None
            self._tools_cache.clear()
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """调用工具"""
        if not self.client:
            raise RuntimeError("未连接到 MCP 服务器")
        
        result = await self.client.call_tool(tool_name, kwargs)
        return result
    
    def list_tools(self) -> Dict[str, str]:
        """列出可用工具"""
        return {
            name: info.get("description", "")
            for name, info in self._tools_cache.items()
        }
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """获取工具详细信息"""
        return self._tools_cache.get(tool_name)
    
    # ========== 便捷方法 ==========
    
    async def get_system_info(self) -> Dict:
        """获取系统信息"""
        return await self.call_tool("get_system_info")
    
    async def read_file(self, path: str, encoding: str = "utf-8") -> Dict:
        """读取文件"""
        return await self.call_tool("read_file", path=path, encoding=encoding)
    
    async def list_directory(self, path: str = ".", pattern: str = "*") -> Dict:
        """列出目录"""
        return await self.call_tool("list_directory", path=path, pattern=pattern)
    
    async def search_in_files(self, directory: str, keyword: str, file_pattern: str = "*.txt") -> Dict:
        """搜索文件"""
        return await self.call_tool(
            "search_in_files",
            directory=directory,
            keyword=keyword,
            file_pattern=file_pattern
        )
    
    async def convert_data(self, data: str, from_format: str, to_format: str) -> Dict:
        """转换数据格式"""
        return await self.call_tool(
            "convert_data",
            data=data,
            from_format=from_format,
            to_format=to_format
        )
    
    async def calculate(self, expression: str) -> Dict:
        """计算表达式"""
        return await self.call_tool("calculate", expression=expression)
    
    async def get_datetime(self, action: str = "now", timezone: str = "Asia/Shanghai") -> Dict:
        """获取时间"""
        return await self.call_tool("datetime_utils", action=action, timezone=timezone)
    
    async def query_database(self, db_name: str, sql: str) -> Dict:
        """查询数据库"""
        return await self.call_tool("query_database", db_name=db_name, sql=sql)
    
    async def query_knowledge_base(self, kb_name: str, query: str) -> Dict:
        """查询知识库"""
        return await self.call_tool("query_knowledge_base", kb_name=kb_name, query=query)


async def demo_basic_usage():
    """演示基础用法"""
    print("\n" + "="*60)
    print("演示1: 基础用法")
    print("="*60)
    
    client = CustomMCPClient()
    
    if await client.connect():
        print("✓ 连接成功\n")
        
        # 列出工具
        tools = client.list_tools()
        print(f"可用工具 ({len(tools)}个):")
        for name, desc in tools.items():
            print(f"  • {name}: {desc[:50]}...")
        
        # 获取系统信息
        print("\n--- 系统信息 ---")
        info = await client.get_system_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
        
        # 计算
        print("\n--- 计算 ---")
        result = await client.calculate("2 ** 10 + 100 * 3")
        print(f"2 ** 10 + 100 * 3 = {result.get('result')}")
        
        # 获取时间
        print("\n--- 当前时间 ---")
        dt = await client.get_datetime("now", "Asia/Shanghai")
        print(f"北京时间: {dt.get('datetime')}")
        
        await client.disconnect()
    else:
        print("✗ 连接失败，请确保 MCP 服务器已启动")
        print("  启动命令: python custom_mcp_server.py")


async def demo_file_operations():
    """演示文件操作"""
    print("\n" + "="*60)
    print("演示2: 文件操作")
    print("="*60)
    
    client = CustomMCPClient()
    
    if await client.connect():
        # 列出当前目录
        print("\n--- 当前目录内容 ---")
        result = await client.list_directory(".", "*.py")
        if result.get("success"):
            items = result.get("items", [])
            print(f"找到 {len(items)} 个 Python 文件:")
            for item in items[:5]:  # 只显示前5个
                print(f"  - {item['name']} ({item['size']} bytes)")
        
        # 读取文件
        print("\n--- 读取配置文件 ---")
        result = await client.read_file("config.py")
        if result.get("success"):
            content = result.get("content", "")[:500]
            print(f"文件内容预览:\n{content}...")
        else:
            print(f"读取失败: {result.get('error')}")
        
        await client.disconnect()


async def demo_data_conversion():
    """演示数据转换"""
    print("\n" + "="*60)
    print("演示3: 数据格式转换")
    print("="*60)
    
    client = CustomMCPClient()
    
    if await client.connect():
        # JSON to YAML
        json_data = json.dumps({
            "name": "张三",
            "age": 30,
            "skills": ["Python", "AI", "Data"]
        }, ensure_ascii=False)
        
        print("\n--- JSON 转 YAML ---")
        print(f"输入 (JSON):\n{json_data}")
        
        result = await client.convert_data(json_data, "json", "yaml")
        if result.get("success"):
            print(f"\n输出 (YAML):\n{result.get('result')}")
        
        await client.disconnect()


async def demo_agent_integration():
    """演示与 Agent 集成"""
    print("\n" + "="*60)
    print("演示4: MCP 工具与 Agent 集成")
    print("="*60)
    
    client = CustomMCPClient()
    
    if await client.connect():
        print("✓ MCP 客户端已连接\n")
        
        # 创建 Agent
        agent = create_react_agent(
            name="mcp_agent",
            llm=get_llm()
        )
        
        # 将 MCP 工具注册到 Agent
        async def mcp_tool_wrapper(tool_name: str, **kwargs):
            """MCP 工具包装器"""
            return await client.call_tool(tool_name, kwargs)
        
        # 注册几个常用工具
        agent.register_tool(
            "get_system_info",
            lambda: asyncio.run(mcp_tool_wrapper("get_system_info")),
            "获取系统信息"
        )
        
        agent.register_tool(
            "calculate",
            lambda expression: asyncio.run(mcp_tool_wrapper("calculate", expression=expression)),
            "计算数学表达式"
        )
        
        agent.register_tool(
            "list_directory",
            lambda path=".": asyncio.run(mcp_tool_wrapper("list_directory", path=path)),
            "列出目录内容"
        )
        
        print("已注册 MCP 工具到 Agent")
        print("工具列表:")
        for tool in agent.list_tools():
            print(f"  - {tool['name']}: {tool['description']}")
        
        # 运行 Agent（示例查询）
        print("\n--- Agent 执行示例 ---")
        queries = [
            "计算 1234 * 5678",
            "获取系统信息",
        ]
        
        for query in queries:
            print(f"\n用户: {query}")
            try:
                result = agent.run(query)
                print(f"Agent: {result[:200]}...")
            except Exception as e:
                print(f"执行出错: {e}")
            agent.reset()
        
        await client.disconnect()


async def demo_advanced_features():
    """演示高级功能"""
    print("\n" + "="*60)
    print("演示5: 高级功能")
    print("="*60)
    
    client = CustomMCPClient()
    
    if await client.connect():
        # 搜索文件
        print("\n--- 搜索文件 ---")
        result = await client.search_in_files(".", "class", "*.py")
        if result.get("success"):
            results = result.get("results", [])
            print(f"在 {len(results)} 个文件中找到 'class' 关键字")
            for r in results[:3]:
                print(f"\n  文件: {r['file']}")
                print(f"  匹配数: {r['match_count']}")
                for match in r['matches'][:2]:
                    print(f"    行 {match['line']}: {match['content'][:60]}...")
        
        # 多工具链式调用
        print("\n--- 多工具链式调用 ---")
        
        # 1. 获取系统信息
        sys_info = await client.get_system_info()
        memory = sys_info.get("memory_available", "unknown")
        print(f"系统内存: {memory}")
        
        # 2. 计算内存百分比
        if "GB" in str(memory):
            mem_num = float(str(memory).replace(" GB", ""))
            calc_result = await client.calculate(f"{mem_num} / 16 * 100")
            print(f"可用内存占比: {calc_result.get('result', 'unknown'):.2f}%")
        
        # 3. 获取当前时间
        dt = await client.get_datetime("now")
        print(f"当前时间: {dt.get('datetime')}")
        
        await client.disconnect()


async def demo_resource_access():
    """演示资源访问"""
    print("\n" + "="*60)
    print("演示6: 资源访问")
    print("="*60)
    
    client = CustomMCPClient()
    
    if await client.connect():
        print("\n--- 读取 MCP 资源 ---")
        
        # 服务器信息
        info = await client.client.read_resource("system://info")
        print(f"服务器信息:\n{json.dumps(info, indent=2, ensure_ascii=False)}")
        
        # 工具列表
        tools_res = await client.client.read_resource("system://tools")
        print(f"\n工具列表资源:\n{json.dumps(tools_res, indent=2, ensure_ascii=False)[:500]}...")
        
        await client.disconnect()


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              自定义 MCP 客户端演示                           ║
╚══════════════════════════════════════════════════════════════╝

请先启动 MCP 服务器:
  python custom_mcp_server.py
    """)
    
    try:
        await demo_basic_usage()
        await demo_file_operations()
        await demo_data_conversion()
        await demo_agent_integration()
        await demo_advanced_features()
        await demo_resource_access()
        
    except Exception as e:
        print(f"\n运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("MCP 客户端演示完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
