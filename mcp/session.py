"""
MCP 会话管理 - 维护与 MCP 服务器的会话状态
"""
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from .client import MCPClient, MCPServerConfig


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    server_name: str
    created_at: datetime
    last_active: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)


class MCPSession:
    """
    MCP 会话
    维护与单个 MCP 服务器的会话状态
    """
    
    def __init__(self, client: MCPClient = None, config: MCPServerConfig = None):
        self.session_id = str(uuid.uuid4())
        self.client = client
        self.config = config
        self.context: Optional[SessionContext] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """建立会话连接"""
        if not self.client:
            if not self.config:
                raise ValueError("需要提供 MCPClient 或 MCPServerConfig")
            self.client = MCPClient(self.config)
        
        success = await self.client.connect()
        
        if success:
            now = datetime.now()
            self.context = SessionContext(
                session_id=self.session_id,
                server_name=self.client.config.name,
                created_at=now,
                last_active=now
            )
            self._connected = True
            logger.info(f"MCP 会话已建立: {self.session_id}")
        
        return success
    
    async def disconnect(self):
        """断开会话"""
        if self.client:
            await self.client.disconnect()
        
        self._connected = False
        self.context = None
        logger.info(f"MCP 会话已断开: {self.session_id}")
    
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具并记录到会话历史
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        if not self._connected:
            raise RuntimeError("会话未连接")
        
        # 记录调用
        invocation = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool_call",
            "tool": tool_name,
            "arguments": arguments
        }
        
        try:
            result = await self.client.call_tool(tool_name, arguments)
            
            invocation["success"] = True
            invocation["result"] = result
            
            # 更新上下文
            self.context.conversation_history.append(invocation)
            self.context.last_active = datetime.now()
            
            return result
            
        except Exception as e:
            invocation["success"] = False
            invocation["error"] = str(e)
            self.context.conversation_history.append(invocation)
            raise
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        读取资源并记录到会话历史
        
        Args:
            uri: 资源 URI
            
        Returns:
            资源内容
        """
        if not self._connected:
            raise RuntimeError("会话未连接")
        
        access = {
            "timestamp": datetime.now().isoformat(),
            "type": "resource_access",
            "uri": uri
        }
        
        try:
            result = await self.client.read_resource(uri)
            
            access["success"] = True
            self.context.conversation_history.append(access)
            self.context.last_active = datetime.now()
            
            return result
            
        except Exception as e:
            access["success"] = False
            access["error"] = str(e)
            self.context.conversation_history.append(access)
            raise
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取会话历史"""
        if self.context:
            return self.context.conversation_history.copy()
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计"""
        if not self.context:
            return {}
        
        history = self.context.conversation_history
        tool_calls = [h for h in history if h["type"] == "tool_call"]
        resource_accesses = [h for h in history if h["type"] == "resource_access"]
        
        return {
            "session_id": self.session_id,
            "server_name": self.context.server_name,
            "created_at": self.context.created_at.isoformat(),
            "last_active": self.context.last_active.isoformat(),
            "total_interactions": len(history),
            "tool_calls": len(tool_calls),
            "resource_accesses": len(resource_accesses),
            "successful_calls": sum(1 for h in history if h.get("success", False)),
            "failed_calls": sum(1 for h in history if not h.get("success", True))
        }
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected


class MCPSessionManager:
    """
    MCP 会话管理器
    管理多个 MCP 会话
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: Dict[str, MCPSession] = {}
        return cls._instance
    
    async def create_session(
        self,
        server_name: str,
        url: str,
        api_key: str = None
    ) -> MCPSession:
        """
        创建新会话
        
        Args:
            server_name: 服务器名称
            url: 服务器 URL
            api_key: API 密钥
            
        Returns:
            新会话实例
        """
        config = MCPServerConfig(
            name=server_name,
            url=url,
            api_key=api_key
        )
        
        session = MCPSession(config=config)
        success = await session.connect()
        
        if success:
            self._sessions[session.session_id] = session
            return session
        else:
            raise ConnectionError(f"无法连接到 MCP 服务器: {server_name}")
    
    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """关闭会话"""
        session = self._sessions.get(session_id)
        if session:
            await session.disconnect()
            del self._sessions[session_id]
    
    async def close_all_sessions(self):
        """关闭所有会话"""
        for session in list(self._sessions.values()):
            await session.disconnect()
        self._sessions.clear()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return [
            {
                "session_id": sid,
                "server_name": session.context.server_name if session.context else None,
                "connected": session.is_connected()
            }
            for sid, session in self._sessions.items()
        ]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取所有会话的统计信息"""
        stats = {
            "total_sessions": len(self._sessions),
            "active_sessions": sum(1 for s in self._sessions.values() if s.is_connected()),
            "sessions": []
        }
        
        for session in self._sessions.values():
            if session.context:
                stats["sessions"].append(session.get_stats())
        
        return stats


# 全局会话管理器
session_manager = MCPSessionManager()


# 便捷函数
async def create_mcp_session(server_name: str, url: str, api_key: str = None) -> MCPSession:
    """创建 MCP 会话"""
    return await session_manager.create_session(server_name, url, api_key)


def get_session(session_id: str) -> Optional[MCPSession]:
    """获取会话"""
    return session_manager.get_session(session_id)


async def close_session(session_id: str):
    """关闭会话"""
    await session_manager.close_session(session_id)
