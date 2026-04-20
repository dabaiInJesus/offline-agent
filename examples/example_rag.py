"""
RAG 知识库示例 - 展示完整的 RAG 流程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()


def create_sample_documents():
    """创建示例文档"""
    docs_dir = "./sample_docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    # 创建示例文本文件
    with open(f"{docs_dir}/ai_intro.txt", "w", encoding="utf-8") as f:
        f.write("""
人工智能简介

人工智能（Artificial Intelligence，简称 AI）是计算机科学的一个分支，
致力于创造能够模拟人类智能的系统。

主要应用领域包括：
1. 机器学习 - 让计算机从数据中学习
2. 自然语言处理 - 理解和生成人类语言
3. 计算机视觉 - 识别和理解图像
4. 语音识别 - 将语音转换为文本
5. 专家系统 - 模拟人类专家的决策能力

深度学习是机器学习的一个子集，使用神经网络来处理数据。
神经网络由多层神经元组成，可以学习复杂的模式。
        """)
    
    with open(f"{docs_dir}/python_guide.md", "w", encoding="utf-8") as f:
        f.write("""
# Python 编程指南

## 基础语法

Python 是一种高级编程语言，以简洁和易读性著称。

### 变量和数据类型

```python
# 字符串
name = "Python"

# 数字
age = 30
pi = 3.14159

# 列表
fruits = ["apple", "banana", "cherry"]

# 字典
person = {"name": "Alice", "age": 25}
```

### 函数定义

```python
def greet(name):
    return f"Hello, {name}!"
```

## 常用库

- NumPy: 数值计算
- Pandas: 数据处理
- Matplotlib: 数据可视化
- Scikit-learn: 机器学习
        """)
    
    return docs_dir


def example_create_kb():
    """示例：创建知识库"""
    print("\n" + "="*50)
    print("示例：创建知识库")
    print("="*50)
    
    from knowledge_base.knowledge_base import KnowledgeBase
    from models.ollama_model import get_embeddings, get_llm
    
    # 创建示例文档
    docs_dir = create_sample_documents()
    print(f"✓ 创建示例文档目录: {docs_dir}")
    
    # 创建知识库
    print("\n正在创建知识库...")
    kb = KnowledgeBase.create_from_directory(
        name="tech_docs",
        directory=docs_dir,
        embedding_model=get_embeddings(),
        llm=get_llm(),
        chunk_size=500,
        chunk_overlap=100
    )
    
    print(f"✓ 知识库 'tech_docs' 创建完成")
    print(f"✓ 文档数量: {kb.get_stats()['document_count']}")
    
    return kb


def example_query_kb(kb):
    """示例：查询知识库"""
    print("\n" + "="*50)
    print("示例：查询知识库")
    print("="*50)
    
    questions = [
        "什么是人工智能？",
        "Python 有哪些常用库？",
        "什么是深度学习？",
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        print("-" * 40)
        
        try:
            result = kb.query(question, top_k=3)
            print(f"回答: {result['answer'][:200]}...")
            
            if result.get('sources'):
                print(f"\n来源:")
                for i, source in enumerate(result['sources'][:2], 1):
                    print(f"  {i}. {source['metadata'].get('source', 'unknown')} (score: {source['score']:.3f})")
        except Exception as e:
            print(f"查询失败: {e}")


def example_search_only(kb):
    """示例：仅检索不生成"""
    print("\n" + "="*50)
    print("示例：仅检索文档")
    print("="*50)
    
    query = "机器学习"
    print(f"\n查询: {query}")
    
    documents = kb.search(query, top_k=3)
    
    print(f"\n找到 {len(documents)} 个相关文档:")
    for i, doc in enumerate(documents, 1):
        print(f"\n{i}. 来源: {doc.metadata.get('source', 'unknown')}")
        print(f"   内容: {doc.page_content[:150]}...")


def example_add_documents(kb):
    """示例：动态添加文档"""
    print("\n" + "="*50)
    print("示例：动态添加文档")
    print("="*50)
    
    # 添加文本
    new_text = """
    LangChain 是一个用于开发大语言模型应用的框架。
    它提供了链式调用、提示词管理、记忆功能等组件。
    LangGraph 是 LangChain 的扩展，用于构建复杂的 Agent 工作流。
    """
    
    doc_ids = kb.add_text(
        text=new_text,
        metadata={"source": "langchain_notes", "category": "framework"}
    )
    
    print(f"✓ 已添加新文档，生成 {len(doc_ids)} 个片段")
    
    # 查询新内容
    result = kb.query("什么是 LangChain？")
    print(f"\n查询结果: {result['answer'][:200]}...")


def example_multi_kb():
    """示例：多知识库查询"""
    print("\n" + "="*50)
    print("示例：多知识库 RAG")
    print("="*50)
    
    from knowledge_base.rag_engine import MultiStoreRAG
    from knowledge_base.knowledge_base import kb_manager
    from models.ollama_model import get_llm
    
    print("\n创建多个知识库...")
    
    # 创建知识库（如果还没有）
    kb_names = []
    for name in ["tech_docs", "business_docs"]:
        kb = kb_manager.get(name)
        if kb:
            kb_names.append(name)
    
    if len(kb_names) >= 1:
        print(f"使用知识库: {kb_names}")
        
        # 获取知识库实例
        stores = {name: kb_manager.get(name).vector_store for name in kb_names}
        
        # 创建多知识库 RAG
        multi_rag = MultiStoreRAG(
            vector_stores=stores,
            llm=get_llm()
        )
        
        print("\n多知识库查询示例:")
        result = multi_rag.query(
            question="编程和人工智能相关的内容",
            store_names=kb_names,
            top_k_per_store=2
        )
        
        print(f"回答: {result['answer'][:200]}...")
        print(f"\n来源知识库:")
        for source in result.get('sources', []):
            print(f"  - {source.get('knowledge_base')}")
    else:
        print("⚠ 需要至少一个知识库才能演示多知识库查询")


def example_kb_management():
    """示例：知识库管理"""
    print("\n" + "="*50)
    print("示例：知识库管理")
    print("="*50)
    
    from knowledge_base.knowledge_base import kb_manager
    
    # 列出知识库
    print("\n知识库列表:")
    kb_list = kb_manager.list_knowledge_bases()
    for name in kb_list:
        kb = kb_manager.get(name)
        stats = kb.get_stats()
        print(f"  - {name}: {stats['document_count']} 文档")
    
    # 获取统计信息
    if kb_list:
        kb = kb_manager.get(kb_list[0])
        stats = kb.get_stats()
        print(f"\n知识库 '{kb_list[0]}' 统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


def main():
    """运行 RAG 示例"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              RAG 知识库完整示例                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 1. 创建知识库
        kb = example_create_kb()
        
        # 2. 查询知识库
        example_query_kb(kb)
        
        # 3. 仅检索
        example_search_only(kb)
        
        # 4. 动态添加文档
        example_add_documents(kb)
        
        # 5. 多知识库查询
        example_multi_kb()
        
        # 6. 知识库管理
        example_kb_management()
        
    except Exception as e:
        print(f"\n运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50)
    print("RAG 示例完成！")
    print("="*50)
    
    # 清理
    import shutil
    if os.path.exists("./sample_docs"):
        shutil.rmtree("./sample_docs")
        print("\n已清理示例文档")


if __name__ == "__main__":
    main()
