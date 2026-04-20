"""
ReAct Agent - 推理和行动循环
"""
import json
import re
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from loguru import logger

from .base import BaseAgent, AgentState, AgentStatus


class ReActAgent(BaseAgent):
    """
    ReAct (Reasoning + Acting) Agent
    通过推理和行动循环解决问题
    """
    
    REACT_PROMPT_TEMPLATE = """你是一个能够使用工具解决问题的AI助手。你可以通过以下步骤完成任务：
1. 思考 (Thought): 分析问题并决定下一步行动
2. 行动 (Action): 选择并使用合适的工具
3. 观察 (Observation): 观察工具返回的结果
4. 回答 (Answer): 给出最终答案

你可以使用以下工具：
{tools}

请按以下格式输出：
Thought: 你的思考过程
Action: 工具名称
Action Input: 工具的输入参数（JSON格式）

或者当你有最终答案时：
Thought: 我已经得到了答案
Answer: 你的最终答案

当前任务：{input}

{history}

请继续："""
    
    def __init__(
        self,
        name: str = "react_agent",
        llm=None,
        system_prompt: str = None,
        max_steps: int = 10
    ):
        super().__init__(name, llm, system_prompt, max_steps)
        self._action_pattern = re.compile(
            r'Thought:\s*(.*?)\s*Action:\s*(\w+)\s*Action Input:\s*(\{.*?\})',
            re.DOTALL
        )
        self._answer_pattern = re.compile(
            r'Thought:\s*(.*?)\s*Answer:\s*(.*)',
            re.DOTALL
        )
    
    def _format_tools(self) -> str:
        """格式化工具描述"""
        tool_descriptions = []
        for name, tool in self._tools.items():
            tool_descriptions.append(f"- {name}: {tool['description']}")
        return "\n".join(tool_descriptions)
    
    def _format_history(self) -> str:
        """格式化历史记录"""
        if not self.state.messages:
            return ""
        
        history_lines = []
        for msg in self.state.messages[-6:]:  # 只保留最近6条
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "observation":
                history_lines.append(f"Observation: {content}")
            elif role == "assistant":
                history_lines.append(f"Assistant: {content}")
        
        return "\n\n".join(history_lines)
    
    def _parse_action(self, text: str) -> Optional[Dict[str, Any]]:
        """解析行动"""
        # 尝试匹配行动模式
        action_match = self._action_pattern.search(text)
        if action_match:
            thought = action_match.group(1).strip()
            action_name = action_match.group(2).strip()
            action_input = action_match.group(3).strip()
            
            try:
                action_params = json.loads(action_input)
            except json.JSONDecodeError:
                action_params = {"input": action_input}
            
            return {
                "thought": thought,
                "action": action_name,
                "action_input": action_params
            }
        
        # 尝试匹配答案模式
        answer_match = self._answer_pattern.search(text)
        if answer_match:
            return {
                "thought": answer_match.group(1).strip(),
                "answer": answer_match.group(2).strip()
            }
        
        return None
    
    def _execute_action(self, action_name: str, action_input: Dict) -> str:
        """执行工具"""
        tool = self._tools.get(action_name)
        if not tool:
            return f"错误：工具 '{action_name}' 不存在"
        
        try:
            result = tool["func"](**action_input)
            return str(result)
        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return f"工具执行错误: {str(e)}"
    
    def run(self, input_text: str, **kwargs) -> str:
        """
        运行 ReAct Agent
        
        Args:
            input_text: 用户输入
            
        Returns:
            最终答案
        """
        self.state.status = AgentStatus.RUNNING
        self.state.add_message("user", input_text)
        
        try:
            for step in range(self.max_steps):
                self.state.current_step = step
                
                # 构建提示词
                prompt = self.REACT_PROMPT_TEMPLATE.format(
                    tools=self._format_tools(),
                    input=input_text,
                    history=self._format_history()
                )
                
                # 调用 LLM
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt)
                ]
                response = self.llm.invoke(messages)
                content = response.content
                
                # 解析响应
                parsed = self._parse_action(content)
                
                if not parsed:
                    # 无法解析，直接返回内容
                    self.state.add_message("assistant", content)
                    self.state.status = AgentStatus.COMPLETED
                    return content
                
                if "answer" in parsed:
                    # 得到最终答案
                    answer = parsed["answer"]
                    self.state.add_message("assistant", answer, thought=parsed.get("thought"))
                    self.state.status = AgentStatus.COMPLETED
                    return answer
                
                # 执行工具
                action_name = parsed["action"]
                action_input = parsed["action_input"]
                
                self.state.add_message(
                    "assistant",
                    f"Action: {action_name}",
                    thought=parsed.get("thought"),
                    action=action_name,
                    action_input=action_input
                )
                
                # 执行并观察
                observation = self._execute_action(action_name, action_input)
                self.state.add_message("observation", observation)
                
                # 通知回调
                self._notify_callbacks("step", {
                    "step": step,
                    "action": action_name,
                    "observation": observation
                })
            
            # 达到最大步数
            self.state.status = AgentStatus.ERROR
            return "已达到最大执行步数，无法完成任务。"
            
        except Exception as e:
            logger.error(f"ReAct Agent 执行失败: {e}")
            self.state.status = AgentStatus.ERROR
            return f"执行出错: {str(e)}"
    
    async def arun(self, input_text: str, **kwargs) -> str:
        """异步运行"""
        # 简化实现，直接调用同步版本
        return self.run(input_text, **kwargs)


class SimpleReActAgent(ReActAgent):
    """简化版 ReAct Agent - 更轻量的实现"""
    
    def run(self, input_text: str, **kwargs) -> str:
        """简化运行逻辑"""
        self.state.status = AgentStatus.RUNNING
        
        # 单步推理+行动
        prompt = f"""请回答以下问题。如果需要使用工具，请说明你会使用什么工具。

可用工具：
{self._format_tools()}

问题：{input_text}

请给出你的思考过程和最终答案："""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        content = response.content
        
        self.state.add_message("assistant", content)
        self.state.status = AgentStatus.COMPLETED
        
        return content
