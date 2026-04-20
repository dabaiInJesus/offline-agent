"""
Oracle 数据库连接模块
"""
from typing import List, Dict, Any
from .base import BaseDatabase
from config import oracle_config


class OracleDatabase(BaseDatabase):
    """Oracle 数据库封装"""
    
    def __init__(self, config=None):
        config = config or oracle_config
        super().__init__(config.connection_string)
        self.config = config
    
    def get_dialect(self) -> str:
        return "oracle"
    
    def limit_sql(self, sql: str, limit: int) -> str:
        """Oracle 分页语法"""
        return f"SELECT * FROM ({sql}) WHERE ROWNUM <= {limit}"
    
    def get_schemas(self) -> List[str]:
        """获取所有 schema"""
        sql = """
        SELECT username FROM all_users 
        WHERE oracle_maintained = 'N'
        ORDER BY username
        """
        result = self.execute(sql)
        return [row["USERNAME"] for row in result]
    
    def get_tables_in_schema(self, schema: str) -> List[str]:
        """获取指定 schema 的所有表"""
        sql = """
        SELECT table_name FROM all_tables 
        WHERE owner = :schema
        ORDER BY table_name
        """
        result = self.execute(sql, {"schema": schema.upper()})
        return [row["TABLE_NAME"] for row in result]
    
    def get_table_indexes(self, table_name: str, schema: str = None) -> List[Dict[str, Any]]:
        """获取表索引信息"""
        schema = schema or self.config.user.upper()
        sql = """
        SELECT index_name, index_type, uniqueness, column_name
        FROM all_ind_columns aic
        JOIN all_indexes ai ON aic.index_name = ai.index_name
        WHERE ai.table_name = :table_name
        AND ai.table_owner = :schema
        ORDER BY aic.column_position
        """
        return self.execute(sql, {"table_name": table_name.upper(), "schema": schema.upper()})
    
    def get_table_constraints(self, table_name: str, schema: str = None) -> List[Dict[str, Any]]:
        """获取表约束信息"""
        schema = schema or self.config.user.upper()
        sql = """
        SELECT constraint_name, constraint_type, search_condition, r_constraint_name
        FROM all_constraints
        WHERE table_name = :table_name
        AND owner = :schema
        """
        return self.execute(sql, {"table_name": table_name.upper(), "schema": schema.upper()})
    
    def explain_plan(self, sql: str) -> List[Dict[str, Any]]:
        """获取 SQL 执行计划"""
        # 生成执行计划
        self.execute("EXPLAIN PLAN FOR " + sql)
        # 查询执行计划
        plan_sql = """
        SELECT plan_table_output FROM table(DBMS_XPLAN.DISPLAY())
        """
        return self.execute(plan_sql)
    
    def get_db_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        info = {}
        
        # 数据库版本
        version_sql = "SELECT * FROM v$version"
        info["version"] = self.execute(version_sql)
        
        # 数据库大小
        size_sql = """
        SELECT SUM(bytes)/1024/1024/1024 AS size_gb 
        FROM dba_segments
        """
        info["size"] = self.execute(size_sql)
        
        # 会话数
        session_sql = "SELECT COUNT(*) as session_count FROM v$session"
        info["sessions"] = self.execute(session_sql)
        
        return info
