"""
RAG 引擎 - 检索增强生成
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable
from loguru import logger

from vectorstore.base import BaseVectorStore, Document, SearchResult
from models.ollama_model import OllamaLLM


@dataclass
class RAGConfig:
    """RAG 配置"""
    top_k: int = 5                    # 检索文档数量
    score_threshold: float = 0.5      # 相似度阈值
    max_context_length: int = 4000    # 最大上下文长度
    include_metadata: bool = True     # 是否包含元数据
    return_sources: bool = True       # 是否返回来源
    system_prompt: Optional[str] = None  # 系统提示词


class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) 引擎
    结合向量检索和大语言模型生成回答
    """
    
    DEFAULT_SYSTEM_PROMPT = """你是一个基于知识库的AI助手。请根据以下检索到的上下文信息回答用户的问题。
如果上下文中没有相关信息，请明确告知用户你无法从知识库中找到答案。
请保持回答的准确性和专业性，并尽可能引用上下文中的信息。

上下文信息：
{context}

用户问题：{question}

请基于上述上下文回答问题："""
    
    def __init__(
        self,
        vector_store: BaseVectorStore,
        llm: Optional[OllamaLLM] = None,
        config: Optional[RAGConfig] = None
    ):
        self.vector_store = vector_store
        self.llm = llm or OllamaLLM()
        self.config = config or RAGConfig()
        self._prompt_template = self.config.system_prompt or self.DEFAULT_SYSTEM_PROMPT
    
    def set_prompt_template(self, template: str):
        """设置自定义提示模板"""
        self._prompt_template = template
    
    def _format_context(self, search_results: List[SearchResult]) -> str:
        """格式化检索结果作为上下文"""
        contexts = []
        
        for i, result in enumerate(search_results, 1):
            doc = result.document
            context_text = f"[文档 {i}]\n{doc.page_content}"
            
            if self.config.include_metadata and doc.metadata:
                source = doc.metadata.get('source', '未知来源')
                context_text += f"\n来源: {source}"
            
            contexts.append(context_text)
        
        return "\n\n---\n\n".join(contexts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """构建提示词"""
        return self._prompt_template.format(
            context=context,
            question=question
        )
    
    def query(self, question: str, filter_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """
        执行 RAG 查询
        
        Args:
            question: 用户问题
            filter_dict: 文档过滤条件
            
        Returns:
            包含回答和来源信息的字典
        """
        # 1. 检索相关文档
        search_results = self.vector_store.similarity_search_with_score(
            query=question,
            top_k=self.config.top_k,
            score_threshold=self.config.score_threshold
        )
        
        if not search_results:
            return {
                'answer': "抱歉，我在知识库中没有找到与您问题相关的信息。",
                'sources': [],
                'context': "",
                'has_relevant_info': False
            }
        
        # 2. 格式化上下文
        context = self._format_context(search_results)
        
        # 3. 构建提示词
        prompt = self._build_prompt(question, context)
        
        # 4. 调用 LLM 生成回答
        from langchain_core.messages import HumanMessage
        response = self.llm.invoke([HumanMessage(content=prompt)])
        answer = response.content
        
        # 5. 准备返回结果
        result = {
            'answer': answer,
            'context': context if self.config.return_sources else "",
            'has_relevant_info': True
        }
        
        if self.config.return_sources:
            result['sources'] = [
                {
                    'content': r.document.page_content[:200] + "...",
                    'metadata': r.document.metadata,
                    'score': r.score
                }
                for r in search_results
            ]
        
        return result
    
    async def aquery(self, question: str, filter_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """异步执行 RAG 查询"""
        # 1. 检索相关文档
        search_results = self.vector_store.similarity_search_with_score(
            query=question,
            top_k=self.config.top_k,
            score_threshold=self.config.score_threshold
        )
        
        if not search_results:
            return {
                'answer': "抱歉，我在知识库中没有找到与您问题相关的信息。",
                'sources': [],
                'context': "",
                'has_relevant_info': False
            }
        
        # 2. 格式化上下文
        context = self._format_context(search_results)
        
        # 3. 构建提示词
        prompt = self._build_prompt(question, context)
        
        # 4. 异步调用 LLM
        from langchain_core.messages import HumanMessage
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        answer = response.content
        
        result = {
            'answer': answer,
            'context': context if self.config.return_sources else "",
            'has_relevant_info': True
        }
        
        if self.config.return_sources:
            result['sources'] = [
                {
                    'content': r.document.page_content[:200] + "...",
                    'metadata': r.document.metadata,
                    'score': r.score
                }
                for r in search_results
            ]
        
        return result
    
    def stream_query(self, question: str, filter_dict: Optional[Dict] = None):
        """
        流式执行 RAG 查询
        
        Yields:
            生成的文本片段
        """
        # 1. 检索相关文档
        search_results = self.vector_store.similarity_search_with_score(
            query=question,
            top_k=self.config.top_k,
            score_threshold=self.config.score_threshold
        )
        
        if not search_results:
            yield "抱歉，我在知识库中没有找到与您问题相关的信息。"
            return
        
        # 2. 格式化上下文
        context = self._format_context(search_results)
        
        # 3. 构建提示词
        prompt = self._build_prompt(question, context)
        
        # 4. 流式调用 LLM
        from langchain_core.messages import HumanMessage
        for chunk in self.llm.stream([HumanMessage(content=prompt)]):
            yield chunk.content
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到知识库"""
        return self.vector_store.add_documents(documents)
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> List[str]:
        """添加文本到知识库"""
        return self.vector_store.add_texts(texts, metadatas)
    
    def delete_documents(self, ids: List[str]) -> bool:
        """删除文档"""
        return self.vector_store.delete(ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return {
            'document_count': self.vector_store.count(),
            'collection_name': self.vector_store.collection_name,
            'top_k': self.config.top_k,
            'score_threshold': self.config.score_threshold
        }


class MultiStoreRAG:
    """多向量库 RAG - 支持从多个知识库检索"""
    
    def __init__(
        self,
        vector_stores: Dict[str, BaseVectorStore],
        llm: Optional[OllamaLLM] = None,
        config: Optional[RAGConfig] = None
    ):
        self.vector_stores = vector_stores
        self.llm = llm or OllamaLLM()
        self.config = config or RAGConfig()
    
    def query(
        self,
        question: str,
        store_names: Optional[List[str]] = None,
        top_k_per_store: int = 3
    ) -> Dict[str, Any]:
        """
        从多个知识库检索并生成回答
        
        Args:
            question: 用户问题
            store_names: 要查询的知识库名称列表，None 表示查询所有
            top_k_per_store: 每个知识库检索的文档数
        """
        # 确定要查询的知识库
        stores_to_query = store_names or list(self.vector_stores.keys())
        
        # 从各个知识库检索
        all_results = []
        for name in stores_to_query:
            if name not in self.vector_stores:
                logger.warning(f"知识库 '{name}' 不存在")
                continue
            
            store = self.vector_stores[name]
            results = store.similarity_search_with_score(
                query=question,
                top_k=top_k_per_store,
                score_threshold=self.config.score_threshold
            )
            
            # 添加知识库名称到结果
            for r in results:
                r.document.metadata['knowledge_base'] = name
            
            all_results.extend(results)
        
        # 按分数排序
        all_results.sort(key=lambda x: x.score, reverse=True)
        all_results = all_results[:self.config.top_k]
        
        if not all_results:
            return {
                'answer': "抱歉，在所有知识库中都没有找到相关信息。",
                'sources': [],
                'has_relevant_info': False
            }
        
        # 构建上下文并生成回答
        contexts = []
        for i, result in enumerate(all_results, 1):
            doc = result.document
            kb_name = doc.metadata.get('knowledge_base', '未知')
            context_text = f"[来源: {kb_name}]\n{doc.page_content}"
            contexts.append(context_text)
        
        context = "\n\n---\n\n".join(contexts)
        
        prompt = f"""基于以下从多个知识库检索到的信息，回答用户问题：

{context}

用户问题：{question}

请综合以上信息回答问题："""
        
        from langchain_core.messages import HumanMessage
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        return {
            'answer': response.content,
            'sources': [
                {
                    'knowledge_base': r.document.metadata.get('knowledge_base'),
                    'content': r.document.page_content[:200] + "...",
                    'score': r.score
                }
                for r in all_results
            ],
            'has_relevant_info': True
        }
