"""
MCP 服务器 - 将本地工具暴露为 MCP 服务
"""
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from loguru import logger


@dataclass
class MCPToolDefinition:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


class MCPServer:
    """
    MCP 服务器
    将本地工具和资源暴露为 MCP 服务
    """
    
    def __init__(self, name: str = "offline-agent-server", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._resources: Dict[str, Callable] = {}
        self._initialized = False
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str = None,
        input_schema: Dict[str, Any] = None
    ):
        """
        注册工具
        
        Args:
            name: 工具名称
            handler: 处理函数
            description: 工具描述
            input_schema: 输入参数 schema
        """
        import inspect
        
        # 自动生成 schema
        if input_schema is None:
            input_schema = self._generate_schema_from_function(handler)
        
        if description is None:
            description = handler.__doc__ or f"Tool: {name}"
        
        self._tools[name] = MCPToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )
        
        logger.info(f"MCP 服务器注册工具: {name}")
    
    def _generate_schema_from_function(self, func: Callable) -> Dict[str, Any]:
        """从函数签名生成 JSON Schema"""
        import inspect
        
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
            
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list or param.annotation == List:
                    param_type = "array"
                elif param.annotation == dict or param.annotation == Dict:
                    param_type = "object"
            
            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter: {param_name}"
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def register_resource(self, uri: str, handler: Callable):
        """
        注册资源
        
        Args:
            uri: 资源 URI
            handler: 资源处理器
        """
        self._resources[uri] = handler
        logger.info(f"MCP 服务器注册资源: {uri}")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self._tools.values()
        ]
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """列出所有资源"""
        return [
            {
                "uri": uri,
                "name": uri.split("/")[-1] if "/" in uri else uri
            }
            for uri in self._resources.keys()
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"工具 '{name}' 不存在")
        
        try:
            import asyncio
            
            # 检查是否是异步函数
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)
            
            # 格式化结果
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"工具执行失败 {name}: {e}")
            raise
    
    def _format_result(self, result: Any) -> Dict[str, Any]:
        """格式化结果为 MCP 格式"""
        if isinstance(result, dict):
            content = json.dumps(result, ensure_ascii=False)
        elif isinstance(result, list):
            content = json.dumps(result, ensure_ascii=False)
        else:
            content = str(result)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        }
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        读取资源
        
        Args:
            uri: 资源 URI
            
        Returns:
            资源内容
        """
        handler = self._resources.get(uri)
        if not handler:
            raise ValueError(f"资源 '{uri}' 不存在")
        
        try:
            import asyncio
            
            if asyncio.iscoroutinefunction(handler):
                result = await handler()
            else:
                result = handler()
            
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"读取资源失败 {uri}: {e}")
            raise
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 JSON-RPC 请求
        
        Args:
            request: JSON-RPC 请求
            
        Returns:
            JSON-RPC 响应
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return self._handle_initialize(request_id, params)
            elif method == "tools/list":
                return self._handle_tools_list(request_id)
            elif method == "tools/call":
                return self._handle_tools_call(request_id, params)
            elif method == "resources/list":
                return self._handle_resources_list(request_id)
            elif method == "resources/read":
                return self._handle_resources_read(request_id, params)
            else:
                return self._error_response(request_id, -32601, f"未知方法: {method}")
                
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return self._error_response(request_id, -32603, str(e))
    
    def _handle_initialize(self, request_id: Any, params: Dict) -> Dict:
        """处理初始化请求"""
        self._initialized = True
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }
    
    def _handle_tools_list(self, request_id: Any) -> Dict:
        """处理工具列表请求"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": self.list_tools()
            }
        }
    
    def _handle_tools_call(self, request_id: Any, params: Dict) -> Dict:
        """处理工具调用请求"""
        import asyncio
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            # 运行异步调用
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(self.call_tool(tool_name, arguments))
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            return self._error_response(request_id, -32603, str(e))
    
    def _handle_resources_list(self, request_id: Any) -> Dict:
        """处理资源列表请求"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": self.list_resources()
            }
        }
    
    def _handle_resources_read(self, request_id: Any, params: Dict) -> Dict:
        """处理资源读取请求"""
        import asyncio
        
        uri = params.get("uri")
        
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(self.read_resource(uri))
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            return self._error_response(request_id, -32603, str(e))
    
    def _error_response(self, request_id: Any, code: int, message: str) -> Dict:
        """生成错误响应"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


class FastAPIMCPServer:
    """
    基于 FastAPI 的 MCP 服务器
    提供 HTTP 接口
    """
    
    def __init__(self, mcp_server: MCPServer = None):
        self.mcp_server = mcp_server or MCPServer()
        self.app = None
    
    def create_app(self):
        """创建 FastAPI 应用"""
        try:
            from fastapi import FastAPI, Request, Response
            from fastapi.responses import JSONResponse
        except ImportError:
            raise ImportError("请安装 fastapi: pip install fastapi uvicorn")
        
        app = FastAPI(title="MCP Server", version="1.0.0")
        
        @app.post("/mcp")
        async def mcp_endpoint(request: Request):
            """MCP JSON-RPC 端点"""
            body = await request.json()
            
            if isinstance(body, list):
                # 批量请求
                responses = [self.mcp_server.handle_request(req) for req in body]
                return JSONResponse(responses)
            else:
                # 单个请求
                response = self.mcp_server.handle_request(body)
                return JSONResponse(response)
        
        @app.get("/mcp/tools")
        async def list_tools():
            """列出工具"""
            return JSONResponse({
                "tools": self.mcp_server.list_tools()
            })
        
        @app.get("/mcp/resources")
        async def list_resources():
            """列出资源"""
            return JSONResponse({
                "resources": self.mcp_server.list_resources()
            })
        
        @app.get("/health")
        async def health():
            """健康检查"""
            return JSONResponse({"status": "ok"})
        
        self.app = app
        return app
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """运行服务器"""
        import uvicorn
        
        if not self.app:
            self.create_app()
        
        uvicorn.run(self.app, host=host, port=port)


def create_mcp_server_with_local_tools(
    db_manager=None,
    vector_manager=None,
    kb_manager=None
) -> MCPServer:
    """
    创建包含本地工具的 MCP 服务器
    
    Args:
        db_manager: 数据库管理器
        vector_manager: 向量库管理器
        kb_manager: 知识库管理器
        
    Returns:
        MCP 服务器实例
    """
    server = MCPServer(name="offline-agent-mcp")
    
    # 注册数据库工具
    if db_manager:
        def query_database(db_name: str, sql: str):
            """查询数据库"""
            db = db_manager.get(db_name)
            if not db:
                return {"error": f"数据库 '{db_name}' 不存在"}
            return db.execute(sql)
        
        server.register_tool(
            "query_database",
            query_database,
            "执行数据库查询",
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
    
    # 注册知识库工具
    if kb_manager:
        def query_knowledge_base(kb_name: str, query: str):
            """查询知识库"""
            kb = kb_manager.get(kb_name)
            if not kb:
                return {"error": f"知识库 '{kb_name}' 不存在"}
            return kb.query(query)
        
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
        
        def list_knowledge_bases():
            """列出所有知识库"""
            return kb_manager.list_knowledge_bases()
        
        server.register_tool("list_knowledge_bases", list_knowledge_bases, "列出所有知识库")
    
    return server
