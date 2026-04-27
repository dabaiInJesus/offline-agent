"""
项目配置文件
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class OllamaConfig:
    """Ollama 配置"""
    base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:32b"))
    temperature: float = 0.7
    timeout: int = 300


@dataclass
class OracleConfig:
    """Oracle 数据库配置"""
    host: str = field(default_factory=lambda: os.getenv("ORACLE_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("ORACLE_PORT", "1521")))
    service_name: str = field(default_factory=lambda: os.getenv("ORACLE_SERVICE_NAME", "ORCL"))
    user: str = field(default_factory=lambda: os.getenv("ORACLE_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("ORACLE_PASSWORD", ""))

    @property
    def connection_string(self) -> str:
        return f"oracle+cx_oracle://{self.user}:{self.password}@{self.host}:{self.port}/?service_name={self.service_name}"


@dataclass
class MySQLConfig:
    """MySQL 数据库配置"""
    host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    database: str = field(default_factory=lambda: os.getenv("MYSQL_DATABASE", ""))
    user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", ""))

    @property
    def connection_string(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class PostgreSQLConfig:
    """PostgreSQL 数据库配置"""
    host: str = field(default_factory=lambda: os.getenv("PG_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("PG_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("PG_DATABASE", ""))
    user: str = field(default_factory=lambda: os.getenv("PG_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("PG_PASSWORD", ""))

    @property
    def connection_string(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class HiveConfig:
    """Hive 数据库配置"""
    host: str = field(default_factory=lambda: os.getenv("HIVE_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("HIVE_PORT", "10000")))
    database: str = field(default_factory=lambda: os.getenv("HIVE_DATABASE", "default"))
    user: str = field(default_factory=lambda: os.getenv("HIVE_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("HIVE_PASSWORD", ""))

    @property
    def connection_string(self) -> str:
        return f"hive://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class VectorDBConfig:
    """向量数据库配置"""
    db_path: str = field(default_factory=lambda: os.getenv("VECTOR_DB_PATH", "./vector_db"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200")))


@dataclass
class KnowledgeBaseConfig:
    """知识库配置"""
    base_path: str = field(default_factory=lambda: os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base"))
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class MCPConfig:
    """MCP 配置"""
    server_url: str = field(default_factory=lambda: os.getenv("MCP_SERVER_URL", "http://localhost:3000"))


# 全局配置实例
ollama_config = OllamaConfig()
oracle_config = OracleConfig()
mysql_config = MySQLConfig()
pg_config = PostgreSQLConfig()
hive_config = HiveConfig()
vector_db_config = VectorDBConfig()
kb_config = KnowledgeBaseConfig()
mcp_config = MCPConfig()
