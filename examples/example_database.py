"""
数据库操作示例 - 展示多数据库连接和查询
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()


def example_db_manager():
    """示例：数据库管理器"""
    print("\n" + "="*60)
    print("示例1: 数据库管理器")
    print("="*60)
    
    from database.db_manager import db_manager, DatabaseManager
    
    print("\n数据库管理器是单例模式，全局统一管理数据库连接")
    
    # 创建两个管理器实例，验证单例
    manager1 = DatabaseManager()
    manager2 = DatabaseManager()
    
    print(f"manager1 is manager2: {manager1 is manager2}")
    
    print("\n支持的数据库类型:")
    print("  - OracleDatabase: Oracle 数据库")
    print("  - MySQLDatabase: MySQL 数据库")
    print("  - PostgreSQLDatabase: PostgreSQL 数据库")
    print("  - HiveDatabase: Hive 大数据平台")


def example_mysql_operations():
    """示例：MySQL 操作"""
    print("\n" + "="*60)
    print("示例2: MySQL 数据库操作")
    print("="*60)
    
    from database.mysql_db import MySQLDatabase
    from config import mysql_config
    
    print("\nMySQL 配置:")
    print(f"  主机: {mysql_config.host}")
    print(f"  端口: {mysql_config.port}")
    print(f"  数据库: {mysql_config.database}")
    
    print("\n示例代码:")
    print("""
    from database.mysql_db import MySQLDatabase
    from database.db_manager import db_manager
    
    # 方式1: 快速连接
    db_manager.quick_connect_mysql("mysql_db")
    
    # 方式2: 手动创建并注册
    mysql_db = MySQLDatabase()
    db_manager.register("mysql", mysql_db)
    
    # 执行查询
    result = mysql_db.execute("SELECT * FROM users WHERE age > %s", {"age": 18})
    
    # 获取所有表
    tables = mysql_db.get_tables()
    
    # 获取表结构
    schema = mysql_db.get_table_schema("users")
    
    # 获取索引
    indexes = mysql_db.get_table_indexes("users")
    
    # 获取执行计划
    plan = mysql_db.explain_query("SELECT * FROM users")
    
    # 获取数据库信息
    info = mysql_db.get_db_info()
    """)


def example_oracle_operations():
    """示例：Oracle 操作"""
    print("\n" + "="*60)
    print("示例3: Oracle 数据库操作")
    print("="*60)
    
    from database.oracle_db import OracleDatabase
    from config import oracle_config
    
    print("\nOracle 特有功能:")
    
    print("""
    from database.oracle_db import OracleDatabase
    
    oracle_db = OracleDatabase()
    
    # 获取所有 Schema
    schemas = oracle_db.get_schemas()
    
    # 获取指定 Schema 的表
    tables = oracle_db.get_tables_in_schema("HR")
    
    # 获取表索引
    indexes = oracle_db.get_table_indexes("EMPLOYEES", schema="HR")
    
    # 获取表约束
    constraints = oracle_db.get_table_constraints("EMPLOYEES", schema="HR")
    
    # 获取执行计划
    plan = oracle_db.explain_plan("SELECT * FROM employees")
    
    # 分页查询 (Oracle 语法)
    limited_sql = oracle_db.limit_sql("SELECT * FROM employees", 100)
    """)


def example_postgresql_operations():
    """示例：PostgreSQL 操作"""
    print("\n" + "="*60)
    print("示例4: PostgreSQL 数据库操作")
    print("="*60)
    
    from database.postgresql_db import PostgreSQLDatabase
    
    print("\nPostgreSQL 特有功能:")
    
    print("""
    from database.postgresql_db import PostgreSQLDatabase
    
    pg_db = PostgreSQLDatabase()
    
    # 获取所有 Schema
    schemas = pg_db.get_schemas()
    
    # 获取 Schema 中的表
    tables = pg_db.get_tables_in_schema("public")
    
    # 获取视图
    views = pg_db.get_views("public")
    
    # 获取索引定义
    indexes = pg_db.get_indexes("users", schema="public")
    
    # 获取约束
    constraints = pg_db.get_constraints("users", schema="public")
    
    # 获取表大小
    size_info = pg_db.get_table_size("users", schema="public")
    
    # 获取活动查询
    active_queries = pg_db.get_active_queries()
    
    # 终止进程
    pg_db.terminate_backend(12345)
    """)


def example_hive_operations():
    """示例：Hive 操作"""
    print("\n" + "="*60)
    print("示例5: Hive 大数据平台操作")
    print("="*60)
    
    from database.hive_db import HiveDatabase
    
    print("\nHive 特有功能:")
    
    print("""
    from database.hive_db import HiveDatabase
    
    hive_db = HiveDatabase()
    
    # 获取所有数据库
    databases = hive_db.get_databases()
    
    # 获取当前数据库的表
    tables = hive_db.get_tables()
    
    # 获取表结构
    schema = hive_db.get_table_schema("user_logs")
    
    # 获取分区信息
    partitions = hive_db.get_partitions("user_logs")
    
    # 获取表属性
    properties = hive_db.get_table_properties("user_logs")
    
    # 分析表
    hive_db.analyze_table("user_logs")
    
    # 流式查询（适合大数据量）
    for row in hive_db.stream_query("SELECT * FROM big_table", batch_size=1000):
        process(row)
    """)


def example_sqlalchemy_features():
    """示例：SQLAlchemy 高级特性"""
    print("\n" + "="*60)
    print("示例6: SQLAlchemy 高级特性")
    print("="*60)
    
    print("\n所有数据库都基于 SQLAlchemy，支持以下特性:")
    
    print("""
    from database.db_manager import db_manager
    
    db = db_manager.get("mysql")
    
    # 1. 使用会话上下文管理器
    with db.get_session() as session:
        result = session.execute(text("SELECT * FROM users"))
        for row in result:
            print(row)
    
    # 2. 批量插入
    db.execute_many(
        "INSERT INTO users (name, email) VALUES (:name, :email)",
        [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
    )
    
    # 3. 流式查询（适合大数据集）
    for row in db.stream_query("SELECT * FROM big_table", batch_size=1000):
        process(row)
    
    # 4. 执行 DDL
    db.execute_ddl("""
        CREATE TABLE IF NOT EXISTS new_table (
            id INT PRIMARY KEY,
            name VARCHAR(100)
        )
    """)
    """)


def example_database_skill():
    """示例：数据库技能"""
    print("\n" + "="*60)
    print("示例7: 使用数据库 Skill")
    print("="*60)
    
    from skills.registry import skill_registry, discover_skills
    
    # 发现技能
    discover_skills()
    
    print("\n数据库相关 Skills:")
    db_skills = skill_registry.find_by_tag("database")
    for skill_name in db_skills:
        skill_class = skill_registry.get_skill_class(skill_name)
        print(f"  - {skill_name}: {skill_class.description}")
    
    print("\n示例代码:")
    print("""
    from skills.registry import execute_skill
    
    # 执行查询
    result = execute_skill(
        "database",
        db_name="mysql",
        operation="query",
        sql="SELECT COUNT(*) as total FROM users"
    )
    
    if result.success:
        print(f"用户总数: {result.data[0]['total']}")
    
    # SQL 分析
    result = execute_skill(
        "sql_analysis",
        db_name="mysql",
        sql="SELECT * FROM users WHERE age > 18"
    )
    
    print(f"执行计划: {result.data['plan']}")
    print(f"优化建议: {result.data['suggestions']}")
    
    # 数据导出
    result = execute_skill(
        "data_export",
        db_name="mysql",
        sql="SELECT * FROM users",
        format="csv",
        output_path="./users.csv"
    )
    """)


def example_connection_pool():
    """示例：连接池配置"""
    print("\n" + "="*60)
    print("示例8: 连接池配置")
    print("="*60)
    
    print("\n数据库连接池配置:")
    
    print("""
    from database.base import BaseDatabase
    
    # 自定义连接池参数
    db = BaseDatabase(
        connection_string="mysql+pymysql://...",
        pool_size=10,           # 连接池大小
        max_overflow=20         # 最大溢出连接
    )
    
    # SQLAlchemy 连接池特性:
    # - pool_pre_ping=True: 连接前检查连接是否有效
    # - pool_recycle=3600: 连接回收时间（秒）
    # - 自动重连和故障转移
    """)


def main():
    """运行数据库示例"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              数据库操作完整示例                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    example_db_manager()
    example_mysql_operations()
    example_oracle_operations()
    example_postgresql_operations()
    example_hive_operations()
    example_sqlalchemy_features()
    example_database_skill()
    example_connection_pool()
    
    print("\n" + "="*60)
    print("数据库示例完成！")
    print("="*60)
    print("""
提示：
1. 在 .env 文件中配置数据库连接信息
2. 确保数据库服务已启动并可访问
3. 安装对应的数据库驱动:
   - MySQL: pip install pymysql
   - Oracle: pip install cx-oracle
   - PostgreSQL: pip install psycopg2-binary
   - Hive: pip install pyhive thrift sasl
    """)


if __name__ == "__main__":
    main()
