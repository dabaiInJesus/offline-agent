"""
Hive 数据库连接模块
"""
from typing import List, Dict, Any, Iterator
from .base import BaseDatabase
from config import hive_config
from loguru import logger


class HiveDatabase(BaseDatabase):
    """Hive 数据库封装"""
    
    def __init__(self, config=None):
        config = config or hive_config
        super().__init__(config.connection_string, pool_size=2, max_overflow=5)
        self.config = config
        self._cursor = None
    
    def get_dialect(self) -> str:
        return "hive"
    
    def limit_sql(self, sql: str, limit: int) -> str:
        """Hive 分页语法"""
        return f"{sql} LIMIT {limit}"
    
    def connect(self) -> bool:
        """建立 Hive 连接（使用 pyhive）"""
        try:
            from pyhive import hive
            
            self._connection = hive.connect(
                host=self.config.host,
                port=self.config.port,
                username=self.config.user,
                password=self.config.password,
                database=self.config.database,
                auth='LDAP' if self.config.password else 'NONE'
            )
            self._cursor = self._connection.cursor()
            
            logger.info(f"Hive 连接成功: {self.config.host}:{self.config.port}/{self.config.database}")
            return True
        except Exception as e:
            logger.error(f"Hive 连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开 Hive 连接"""
        if self._cursor:
            self._cursor.close()
        if hasattr(self, '_connection') and self._connection:
            self._connection.close()
        logger.info("Hive 连接已断开")
    
    def execute(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行 Hive SQL"""
        if not self._cursor:
            raise RuntimeError("Hive 未连接，请先调用 connect()")
        
        try:
            self._cursor.execute(sql)
            
            if self._cursor.description:
                columns = [desc[0] for desc in self._cursor.description]
                rows = self._cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Hive SQL 执行失败: {e}, SQL: {sql}")
            raise
    
    def stream_query(self, sql: str, params: Dict[str, Any] = None, batch_size: int = 1000) -> Iterator[Dict[str, Any]]:
        """流式查询 Hive 数据"""
        if not self._cursor:
            raise RuntimeError("Hive 未连接，请先调用 connect()")
        
        try:
            self._cursor.execute(sql)
            
            if self._cursor.description:
                columns = [desc[0] for desc in self._cursor.description]
                
                while True:
                    rows = self._cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    for row in rows:
                        yield dict(zip(columns, row))
                        
        except Exception as e:
            logger.error(f"Hive 流式查询失败: {e}")
            raise
    
    def get_databases(self) -> List[str]:
        """获取所有数据库"""
        result = self.execute("SHOW DATABASES")
        return [row.get("database_name", row.get("name", "")) for row in result]
    
    def get_tables(self) -> List[str]:
        """获取当前数据库的所有表"""
        result = self.execute("SHOW TABLES")
        # Hive 返回的列名可能是 tab_name 或 tableName
        if result:
            key = list(result[0].keys())[0]
            return [row[key] for row in result]
        return []
    
    def get_tables_in_db(self, database: str) -> List[str]:
        """获取指定数据库的所有表"""
        result = self.execute(f"SHOW TABLES IN {database}")
        if result:
            key = list(result[0].keys())[0]
            return [row[key] for row in result]
        return []
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构"""
        result = self.execute(f"DESCRIBE FORMATTED {table_name}")
        columns = []
        
        for row in result:
            col_name = row.get("col_name", "").strip()
            data_type = row.get("data_type", "").strip()
            
            # 跳过分隔线和元数据部分
            if col_name and col_name not in ["", "# col_name", "# Partition Information"]:
                if data_type:
                    columns.append({
                        "name": col_name,
                        "type": data_type,
                        "comment": row.get("comment", "").strip()
                    })
        
        return columns
    
    def get_partitions(self, table_name: str) -> List[str]:
        """获取表分区信息"""
        try:
            result = self.execute(f"SHOW PARTITIONS {table_name}")
            return [row.get("partition", "") for row in result]
        except Exception as e:
            logger.warning(f"获取分区信息失败: {e}")
            return []
    
    def get_table_properties(self, table_name: str) -> Dict[str, Any]:
        """获取表属性"""
        result = self.execute(f"DESCRIBE FORMATTED {table_name}")
        properties = {}
        
        in_properties = False
        for row in result:
            col_name = row.get("col_name", "").strip()
            data_type = row.get("data_type", "").strip()
            
            if col_name == "Table Parameters:":
                in_properties = True
                continue
            
            if in_properties:
                if not col_name or col_name.startswith("#"):
                    break
                properties[col_name] = data_type
        
        return properties
    
    def get_db_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        info = {}
        
        # 版本信息
        try:
            info["version"] = self.execute("SET hive.version")
        except:
            pass
        
        # 当前数据库
        info["current_database"] = self.config.database
        
        # 数据库列表
        info["databases"] = self.get_databases()
        
        return info
    
    def explain_query(self, sql: str) -> List[Dict[str, Any]]:
        """获取查询执行计划"""
        return self.execute(f"EXPLAIN {sql}")
    
    def analyze_table(self, table_name: str) -> bool:
        """分析表统计信息"""
        try:
            self.execute(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS")
            return True
        except Exception as e:
            logger.error(f"分析表失败: {e}")
            return False
