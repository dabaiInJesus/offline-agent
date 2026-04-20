"""
Tool Agent - 工具调用型 Agent
"""
import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import Tool
from loguru import logger

from .base import BaseAgent, AgentStatus


class ToolAgent(BaseAgent):
    """
    工具调用型 Agent
    支持函数调用 (Function Calling) 风格的工具使用
    """
    
    def __init__(
        self,
        name: str = "tool_agent",
        llm=None,
        system_prompt: str = None,
        max_steps: int = 10
    ):
        super().__init__(name, llm, system_prompt, max_steps)
        self._tool_schemas: List[Dict] = []
    
    def register_tool(self, name: str, func: callable, description: str = None, parameters: Dict = None):
        """注册工具（带参数描述）"""
        super().register_tool(name, func, description)
        
        # 构建工具 schema
        import inspect
        sig = inspect.signature(func)
        
        if parameters is None:
            # 自动从函数签名生成参数
            properties = {}
            required = []
            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"参数: {param_name}"
                }
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            parameters = {
                "type": "object",
                "properties": properties,
                "required": required
            }
        
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description or func.__doc__ or f"工具: {name}",
                "parameters": parameters
            }
        }
        self._tool_schemas.append(schema)
    
    def _get_tool_definitions(self) -> List[Dict]:
        """获取工具定义（用于 LLM）"""
        return self._tool_schemas
    
    def _execute_tool_call(self, tool_call: Dict) -> str:
        """执行工具调用"""
        function_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
        arguments = tool_call.get("arguments") or tool_call.get("function", {}).get("arguments", {})
        
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return f"参数解析错误: {arguments}"
        
        tool = self._tools.get(function_name)
        if not tool:
            return f"工具 '{function_name}' 不存在"
        
        try:
            result = tool["func"](**arguments)
            return str(result) if result is not None else "执行成功"
        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return f"执行错误: {str(e)}"
    
    def run(self, input_text: str, **kwargs) -> str:
        """
        运行 Tool Agent
        
        Args:
            input_text: 用户输入
            
        Returns:
            最终答案
        """
        self.state.status = AgentStatus.RUNNING
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=input_text)
        ]
        
        try:
            for step in range(self.max_steps):
                self.state.current_step = step
                
                # 调用 LLM
                # 注意：这里假设 LLM 支持工具调用
                # 如果不支持，需要手动处理工具调用逻辑
                response = self.llm.invoke(messages)
                content = response.content
                
                # 检查是否有工具调用
                # 这里简化处理，实际应根据 LLM 的响应格式处理
                tool_calls = self._extract_tool_calls(content)
                
                if not tool_calls:
                    # 没有工具调用，直接返回结果
                    self.state.add_message("assistant", content)
                    self.state.status = AgentStatus.COMPLETED
                    return content
                
                # 执行工具调用
                for tool_call in tool_calls:
                    self.state.add_message(
                        "assistant",
                        f"调用工具: {tool_call.get('name')}",
                        tool_call=tool_call
                    )
                    
                    result = self._execute_tool_call(tool_call)
                    
                    self.state.add_message(
                        "tool",
                        result,
                        tool_name=tool_call.get("name")
                    )
                    
                    # 添加工具结果到消息
                    messages.append(AIMessage(content=f"我将使用工具: {tool_call.get('name')}"))
                    messages.append(HumanMessage(content=f"工具返回结果: {result}"))
                
                # 通知回调
                self._notify_callbacks("step", {
                    "step": step,
                    "tool_calls": tool_calls
                })
            
            self.state.status = AgentStatus.ERROR
            return "已达到最大执行步数"
            
        except Exception as e:
            logger.error(f"Tool Agent 执行失败: {e}")
            self.state.status = AgentStatus.ERROR
            return f"执行出错: {str(e)}"
    
    def _extract_tool_calls(self, content: str) -> List[Dict]:
        """从 LLM 响应中提取工具调用"""
        tool_calls = []
        
        # 尝试解析 JSON 格式的工具调用
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                data = json.loads(json_str)
                if isinstance(data, dict) and "tool" in data:
                    tool_calls.append({
                        "name": data["tool"],
                        "arguments": data.get("arguments", {})
                    })
        except Exception:
            pass
        
        # 尝试解析特定格式: TOOL: name ARGS: {...}
        import re
        pattern = r'TOOL:\s*(\w+)\s*ARGS:\s*(\{[^}]+\})'
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            try:
                tool_calls.append({
                    "name": match[0],
                    "arguments": json.loads(match[1])
                })
            except json.JSONDecodeError:
                pass
        
        return tool_calls
    
    async def arun(self, input_text: str, **kwargs) -> str:
        """异步运行"""
        return self.run(input_text, **kwargs)


class PlanAndExecuteAgent(ToolAgent):
    """
    计划-执行型 Agent
    先制定计划，再逐步执行
    """
    
    def run(self, input_text: str, **kwargs) -> str:
        """运行计划-执行 Agent"""
        self.state.status = AgentStatus.RUNNING
        
        # 第一步：制定计划
        plan_prompt = f"""请为以下任务制定一个详细的执行计划：

任务：{input_text}

可用工具：
{self._format_tools()}

请按以下格式输出执行计划：
1. [步骤1描述] -> 使用工具: [工具名]
2. [步骤2描述] -> 使用工具: [工具名]
...

执行计划："""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=plan_prompt)
        ]
        
        response = self.llm.invoke(messages)
        plan = response.content
        
        self.state.add_message("plan", plan)
        self.state.memory["plan"] = plan
        
        # 第二步：执行计划
        execute_prompt = f"""请按照以下计划执行任务：

计划：
{plan}

原始任务：{input_text}

请逐步执行，每完成一步报告结果。"""
        
        messages.append(HumanMessage(content=execute_prompt))
        
        # 使用父类的工具调用逻辑
        result = super().run(execute_prompt)
        
        return f"计划：\n{plan}\n\n执行结果：\n{result}"
    
    def _format_tools(self) -> str:
        """格式化工具列表"""
        lines = []
        for name, tool in self._tools.items():
            lines.append(f"- {name}: {tool['description']}")
        return "\n".join(lines)
