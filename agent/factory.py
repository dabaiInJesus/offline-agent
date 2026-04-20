"""
Agent 工厂 - 创建和管理各种 Agent
"""
from typing import Dict, Type, Optional, List, Any
from loguru import logger

from .base import BaseAgent
from .react_agent import ReActAgent, SimpleReActAgent
from .tool_agent import ToolAgent, PlanAndExecuteAgent
from .graph_agent import GraphAgent


class AgentFactory:
    """
    Agent 工厂类
    用于创建和管理各种类型的 Agent
    """
    
    _agent_types: Dict[str, Type[BaseAgent]] = {
        "react": ReActAgent,
        "simple_react": SimpleReActAgent,
        "tool": ToolAgent,
        "plan_execute": PlanAndExecuteAgent,
        "graph": GraphAgent,
    }
    
    _instances: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register_agent_type(cls, name: str, agent_class: Type[BaseAgent]):
        """注册新的 Agent 类型"""
        cls._agent_types[name] = agent_class
        logger.info(f"注册 Agent 类型: {name}")
    
    @classmethod
    def create(
        cls,
        agent_type: str,
        name: str = None,
        llm=None,
        system_prompt: str = None,
        max_steps: int = 10,
        **kwargs
    ) -> BaseAgent:
        """
        创建 Agent 实例
        
        Args:
            agent_type: Agent 类型名称
            name: Agent 名称
            llm: 语言模型
            system_prompt: 系统提示词
            max_steps: 最大执行步数
            **kwargs: 其他参数
            
        Returns:
            Agent 实例
        """
        if agent_type not in cls._agent_types:
            raise ValueError(f"未知的 Agent 类型: {agent_type}。可用类型: {list(cls._agent_types.keys())}")
        
        agent_class = cls._agent_types[agent_type]
        
        agent = agent_class(
            name=name or f"{agent_type}_agent",
            llm=llm,
            system_prompt=system_prompt,
            max_steps=max_steps,
            **kwargs
        )
        
        logger.info(f"创建 Agent: {agent.name} (类型: {agent_type})")
        return agent
    
    @classmethod
    def get_or_create(
        cls,
        agent_type: str,
        name: str,
        llm=None,
        system_prompt: str = None,
        max_steps: int = 10,
        **kwargs
    ) -> BaseAgent:
        """获取或创建 Agent（单例模式）"""
        if name in cls._instances:
            return cls._instances[name]
        
        agent = cls.create(
            agent_type=agent_type,
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            max_steps=max_steps,
            **kwargs
        )
        cls._instances[name] = agent
        return agent
    
    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseAgent]:
        """获取已创建的 Agent"""
        return cls._instances.get(name)
    
    @classmethod
    def list_agents(cls) -> List[str]:
        """列出所有已创建的 Agent"""
        return list(cls._instances.keys())
    
    @classmethod
    def remove_agent(cls, name: str):
        """移除 Agent"""
        if name in cls._instances:
            del cls._instances[name]
            logger.info(f"移除 Agent: {name}")
    
    @classmethod
    def list_agent_types(cls) -> List[str]:
        """列出所有可用的 Agent 类型"""
        return list(cls._agent_types.keys())
    
    @classmethod
    def create_with_tools(
        cls,
        agent_type: str,
        name: str,
        tools: Dict[str, Any],
        llm=None,
        system_prompt: str = None,
        **kwargs
    ) -> BaseAgent:
        """
        创建带工具的 Agent
        
        Args:
            agent_type: Agent 类型
            name: Agent 名称
            tools: 工具字典 {名称: (函数, 描述)}
            llm: 语言模型
            system_prompt: 系统提示词
            
        Returns:
            配置好的 Agent 实例
        """
        agent = cls.create(
            agent_type=agent_type,
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 注册工具
        for tool_name, tool_config in tools.items():
            if isinstance(tool_config, tuple):
                func, desc = tool_config
                agent.register_tool(tool_name, func, desc)
            else:
                # 假设只是函数
                agent.register_tool(tool_name, tool_config)
        
        return agent


# 便捷函数
def create_agent(
    agent_type: str = "react",
    name: str = None,
    llm=None,
    system_prompt: str = None,
    **kwargs
) -> BaseAgent:
    """创建 Agent"""
    return AgentFactory.create(
        agent_type=agent_type,
        name=name,
        llm=llm,
        system_prompt=system_prompt,
        **kwargs
    )


def get_agent(name: str) -> Optional[BaseAgent]:
    """获取 Agent"""
    return AgentFactory.get_agent(name)


def create_react_agent(name: str = None, llm=None, tools: Dict = None, **kwargs) -> ReActAgent:
    """创建 ReAct Agent"""
    agent = AgentFactory.create("react", name, llm, **kwargs)
    if tools:
        for tool_name, tool_func in tools.items():
            agent.register_tool(tool_name, tool_func)
    return agent


def create_tool_agent(name: str = None, llm=None, tools: Dict = None, **kwargs) -> ToolAgent:
    """创建 Tool Agent"""
    agent = AgentFactory.create("tool", name, llm, **kwargs)
    if tools:
        for tool_name, tool_func in tools.items():
            agent.register_tool(tool_name, tool_func)
    return agent


def create_graph_agent(name: str = None, llm=None, tools: Dict = None, **kwargs) -> GraphAgent:
    """创建 Graph Agent"""
    agent = AgentFactory.create("graph", name, llm, **kwargs)
    if tools:
        for tool_name, tool_func in tools.items():
            agent.register_tool(tool_name, tool_func)
    return agent
