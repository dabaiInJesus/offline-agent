"""
FAISS 向量数据库实现
"""
import os
import pickle
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger

from .base import BaseVectorStore, Document, SearchResult


class FAISSVectorStore(BaseVectorStore):
    """基于 FAISS 的向量存储"""
    
    def __init__(self, embedding_model=None, collection_name: str = "default", dimension: int = 384):
        super().__init__(embedding_model, collection_name)
        self.dimension = dimension
        self._documents: Dict[str, Document] = {}
        self._index = None
        self._id_map: Dict[int, str] = {}  # faiss id -> doc id
        self._next_id = 0
        
        # 延迟导入 faiss
        try:
            import faiss
            self._faiss = faiss
        except ImportError:
            raise ImportError("请安装 faiss: pip install faiss-cpu")
    
    def _ensure_index(self):
        """确保索引已创建"""
        if self._index is None:
            # 使用内积度量（余弦相似度需要先归一化）
            self._index = self._faiss.IndexFlatIP(self.dimension)
            logger.info(f"创建 FAISS 索引，维度: {self.dimension}")
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """获取文本的嵌入向量"""
        if self.embedding_model is None:
            raise ValueError("未设置嵌入模型")
        
        embeddings = self.embedding_model.embed_documents(texts)
        return np.array(embeddings, dtype=np.float32)
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量库"""
        self._ensure_index()
        
        if not documents:
            return []
        
        # 生成文档 ID
        doc_ids = []
        texts = []
        for doc in documents:
            if doc.id is None:
                doc.id = str(uuid.uuid4())
            doc_ids.append(doc.id)
            texts.append(doc.page_content)
            self._documents[doc.id] = doc
        
        # 获取嵌入向量
        embeddings = self._get_embeddings(texts)
        
        # 归一化向量（用于余弦相似度）
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 避免除零
        embeddings = embeddings / norms
        
        # 添加到 FAISS 索引
        start_id = self._next_id
        self._index.add(embeddings)
        
        # 维护 ID 映射
        for i, doc_id in enumerate(doc_ids):
            faiss_id = start_id + i
            self._id_map[faiss_id] = doc_id
        
        self._next_id += len(documents)
        
        logger.info(f"已添加 {len(documents)} 个文档到 FAISS")
        return doc_ids
    
    def search(self, query: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[SearchResult]:
        """搜索相似文档"""
        if self._index is None or self._index.ntotal == 0:
            return []
        
        # 获取查询向量
        query_embedding = self.embedding_model.embed_query(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # 归一化
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        # 搜索
        scores, indices = self._index.search(query_vector, min(top_k * 2, self._index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS 返回 -1 表示没有更多结果
                break
            
            doc_id = self._id_map.get(int(idx))
            if doc_id and doc_id in self._documents:
                doc = self._documents[doc_id]
                
                # 应用过滤器
                if filter_dict:
                    if not all(doc.metadata.get(k) == v for k, v in filter_dict.items()):
                        continue
                
                results.append(SearchResult(document=doc, score=float(score)))
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def delete(self, ids: List[str]) -> bool:
        """删除指定文档（FAISS 不支持直接删除，需要重建索引）"""
        # 标记删除
        for doc_id in ids:
            if doc_id in self._documents:
                del self._documents[doc_id]
        
        # 重建索引
        self._rebuild_index()
        logger.info(f"已删除 {len(ids)} 个文档")
        return True
    
    def _rebuild_index(self):
        """重建 FAISS 索引"""
        if not self._documents:
            self._index = None
            self._id_map = {}
            self._next_id = 0
            return
        
        # 创建新索引
        self._index = self._faiss.IndexFlatIP(self.dimension)
        self._id_map = {}
        self._next_id = 0
        
        # 重新添加所有文档
        docs = list(self._documents.values())
        self.add_documents(docs)
    
    def update(self, id: str, document: Document) -> bool:
        """更新文档"""
        if id not in self._documents:
            return False
        
        document.id = id
        self._documents[id] = document
        self._rebuild_index()
        return True
    
    def get(self, id: str) -> Optional[Document]:
        """获取指定文档"""
        return self._documents.get(id)
    
    def list_collections(self) -> List[str]:
        """FAISS 不支持多集合，返回当前集合"""
        return [self.collection_name]
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除集合（清空当前索引）"""
        if collection_name == self.collection_name:
            self._index = None
            self._documents = {}
            self._id_map = {}
            self._next_id = 0
            return True
        return False
    
    def count(self) -> int:
        """获取文档数量"""
        return len(self._documents)
    
    def save(self, path: str) -> bool:
        """保存向量库到本地"""
        try:
            os.makedirs(path, exist_ok=True)
            
            # 保存 FAISS 索引
            if self._index is not None:
                index_path = os.path.join(path, "index.faiss")
                self._faiss.write_index(self._index, index_path)
            
            # 保存文档和元数据
            metadata = {
                "collection_name": self.collection_name,
                "dimension": self.dimension,
                "documents": self._documents,
                "id_map": self._id_map,
                "next_id": self._next_id,
            }
            metadata_path = os.path.join(path, "metadata.pkl")
            with open(metadata_path, "wb") as f:
                pickle.dump(metadata, f)
            
            logger.info(f"FAISS 向量库已保存到: {path}")
            return True
        except Exception as e:
            logger.error(f"保存 FAISS 向量库失败: {e}")
            return False
    
    def load(self, path: str) -> bool:
        """从本地加载向量库"""
        try:
            # 加载 FAISS 索引
            index_path = os.path.join(path, "index.faiss")
            if os.path.exists(index_path):
                self._index = self._faiss.read_index(index_path)
            
            # 加载元数据
            metadata_path = os.path.join(path, "metadata.pkl")
            if os.path.exists(metadata_path):
                with open(metadata_path, "rb") as f:
                    metadata = pickle.load(f)
                
                self.collection_name = metadata["collection_name"]
                self.dimension = metadata["dimension"]
                self._documents = metadata["documents"]
                self._id_map = metadata["id_map"]
                self._next_id = metadata["next_id"]
            
            logger.info(f"FAISS 向量库已从 {path} 加载，包含 {len(self._documents)} 个文档")
            return True
        except Exception as e:
            logger.error(f"加载 FAISS 向量库失败: {e}")
            return False
    
    def search_by_vector(self, vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """通过向量搜索"""
        if self._index is None or self._index.ntotal == 0:
            return []
        
        query_vector = np.array([vector], dtype=np.float32)
        
        # 归一化
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        scores, indices = self._index.search(query_vector, min(top_k, self._index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                break
            
            doc_id = self._id_map.get(int(idx))
            if doc_id and doc_id in self._documents:
                results.append(SearchResult(
                    document=self._documents[doc_id],
                    score=float(score)
                ))
        
        return results
