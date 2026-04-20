"""
Skill 基类 - 定义可复用的 Agent 技能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class SkillStatus(Enum):
    """技能执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(cls, data: Any = None, message: str = "", **kwargs) -> "SkillResult":
        """创建成功结果"""
        return cls(
            success=True,
            data=data,
            message=message,
            metadata=kwargs
        )
    
    @classmethod
    def error(cls, error: str, message: str = "", **kwargs) -> "SkillResult":
        """创建失败结果"""
        return cls(
            success=False,
            error=error,
            message=message,
            metadata=kwargs
        )


@dataclass
class SkillContext:
    """技能执行上下文"""
    input_data: Any = None
    memory: Dict[str, Any] = field(default_factory=dict)
    parent_context: Optional["SkillContext"] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default=None):
        """获取上下文值"""
        return self.memory.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置上下文值"""
        self.memory[key] = value
    
    def fork(self, **kwargs) -> "SkillContext":
        """创建子上下文"""
        return SkillContext(
            memory=self.memory.copy(),
            parent_context=self,
            **kwargs
        )


class BaseSkill(ABC):
    """
    技能基类
    所有可复用技能的基础抽象类
    """
    
    # 技能元数据
    name: str = "base_skill"
    description: str = "基础技能"
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = []
    
    # 参数定义
    parameters: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._status = SkillStatus.PENDING
        self._callbacks: List[Callable] = []
    
    @property
    def status(self) -> SkillStatus:
        return self._status
    
    def add_callback(self, callback: Callable):
        """添加执行回调"""
        self._callbacks.append(callback)
    
    def _notify(self, event: str, data: Any):
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(event, data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证参数"""
        for param_name, param_def in self.parameters.items():
            if param_def.get("required", False) and param_name not in params:
                return False, f"缺少必需参数: {param_name}"
            
            if param_name in params:
                value = params[param_name]
                param_type = param_def.get("type")
                
                if param_type and not isinstance(value, eval(param_type)):
                    return False, f"参数 {param_name} 类型错误，期望 {param_type}"
        
        return True, None
    
    def get_param_info(self) -> Dict[str, Dict[str, Any]]:
        """获取参数信息"""
        return self.parameters
    
    def execute(self, context: SkillContext = None, **kwargs) -> SkillResult:
        """
        执行技能
        
        Args:
            context: 执行上下文
            **kwargs: 执行参数
            
        Returns:
            执行结果
        """
        # 验证参数
        valid, error = self.validate_params(kwargs)
        if not valid:
            return SkillResult.error(error)
        
        # 创建上下文
        if context is None:
            context = SkillContext(input_data=kwargs)
        
        self._status = SkillStatus.RUNNING
        self._notify("start", {"skill": self.name, "params": kwargs})
        
        try:
            result = self._execute(context, **kwargs)
            self._status = SkillResult.SUCCESS if result.success else SkillStatus.FAILED
            self._notify("complete", {"skill": self.name, "result": result})
            return result
        except Exception as e:
            logger.error(f"技能执行失败 {self.name}: {e}")
            self._status = SkillStatus.FAILED
            error_result = SkillResult.error(str(e))
            self._notify("error", {"skill": self.name, "error": str(e)})
            return error_result
    
    @abstractmethod
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """子类实现的具体执行逻辑"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "parameters": self.parameters,
            "status": self._status.value
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', status='{self._status.value}')>"


class CompositeSkill(BaseSkill):
    """组合技能 - 由多个子技能组成"""
    
    name = "composite_skill"
    description = "组合多个技能的执行流程"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._skills: List[tuple[BaseSkill, Dict[str, Any]]] = []
        self._execution_mode = config.get("mode", "sequential")  # sequential/parallel
    
    def add_skill(self, skill: BaseSkill, params_map: Dict[str, str] = None):
        """
        添加子技能
        
        Args:
            skill: 技能实例
            params_map: 参数映射 {子技能参数名: 父参数名}
        """
        self._skills.append((skill, params_map or {}))
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行组合技能"""
        results = []
        
        for skill, params_map in self._skills:
            # 映射参数
            skill_params = {}
            for skill_param, parent_param in params_map.items():
                skill_params[skill_param] = kwargs.get(parent_param)
            
            # 执行子技能
            result = skill.execute(context, **skill_params)
            results.append(result)
            
            if not result.success:
                return SkillResult.error(
                    f"子技能 {skill.name} 执行失败: {result.error}",
                    partial_results=results
                )
            
            # 将结果存入上下文
            context.set(f"{skill.name}_result", result.data)
        
        return SkillResult.ok(
            data=[r.data for r in results],
            message="所有子技能执行成功"
        )


class ConditionalSkill(BaseSkill):
    """条件技能 - 根据条件选择执行路径"""
    
    name = "conditional_skill"
    description = "根据条件选择执行路径"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._branches: List[tuple[Callable, BaseSkill]] = []
        self._default_skill: Optional[BaseSkill] = None
    
    def add_branch(self, condition: Callable, skill: BaseSkill):
        """添加条件分支"""
        self._branches.append((condition, skill))
    
    def set_default(self, skill: BaseSkill):
        """设置默认分支"""
        self._default_skill = skill
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行条件技能"""
        for condition, skill in self._branches:
            if condition(context, **kwargs):
                return skill.execute(context, **kwargs)
        
        if self._default_skill:
            return self._default_skill.execute(context, **kwargs)
        
        return SkillResult.error("没有匹配的条件分支")


class LoopSkill(BaseSkill):
    """循环技能 - 重复执行直到满足条件"""
    
    name = "loop_skill"
    description = "循环执行技能"
    
    parameters = {
        "max_iterations": {
            "type": "int",
            "required": False,
            "default": 10,
            "description": "最大迭代次数"
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._skill: Optional[BaseSkill] = None
        self._condition: Optional[Callable] = None
    
    def set_loop(self, skill: BaseSkill, condition: Callable):
        """
        设置循环
        
        Args:
            skill: 要循环执行的技能
            condition: 循环条件函数，返回 True 继续循环
        """
        self._skill = skill
        self._condition = condition
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行循环技能"""
        max_iterations = kwargs.get("max_iterations", 10)
        results = []
        
        for i in range(max_iterations):
            # 执行技能
            result = self._skill.execute(context, **kwargs)
            results.append(result)
            
            # 检查条件
            if not self._condition(context, result, **kwargs):
                break
        
        return SkillResult.ok(
            data=results,
            message=f"循环执行 {len(results)} 次"
        )
