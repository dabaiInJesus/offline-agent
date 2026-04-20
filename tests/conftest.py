"""
Pytest 配置文件
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def mock_ollama():
    """模拟 Ollama 连接的 fixture"""
    from unittest.mock import patch, MagicMock
    
    with patch('models.ollama_model.ChatOllama') as mock_chat, \
         patch('models.ollama_model.OllamaEmbeddings') as mock_embed:
        
        mock_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance
        
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        
        yield {
            'chat': mock_chat_instance,
            'embed': mock_embed_instance
        }


@pytest.fixture
def clean_registry():
    """提供干净的技能注册表"""
    from skills.registry import SkillRegistry
    return SkillRegistry()


@pytest.fixture
def test_client():
    """FastAPI 测试客户端"""
    from fastapi.testclient import TestClient
    from webapp.backend.main import app
    return TestClient(app)
