"""
数据库技能 - 数据库查询和操作
"""
from typing import Dict, Any, List, Optional
from .base import BaseSkill, SkillResult, SkillContext
from database.db_manager import db_manager
from loguru import logger


class DatabaseSkill(BaseSkill):
    """
    数据库操作技能
    支持 SQL 查询、数据分析和报表生成
    """
    
    name = "database"
    description = "执行数据库查询和操作"
    version = "1.0.0"
    tags = ["database", "sql", "query"]
    
    parameters = {
        "db_name": {
            "type": "str",
            "required": True,
            "description": "数据库名称"
        },
        "operation": {
            "type": "str",
            "required": True,
            "description": "操作类型: query/execute/schema/stats"
        },
        "sql": {
            "type": "str",
            "required": False,
            "description": "SQL 语句"
        },
        "table_name": {
            "type": "str",
            "required": False,
            "description": "表名"
        },
        "params": {
            "type": "dict",
            "required": False,
            "description": "SQL 参数"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行数据库操作"""
        db_name = kwargs.get("db_name")
        operation = kwargs.get("operation")
        
        db = db_manager.get(db_name)
        if not db:
            return SkillResult.error(f"数据库 '{db_name}' 不存在")
        
        try:
            if operation == "query":
                return self._execute_query(db, kwargs)
            elif operation == "execute":
                return self._execute_ddl(db, kwargs)
            elif operation == "schema":
                return self._get_schema(db, kwargs)
            elif operation == "stats":
                return self._get_stats(db, kwargs)
            elif operation == "tables":
                return SkillResult.ok(data=db.get_tables())
            elif operation == "table_info":
                table_name = kwargs.get("table_name")
                if not table_name:
                    return SkillResult.error("缺少 table_name 参数")
                return SkillResult.ok(data=db.get_table_info(table_name))
            else:
                return SkillResult.error(f"未知的操作类型: {operation}")
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            return SkillResult.error(str(e))
    
    def _execute_query(self, db, kwargs: Dict) -> SkillResult:
        """执行查询"""
        sql = kwargs.get("sql")
        params = kwargs.get("params", {})
        
        if not sql:
            return SkillResult.error("缺少 SQL 语句")
        
        result = db.execute(sql, params)
        return SkillResult.ok(
            data=result,
            message=f"查询返回 {len(result)} 条记录"
        )
    
    def _execute_ddl(self, db, kwargs: Dict) -> SkillResult:
        """执行 DDL"""
        sql = kwargs.get("sql")
        
        if not sql:
            return SkillResult.error("缺少 SQL 语句")
        
        success = db.execute_ddl(sql)
        if success:
            return SkillResult.ok(message="DDL 执行成功")
        return SkillResult.error("DDL 执行失败")
    
    def _get_schema(self, db, kwargs: Dict) -> SkillResult:
        """获取表结构"""
        table_name = kwargs.get("table_name")
        
        if not table_name:
            return SkillResult.error("缺少 table_name 参数")
        
        schema = db.get_table_schema(table_name)
        return SkillResult.ok(data=schema)
    
    def _get_stats(self, db, kwargs: Dict) -> SkillResult:
        """获取统计信息"""
        if hasattr(db, 'get_db_info'):
            stats = db.get_db_info()
            return SkillResult.ok(data=stats)
        return SkillResult.error("该数据库不支持统计信息查询")


class SQLAnalysisSkill(BaseSkill):
    """
    SQL 分析技能
    分析 SQL 查询并提供优化建议
    """
    
    name = "sql_analysis"
    description = "分析 SQL 查询性能"
    version = "1.0.0"
    tags = ["database", "sql", "analysis"]
    
    parameters = {
        "db_name": {
            "type": "str",
            "required": True,
            "description": "数据库名称"
        },
        "sql": {
            "type": "str",
            "required": True,
            "description": "要分析的 SQL"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行 SQL 分析"""
        db_name = kwargs.get("db_name")
        sql = kwargs.get("sql")
        
        db = db_manager.get(db_name)
        if not db:
            return SkillResult.error(f"数据库 '{db_name}' 不存在")
        
        try:
            analysis = {
                "sql": sql,
                "db_type": db.get_dialect(),
                "plan": None,
                "suggestions": []
            }
            
            # 获取执行计划
            if hasattr(db, 'explain_query'):
                plan = db.explain_query(sql)
                analysis["plan"] = plan
            elif hasattr(db, 'explain_plan'):
                plan = db.explain_plan(sql)
                analysis["plan"] = plan
            
            # 基础优化建议
            suggestions = self._analyze_sql(sql)
            analysis["suggestions"] = suggestions
            
            return SkillResult.ok(data=analysis)
        except Exception as e:
            return SkillResult.error(str(e))
    
    def _analyze_sql(self, sql: str) -> List[str]:
        """分析 SQL 给出建议"""
        suggestions = []
        sql_upper = sql.upper()
        
        # SELECT * 检查
        if "SELECT *" in sql_upper:
            suggestions.append("避免使用 SELECT *，只选择需要的列")
        
        # WHERE 子句检查
        if "WHERE" not in sql_upper:
            suggestions.append("考虑添加 WHERE 子句限制结果集")
        
        # LIMIT 检查
        if "LIMIT" not in sql_upper and "ROWNUM" not in sql_upper:
            suggestions.append("考虑添加 LIMIT 限制返回行数")
        
        # JOIN 检查
        if "JOIN" in sql_upper:
            suggestions.append("确保 JOIN 条件上有索引")
        
        return suggestions


class DataExportSkill(BaseSkill):
    """
    数据导出技能
    将查询结果导出为各种格式
    """
    
    name = "data_export"
    description = "导出数据到文件"
    version = "1.0.0"
    tags = ["database", "export", "data"]
    
    parameters = {
        "db_name": {
            "type": "str",
            "required": True,
            "description": "数据库名称"
        },
        "sql": {
            "type": "str",
            "required": True,
            "description": "查询 SQL"
        },
        "format": {
            "type": "str",
            "required": True,
            "description": "导出格式: csv/json/excel"
        },
        "output_path": {
            "type": "str",
            "required": True,
            "description": "输出文件路径"
        }
    }
    
    def _execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行数据导出"""
        db_name = kwargs.get("db_name")
        sql = kwargs.get("sql")
        fmt = kwargs.get("format", "csv")
        output_path = kwargs.get("output_path")
        
        db = db_manager.get(db_name)
        if not db:
            return SkillResult.error(f"数据库 '{db_name}' 不存在")
        
        try:
            # 执行查询
            result = db.execute(sql)
            
            # 根据格式导出
            if fmt == "csv":
                self._export_csv(result, output_path)
            elif fmt == "json":
                self._export_json(result, output_path)
            elif fmt == "excel":
                self._export_excel(result, output_path)
            else:
                return SkillResult.error(f"不支持的格式: {fmt}")
            
            return SkillResult.ok(
                message=f"成功导出 {len(result)} 条记录到 {output_path}"
            )
        except Exception as e:
            return SkillResult.error(str(e))
    
    def _export_csv(self, data: List[Dict], path: str):
        """导出 CSV"""
        import csv
        
        if not data:
            return
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _export_json(self, data: List[Dict], path: str):
        """导出 JSON"""
        import json
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_excel(self, data: List[Dict], path: str):
        """导出 Excel"""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_excel(path, index=False)
        except ImportError:
            raise ImportError("请安装 pandas 和 openpyxl: pip install pandas openpyxl")
