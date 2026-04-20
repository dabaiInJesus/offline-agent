"""
基础示例 - 展示各模块的基本用法
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger

# 禁用日志输出到控制台，保持示例输出清晰
logger.remove()


def example_ollama():
    """示例1: Ollama 模型连接"""
    print("\n" + "="*50)
    print("示例1: Ollama 本地模型连接")
    print("="*50)
    
    from models.ollama_model import get_llm, get_embeddings
    
    # 获取 LLM
    llm = get_llm(model="qwen2.5:14b")
    print(f"✓ 已创建 LLM 实例: {llm.model}")
    
    # 获取嵌入模型
    embeddings = get_embeddings(model="nomic-embed-text:latest")
    print(f"✓ 已创建嵌入模型")
    
    # 简单对话
    from langchain_core.messages import HumanMessage
    
    print("\n发送消息: '你好，请介绍一下自己'")
    try:
        response = llm.invoke([HumanMessage(content="你好，请用一句话介绍自己")])
        print(f"模型回复: {response.content}")
    except Exception as e:
        print(f"⚠ 模型调用失败（请确保 Ollama 服务已启动）: {e}")
    
    # 列出可用模型
    print("\n可用模型列表:")
    try:
        models = llm.list_models()
        for model in models[:5]:  # 只显示前5个
            print(f"  - {model.get('name', 'unknown')}")
    except Exception as e:
        print(f"  ⚠ 无法获取模型列表: {e}")


def example_database():
    """示例2: 数据库连接"""
    print("\n" + "="*50)
    print("示例2: 数据库连接")
    print("="*50)
    
    from database.db_manager import db_manager
    from database.mysql_db import MySQLDatabase
    from database.postgresql_db import PostgreSQLDatabase
    
    print("\n支持的数据库类型:")
    print("  - Oracle (OracleDatabase)")
    print("  - MySQL (MySQLDatabase)")
    print("  - PostgreSQL (PostgreSQLDatabase)")
    print("  - Hive (HiveDatabase)")
    
    print("\n示例代码:")
    print("""
    # 连接 MySQL
    db_manager.quick_connect_mysql("mysql_db")
    
    # 执行查询
    result = db_manager.get("mysql_db").execute("SELECT * FROM users LIMIT 10")
    
    # 获取表结构
    schema = db_manager.get("mysql_db").get_table_schema("users")
    
    # 关闭连接
    db_manager.close_all()
    """)


def example_vector_store():
    """示例3: 向量数据库"""
    print("\n" + "="*50)
    print("示例3: 向量数据库")
    print("="*50)
    
    from vectorstore.manager import vector_manager
    from models.ollama_model import get_embeddings
    
    print("\n支持的向量库:")
    print("  - FAISS (高性能本地向量库)")
    print("  - ChromaDB (持久化向量库)")
    
    print("\n示例代码:")
    print("""
    from vectorstore.manager import vector_manager
    from models.ollama_model import get_embeddings
    
    # 设置嵌入模型
    embeddings = get_embeddings()
    vector_manager.set_default_embedding_model(embeddings)
    
    # 创建 FAISS 向量库
    store = vector_manager.create_faiss_store("my_store")
    
    # 添加文档
    from vectorstore.base import Document
    docs = [
        Document(page_content="这是第一个文档", metadata={"source": "doc1"}),
        Document(page_content="这是第二个文档", metadata={"source": "doc2"})
    ]
    store.add_documents(docs)
    
    # 搜索
    results = store.search("第一个", top_k=2)
    for r in results:
        print(f"内容: {r.document.page_content}, 分数: {r.score}")
    """)


def example_knowledge_base():
    """示例4: 知识库 RAG"""
    print("\n" + "="*50)
    print("示例4: 知识库 RAG")
    print("="*50)
    
    print("\n功能特性:")
    print("  - 多格式文档加载 (PDF/Word/Excel/TXT/Markdown)")
    print("  - 智能文档分割")
    print("  - 向量检索增强生成")
    print("  - 多知识库联合查询")
    
    print("\n示例代码:")
    print("""
    from knowledge_base.knowledge_base import create_knowledge_base
    
    # 从目录创建知识库
    kb = create_knowledge_base(
        name="product_docs",
        directory="./documents"
    )
    
    # 查询知识库
    result = kb.query("产品的核心功能是什么？")
    print(result['answer'])
    
    # 查看来源
    for source in result.get('sources', []):
        print(f"来源: {source['metadata']['source']}")
    """)


def example_agent():
    """示例5: Agent 智能体"""
    print("\n" + "="*50)
    print("示例5: Agent 智能体")
    print("="*50)
    
    from agent.factory import AgentFactory
    
    print("\n支持的 Agent 类型:")
    for agent_type in AgentFactory.list_agent_types():
        print(f"  - {agent_type}")
    
    print("\n示例代码:")
    print("""
    from agent.factory import create_agent
    
    # 创建 ReAct Agent
    agent = create_agent("react", name="my_agent")
    
    # 注册工具
    def search_tool(query: str):
        return f"搜索结果: {query}"
    
    agent.register_tool("search", search_tool, "搜索工具")
    
    # 运行 Agent
    result = agent.run("请使用搜索工具查询'Python'")
    print(result)
    
    # 查看执行历史
    for msg in agent.get_conversation_history():
        print(f"{msg['role']}: {msg['content']}")
    """)


def example_skills():
    """示例6: AgentSkill 技能系统"""
    print("\n" + "="*50)
    print("示例6: AgentSkill 技能系统")
    print("="*50)
    
    from skills.registry import skill_registry, discover_skills
    
    # 发现所有技能
    discover_skills()
    
    print(f"\n已注册技能 ({len(skill_registry.list_skills())}个):")
    for skill_info in skill_registry.list_skill_info():
        print(f"  - {skill_info['name']}: {skill_info['description']}")
    
    print("\n示例代码:")
    print("""
    from skills.registry import execute_skill
    
    # 执行数据库查询技能
    result = execute_skill(
        "database",
        db_name="mysql_db",
        operation="query",
        sql="SELECT COUNT(*) as count FROM users"
    )
    
    if result.success:
        print(f"查询结果: {result.data}")
    else:
        print(f"执行失败: {result.error}")
    
    # 执行代码分析技能
    result = execute_skill(
        "code_analysis",
        code="def hello():\\n    print('Hello')"
    )
    print(f"代码统计: {result.data}")
    """)


def example_mcp():
    """示例7: MCP 协议支持"""
    print("\n" + "="*50)
    print("示例7: MCP (Model Context Protocol)")
    print("="*50)
    
    print("\n功能特性:")
    print("  - 连接 MCP 服务器")
    print("  - 调用远程工具")
    print("  - 读取远程资源")
    print("  - 将 MCP 工具集成到 Agent")
    
    print("\n示例代码:")
    print("""
    import asyncio
    from mcp.client import mcp_manager, MCPServerConfig
    
    async def use_mcp():
        # 连接 MCP 服务器
        config = MCPServerConfig(
            name="remote_server",
            url="http://localhost:3000/mcp"
        )
        await mcp_manager.add_server(config)
        
        # 列出可用工具
        client = mcp_manager.get_client("remote_server")
        tools = client.list_tools()
        for tool in tools:
            print(f"工具: {tool['name']}")
        
        # 调用工具
        result = await mcp_manager.call_tool(
            "remote_server",
            "get_weather",
            {"city": "北京"}
        )
        print(result)
    
    asyncio.run(use_mcp())
    """)


def main():
    """运行所有示例"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Offline Agent - 基础功能示例                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 运行示例
    example_ollama()
    example_database()
    example_vector_store()
    example_knowledge_base()
    example_agent()
    example_skills()
    example_mcp()
    
    print("\n" + "="*50)
    print("所有示例展示完成！")
    print("="*50)
    print("""
提示：
1. 确保 Ollama 服务已启动 (http://localhost:11434)
2. 配置 .env 文件中的数据库连接信息
3. 安装依赖: pip install -r requirements.txt
4. 运行主程序: python main.py

更多示例请查看 examples/ 目录
    """)


if __name__ == "__main__":
    main()
