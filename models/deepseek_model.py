"""
DeepSeek 云端大模型连接模块
支持 DeepSeek Chat API (OpenAI 兼容格式)
"""
from typing import AsyncIterator, Iterator, List, Optional, Any, Dict
import os
import aiohttp
import requests
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field, BaseModel, field_validator
from loguru import logger


class DeepSeekConfig(BaseModel):
    """DeepSeek 配置"""
    api_key: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    base_url: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    model: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    temperature: float = Field(default=0.7)
    timeout: int = Field(default=120)
    
    @field_validator('api_key')
    @classmethod
    def check_api_key(cls, v: str) -> str:
        if not v:
            logger.warning("DeepSeek API key 未设置，请设置 DEEPSEEK_API_KEY 环境变量")
        return v


# 全局配置实例
deepseek_config = DeepSeekConfig()


class DeepSeekLLM(BaseChatModel, BaseModel):
    """
    DeepSeek 大语言模型封装
    支持流式输出、多轮对话
    """
    
    base_url: str = Field(default=deepseek_config.base_url)
    api_key: str = Field(default=deepseek_config.api_key)
    model: str = Field(default=deepseek_config.model)
    temperature: float = Field(default=deepseek_config.temperature)
    timeout: int = Field(default=deepseek_config.timeout)
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "base_url": self.base_url,
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """将 LangChain 消息转换为 DeepSeek 格式"""
        deepseek_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                deepseek_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                deepseek_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                deepseek_messages.append({"role": "system", "content": msg.content})
            else:
                deepseek_messages.append({"role": "user", "content": str(msg.content)})
        return deepseek_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成回复"""
        try:
            deepseek_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": deepseek_messages,
                "stream": False,
                "temperature": self.temperature,
            }
            
            if stop:
                payload["stop"] = stop
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            message = AIMessage(content=result["choices"][0]["message"]["content"])
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"DeepSeek 生成失败: {e}")
            raise
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """流式生成回复"""
        try:
            deepseek_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": deepseek_messages,
                "stream": True,
                "temperature": self.temperature,
            }
            
            if stop:
                payload["stop"] = stop
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    if line_str == "[DONE]":
                        break
                    if line_str:
                        import json
                        chunk = json.loads(line_str)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                content += delta
                                yield ChatGeneration(message=AIMessage(content=content))
                                
        except Exception as e:
            logger.error(f"DeepSeek 流式生成失败: {e}")
            raise
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成回复"""
        try:
            deepseek_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": deepseek_messages,
                "stream": False,
                "temperature": self.temperature,
            }
            
            if stop:
                payload["stop"] = stop
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    result = await response.json()
                    
                    message = AIMessage(content=result["choices"][0]["message"]["content"])
                    generation = ChatGeneration(message=message)
                    
                    return ChatResult(generations=[generation])
                    
        except Exception as e:
            logger.error(f"DeepSeek 异步生成失败: {e}")
            raise
    
    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGeneration]:
        """异步流式生成回复"""
        try:
            deepseek_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": deepseek_messages,
                "stream": True,
                "temperature": self.temperature,
            }
            
            if stop:
                payload["stop"] = stop
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    content = ""
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith("data: "):
                                line_str = line_str[6:]
                            if line_str == "[DONE]":
                                break
                            if line_str:
                                import json
                                chunk = json.loads(line_str)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {}).get("content", "")
                                    if delta:
                                        content += delta
                                        yield ChatGeneration(message=AIMessage(content=content))
                                        
        except Exception as e:
            logger.error(f"DeepSeek 异步流式生成失败: {e}")
            raise


# 便捷函数
def get_deepseek_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None
) -> DeepSeekLLM:
    """获取 DeepSeek LLM 实例"""
    return DeepSeekLLM(
        api_key=api_key or deepseek_config.api_key,
        model=model or deepseek_config.model,
        temperature=temperature or deepseek_config.temperature
    )


def is_deepseek_available() -> bool:
    """检查 DeepSeek API 是否可用"""
    if not deepseek_config.api_key:
        return False
    try:
        response = requests.get(
            f"{deepseek_config.base_url}/models",
            headers={"Authorization": f"Bearer {deepseek_config.api_key}"},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False
