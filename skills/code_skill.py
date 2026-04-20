"""
代码技能 - 代码分析、生成和执行
"""
import os
import tempfile
from typing import Dict, Any, List, Optional
from .base import BaseSkill, SkillResult, SkillContext
from loguru import logger


class CodeSkill(BaseSkill):
    """
    代码执行技能
    执行 Python 代码并返回结果
    """
    
    name = "code_execute"
    description = "执行 Python 代码"
    version = "1.0.0"
    tags = ["code", "python", "execute"]
    
    parameters = {
        "code": {
            "type": "str",
            "required": True,
            "description": "要执行的 Python 代码"
        },
        "timeout": {
            "type": "int",
            "required": False,
            "default": 30,
            "description": "执行超时时间（秒）"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行代码"""
        code = kwargs.get("code", "")
        timeout = kwargs.get("timeout", 30)
        
        if not code.strip():
            return SkillResult.error("代码不能为空")
        
        try:
            # 创建安全的执行环境
            import subprocess
            import sys
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # 执行代码
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                output = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
                
                if result.returncode == 0:
                    return SkillResult.ok(
                        data=output,
                        message="代码执行成功"
                    )
                else:
                    return SkillResult.error(
                        error=result.stderr,
                        message="代码执行失败",
                        output=output
                    )
            finally:
                # 清理临时文件
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return SkillResult.error(f"代码执行超时（{timeout}秒）")
        except Exception as e:
            logger.error(f"代码执行失败: {e}")
            return SkillResult.error(str(e))


class CodeAnalysisSkill(BaseSkill):
    """
    代码分析技能
    分析代码质量、复杂度等
    """
    
    name = "code_analysis"
    description = "分析代码质量和复杂度"
    version = "1.0.0"
    tags = ["code", "analysis", "quality"]
    
    parameters = {
        "code": {
            "type": "str",
            "required": False,
            "description": "代码内容"
        },
        "file_path": {
            "type": "str",
            "required": False,
            "description": "代码文件路径"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行代码分析"""
        code = kwargs.get("code")
        file_path = kwargs.get("file_path")
        
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        
        if not code:
            return SkillResult.error("请提供代码内容或文件路径")
        
        try:
            analysis = {
                "lines": len(code.split('\n')),
                "characters": len(code),
                "functions": self._count_functions(code),
                "classes": self._count_classes(code),
                "imports": self._extract_imports(code),
                "complexity": self._calculate_complexity(code)
            }
            
            return SkillResult.ok(data=analysis)
        except Exception as e:
            return SkillResult.error(str(e))
    
    def _count_functions(self, code: str) -> int:
        """统计函数数量"""
        import re
        return len(re.findall(r'\bdef\s+\w+\s*\(', code))
    
    def _count_classes(self, code: str) -> int:
        """统计类数量"""
        import re
        return len(re.findall(r'\bclass\s+\w+', code))
    
    def _extract_imports(self, code: str) -> List[str]:
        """提取导入语句"""
        import re
        imports = re.findall(r'^(?:from|import)\s+([\w.]+)', code, re.MULTILINE)
        return imports
    
    def _calculate_complexity(self, code: str) -> Dict:
        """计算复杂度指标"""
        import re
        
        # 简单的圈复杂度估计
        branches = len(re.findall(r'\b(if|elif|else|for|while|except|with|and|or)\b', code))
        
        return {
            "estimated_cyclomatic": branches + 1,
            "branch_count": branches
        }


class CodeGenerateSkill(BaseSkill):
    """
    代码生成技能
    使用 LLM 生成代码
    """
    
    name = "code_generate"
    description = "根据描述生成代码"
    version = "1.0.0"
    tags = ["code", "generation", "llm"]
    
    parameters = {
        "description": {
            "type": "str",
            "required": True,
            "description": "代码功能描述"
        },
        "language": {
            "type": "str",
            "required": False,
            "default": "python",
            "description": "编程语言"
        },
        "context": {
            "type": "str",
            "required": False,
            "description": "额外上下文信息"
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.llm = config.get("llm") if config else None
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """生成代码"""
        description = kwargs.get("description")
        language = kwargs.get("language", "python")
        extra_context = kwargs.get("context", "")
        
        if not self.llm:
            return SkillResult.error("未配置 LLM")
        
        prompt = f"""请根据以下描述生成 {language} 代码：

功能描述：
{description}

{extra_context}

请生成完整、可运行的代码，并包含必要的注释："""
        
        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # 提取代码块
            code = self._extract_code(response.content)
            
            return SkillResult.ok(
                data={
                    "code": code,
                    "full_response": response.content
                },
                message="代码生成成功"
            )
        except Exception as e:
            return SkillResult.error(str(e))
    
    def _extract_code(self, text: str) -> str:
        """从响应中提取代码"""
        import re
        
        # 尝试提取代码块
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        return text.strip()


class CodeRefactorSkill(BaseSkill):
    """
    代码重构技能
    优化和改进代码
    """
    
    name = "code_refactor"
    description = "重构和优化代码"
    version = "1.0.0"
    tags = ["code", "refactor", "optimization"]
    
    parameters = {
        "code": {
            "type": "str",
            "required": True,
            "description": "要重构的代码"
        },
        "goal": {
            "type": "str",
            "required": False,
            "default": "general",
            "description": "重构目标: general/performance/readability/safety"
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.llm = config.get("llm") if config else None
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行代码重构"""
        code = kwargs.get("code")
        goal = kwargs.get("goal", "general")
        
        if not self.llm:
            return SkillResult.error("未配置 LLM")
        
        goal_descriptions = {
            "general": "进行一般性优化，提高代码质量",
            "performance": "优化性能，提高执行效率",
            "readability": "提高代码可读性和可维护性",
            "safety": "增强代码安全性和健壮性"
        }
        
        prompt = f"""请重构以下代码。{goal_descriptions.get(goal, goal_descriptions['general'])}

原始代码：
```python
{code}
```

请提供：
1. 重构后的代码
2. 主要改进点说明
3. 如果适用，说明性能或可读性提升

重构后的代码："""
        
        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            return SkillResult.ok(
                data={
                    "refactored": response.content,
                    "original": code
                },
                message="代码重构完成"
            )
        except Exception as e:
            return SkillResult.error(str(e))
