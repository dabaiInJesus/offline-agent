"""
FastAPI 后端 API 测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp.backend.main import app, app_state


client = TestClient(app)


class TestStatusAPI:
    """测试状态 API"""
    
    def test_get_status(self):
        """测试获取系统状态"""
        # 设置初始状态
        app_state["initialized"] = True
        
        response = client.get("/api/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["initialized"] is True
        assert "version" in data
        assert "timestamp" in data


class TestDatabaseAPI:
    """测试数据库 API"""
    
    @patch('webapp.backend.main.db_manager')
    def test_list_databases(self, mock_db_manager):
        """测试列出数据库"""
        mock_db_manager.list_databases.return_value = ["db1", "db2"]
        
        response = client.get("/api/databases")
        
        assert response.status_code == 200
        data = response.json()
        assert "databases" in data
        assert data["databases"] == ["db1", "db2"]
    
    @patch('webapp.backend.main.db_manager')
    def test_query_database(self, mock_db_manager):
        """测试数据库查询"""
        mock_db = MagicMock()
        mock_db.execute.return_value = [{"id": 1, "name": "test"}]
        mock_db_manager.get.return_value = mock_db
        
        response = client.post(
            "/api/database/query",
            json={"db_name": "test_db", "sql": "SELECT * FROM users"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
    
    @patch('webapp.backend.main.db_manager')
    def test_query_nonexistent_database(self, mock_db_manager):
        """测试查询不存在的数据库"""
        mock_db_manager.get.return_value = None
        
        response = client.post(
            "/api/database/query",
            json={"db_name": "nonexistent", "sql": "SELECT * FROM users"}
        )
        
        assert response.status_code == 404


class TestKnowledgeBaseAPI:
    """测试知识库 API"""
    
    @patch('webapp.backend.main.kb_manager')
    def test_list_knowledge_bases(self, mock_kb_manager):
        """测试列出知识库"""
        mock_kb_manager.list_knowledge_bases.return_value = ["kb1", "kb2"]
        
        mock_kb = MagicMock()
        mock_kb.get_stats.return_value = {
            "name": "kb1",
            "document_count": 10,
            "chunk_count": 50
        }
        mock_kb_manager.get.return_value = mock_kb
        
        response = client.get("/api/knowledge-bases")
        
        assert response.status_code == 200
        data = response.json()
        assert "knowledge_bases" in data
    
    @patch('webapp.backend.main.kb_manager')
    def test_query_knowledge_base(self, mock_kb_manager):
        """测试查询知识库"""
        mock_kb = MagicMock()
        mock_kb.query.return_value = {
            "answer": "测试答案",
            "sources": [{"content": "来源1"}]
        }
        mock_kb_manager.get.return_value = mock_kb
        
        response = client.post(
            "/api/knowledge-base/query",
            json={"kb_name": "test_kb", "query": "测试问题"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "测试答案"
        assert "sources" in data


class TestSkillsAPI:
    """测试技能 API"""
    
    @patch('webapp.backend.main.skill_registry')
    def test_list_skills(self, mock_skill_registry):
        """测试列出技能"""
        mock_skill_registry.list_skill_info.return_value = [
            {"name": "skill1", "description": "技能1"},
            {"name": "skill2", "description": "技能2"}
        ]
        
        response = client.get("/api/skills")
        
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert len(data["skills"]) == 2
    
    @patch('webapp.backend.main.execute_skill')
    def test_execute_skill(self, mock_execute_skill):
        """测试执行技能"""
        from skills.base import SkillResult
        mock_execute_skill.return_value = SkillResult.success(
            data={"result": "ok"},
            message="执行成功"
        )
        
        response = client.post(
            "/api/skill/execute",
            json={"skill_name": "test_skill", "parameters": {"key": "value"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["result"] == "ok"


class TestAgentAPI:
    """测试 Agent API"""
    
    @patch('webapp.backend.main.AgentFactory')
    def test_list_agent_types(self, mock_factory):
        """测试列出 Agent 类型"""
        mock_factory.list_agent_types.return_value = ["react", "tool", "graph"]
        
        response = client.get("/api/agents/types")
        
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "react" in data["types"]
    
    @patch('webapp.backend.main.create_agent')
    @patch('webapp.backend.main.app_state')
    def test_create_agent(self, mock_app_state, mock_create_agent):
        """测试创建 Agent"""
        mock_app_state.__getitem__ = Mock(return_value=MagicMock())
        
        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.list_tools.return_value = []
        mock_create_agent.return_value = mock_agent
        
        response = client.post(
            "/api/agent/create",
            json={"name": "test_agent", "agent_type": "react"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_name"] == "test_agent"


class TestChatAPI:
    """测试对话 API"""
    
    @patch('webapp.backend.main.app_state')
    @patch('webapp.backend.main.create_agent')
    def test_chat_with_agent(self, mock_create_agent, mock_app_state):
        """测试使用 Agent 对话"""
        mock_app_state.__getitem__ = Mock(return_value=MagicMock())
        mock_app_state.__contains__ = Mock(return_value=True)
        
        mock_agent = MagicMock()
        mock_agent.run.return_value = "这是回答"
        mock_agent.get_conversation_history.return_value = []
        mock_create_agent.return_value = mock_agent
        
        response = client.post(
            "/api/chat",
            json={"message": "你好", "agent_type": "react"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestModelAPI:
    """测试模型 API"""
    
    @patch('webapp.backend.main.app_state')
    def test_list_models(self, mock_app_state):
        """测试列出模型"""
        mock_llm = MagicMock()
        mock_llm.model = "qwen2.5:14b"
        mock_llm.list_models.return_value = ["qwen2.5:14b", "llama3.1"]
        mock_app_state.__getitem__ = Mock(return_value=mock_llm)
        
        response = client.get("/api/models")
        
        assert response.status_code == 200
        data = response.json()
        assert "current_model" in data
        assert "available_models" in data
