"""
MCP 工具适配器 - 将 MCP 工具转换为 Agent 可用工具
"""
from typing import Dict, Any, Callable, Optional
from loguru import logger

from .client import MCPClient, mcp_manager


class MCPToolAdapter:
    """
    MCP 工具适配器
    将 MCP 服务器提供的工具转换为 Agent 可调用的函数
    """
    
    def __init__(self, server_name: str, client: MCPClient = None):
        self.server_name = server_name
        self.client = client or mcp_manager.get_client(server_name)
    
    def get_tools(self) -> Dict[str, Callable]:
        """
        获取所有可用的 MCP 工具，转换为可调用函数
        
        Returns:
            工具名称到函数的映射
        """
        if not self.client:
            raise ValueError(f"MCP 客户端 '{self.server_name}' 不可用")
        
        tools = {}
        for tool_info in self.client.list_tools():
            tool_name = tool_info.get("name")
            if tool_name:
                tools[tool_name] = self._create_tool_wrapper(tool_info)
        
        return tools
    
    def _create_tool_wrapper(self, tool_info: Dict[str, Any]) -> Callable:
        """
        为 MCP 工具创建包装函数
        
        Args:
            tool_info: 工具信息
            
        Returns:
            包装后的函数
        """
        tool_name = tool_info.get("name")
        description = tool_info.get("description", "")
        input_schema = tool_info.get("inputSchema", {})
        
        async def tool_wrapper(**kwargs) -> Any:
            """MCP 工具包装函数"""
            try:
                result = await self.client.call_tool(tool_name, kwargs)
                
                # 解析结果
                if "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        # 提取文本内容
                        texts = []
                        for item in content:
                            if item.get("type") == "text":
                                texts.append(item.get("text", ""))
                        return "\n".join(texts)
                    return content
                
                return result
                
            except Exception as e:
                logger.error(f"MCP 工具调用失败 {tool_name}: {e}")
                raise
        
        # 设置函数元数据
        tool_wrapper.__name__ = tool_name
        tool_wrapper.__doc__ = description
        tool_wrapper._mcp_tool_info = tool_info
        tool_wrapper._is_mcp_tool = True
        
        return tool_wrapper
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具详细信息"""
        return self.client.get_tool_schema(tool_name)
    
    def create_langchain_tool(self, tool_name: str):
        """
        创建 LangChain 格式的工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            LangChain Tool 对象
        """
        try:
            from langchain.tools import Tool
        except ImportError:
            raise ImportError("请安装 langchain: pip install langchain")
        
        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            raise ValueError(f"工具 '{tool_name}' 不存在")
        
        wrapper = self._create_tool_wrapper(tool_info)
        
        return Tool(
            name=tool_name,
            description=tool_info.get("description", ""),
            func=wrapper,
            coroutine=wrapper
        )
    
    def get_all_langchain_tools(self) -> list:
        """获取所有 LangChain 格式的工具"""
        tools = []
        for tool_info in self.client.list_tools():
            tool_name = tool_info.get("name")
            if tool_name:
                try:
                    tools.append(self.create_langchain_tool(tool_name))
                except Exception as e:
                    logger.warning(f"创建工具 {tool_name} 失败: {e}")
        return tools


class MCPAgentAdapter:
    """
    MCP Agent 适配器
    将 MCP 服务器集成到 Agent 中
    """
    
    def __init__(self, agent):
        self.agent = agent
        self._mcp_tools: Dict[str, MCPToolAdapter] = {}
    
    async def connect_mcp_server(self, server_name: str, url: str, api_key: str = None) -> bool:
        """
        连接 MCP 服务器并注册工具
        
        Args:
            server_name: 服务器名称
            url: 服务器 URL
            api_key: API 密钥
            
        Returns:
            是否连接成功
        """
        from .client import MCPServerConfig
        
        config = MCPServerConfig(
            name=server_name,
            url=url,
            api_key=api_key
        )
        
        success = await mcp_manager.add_server(config)
        
        if success:
            # 创建工具适配器
            adapter = MCPToolAdapter(server_name)
            self._mcp_tools[server_name] = adapter
            
            # 注册工具到 Agent
            tools = adapter.get_tools()
            for tool_name, tool_func in tools.items():
                full_name = f"{server_name}.{tool_name}"
                self.agent.register_tool(full_name, tool_func)
            
            logger.info(f"已将 MCP 服务器 '{server_name}' 的工具注册到 Agent")
        
        return success
    
    def disconnect_mcp_server(self, server_name: str):
        """断开 MCP 服务器"""
        if server_name in self._mcp_tools:
            del self._mcp_tools[server_name]
        
        # 从 Agent 中移除相关工具
        # 注意：这里需要 Agent 支持移除工具
    
    def list_mcp_tools(self) -> Dict[str, list]:
        """列出所有 MCP 工具"""
        result = {}
        for server_name, adapter in self._mcp_tools.items():
            result[server_name] = [
                tool.get("name")
                for tool in adapter.client.list_tools()
            ]
        return result


def create_mcp_tool_function(server_name: str, tool_name: str) -> Callable:
    """
    创建 MCP 工具函数
    
    Args:
        server_name: MCP 服务器名称
        tool_name: 工具名称
        
    Returns:
        可调用的工具函数
    """
    client = mcp_manager.get_client(server_name)
    if not client:
        raise ValueError(f"MCP 服务器 '{server_name}' 不存在")
    
    adapter = MCPToolAdapter(server_name, client)
    tools = adapter.get_tools()
    
    if tool_name not in tools:
        raise ValueError(f"工具 '{tool_name}' 不存在")
    
    return tools[tool_name]


# 便捷函数
async def register_mcp_tools_to_agent(agent, server_name: str, url: str, api_key: str = None):
    """
    将 MCP 服务器工具注册到 Agent
    
    Args:
        agent: Agent 实例
        server_name: MCP 服务器名称
        url: MCP 服务器 URL
        api_key: API 密钥
    """
    adapter = MCPAgentAdapter(agent)
    return await adapter.connect_mcp_server(server_name, url, api_key)
