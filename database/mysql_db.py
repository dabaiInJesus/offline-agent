"""
MySQL 数据库连接模块
"""
from typing import List, Dict, Any
from .base import BaseDatabase
from config import mysql_config


class MySQLDatabase(BaseDatabase):
    """MySQL 数据库封装"""
    
    def __init__(self, config=None):
        config = config or mysql_config
        super().__init__(config.connection_string)
        self.config = config
    
    def get_dialect(self) -> str:
        return "mysql"
    
    def limit_sql(self, sql: str, limit: int) -> str:
        """MySQL 分页语法"""
        return f"{sql} LIMIT {limit}"
    
    def get_databases(self) -> List[str]:
        """获取所有数据库"""
        result = self.execute("SHOW DATABASES")
        return [row["Database"] for row in result]
    
    def get_tables_in_db(self, database: str) -> List[str]:
        """获取指定数据库的所有表"""
        sql = f"SHOW TABLES FROM `{database}`"
        result = self.execute(sql)
        key = list(result[0].keys())[0] if result else "Tables_in_" + database
        return [row[key] for row in result]
    
    def get_table_indexes(self, table_name: str, database: str = None) -> List[Dict[str, Any]]:
        """获取表索引信息"""
        database = database or self.config.database
        sql = f"SHOW INDEX FROM `{table_name}` FROM `{database}`"
        return self.execute(sql)
    
    def get_create_table_sql(self, table_name: str) -> str:
        """获取建表 SQL"""
        sql = f"SHOW CREATE TABLE `{table_name}`"
        result = self.execute(sql)
        return result[0].get("Create Table", "") if result else ""
    
    def explain_query(self, sql: str) -> List[Dict[str, Any]]:
        """获取查询执行计划"""
        explain_sql = f"EXPLAIN {sql}"
        return self.execute(explain_sql)
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """获取表统计信息"""
        sql = f"""
        SELECT 
            table_rows,
            data_length,
            index_length,
            data_free,
            auto_increment
        FROM information_schema.tables
        WHERE table_name = '{table_name}'
        AND table_schema = '{self.config.database}'
        """
        result = self.execute(sql)
        return result[0] if result else {}
    
    def get_db_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        info = {}
        
        # 版本信息
        info["version"] = self.execute("SELECT VERSION() as version")
        
        # 状态信息
        status = self.execute("SHOW STATUS")
        info["status"] = {row["Variable_name"]: row["Value"] for row in status}
        
        # 变量信息
        variables = self.execute("SHOW VARIABLES")
        info["variables"] = {row["Variable_name"]: row["Value"] for row in variables}
        
        return info
    
    def get_processlist(self) -> List[Dict[str, Any]]:
        """获取当前进程列表"""
        return self.execute("SHOW PROCESSLIST")
    
    def kill_process(self, process_id: int) -> bool:
        """终止指定进程"""
        try:
            self.execute(f"KILL {process_id}")
            return True
        except Exception:
            return False
