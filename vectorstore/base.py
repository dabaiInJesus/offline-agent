"""
向量数据库基类 - 定义通用向量存储接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Document:
    """文档数据类"""
    page_content: str
    metadata: Dict[str, Any] = None
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """搜索结果数据类"""
    document: Document
    score: float


class BaseVectorStore(ABC):
    """向量数据库基类"""
    
    def __init__(self, embedding_model=None, collection_name: str = "default"):
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self._store = None
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量库"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[SearchResult]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """删除指定文档"""
        pass
    
    @abstractmethod
    def update(self, id: str, document: Document) -> bool:
        """更新文档"""
        pass
    
    @abstractmethod
    def get(self, id: str) -> Optional[Document]:
        """获取指定文档"""
        pass
    
    @abstractmethod
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取文档数量"""
        pass
    
    @abstractmethod
    def save(self, path: str) -> bool:
        """保存向量库到本地"""
        pass
    
    @abstractmethod
    def load(self, path: str) -> bool:
        """从本地加载向量库"""
        pass
    
    def similarity_search_with_score(
        self, 
        query: str, 
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """带分数阈值的相似度搜索"""
        results = self.search(query, top_k)
        
        if score_threshold is not None:
            results = [r for r in results if r.score >= score_threshold]
        
        return results
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> List[str]:
        """便捷方法：添加文本列表"""
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        documents = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(texts, metadatas)
        ]
        return self.add_documents(documents)
    
    def search_by_vector(self, vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """通过向量搜索"""
        raise NotImplementedError("子类需要实现此方法")
