"""
技能系统测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from skills.base import SkillResult, AgentSkill
from skills.registry import SkillRegistry, skill_registry, register, execute_skill


class TestSkillResult:
    """测试 SkillResult 类"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = SkillResult.success(data={"key": "value"}, message="操作成功")
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.message == "操作成功"
        assert result.error is None
    
    def test_error_result(self):
        """测试错误结果"""
        result = SkillResult.error(message="操作失败", error="错误详情")
        assert result.success is False
        assert result.data is None
        assert result.message == "操作失败"
        assert result.error == "错误详情"
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = SkillResult.success(data={"key": "value"})
        data = result.to_dict()
        assert data["success"] is True
        assert data["data"] == {"key": "value"}


class TestAgentSkill:
    """测试 AgentSkill 基类"""
    
    def test_abstract_methods(self):
        """测试抽象方法"""
        with pytest.raises(TypeError):
            AgentSkill()  # 不能直接实例化抽象类
    
    def test_concrete_skill(self):
        """测试具体技能实现"""
        class TestSkill(AgentSkill):
            @property
            def name(self):
                return "test_skill"
            
            @property
            def description(self):
                return "测试技能"
            
            @property
            def parameters(self):
                return {"param1": {"type": "string", "required": True}}
            
            def execute(self, **kwargs):
                return SkillResult.success(data=kwargs)
        
        skill = TestSkill()
        assert skill.name == "test_skill"
        assert skill.description == "测试技能"
        
        result = skill.execute(param1="test")
        assert result.success is True
        assert result.data == {"param1": "test"}


class TestSkillRegistry:
    """测试 SkillRegistry 类"""
    
    def setup_method(self):
        """每个测试前重置注册表"""
        self.registry = SkillRegistry()
    
    def test_register_skill(self):
        """测试注册技能"""
        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        
        self.registry.register(mock_skill)
        
        assert "test_skill" in self.registry._skills
        assert self.registry._skills["test_skill"] == mock_skill
    
    def test_get_skill(self):
        """测试获取技能"""
        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        
        self.registry.register(mock_skill)
        retrieved = self.registry.get("test_skill")
        
        assert retrieved == mock_skill
    
    def test_get_nonexistent_skill(self):
        """测试获取不存在的技能"""
        result = self.registry.get("nonexistent")
        assert result is None
    
    def test_list_skills(self):
        """测试列出所有技能"""
        mock_skill1 = MagicMock()
        mock_skill1.name = "skill1"
        mock_skill2 = MagicMock()
        mock_skill2.name = "skill2"
        
        self.registry.register(mock_skill1)
        self.registry.register(mock_skill2)
        
        skills = self.registry.list_skills()
        assert len(skills) == 2
        assert "skill1" in skills
        assert "skill2" in skills
    
    def test_list_skill_info(self):
        """测试列出技能信息"""
        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.description = "测试描述"
        mock_skill.parameters = {"param1": {"type": "string"}}
        
        self.registry.register(mock_skill)
        info = self.registry.list_skill_info()
        
        assert len(info) == 1
        assert info[0]["name"] == "test_skill"
        assert info[0]["description"] == "测试描述"


class TestRegisterDecorator:
    """测试注册装饰器"""
    
    def test_register_decorator(self):
        """测试装饰器注册技能"""
        @register
        class TestSkill(AgentSkill):
            @property
            def name(self):
                return "decorated_skill"
            
            @property
            def description(self):
                return "装饰器测试技能"
            
            @property
            def parameters(self):
                return {}
            
            def execute(self, **kwargs):
                return SkillResult.success()
        
        assert "decorated_skill" in skill_registry.list_skills()


class TestExecuteSkill:
    """测试 execute_skill 函数"""
    
    @patch('skills.registry.skill_registry')
    def test_execute_existing_skill(self, mock_registry):
        """测试执行存在的技能"""
        mock_skill = MagicMock()
        mock_skill.execute.return_value = SkillResult.success(data={"result": "ok"})
        mock_registry.get.return_value = mock_skill
        
        result = execute_skill("test_skill", param="value")
        
        assert result.success is True
        mock_skill.execute.assert_called_once_with(param="value")
    
    @patch('skills.registry.skill_registry')
    def test_execute_nonexistent_skill(self, mock_registry):
        """测试执行不存在的技能"""
        mock_registry.get.return_value = None
        
        result = execute_skill("nonexistent")
        
        assert result.success is False
        assert "未找到" in result.message
