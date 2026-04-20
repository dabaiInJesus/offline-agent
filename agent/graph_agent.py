"""
Graph Agent - 基于 LangGraph 的智能体
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from loguru import logger

from .base import BaseAgent, AgentStatus


class GraphState(TypedDict):
    """图状态定义"""
    messages: List[Dict[str, Any]]
    next_step: str
    tool_calls: List[Dict]
    final_answer: Optional[str]
    iteration_count: int


class GraphAgent(BaseAgent):
    """
    基于 LangGraph 的智能体
    使用状态图定义 Agent 的工作流
    """
    
    def __init__(
        self,
        name: str = "graph_agent",
        llm=None,
        system_prompt: str = None,
        max_steps: int = 10
    ):
        super().__init__(name, llm, system_prompt, max_steps)
        self.graph = None
        self._build_graph()
    
    def _build_graph(self):
        """构建状态图"""
        # 定义状态图
        workflow = StateGraph(GraphState)
        
        # 添加节点
        workflow.add_node("think", self._node_think)
        workflow.add_node("act", self._node_act)
        workflow.add_node("observe", self._node_observe)
        workflow.add_node("finish", self._node_finish)
        
        # 添加边
        workflow.set_entry_point("think")
        
        workflow.add_conditional_edges(
            "think",
            self._should_act,
            {
                "act": "act",
                "finish": "finish"
            }
        )
        
        workflow.add_edge("act", "observe")
        
        workflow.add_conditional_edges(
            "observe",
            self._should_continue,
            {
                "think": "think",
                "finish": "finish"
            }
        )
        
        workflow.add_edge("finish", END)
        
        # 编译图
        self.graph = workflow.compile()
    
    def _node_think(self, state: GraphState) -> GraphState:
        """思考节点"""
        messages = state["messages"]
        
        # 构建提示
        prompt_messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        for msg in messages:
            if msg["role"] == "user":
                prompt_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                prompt_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "tool":
                prompt_messages.append(HumanMessage(content=f"工具结果: {msg['content']}"))
        
        # 添加工具说明
        tools_desc = self._format_tools()
        prompt_messages.append(HumanMessage(
            content=f"\n可用工具：\n{tools_desc}\n\n请决定：1) 使用工具（请说明工具名称和参数）2) 直接回答"
        ))
        
        # 调用 LLM
        response = self.llm.invoke(prompt_messages)
        content = response.content
        
        # 检查是否需要调用工具
        tool_calls = self._parse_tool_calls(content)
        
        new_messages = messages + [{"role": "assistant", "content": content}]
        
        return {
            **state,
            "messages": new_messages,
            "tool_calls": tool_calls,
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    
    def _node_act(self, state: GraphState) -> GraphState:
        """行动节点 - 执行工具"""
        tool_calls = state["tool_calls"]
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})
            
            tool = self._tools.get(tool_name)
            if tool:
                try:
                    result = tool["func"](**tool_args)
                    results.append({
                        "tool": tool_name,
                        "result": str(result),
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "tool": tool_name,
                        "result": f"错误: {str(e)}",
                        "success": False
                    })
            else:
                results.append({
                    "tool": tool_name,
                    "result": f"工具 '{tool_name}' 不存在",
                    "success": False
                })
        
        # 添加工具结果到消息
        tool_results_text = "\n".join([
            f"[{r['tool']}]: {r['result']}" for r in results
        ])
        
        new_messages = state["messages"] + [{"role": "tool", "content": tool_results_text}]
        
        return {
            **state,
            "messages": new_messages
        }
    
    def _node_observe(self, state: GraphState) -> GraphState:
        """观察节点 - 处理工具结果"""
        # 观察节点可以添加额外的处理逻辑
        # 目前只是传递状态
        return state
    
    def _node_finish(self, state: GraphState) -> GraphState:
        """完成节点"""
        messages = state["messages"]
        
        # 获取最后一条助手消息作为最终答案
        final_answer = ""
        for msg in reversed(messages):
            if msg["role"] == "assistant":
                final_answer = msg["content"]
                break
        
        return {
            **state,
            "final_answer": final_answer
        }
    
    def _should_act(self, state: GraphState) -> str:
        """决定是行动还是结束"""
        tool_calls = state.get("tool_calls", [])
        if tool_calls:
            return "act"
        return "finish"
    
    def _should_continue(self, state: GraphState) -> str:
        """决定是否继续迭代"""
        iteration = state.get("iteration_count", 0)
        
        if iteration >= self.max_steps:
            return "finish"
        
        return "think"
    
    def _format_tools(self) -> str:
        """格式化工具描述"""
        lines = []
        for name, tool in self._tools.items():
            lines.append(f"- {name}: {tool['description']}")
        return "\n".join(lines)
    
    def _parse_tool_calls(self, content: str) -> List[Dict]:
        """解析工具调用"""
        import re
        tool_calls = []
        
        # 匹配格式: TOOL: tool_name PARAMS: {...}
        pattern = r'TOOL:\s*(\w+)\s*PARAMS:\s*(\{[^}]+\})'
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                import json
                params = json.loads(match[1])
                tool_calls.append({
                    "name": match[0],
                    "arguments": params
                })
            except json.JSONDecodeError:
                pass
        
        return tool_calls
    
    def run(self, input_text: str, **kwargs) -> str:
        """运行 Graph Agent"""
        self.state.status = AgentStatus.RUNNING
        
        # 初始化状态
        initial_state: GraphState = {
            "messages": [{"role": "user", "content": input_text}],
            "next_step": "think",
            "tool_calls": [],
            "final_answer": None,
            "iteration_count": 0
        }
        
        try:
            # 执行图
            final_state = self.graph.invoke(initial_state)
            
            # 更新 Agent 状态
            self.state.messages = final_state["messages"]
            self.state.current_step = final_state["iteration_count"]
            
            answer = final_state.get("final_answer", "")
            if not answer:
                # 如果没有最终答案，返回最后一条消息
                if final_state["messages"]:
                    answer = final_state["messages"][-1]["content"]
            
            self.state.status = AgentStatus.COMPLETED
            return answer
            
        except Exception as e:
            logger.error(f"Graph Agent 执行失败: {e}")
            self.state.status = AgentStatus.ERROR
            return f"执行出错: {str(e)}"
    
    async def arun(self, input_text: str, **kwargs) -> str:
        """异步运行"""
        # LangGraph 支持异步执行
        self.state.status = AgentStatus.RUNNING
        
        initial_state: GraphState = {
            "messages": [{"role": "user", "content": input_text}],
            "next_step": "think",
            "tool_calls": [],
            "final_answer": None,
            "iteration_count": 0
        }
        
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            self.state.messages = final_state["messages"]
            self.state.current_step = final_state["iteration_count"]
            
            answer = final_state.get("final_answer", "")
            if not answer and final_state["messages"]:
                answer = final_state["messages"][-1]["content"]
            
            self.state.status = AgentStatus.COMPLETED
            return answer
            
        except Exception as e:
            logger.error(f"Graph Agent 异步执行失败: {e}")
            self.state.status = AgentStatus.ERROR
            return f"执行出错: {str(e)}"


class MultiAgentGraph:
    """多 Agent 协作图"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.graph = None
    
    def add_agent(self, name: str, agent: BaseAgent):
        """添加 Agent"""
        self.agents[name] = agent
    
    def build_collaboration_graph(self):
        """构建协作图"""
        # 定义状态
        class CollaborationState(TypedDict):
            current_agent: str
            input_text: str
            intermediate_results: List[str]
            final_output: Optional[str]
        
        workflow = StateGraph(CollaborationState)
        
        # 为每个 Agent 添加节点
        for name, agent in self.agents.items():
            workflow.add_node(
                name,
                lambda state, agent=agent: self._run_agent_node(agent, state)
            )
        
        # 添加路由逻辑
        # 这里可以实现复杂的路由策略
        
        workflow.set_entry_point(list(self.agents.keys())[0])
        workflow.add_edge(list(self.agents.keys())[-1], END)
        
        self.graph = workflow.compile()
    
    def _run_agent_node(self, agent: BaseAgent, state: Dict) -> Dict:
        """运行 Agent 节点"""
        input_text = state.get("input_text", "")
        result = agent.run(input_text)
        
        return {
            **state,
            "intermediate_results": state.get("intermediate_results", []) + [result]
        }
