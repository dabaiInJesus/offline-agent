"""
RAG 技能 - 知识库检索和问答
"""
from typing import Dict, Any, List, Optional
from .base import BaseSkill, SkillResult, SkillContext
from knowledge_base.knowledge_base import KnowledgeBase, kb_manager
from loguru import logger


class RAGSkill(BaseSkill):
    """
    RAG 检索技能
    从知识库检索信息并生成回答
    """
    
    name = "rag"
    description = "从知识库检索信息并回答问题"
    version = "1.0.0"
    tags = ["rag", "knowledge", "search", "qa"]
    
    parameters = {
        "kb_name": {
            "type": "str",
            "required": True,
            "description": "知识库名称"
        },
        "query": {
            "type": "str",
            "required": True,
            "description": "查询问题"
        },
        "top_k": {
            "type": "int",
            "required": False,
            "default": 5,
            "description": "检索文档数量"
        },
        "return_sources": {
            "type": "bool",
            "required": False,
            "default": True,
            "description": "是否返回来源"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行 RAG 检索"""
        kb_name = kwargs.get("kb_name")
        query = kwargs.get("query")
        top_k = kwargs.get("top_k", 5)
        return_sources = kwargs.get("return_sources", True)
        
        # 获取知识库
        kb = kb_manager.get(kb_name)
        if not kb:
            return SkillResult.error(f"知识库 '{kb_name}' 不存在")
        
        try:
            # 执行查询
            result = kb.query(
                question=query,
                top_k=top_k,
                return_sources=return_sources
            )
            
            return SkillResult.ok(
                data=result,
                message="检索完成"
            )
        except Exception as e:
            logger.error(f"RAG 检索失败: {e}")
            return SkillResult.error(str(e))


class KnowledgeBaseManageSkill(BaseSkill):
    """
    知识库管理技能
    创建、更新、删除知识库
    """
    
    name = "kb_manage"
    description = "管理知识库"
    version = "1.0.0"
    tags = ["rag", "knowledge", "management"]
    
    parameters = {
        "operation": {
            "type": "str",
            "required": True,
            "description": "操作: create/add_document/delete/clear/stats"
        },
        "kb_name": {
            "type": "str",
            "required": True,
            "description": "知识库名称"
        },
        "file_path": {
            "type": "str",
            "required": False,
            "description": "文档路径（添加文档时使用）"
        },
        "directory": {
            "type": "str",
            "required": False,
            "description": "目录路径（批量添加时使用）"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行知识库管理操作"""
        operation = kwargs.get("operation")
        kb_name = kwargs.get("kb_name")
        
        try:
            if operation == "create":
                return self._create_kb(kb_name, kwargs)
            elif operation == "add_document":
                return self._add_document(kb_name, kwargs)
            elif operation == "add_directory":
                return self._add_directory(kb_name, kwargs)
            elif operation == "delete":
                return self._delete_kb(kb_name)
            elif operation == "clear":
                return self._clear_kb(kb_name)
            elif operation == "stats":
                return self._get_stats(kb_name)
            elif operation == "list":
                return SkillResult.ok(data=kb_manager.list_knowledge_bases())
            else:
                return SkillResult.error(f"未知的操作: {operation}")
        except Exception as e:
            return SkillResult.error(str(e))
    
    def _create_kb(self, kb_name: str, kwargs: Dict) -> SkillResult:
        """创建知识库"""
        from models.ollama_model import get_embeddings
        
        kb = KnowledgeBase(
            name=kb_name,
            embedding_model=get_embeddings()
        )
        kb_manager._knowledge_bases[kb_name] = kb
        
        return SkillResult.ok(message=f"知识库 '{kb_name}' 创建成功")
    
    def _add_document(self, kb_name: str, kwargs: Dict) -> SkillResult:
        """添加文档"""
        kb = kb_manager.get(kb_name)
        if not kb:
            return SkillResult.error(f"知识库 '{kb_name}' 不存在")
        
        file_path = kwargs.get("file_path")
        if not file_path:
            return SkillResult.error("缺少 file_path 参数")
        
        doc_ids = kb.add_document(file_path)
        return SkillResult.ok(
            data={"doc_ids": doc_ids},
            message=f"已添加文档，生成 {len(doc_ids)} 个片段"
        )
    
    def _add_directory(self, kb_name: str, kwargs: Dict) -> SkillResult:
        """添加目录"""
        kb = kb_manager.get(kb_name)
        if not kb:
            return SkillResult.error(f"知识库 '{kb_name}' 不存在")
        
        directory = kwargs.get("directory")
        if not directory:
            return SkillResult.error("缺少 directory 参数")
        
        result = kb.add_documents_from_directory(directory)
        total = sum(len(ids) for ids in result.values())
        return SkillResult.ok(
            data=result,
            message=f"已添加目录，共 {total} 个文档片段"
        )
    
    def _delete_kb(self, kb_name: str) -> SkillResult:
        """删除知识库"""
        kb_manager.remove(kb_name)
        return SkillResult.ok(message=f"知识库 '{kb_name}' 已删除")
    
    def _clear_kb(self, kb_name: str) -> SkillResult:
        """清空知识库"""
        kb = kb_manager.get(kb_name)
        if not kb:
            return SkillResult.error(f"知识库 '{kb_name}' 不存在")
        
        success = kb.clear()
        if success:
            return SkillResult.ok(message=f"知识库 '{kb_name}' 已清空")
        return SkillResult.error("清空失败")
    
    def _get_stats(self, kb_name: str) -> SkillResult:
        """获取统计信息"""
        kb = kb_manager.get(kb_name)
        if not kb:
            return SkillResult.error(f"知识库 '{kb_name}' 不存在")
        
        stats = kb.get_stats()
        return SkillResult.ok(data=stats)


class MultiKBRAGSkill(BaseSkill):
    """
    多知识库 RAG 技能
    同时从多个知识库检索信息
    """
    
    name = "multi_kb_rag"
    description = "从多个知识库检索信息"
    version = "1.0.0"
    tags = ["rag", "knowledge", "multi"]
    
    parameters = {
        "kb_names": {
            "type": "list",
            "required": True,
            "description": "知识库名称列表"
        },
        "query": {
            "type": "str",
            "required": True,
            "description": "查询问题"
        },
        "top_k_per_kb": {
            "type": "int",
            "required": False,
            "default": 3,
            "description": "每个知识库检索数量"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行多知识库检索"""
        kb_names = kwargs.get("kb_names", [])
        query = kwargs.get("query")
        top_k = kwargs.get("top_k_per_kb", 3)
        
        if not kb_names:
            return SkillResult.error("未指定知识库")
        
        all_results = []
        errors = []
        
        for kb_name in kb_names:
            kb = kb_manager.get(kb_name)
            if not kb:
                errors.append(f"知识库 '{kb_name}' 不存在")
                continue
            
            try:
                docs = kb.search(query, top_k=top_k)
                all_results.append({
                    "kb_name": kb_name,
                    "documents": docs
                })
            except Exception as e:
                errors.append(f"检索 '{kb_name}' 失败: {str(e)}")
        
        return SkillResult.ok(
            data={
                "results": all_results,
                "errors": errors
            },
            message=f"从 {len(all_results)} 个知识库检索完成"
        )
