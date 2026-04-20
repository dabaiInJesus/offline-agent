"""
向量存储管理器 - 统一管理多个向量库
"""
from typing import Dict, Optional, List
from .base import BaseVectorStore
from .faiss_store import FAISSVectorStore
from .chroma_store import ChromaVectorStore
from loguru import logger


class VectorStoreManager:
    """向量存储管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._stores: Dict[str, BaseVectorStore] = {}
            cls._instance._default_embedding_model = None
        return cls._instance
    
    def set_default_embedding_model(self, embedding_model):
        """设置默认嵌入模型"""
        self._default_embedding_model = embedding_model
    
    def create_faiss_store(
        self, 
        name: str, 
        collection_name: str = "default",
        dimension: int = 384,
        embedding_model=None
    ) -> FAISSVectorStore:
        """创建 FAISS 向量库"""
        model = embedding_model or self._default_embedding_model
        store = FAISSVectorStore(
            embedding_model=model,
            collection_name=collection_name,
            dimension=dimension
        )
        self._stores[name] = store
        logger.info(f"创建 FAISS 向量库: {name}")
        return store
    
    def create_chroma_store(
        self,
        name: str,
        collection_name: str = "default",
        persist_path: str = None,
        embedding_model=None
    ) -> ChromaVectorStore:
        """创建 ChromaDB 向量库"""
        model = embedding_model or self._default_embedding_model
        store = ChromaVectorStore(
            embedding_model=model,
            collection_name=collection_name,
            persist_path=persist_path or f"./chroma_db/{name}"
        )
        self._stores[name] = store
        logger.info(f"创建 ChromaDB 向量库: {name}")
        return store
    
    def get(self, name: str) -> Optional[BaseVectorStore]:
        """获取向量库"""
        return self._stores.get(name)
    
    def remove(self, name: str):
        """移除向量库"""
        if name in self._stores:
            del self._stores[name]
            logger.info(f"移除向量库: {name}")
    
    def list_stores(self) -> List[str]:
        """列出所有向量库"""
        return list(self._stores.keys())
    
    def save_all(self, base_path: str):
        """保存所有向量库"""
        import os
        for name, store in self._stores.items():
            path = os.path.join(base_path, name)
            store.save(path)
    
    def load_faiss(self, name: str, path: str, embedding_model=None) -> bool:
        """加载 FAISS 向量库"""
        model = embedding_model or self._default_embedding_model
        store = FAISSVectorStore(embedding_model=model)
        
        if store.load(path):
            self._stores[name] = store
            return True
        return False
    
    def load_chroma(self, name: str, path: str, embedding_model=None) -> bool:
        """加载 ChromaDB 向量库"""
        model = embedding_model or self._default_embedding_model
        store = ChromaVectorStore(embedding_model=model, persist_path=path)
        
        if store.load(path):
            self._stores[name] = store
            return True
        return False


# 全局向量存储管理器实例
vector_manager = VectorStoreManager()


# 便捷函数
def get_vector_store(name: str) -> Optional[BaseVectorStore]:
    """获取指定名称的向量库"""
    return vector_manager.get(name)


def search_vectors(store_name: str, query: str, top_k: int = 5):
    """在指定向量库中搜索"""
    store = get_vector_store(store_name)
    if not store:
        raise ValueError(f"向量库 '{store_name}' 未找到")
    return store.search(query, top_k)
