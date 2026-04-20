"""
模型模块测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from models.ollama_model import OllamaLLM, get_llm, get_embeddings


class TestOllamaLLM:
    """测试 OllamaLLM 类"""
    
    def test_initialization(self):
        """测试初始化"""
        llm = OllamaLLM(model="qwen2.5:14b", base_url="http://localhost:11434")
        assert llm.model == "qwen2.5:14b"
        assert llm.base_url == "http://localhost:11434"
    
    @patch('models.ollama_model.ChatOllama')
    def test_invoke(self, mock_chat_ollama):
        """测试调用模型"""
        # 设置 mock
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="测试响应")
        mock_chat_ollama.return_value = mock_instance
        
        llm = OllamaLLM(model="qwen2.5:14b")
        
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content="你好")]
        
        result = llm.invoke(messages)
        
        assert result.content == "测试响应"
        mock_instance.invoke.assert_called_once_with(messages)
    
    @patch('models.ollama_model.ChatOllama')
    def test_stream(self, mock_chat_ollama):
        """测试流式输出"""
        mock_instance = MagicMock()
        mock_instance.stream.return_value = [
            MagicMock(content="第一"),
            MagicMock(content="第二")
        ]
        mock_chat_ollama.return_value = mock_instance
        
        llm = OllamaLLM(model="qwen2.5:14b")
        
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content="你好")]
        
        chunks = list(llm.stream(messages))
        
        assert len(chunks) == 2
        assert chunks[0].content == "第一"
        assert chunks[1].content == "第二"


class TestGetLLM:
    """测试 get_llm 函数"""
    
    @patch('models.ollama_model.ChatOllama')
    def test_get_llm_default(self, mock_chat_ollama):
        """测试获取默认 LLM"""
        mock_instance = MagicMock()
        mock_chat_ollama.return_value = mock_instance
        
        llm = get_llm()
        
        assert llm is not None
        mock_chat_ollama.assert_called_once()


class TestGetEmbeddings:
    """测试 get_embeddings 函数"""
    
    @patch('models.ollama_model.OllamaEmbeddings')
    def test_get_embeddings_default(self, mock_embeddings):
        """测试获取默认嵌入模型"""
        mock_instance = MagicMock()
        mock_embeddings.return_value = mock_instance
        
        embeddings = get_embeddings()
        
        assert embeddings is not None
        mock_embeddings.assert_called_once()
