"""
Agent 基类 - 定义智能体接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentState:
    """Agent 状态数据类"""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    current_step: int = 0
    max_steps: int = 10
    status: AgentStatus = AgentStatus.IDLE
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, **kwargs):
        """添加消息"""
        message = {
            "role": role,
            "content": content,
            "step": self.current_step,
            **kwargs
        }
        self.messages.append(message)
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "messages": self.messages,
            "memory": self.memory,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "status": self.status.value,
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """
    Agent 基类
    所有智能体的基础抽象类
    """
    
    def __init__(
        self,
        name: str = "agent",
        llm=None,
        system_prompt: str = None,
        max_steps: int = 10,
        memory_enabled: bool = True
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt or "你是一个有用的AI助手。"
        self.max_steps = max_steps
        self.memory_enabled = memory_enabled
        self.state = AgentState(max_steps=max_steps)
        self._tools: Dict[str, Callable] = {}
        self._callbacks: List[Callable] = []
    
    def register_tool(self, name: str, func: Callable, description: str = None):
        """注册工具"""
        self._tools[name] = {
            "func": func,
            "description": description or func.__doc__ or f"工具: {name}"
        }
        logger.info(f"Agent '{self.name}' 注册工具: {name}")
    
    def register_tools(self, tools: Dict[str, Callable]):
        """批量注册工具"""
        for name, func in tools.items():
            self.register_tool(name, func)
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """获取工具"""
        tool = self._tools.get(name)
        return tool["func"] if tool else None
    
    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有工具"""
        return [
            {"name": name, "description": tool["description"]}
            for name, tool in self._tools.items()
        ]
    
    def add_callback(self, callback: Callable):
        """添加回调函数"""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, event: str, data: Any):
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(event, data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")
    
    def reset(self):
        """重置 Agent 状态"""
        self.state = AgentState(max_steps=self.max_steps)
        logger.info(f"Agent '{self.name}' 状态已重置")
    
    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """运行 Agent"""
        pass
    
    @abstractmethod
    async def arun(self, input_text: str, **kwargs) -> str:
        """异步运行 Agent"""
        pass
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.state.messages
    
    def clear_memory(self):
        """清除记忆"""
        self.state.memory.clear()
        self.state.messages.clear()
        self.state.current_step = 0
