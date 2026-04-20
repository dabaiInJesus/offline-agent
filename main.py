"""
主程序入口 - 整合所有功能
"""
import asyncio
import os
from typing import Optional
from loguru import logger

# 导入各模块
from models.ollama_model import get_llm, get_embeddings, OllamaLLM
from database.db_manager import db_manager
from vectorstore.manager import vector_manager
from knowledge_base.knowledge_base import KnowledgeBase, kb_manager
from agent.factory import create_agent, AgentFactory
from skills.registry import skill_registry, discover_skills
from mcp.client import mcp_manager

# 配置日志
logger.add("logs/app.log", rotation="500 MB", level="INFO")


class OfflineAgent:
    """
    离线智能体主类
    整合所有 AI 功能
    """
    
    def __init__(self):
        self.llm: Optional[OllamaLLM] = None
        self.embedding_model = None
        self._initialized = False
    
    async def initialize(self):
        """初始化系统"""
        if self._initialized:
            return
        
        logger.info("正在初始化 Offline Agent...")
        
        # 1. 初始化模型
        self.llm = get_llm()
        self.embedding_model = get_embeddings()
        logger.info("模型初始化完成")
        
        # 2. 初始化向量库管理器
        vector_manager.set_default_embedding_model(self.embedding_model)
        
        # 3. 发现并注册所有技能
        discover_skills()
        logger.info(f"已注册 {len(skill_registry.list_skills())} 个技能")
        
        self._initialized = True
        logger.info("Offline Agent 初始化完成")
    
    # ========== 数据库功能 ==========
    
    def connect_database(self, db_type: str, name: str = None, **kwargs) -> bool:
        """
        连接数据库
        
        Args:
            db_type: 数据库类型 (oracle/mysql/postgresql/hive)
            name: 连接名称
            **kwargs: 连接参数
        """
        name = name or db_type
        
        if db_type == "oracle":
            from database.oracle_db import OracleDatabase
            db = OracleDatabase()
        elif db_type == "mysql":
            from database.mysql_db import MySQLDatabase
            db = MySQLDatabase()
        elif db_type == "postgresql":
            from database.postgresql_db import PostgreSQLDatabase
            db = PostgreSQLDatabase()
        elif db_type == "hive":
            from database.hive_db import HiveDatabase
            db = HiveDatabase()
        else:
            logger.error(f"不支持的数据库类型: {db_type}")
            return False
        
        return db_manager.register(name, db)
    
    def execute_sql(self, db_name: str, sql: str, params: dict = None):
        """执行 SQL 查询"""
        from database.db_manager import execute_sql
        return execute_sql(db_name, sql, params)
    
    def list_databases(self):
        """列出所有数据库连接"""
        return db_manager.list_databases()
    
    # ========== 向量库功能 ==========
    
    def create_vector_store(self, name: str, store_type: str = "chroma"):
        """
        创建向量库
        
        Args:
            name: 向量库名称
            store_type: 类型 (chroma/faiss)
        """
        if store_type == "chroma":
            return vector_manager.create_chroma_store(name)
        elif store_type == "faiss":
            return vector_manager.create_faiss_store(name)
        else:
            raise ValueError(f"不支持的向量库类型: {store_type}")
    
    def search_vectors(self, store_name: str, query: str, top_k: int = 5):
        """向量搜索"""
        from vectorstore.manager import search_vectors
        return search_vectors(store_name, query, top_k)
    
    # ========== 知识库功能 ==========
    
    def create_knowledge_base(
        self,
        name: str,
        document_dir: str = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> KnowledgeBase:
        """
        创建知识库
        
        Args:
            name: 知识库名称
            document_dir: 文档目录（可选）
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
        """
        if document_dir:
            kb = KnowledgeBase.create_from_directory(
                name=name,
                directory=document_dir,
                embedding_model=self.embedding_model,
                llm=self.llm,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            kb = KnowledgeBase(
                name=name,
                embedding_model=self.embedding_model,
                llm=self.llm,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        kb_manager._knowledge_bases[name] = kb
        return kb
    
    def query_knowledge_base(self, kb_name: str, question: str):
        """查询知识库"""
        kb = kb_manager.get(kb_name)
        if not kb:
            raise ValueError(f"知识库 '{kb_name}' 不存在")
        return kb.query(question)
    
    # ========== Agent 功能 ==========
    
    def create_agent(
        self,
        agent_type: str = "react",
        name: str = None,
        system_prompt: str = None,
        tools: dict = None
    ):
        """
        创建 Agent
        
        Args:
            agent_type: Agent 类型 (react/tool/graph)
            name: Agent 名称
            system_prompt: 系统提示词
            tools: 工具字典
        """
        agent = AgentFactory.create_with_tools(
            agent_type=agent_type,
            name=name or f"{agent_type}_agent",
            tools=tools or {},
            llm=self.llm,
            system_prompt=system_prompt
        )
        return agent
    
    # ========== Skill 功能 ==========
    
    def execute_skill(self, skill_name: str, **kwargs):
        """执行技能"""
        from skills.registry import execute_skill
        return execute_skill(skill_name, **kwargs)
    
    def list_skills(self):
        """列出所有技能"""
        return skill_registry.list_skill_info()
    
    # ========== MCP 功能 ==========
    
    async def connect_mcp_server(self, name: str, url: str, api_key: str = None):
        """连接 MCP 服务器"""
        from mcp.client import MCPServerConfig
        
        config = MCPServerConfig(name=name, url=url, api_key=api_key)
        return await mcp_manager.add_server(config)
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs):
        """调用 MCP 工具"""
        return await mcp_manager.call_tool(server_name, tool_name, kwargs)


# 全局 Agent 实例
_agent: Optional[OfflineAgent] = None


async def get_agent() -> OfflineAgent:
    """获取全局 Agent 实例"""
    global _agent
    if _agent is None:
        _agent = OfflineAgent()
        await _agent.initialize()
    return _agent


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    Offline Agent                             ║
║          本地 AI 智能体 - LangChain + LangGraph              ║
╠══════════════════════════════════════════════════════════════╣
║  功能：                                                      ║
║    • Ollama 本地大模型连接                                   ║
║    • 多数据库支持 (Oracle/MySQL/PostgreSQL/Hive)             ║
║    • 向量数据库 (FAISS/Chroma)                               ║
║    • 知识库 RAG 系统                                         ║
║    • 智能体 Agent (ReAct/Tool/Graph)                         ║
║    • 技能系统 AgentSkill                                     ║
║    • MCP 协议支持                                            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)
    
    # 运行异步初始化
    asyncio.run(get_agent())
    
    print("\n系统已就绪！")
    print("\n示例用法：")
    print("-" * 50)
    print("""
# 1. 连接数据库
agent.connect_database("mysql", "mydb")
result = agent.execute_sql("mydb", "SELECT * FROM users LIMIT 10")

# 2. 创建知识库
kb = agent.create_knowledge_base("docs", "/path/to/documents")
answer = agent.query_knowledge_base("docs", "什么是人工智能？")

# 3. 创建 Agent
react_agent = agent.create_agent("react", tools={"search": search_func})
result = react_agent.run("查询今天的天气")

# 4. 执行技能
result = agent.execute_skill("database", db_name="mydb", operation="query", sql="SELECT * FROM table")

# 5. 连接 MCP 服务器
await agent.connect_mcp_server("remote", "http://localhost:3000/mcp")
result = await agent.call_mcp_tool("remote", "get_weather", city="北京")
    """)
    print("-" * 50)


if __name__ == "__main__":
    main()
