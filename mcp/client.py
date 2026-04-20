"""
MCP 客户端 - 连接 MCP 服务器
"""
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from loguru import logger


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str
    url: str
    api_key: Optional[str] = None
    timeout: int = 30
    headers: Dict[str, str] = None


class MCPClient:
    """
    MCP (Model Context Protocol) 客户端
    用于连接和调用 MCP 服务器
    """
    
    def __init__(self, config: MCPServerConfig = None):
        self.config = config
        self._session = None
        self._tools: List[Dict[str, Any]] = []
        self._connected = False
        self._message_handlers: Dict[str, Callable] = {}
    
    async def connect(self, config: MCPServerConfig = None) -> bool:
        """
        连接到 MCP 服务器
        
        Args:
            config: 服务器配置，如果为 None 使用初始化时的配置
            
        Returns:
            是否连接成功
        """
        if config:
            self.config = config
        
        if not self.config:
            raise ValueError("未提供 MCP 服务器配置")
        
        try:
            import aiohttp
            
            self._session = aiohttp.ClientSession()
            
            # 发送初始化请求
            init_response = await self._send_request({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "clientInfo": {
                        "name": "offline-agent",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            })
            
            if init_response.get("error"):
                logger.error(f"MCP 初始化失败: {init_response['error']}")
                return False
            
            # 获取可用工具
            await self._fetch_tools()
            
            self._connected = True
            logger.info(f"已连接到 MCP 服务器: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"连接 MCP 服务器失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._tools = []
        logger.info("已断开 MCP 服务器连接")
    
    async def _send_request(self, request: Dict) -> Dict:
        """发送 JSON-RPC 请求"""
        import aiohttp
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        if self.config.headers:
            headers.update(self.config.headers)
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        async with self._session.post(
            self.config.url,
            json=request,
            headers=headers,
            timeout=timeout
        ) as response:
            return await response.json()
    
    async def _fetch_tools(self):
        """获取可用工具列表"""
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        })
        
        if "result" in response:
            self._tools = response["result"].get("tools", [])
            logger.info(f"获取到 {len(self._tools)} 个 MCP 工具")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具"""
        return self._tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        if not self._connected:
            raise RuntimeError("未连接到 MCP 服务器")
        
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        })
        
        if "error" in response:
            raise Exception(f"工具调用失败: {response['error']}")
        
        return response.get("result", {})
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        读取资源
        
        Args:
            uri: 资源 URI
            
        Returns:
            资源内容
        """
        if not self._connected:
            raise RuntimeError("未连接到 MCP 服务器")
        
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {
                "uri": uri
            },
            "id": 4
        })
        
        return response.get("result", {})
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """列出可用资源"""
        if not self._connected:
            raise RuntimeError("未连接到 MCP 服务器")
        
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "resources/list",
            "id": 5
        })
        
        return response.get("result", {}).get("resources", [])
    
    def register_message_handler(self, method: str, handler: Callable):
        """注册消息处理器"""
        self._message_handlers[method] = handler
    
    async def handle_notification(self, notification: Dict[str, Any]):
        """处理服务器通知"""
        method = notification.get("method")
        handler = self._message_handlers.get(method)
        
        if handler:
            await handler(notification.get("params", {}))
        else:
            logger.debug(f"未处理的通知: {method}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具 schema"""
        for tool in self._tools:
            if tool.get("name") == tool_name:
                return tool
        return None


class MCPClientManager:
    """MCP 客户端管理器 - 管理多个 MCP 连接"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._clients: Dict[str, MCPClient] = {}
        return cls._instance
    
    async def add_server(self, config: MCPServerConfig) -> bool:
        """添加并连接 MCP 服务器"""
        client = MCPClient(config)
        success = await client.connect()
        
        if success:
            self._clients[config.name] = client
        
        return success
    
    async def remove_server(self, name: str):
        """移除 MCP 服务器"""
        if name in self._clients:
            await self._clients[name].disconnect()
            del self._clients[name]
    
    def get_client(self, name: str) -> Optional[MCPClient]:
        """获取客户端"""
        return self._clients.get(name)
    
    def list_servers(self) -> List[str]:
        """列出所有服务器"""
        return list(self._clients.keys())
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Dict:
        """在指定服务器上调用工具"""
        client = self.get_client(server_name)
        if not client:
            raise ValueError(f"MCP 服务器 '{server_name}' 不存在")
        
        return await client.call_tool(tool_name, arguments)
    
    async def close_all(self):
        """关闭所有连接"""
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()


# 全局 MCP 客户端管理器
mcp_manager = MCPClientManager()


# 便捷函数
async def connect_mcp_server(name: str, url: str, api_key: str = None) -> bool:
    """连接到 MCP 服务器"""
    config = MCPServerConfig(name=name, url=url, api_key=api_key)
    return await mcp_manager.add_server(config)


async def call_mcp_tool(server_name: str, tool_name: str, **kwargs) -> Dict:
    """调用 MCP 工具"""
    return await mcp_manager.call_tool(server_name, tool_name, kwargs)


def get_mcp_client(name: str) -> Optional[MCPClient]:
    """获取 MCP 客户端"""
    return mcp_manager.get_client(name)
