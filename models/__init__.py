"""
模型模块 - 提供大语言模型连接和管理
"""
from .ollama_model import OllamaLLM, OllamaEmbeddings

__all__ = ["OllamaLLM", "OllamaEmbeddings"]
