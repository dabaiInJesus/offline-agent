"""
知识库管理 - 整合文档加载、分割、存储和检索
"""
import os
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from loguru import logger

from vectorstore.base import BaseVectorStore, Document
from vectorstore.faiss_store import FAISSVectorStore
from vectorstore.chroma_store import ChromaVectorStore
from .document_loader import DocumentLoader, TextSplitter
from .rag_engine import RAGEngine, RAGConfig
from models.ollama_model import OllamaLLM, get_embeddings


class KnowledgeBase:
    """
    知识库类 - 一站式知识库管理
    整合文档处理、向量存储和 RAG 检索
    """
    
    def __init__(
        self,
        name: str,
        vector_store: Optional[BaseVectorStore] = None,
        embedding_model=None,
        llm: Optional[OllamaLLM] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        rag_config: Optional[RAGConfig] = None
    ):
        self.name = name
        self.embedding_model = embedding_model or get_embeddings()
        
        # 初始化向量存储
        if vector_store is None:
            # 默认使用 ChromaDB
            persist_path = f"./knowledge_bases/{name}"
            os.makedirs(persist_path, exist_ok=True)
            vector_store = ChromaVectorStore(
                embedding_model=self.embedding_model,
                collection_name=name,
                persist_path=persist_path
            )
        
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 初始化 RAG 引擎
        self.rag_engine = RAGEngine(
            vector_store=vector_store,
            llm=llm,
            config=rag_config or RAGConfig()
        )
        
        # 文本分割器
        self.text_splitter = TextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        logger.info(f"知识库 '{name}' 初始化完成")
    
    def add_document(
        self,
        file_path: str,
        metadata: Optional[Dict] = None,
        split: bool = True
    ) -> List[str]:
        """
        添加单个文档到知识库
        
        Args:
            file_path: 文档路径
            metadata: 附加元数据
            split: 是否分割文档
            
        Returns:
            文档 ID 列表
        """
        # 加载文档
        documents = DocumentLoader.load(file_path, metadata)
        
        # 分割文档
        if split:
            documents = self.text_splitter.split_documents(documents)
        
        # 添加到向量库
        doc_ids = self.vector_store.add_documents(documents)
        
        logger.info(f"已添加文档 '{file_path}'，生成 {len(doc_ids)} 个片段")
        return doc_ids
    
    def add_documents_from_directory(
        self,
        directory: str,
        pattern: str = "*",
        recursive: bool = True,
        metadata: Optional[Dict] = None
    ) -> Dict[str, List[str]]:
        """
        从目录批量添加文档
        
        Returns:
            文件名到文档 ID 列表的映射
        """
        # 加载所有文档
        documents = DocumentLoader.load_directory(
            directory, pattern, recursive, metadata
        )
        
        # 分割文档
        documents = self.text_splitter.split_documents(documents)
        
        # 按源文件分组
        file_docs = {}
        for doc in documents:
            source = doc.metadata.get('source', 'unknown')
            if source not in file_docs:
                file_docs[source] = []
            file_docs[source].append(doc)
        
        # 添加到向量库
        all_ids = {}
        for source, docs in file_docs.items():
            ids = self.vector_store.add_documents(docs)
            all_ids[source] = ids
            logger.info(f"已添加 '{source}'，生成 {len(ids)} 个片段")
        
        return all_ids
    
    def add_text(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        split: bool = True
    ) -> List[str]:
        """添加文本到知识库"""
        doc = Document(page_content=text, metadata=metadata or {})
        
        if split:
            docs = self.text_splitter.split_documents([doc])
        else:
            docs = [doc]
        
        return self.vector_store.add_documents(docs)
    
    def query(
        self,
        question: str,
        top_k: int = None,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        查询知识库
        
        Args:
            question: 问题
            top_k: 检索文档数
            return_sources: 是否返回来源
            
        Returns:
            包含回答和来源的字典
        """
        # 临时修改配置
        original_top_k = self.rag_engine.config.top_k
        original_return = self.rag_engine.config.return_sources
        
        if top_k is not None:
            self.rag_engine.config.top_k = top_k
        self.rag_engine.config.return_sources = return_sources
        
        try:
            result = self.rag_engine.query(question)
            return result
        finally:
            # 恢复配置
            self.rag_engine.config.top_k = original_top_k
            self.rag_engine.config.return_sources = original_return
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Document]:
        """
        仅检索相关文档，不生成回答
        
        Returns:
            相关文档列表
        """
        results = self.vector_store.search(query, top_k, filter_dict)
        return [r.document for r in results]
    
    def delete(self, doc_ids: List[str]) -> bool:
        """删除文档"""
        return self.vector_store.delete(doc_ids)
    
    def delete_by_filter(self, filter_dict: Dict) -> bool:
        """根据条件删除文档"""
        # 注意：这需要向量库支持按元数据过滤删除
        # 这里提供一个基础实现
        logger.warning("按条件删除需要具体向量库支持")
        return False
    
    def clear(self) -> bool:
        """清空知识库"""
        try:
            self.vector_store.delete_collection(self.vector_store.collection_name)
            return True
        except Exception as e:
            logger.error(f"清空知识库失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return {
            'name': self.name,
            'document_count': self.vector_store.count(),
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'vector_store_type': type(self.vector_store).__name__,
        }
    
    def save(self, path: str = None) -> bool:
        """保存知识库"""
        if path is None:
            path = f"./knowledge_bases/{self.name}"
        
        os.makedirs(path, exist_ok=True)
        return self.vector_store.save(path)
    
    def load(self, path: str = None) -> bool:
        """加载知识库"""
        if path is None:
            path = f"./knowledge_bases/{self.name}"
        
        return self.vector_store.load(path)
    
    @classmethod
    def create_from_directory(
        cls,
        name: str,
        directory: str,
        embedding_model=None,
        llm: Optional[OllamaLLM] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        vector_store_type: str = "chroma"
    ) -> "KnowledgeBase":
        """
        从目录创建知识库
        
        Args:
            name: 知识库名称
            directory: 文档目录
            embedding_model: 嵌入模型
            llm: 语言模型
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            vector_store_type: 向量库类型 (chroma/faiss)
        """
        # 创建嵌入模型
        emb_model = embedding_model or get_embeddings()
        
        # 创建向量存储
        if vector_store_type == "chroma":
            persist_path = f"./knowledge_bases/{name}"
            os.makedirs(persist_path, exist_ok=True)
            vector_store = ChromaVectorStore(
                embedding_model=emb_model,
                collection_name=name,
                persist_path=persist_path
            )
        elif vector_store_type == "faiss":
            vector_store = FAISSVectorStore(
                embedding_model=emb_model,
                collection_name=name,
                dimension=384  # 根据嵌入模型调整
            )
        else:
            raise ValueError(f"不支持的向量库类型: {vector_store_type}")
        
        # 创建知识库实例
        kb = cls(
            name=name,
            vector_store=vector_store,
            embedding_model=emb_model,
            llm=llm,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 加载目录中的文档
        kb.add_documents_from_directory(directory)
        
        return kb


class KnowledgeBaseManager:
    """知识库管理器 - 管理多个知识库"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._knowledge_bases: Dict[str, KnowledgeBase] = {}
        return cls._instance
    
    def create(
        self,
        name: str,
        embedding_model=None,
        llm: Optional[OllamaLLM] = None,
        vector_store_type: str = "chroma"
    ) -> KnowledgeBase:
        """创建新知识库"""
        kb = KnowledgeBase(
            name=name,
            embedding_model=embedding_model,
            llm=llm
        )
        self._knowledge_bases[name] = kb
        return kb
    
    def get(self, name: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self._knowledge_bases.get(name)
    
    def list_knowledge_bases(self) -> List[str]:
        """列出所有知识库"""
        return list(self._knowledge_bases.keys())
    
    def remove(self, name: str):
        """移除知识库"""
        if name in self._knowledge_bases:
            del self._knowledge_bases[name]
            logger.info(f"已移除知识库: {name}")


# 全局知识库管理器
kb_manager = KnowledgeBaseManager()


# 便捷函数
def create_knowledge_base(
    name: str,
    directory: str = None,
    embedding_model=None,
    llm: Optional[OllamaLLM] = None
) -> KnowledgeBase:
    """创建知识库"""
    if directory:
        return KnowledgeBase.create_from_directory(
            name=name,
            directory=directory,
            embedding_model=embedding_model,
            llm=llm
        )
    else:
        kb = KnowledgeBase(name=name, embedding_model=embedding_model, llm=llm)
        kb_manager._knowledge_bases[name] = kb
        return kb


def get_knowledge_base(name: str) -> Optional[KnowledgeBase]:
    """获取知识库"""
    return kb_manager.get(name)


def query_knowledge_base(name: str, question: str) -> Dict[str, Any]:
    """查询知识库"""
    kb = get_knowledge_base(name)
    if not kb:
        raise ValueError(f"知识库 '{name}' 不存在")
    return kb.query(question)
