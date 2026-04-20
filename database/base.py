"""
数据库基类 - 定义通用数据库接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from contextlib import contextmanager
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from loguru import logger


class BaseDatabase(ABC):
    """数据库基类"""
    
    def __init__(self, connection_string: str, pool_size: int = 5, max_overflow: int = 10):
        self.connection_string = connection_string
        self.engine: Optional[Engine] = None
        self.SessionLocal = None
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        
    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self.engine = create_engine(
                self.connection_string,
                poolclass=QueuePool,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"数据库连接成功: {self.__class__.__name__}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info(f"数据库连接已断开: {self.__class__.__name__}")
    
    @contextmanager
    def get_session(self):
        """获取数据库会话上下文管理器"""
        if not self.SessionLocal:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行 SQL 查询并返回结果"""
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                rows = result.mappings().all()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SQL 执行失败: {e}, SQL: {sql}")
            raise
    
    def execute_many(self, sql: str, params_list: List[Dict[str, Any]]) -> int:
        """批量执行 SQL"""
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(sql), params_list)
                return result.rowcount
        except Exception as e:
            logger.error(f"批量 SQL 执行失败: {e}")
            raise
    
    def execute_ddl(self, sql: str) -> bool:
        """执行 DDL 语句"""
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        try:
            with self.engine.begin() as conn:
                conn.execute(text(sql))
            return True
        except Exception as e:
            logger.error(f"DDL 执行失败: {e}")
            return False
    
    def get_tables(self) -> List[str]:
        """获取所有表名"""
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构信息"""
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        return [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": col.get("default"),
            }
            for col in columns
        ]
    
    def get_table_info(self, table_name: str) -> str:
        """获取表信息描述（用于 LLM 提示）"""
        columns = self.get_table_schema(table_name)
        lines = [f"表名: {table_name}", "字段:"]
        for col in columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col["default"] else ""
            lines.append(f"  - {col['name']}: {col['type']} {nullable}{default}")
        return "\n".join(lines)
    
    def stream_query(self, sql: str, params: Optional[Dict[str, Any]] = None, batch_size: int = 1000) -> Iterator[Dict[str, Any]]:
        """流式查询大数据集"""
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        try:
            with self.engine.connect().execution_options(stream_results=True) as conn:
                result = conn.execute(text(sql), params or {})
                while True:
                    rows = result.fetchmany(batch_size)
                    if not rows:
                        break
                    for row in rows:
                        yield dict(row._mapping)
        except Exception as e:
            logger.error(f"流式查询失败: {e}")
            raise
    
    @abstractmethod
    def get_dialect(self) -> str:
        """获取数据库方言"""
        pass
    
    @abstractmethod
    def limit_sql(self, sql: str, limit: int) -> str:
        """生成带限制的 SQL"""
        pass
