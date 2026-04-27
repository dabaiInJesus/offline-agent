"""
模型工厂 - 支持 Ollama 和 DeepSeek 切换
"""
from typing import Optional
import os
from loguru import logger

# 尝试导入两种模型
try:
    from models.ollama_model import OllamaLLM, get_llm as get_ollama_llm
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama 不可用")

try:
    from models.deepseek_model import DeepSeekLLM, get_deepseek_llm, deepseek_config
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    logger.warning("DeepSeek 不可用")

from config import ollama_config


class ModelProvider:
    """模型提供者枚举"""
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"


def get_active_provider() -> str:
    """获取当前激活的模型提供者"""
    return os.getenv("ACTIVE_PROVIDER", "ollama").lower()


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs
):
    """
    获取 LLM 实例
    
    Args:
        provider: 模型提供者 ('ollama' 或 'deepseek')
        model: 模型名称（可选）
        temperature: 温度参数（可选）
        **kwargs: 其他参数
    
    Returns:
        LLM 实例
    """
    provider = (provider or get_active_provider()).lower()
    
    if provider == ModelProvider.DEEPSEEK:
        if not DEEPSEEK_AVAILABLE:
            raise RuntimeError("DeepSeek 不可用，请检查是否已安装相关依赖")
        if not deepseek_config.api_key:
            raise RuntimeError("DeepSeek API key 未设置，请设置 DEEPSEEK_API_KEY 环境变量")
        return get_deepseek_llm(model=model, temperature=temperature, **kwargs)
    
    elif provider == ModelProvider.OLLAMA:
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama 不可用，请检查是否已安装相关依赖")
        return get_ollama_llm(model=model, temperature=temperature)
    
    else:
        raise ValueError(f"不支持的模型提供者: {provider}")


def is_model_available(provider: str = None) -> bool:
    """检查模型是否可用"""
    provider = (provider or get_active_provider()).lower()
    
    if provider == ModelProvider.DEEPSEEK:
        return DEEPSEEK_AVAILABLE and bool(deepseek_config.api_key)
    
    elif provider == ModelProvider.OLLAMA:
        return OLLAMA_AVAILABLE
    
    return False


def list_available_providers() -> list:
    """列出可用的模型提供者"""
    providers = []
    if OLLAMA_AVAILABLE:
        providers.append(ModelProvider.OLLAMA)
    if DEEPSEEK_AVAILABLE and deepseek_config.api_key:
        providers.append(ModelProvider.DEEPSEEK)
    return providers
