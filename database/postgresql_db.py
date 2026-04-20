"""
PostgreSQL 数据库连接模块
"""
from typing import List, Dict, Any
from .base import BaseDatabase
from config import pg_config


class PostgreSQLDatabase(BaseDatabase):
    """PostgreSQL 数据库封装"""
    
    def __init__(self, config=None):
        config = config or pg_config
        super().__init__(config.connection_string)
        self.config = config
    
    def get_dialect(self) -> str:
        return "postgresql"
    
    def limit_sql(self, sql: str, limit: int) -> str:
        """PostgreSQL 分页语法"""
        return f"{sql} LIMIT {limit}"
    
    def get_schemas(self) -> List[str]:
        """获取所有 schema"""
        sql = """
        SELECT schema_name 
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        ORDER BY schema_name
        """
        result = self.execute(sql)
        return [row["schema_name"] for row in result]
    
    def get_tables_in_schema(self, schema: str = "public") -> List[str]:
        """获取指定 schema 的所有表"""
        sql = """
        SELECT table_name 
        FROM information_schema.tables
        WHERE table_schema = :schema
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        result = self.execute(sql, {"schema": schema})
        return [row["table_name"] for row in result]
    
    def get_views(self, schema: str = "public") -> List[str]:
        """获取所有视图"""
        sql = """
        SELECT table_name 
        FROM information_schema.views
        WHERE table_schema = :schema
        ORDER BY table_name
        """
        result = self.execute(sql, {"schema": schema})
        return [row["table_name"] for row in result]
    
    def get_indexes(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """获取表索引信息"""
        sql = """
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = :table_name
        AND schemaname = :schema
        """
        return self.execute(sql, {"table_name": table_name, "schema": schema})
    
    def get_constraints(self, table_name: str, schema: str = "public") -> List[Dict[str, Any]]:
        """获取表约束信息"""
        sql = """
        SELECT
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_name = :table_name
        AND tc.table_schema = :schema
        """
        return self.execute(sql, {"table_name": table_name, "schema": schema})
    
    def explain_query(self, sql: str, analyze: bool = False) -> List[Dict[str, Any]]:
        """获取查询执行计划"""
        explain_cmd = "EXPLAIN (FORMAT JSON)"
        if analyze:
            explain_cmd = "EXPLAIN (ANALYZE, FORMAT JSON)"
        
        result = self.execute(f"{explain_cmd} {sql}")
        return result
    
    def get_table_size(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """获取表大小信息"""
        sql = """
        SELECT
            pg_size_pretty(pg_total_relation_size(:full_name)) as total_size,
            pg_size_pretty(pg_relation_size(:full_name)) as table_size,
            pg_size_pretty(pg_indexes_size(:full_name)) as indexes_size
        """
        full_name = f"{schema}.{table_name}"
        result = self.execute(sql, {"full_name": full_name})
        return result[0] if result else {}
    
    def get_db_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        info = {}
        
        # 版本信息
        info["version"] = self.execute("SELECT version()")
        
        # 数据库大小
        info["size"] = self.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        
        # 连接数
        info["connections"] = self.execute("SELECT count(*) FROM pg_stat_activity")
        
        # 表统计
        info["table_stats"] = self.execute("""
            SELECT schemaname, relname, n_live_tup, n_dead_tup
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            LIMIT 10
        """)
        
        return info
    
    def get_active_queries(self) -> List[Dict[str, Any]]:
        """获取当前活动查询"""
        sql = """
        SELECT 
            pid,
            usename,
            application_name,
            client_addr,
            state,
            query_start,
            query
        FROM pg_stat_activity
        WHERE state = 'active'
        AND query NOT LIKE '%pg_stat_activity%'
        """
        return self.execute(sql)
    
    def terminate_backend(self, pid: int) -> bool:
        """终止指定后端进程"""
        try:
            self.execute(f"SELECT pg_terminate_backend({pid})")
            return True
        except Exception:
            return False
