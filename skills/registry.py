"""
技能注册表 - 管理和发现所有可用技能
"""
from typing import Dict, Type, List, Optional, Any
from loguru import logger

from .base import BaseSkill, SkillResult


class SkillRegistry:
    """
    技能注册表
    单例模式管理所有技能
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: Dict[str, Type[BaseSkill]] = {}
            cls._instance._instances: Dict[str, BaseSkill] = {}
        return cls._instance
    
    def register(self, skill_class: Type[BaseSkill], name: str = None):
        """
        注册技能类
        
        Args:
            skill_class: 技能类
            name: 自定义名称，默认使用 skill_class.name
        """
        skill_name = name or skill_class.name
        self._skills[skill_name] = skill_class
        logger.info(f"注册技能: {skill_name}")
    
    def unregister(self, name: str):
        """注销技能"""
        if name in self._skills:
            del self._skills[name]
            if name in self._instances:
                del self._instances[name]
            logger.info(f"注销技能: {name}")
    
    def get_skill_class(self, name: str) -> Optional[Type[BaseSkill]]:
        """获取技能类"""
        return self._skills.get(name)
    
    def create_skill(self, name: str, config: Dict[str, Any] = None) -> Optional[BaseSkill]:
        """
        创建技能实例
        
        Args:
            name: 技能名称
            config: 技能配置
            
        Returns:
            技能实例
        """
        skill_class = self.get_skill_class(name)
        if not skill_class:
            logger.error(f"技能 '{name}' 未注册")
            return None
        
        return skill_class(config)
    
    def get_or_create(self, name: str, config: Dict[str, Any] = None) -> Optional[BaseSkill]:
        """获取或创建技能实例（单例）"""
        if name not in self._instances:
            skill = self.create_skill(name, config)
            if skill:
                self._instances[name] = skill
        
        return self._instances.get(name)
    
    def execute(self, name: str, **kwargs) -> SkillResult:
        """
        执行技能
        
        Args:
            name: 技能名称
            **kwargs: 执行参数
            
        Returns:
            执行结果
        """
        skill = self.get_or_create(name)
        if not skill:
            return SkillResult.error(f"技能 '{name}' 不存在")
        
        return skill.execute(**kwargs)
    
    def list_skills(self) -> List[str]:
        """列出所有已注册的技能"""
        return list(self._skills.keys())
    
    def list_skill_info(self) -> List[Dict[str, Any]]:
        """列出所有技能信息"""
        info = []
        for name, skill_class in self._skills.items():
            info.append({
                "name": name,
                "description": skill_class.description,
                "version": skill_class.version,
                "tags": skill_class.tags,
                "parameters": skill_class.parameters
            })
        return info
    
    def find_by_tag(self, tag: str) -> List[str]:
        """按标签查找技能"""
        matching = []
        for name, skill_class in self._skills.items():
            if tag in skill_class.tags:
                matching.append(name)
        return matching
    
    def search(self, keyword: str) -> List[str]:
        """搜索技能"""
        matching = []
        keyword_lower = keyword.lower()
        
        for name, skill_class in self._skills.items():
            if (keyword_lower in name.lower() or
                keyword_lower in skill_class.description.lower() or
                any(keyword_lower in tag.lower() for tag in skill_class.tags)):
                matching.append(name)
        
        return matching
    
    def clear(self):
        """清空所有技能"""
        self._skills.clear()
        self._instances.clear()
        logger.info("技能注册表已清空")


# 全局技能注册表实例
skill_registry = SkillRegistry()


def register_skill(skill_class: Type[BaseSkill]):
    """装饰器：自动注册技能"""
    skill_registry.register(skill_class)
    return skill_class


def get_skill(name: str) -> Optional[BaseSkill]:
    """获取技能实例"""
    return skill_registry.get_or_create(name)


def execute_skill(name: str, **kwargs) -> SkillResult:
    """执行技能"""
    return skill_registry.execute(name, **kwargs)


def list_skills() -> List[str]:
    """列出所有技能"""
    return skill_registry.list_skills()


def discover_skills():
    """自动发现并注册所有内置技能"""
    from .db_skill import DatabaseSkill, SQLAnalysisSkill, DataExportSkill
    from .rag_skill import RAGSkill, KnowledgeBaseManageSkill, MultiKBRAGSkill
    from .code_skill import CodeSkill, CodeAnalysisSkill, CodeGenerateSkill, CodeRefactorSkill
    from .web_skill import WebSkill, WebScrapeSkill, APIQuerySkill, RSSFeedSkill
    
    skills = [
        DatabaseSkill,
        SQLAnalysisSkill,
        DataExportSkill,
        RAGSkill,
        KnowledgeBaseManageSkill,
        MultiKBRAGSkill,
        CodeSkill,
        CodeAnalysisSkill,
        CodeGenerateSkill,
        CodeRefactorSkill,
        WebSkill,
        WebScrapeSkill,
        APIQuerySkill,
        RSSFeedSkill,
    ]
    
    for skill_class in skills:
        skill_registry.register(skill_class)
    
    logger.info(f"自动发现并注册了 {len(skills)} 个技能")
    return skills
