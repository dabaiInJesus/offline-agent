"""
数据库管理器 - 统一管理多种数据库连接
"""
from typing import Dict, Optional, Type
from .base import BaseDatabase
from .oracle_db import OracleDatabase
from .mysql_db import MySQLDatabase
from .postgresql_db import PostgreSQLDatabase
from .hive_db import HiveDatabase
from loguru import logger


class DatabaseManager:
    """数据库管理器 - 单例模式管理所有数据库连接"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._databases: Dict[str, BaseDatabase] = {}
        return cls._instance
    
    def register(self, name: str, db: BaseDatabase) -> bool:
        """注册数据库连接"""
        try:
            if db.connect():
                self._databases[name] = db
                logger.info(f"数据库 '{name}' 注册成功")
                return True
            return False
        except Exception as e:
            logger.error(f"数据库 '{name}' 注册失败: {e}")
            return False
    
    def get(self, name: str) -> Optional[BaseDatabase]:
        """获取数据库连接"""
        return self._databases.get(name)
    
    def remove(self, name: str):
        """移除数据库连接"""
        if name in self._databases:
            self._databases[name].disconnect()
            del self._databases[name]
            logger.info(f"数据库 '{name}' 已移除")
    
    def list_databases(self) -> Dict[str, str]:
        """列出所有已注册的数据库"""
        return {name: db.__class__.__name__ for name, db in self._databases.items()}
    
    def close_all(self):
        """关闭所有数据库连接"""
        for name, db in self._databases.items():
            try:
                db.disconnect()
                logger.info(f"数据库 '{name}' 连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库 '{name}' 失败: {e}")
        self._databases.clear()
    
    def quick_connect_oracle(self, name: str = "oracle") -> bool:
        """快速连接 Oracle"""
        db = OracleDatabase()
        return self.register(name, db)
    
    def quick_connect_mysql(self, name: str = "mysql") -> bool:
        """快速连接 MySQL"""
        db = MySQLDatabase()
        return self.register(name, db)
    
    def quick_connect_postgresql(self, name: str = "postgresql") -> bool:
        """快速连接 PostgreSQL"""
        db = PostgreSQLDatabase()
        return self.register(name, db)
    
    def quick_connect_hive(self, name: str = "hive") -> bool:
        """快速连接 Hive"""
        db = HiveDatabase()
        return self.register(name, db)


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 便捷函数
def get_db(name: str) -> Optional[BaseDatabase]:
    """获取指定名称的数据库连接"""
    return db_manager.get(name)


def execute_sql(db_name: str, sql: str, params: Optional[Dict] = None):
    """在指定数据库执行 SQL"""
    db = get_db(db_name)
    if not db:
        raise ValueError(f"数据库 '{db_name}' 未找到")
    return db.execute(sql, params)


def get_table_info(db_name: str, table_name: str) -> str:
    """获取指定数据库表的信息"""
    db = get_db(db_name)
    if not db:
        raise ValueError(f"数据库 '{db_name}' 未找到")
    return db.get_table_info(table_name)
