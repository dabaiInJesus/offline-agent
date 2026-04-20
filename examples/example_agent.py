"""
Agent 智能体示例 - 展示不同类型的 Agent
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()


def mock_tools():
    """创建模拟工具"""
    def search(query: str):
        """搜索信息"""
        return f"搜索结果: 关于 '{query}' 的信息..."
    
    def calculate(expression: str):
        """计算表达式"""
        try:
            return str(eval(expression))
        except:
            return "计算错误"
    
    def get_weather(city: str):
        """获取天气"""
        return f"{city} 今天天气晴朗，25°C"
    
    def read_file(path: str):
        """读取文件"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()[:500]
        return "文件不存在"
    
    return {
        "search": search,
        "calculate": calculate,
        "get_weather": get_weather,
        "read_file": read_file
    }


def example_react_agent():
    """示例：ReAct Agent"""
    print("\n" + "="*60)
    print("示例1: ReAct Agent (推理+行动循环)")
    print("="*60)
    
    from agent.factory import create_react_agent
    from models.ollama_model import get_llm
    
    # 创建 Agent
    agent = create_react_agent(
        name="react_demo",
        llm=get_llm(),
        tools=mock_tools()
    )
    
    print("\n工具列表:")
    for tool in agent.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")
    
    # 运行 Agent
    queries = [
        "请计算 123 * 456",
        "查询北京的天气",
    ]
    
    for query in queries:
        print(f"\n用户: {query}")
        print("-" * 40)
        
        try:
            result = agent.run(query)
            print(f"Agent: {result}")
            
            # 显示执行步骤
            print("\n执行步骤:")
            for msg in agent.get_conversation_history():
                if msg['role'] in ['assistant', 'observation']:
                    print(f"  [{msg['role']}] {msg['content'][:100]}...")
            
            agent.reset()  # 重置状态
            
        except Exception as e:
            print(f"执行出错: {e}")


def example_tool_agent():
    """示例：Tool Agent"""
    print("\n" + "="*60)
    print("示例2: Tool Agent (工具调用型)")
    print("="*60)
    
    from agent.factory import create_tool_agent
    from models.ollama_model import get_llm
    
    # 创建 Agent
    agent = create_tool_agent(
        name="tool_demo",
        llm=get_llm(),
        tools=mock_tools()
    )
    
    print("\n运行示例查询...")
    query = "搜索 Python 编程的相关信息"
    
    print(f"\n用户: {query}")
    try:
        result = agent.run(query)
        print(f"Agent: {result}")
    except Exception as e:
        print(f"执行出错: {e}")


def example_graph_agent():
    """示例：Graph Agent"""
    print("\n" + "="*60)
    print("示例3: Graph Agent (基于 LangGraph)")
    print("="*60)
    
    from agent.factory import create_graph_agent
    from models.ollama_model import get_llm
    
    # 创建 Agent
    agent = create_graph_agent(
        name="graph_demo",
        llm=get_llm(),
        tools=mock_tools()
    )
    
    print("\nGraph Agent 使用状态图管理工作流")
    print("节点: think -> act -> observe -> (循环或结束)")
    
    query = "计算 (100 + 200) * 3"
    print(f"\n用户: {query}")
    
    try:
        result = agent.run(query)
        print(f"Agent: {result}")
    except Exception as e:
        print(f"执行出错: {e}")


def example_agent_with_skills():
    """示例：Agent 使用 Skills"""
    print("\n" + "="*60)
    print("示例4: Agent 集成 Skills")
    print("="*60)
    
    from agent.factory import create_react_agent
    from models.ollama_model import get_llm
    from skills.registry import skill_registry, discover_skills
    
    # 发现技能
    discover_skills()
    
    # 创建 Agent
    agent = create_react_agent(
        name="skill_agent",
        llm=get_llm()
    )
    
    # 将技能包装为工具
    def skill_wrapper(skill_name: str, **kwargs):
        """调用技能"""
        result = skill_registry.execute(skill_name, **kwargs)
        if result.success:
            return result.data
        return f"错误: {result.error}"
    
    # 注册技能工具
    for skill_name in skill_registry.list_skills()[:3]:  # 只注册前3个
        agent.register_tool(
            f"skill_{skill_name}",
            lambda **kwargs, sn=skill_name: skill_wrapper(sn, **kwargs),
            f"执行 {skill_name} 技能"
        )
    
    print(f"\n已为 Agent 注册 {len(agent.list_tools())} 个技能工具")
    for tool in agent.list_tools():
        print(f"  - {tool['name']}")


def example_agent_factory():
    """示例：Agent 工厂"""
    print("\n" + "="*60)
    print("示例5: Agent 工厂模式")
    print("="*60)
    
    from agent.factory import AgentFactory
    
    print("\n可用的 Agent 类型:")
    for agent_type in AgentFactory.list_agent_types():
        print(f"  - {agent_type}")
    
    print("\n创建不同类型的 Agent:")
    
    from models.ollama_model import get_llm
    
    for agent_type in ["react", "tool", "graph"]:
        agent = AgentFactory.create(
            agent_type=agent_type,
            name=f"{agent_type}_test",
            llm=get_llm()
        )
        print(f"  ✓ 创建 {agent_type} Agent: {agent.name}")


def example_multi_agent():
    """示例：多 Agent 协作"""
    print("\n" + "="*60)
    print("示例6: 多 Agent 协作")
    print("="*60)
    
    from agent.factory import create_agent
    from agent.graph_agent import MultiAgentGraph
    from models.ollama_model import get_llm
    
    print("\n创建多个专业 Agent...")
    
    # 创建专业 Agent
    research_agent = create_agent(
        "react",
        name="researcher",
        llm=get_llm(),
        system_prompt="你是一个研究专家，擅长收集和分析信息。",
        tools={"search": mock_tools()["search"]}
    )
    
    math_agent = create_agent(
        "react",
        name="mathematician",
        llm=get_llm(),
        system_prompt="你是一个数学专家，擅长计算和逻辑推理。",
        tools={"calculate": mock_tools()["calculate"]}
    )
    
    print("  ✓ 研究员 Agent")
    print("  ✓ 数学家 Agent")
    
    print("\n多 Agent 协作可以通过以下方式实现:")
    print("  1. 使用 MultiAgentGraph 构建协作图")
    print("  2. 主 Agent 协调子 Agent")
    print("  3. Agent 之间通过共享状态通信")


def example_agent_memory():
    """示例：Agent 记忆"""
    print("\n" + "="*60)
    print("示例7: Agent 记忆功能")
    print("="*60)
    
    from agent.factory import create_react_agent
    from models.ollama_model import get_llm
    
    agent = create_react_agent(
        name="memory_agent",
        llm=get_llm()
    )
    
    print("\n多轮对话示例:")
    
    conversations = [
        "我叫张三",
        "我的名字是什么？",
        "我喜欢编程",
        "我的爱好是什么？"
    ]
    
    for msg in conversations:
        print(f"\n用户: {msg}")
        try:
            result = agent.run(msg)
            print(f"Agent: {result[:100]}...")
        except Exception as e:
            print(f"错误: {e}")
    
    print("\n对话历史:")
    for msg in agent.get_conversation_history()[-6:]:
        print(f"  [{msg['role']}] {msg['content'][:50]}...")


def main():
    """运行 Agent 示例"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Agent 智能体完整示例                            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        example_react_agent()
        example_tool_agent()
        example_graph_agent()
        example_agent_with_skills()
        example_agent_factory()
        example_multi_agent()
        example_agent_memory()
        
    except Exception as e:
        print(f"\n运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Agent 示例完成！")
    print("="*60)


if __name__ == "__main__":
    main()
