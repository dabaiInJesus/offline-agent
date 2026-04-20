"""
Ollama 本地大模型连接模块
支持多种 Ollama 模型，包括对话和嵌入功能
"""
from typing import AsyncIterator, Iterator, List, Optional, Any, Dict
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
from langchain_core.embeddings import Embeddings
from pydantic import Field, BaseModel
from config import ollama_config
from loguru import logger


class OllamaEmbeddings(Embeddings, BaseModel):
    """Ollama 嵌入模型封装"""
    
    base_url: str = Field(default=ollama_config.base_url)
    model: str = Field(default="nomic-embed-text:latest")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _embed(self, texts: List[str]) -> List[List[float]]:
        """同步嵌入文本"""
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                embeddings.append(result["embedding"])
            except Exception as e:
                logger.error(f"嵌入生成失败: {e}")
                raise
        return embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表"""
        return self._embed(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        return self._embed([text])[0]
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入文档列表"""
        embeddings = []
        async with aiohttp.ClientSession() as session:
            for text in texts:
                try:
                    async with session.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text}
                    ) as response:
                        result = await response.json()
                        embeddings.append(result["embedding"])
                except Exception as e:
                    logger.error(f"异步嵌入生成失败: {e}")
                    raise
        return embeddings
    
    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入查询文本"""
        return (await self.aembed_documents([text]))[0]


class OllamaLLM(BaseChatModel, BaseModel):
    """
    Ollama 本地大语言模型封装
    支持流式输出、多轮对话、工具调用
    """
    
    base_url: str = Field(default=ollama_config.base_url)
    model: str = Field(default=ollama_config.model)
    temperature: float = Field(default=ollama_config.temperature)
    timeout: int = Field(default=ollama_config.timeout)
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def _llm_type(self) -> str:
        return "ollama"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "base_url": self.base_url,
        }
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """将 LangChain 消息转换为 Ollama 格式"""
        ollama_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                ollama_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                ollama_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                ollama_messages.append({"role": "system", "content": msg.content})
            else:
                ollama_messages.append({"role": "user", "content": str(msg.content)})
        return ollama_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成回复"""
        try:
            ollama_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                }
            }
            
            if stop:
                payload["options"]["stop"] = stop
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            message = AIMessage(content=result["message"]["content"])
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"Ollama 生成失败: {e}")
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
            ollama_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                }
            }
            
            if stop:
                payload["options"]["stop"] = stop
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            content = ""
            for line in response.iter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        delta = chunk["message"]["content"]
                        content += delta
                        yield ChatGeneration(message=AIMessage(content=content))
                        
        except Exception as e:
            logger.error(f"Ollama 流式生成失败: {e}")
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
            ollama_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                }
            }
            
            if stop:
                payload["options"]["stop"] = stop
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    result = await response.json()
                    
                    message = AIMessage(content=result["message"]["content"])
                    generation = ChatGeneration(message=message)
                    
                    return ChatResult(generations=[generation])
                    
        except Exception as e:
            logger.error(f"Ollama 异步生成失败: {e}")
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
            ollama_messages = self._convert_messages(messages)
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                }
            }
            
            if stop:
                payload["options"]["stop"] = stop
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    content = ""
                    async for line in response.content:
                        if line:
                            import json
                            line_str = line.decode('utf-8').strip()
                            if line_str:
                                chunk = json.loads(line_str)
                                if "message" in chunk and "content" in chunk["message"]:
                                    delta = chunk["message"]["content"]
                                    content += delta
                                    yield ChatGeneration(message=AIMessage(content=content))
                                    
        except Exception as e:
            logger.error(f"Ollama 异步流式生成失败: {e}")
            raise
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出可用的 Ollama 模型"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """拉取 Ollama 模型"""
        try:
            logger.info(f"正在拉取模型: {model_name}")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=300
            )
            
            for line in response.iter_lines():
                if line:
                    import json
                    status = json.loads(line)
                    if "status" in status:
                        logger.info(f"拉取进度: {status['status']}")
            
            return True
        except Exception as e:
            logger.error(f"拉取模型失败: {e}")
            return False


# 便捷函数
def get_llm(model: Optional[str] = None, temperature: Optional[float] = None) -> OllamaLLM:
    """获取 Ollama LLM 实例"""
    return OllamaLLM(
        model=model or ollama_config.model,
        temperature=temperature or ollama_config.temperature
    )


def get_embeddings(model: str = "nomic-embed-text:latest") -> OllamaEmbeddings:
    """获取 Ollama 嵌入模型实例"""
    return OllamaEmbeddings(model=model)
