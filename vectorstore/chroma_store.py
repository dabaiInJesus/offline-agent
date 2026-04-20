"""
ChromaDB 向量数据库实现
"""
import os
from typing import List, Dict, Any, Optional
from loguru import logger

from .base import BaseVectorStore, Document, SearchResult


class ChromaVectorStore(BaseVectorStore):
    """基于 ChromaDB 的向量存储"""
    
    def __init__(self, embedding_model=None, collection_name: str = "default", persist_path: str = None):
        super().__init__(embedding_model, collection_name)
        self.persist_path = persist_path or "./chroma_db"
        self._client = None
        self._collection = None
        
        # 延迟导入 chromadb
        try:
            import chromadb
            from chromadb.config import Settings
            self._chromadb = chromadb
            self._settings = Settings
        except ImportError:
            raise ImportError("请安装 chromadb: pip install chromadb")
    
    def _get_client(self):
        """获取或创建 ChromaDB 客户端"""
        if self._client is None:
            self._client = self._chromadb.PersistentClient(
                path=self.persist_path,
                settings=self._settings(
                    anonymized_telemetry=False
                )
            )
        return self._client
    
    def _get_collection(self):
        """获取或创建集合"""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量库"""
        if not documents:
            return []
        
        collection = self._get_collection()
        
        # 准备数据
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            if doc.id is None:
                import uuid
                doc.id = str(uuid.uuid4())
            
            ids.append(doc.id)
            texts.append(doc.page_content)
            metadatas.append(doc.metadata or {})
        
        # 获取嵌入向量
        if self.embedding_model:
            embeddings = self.embedding_model.embed_documents(texts)
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
        else:
            # 让 ChromaDB 自动处理嵌入
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
        
        logger.info(f"已添加 {len(documents)} 个文档到 ChromaDB 集合 '{self.collection_name}'")
        return ids
    
    def search(self, query: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[SearchResult]:
        """搜索相似文档"""
        collection = self._get_collection()
        
        # 准备查询参数
        query_params = {
            "query_texts": [query],
            "n_results": top_k,
        }
        
        # 添加过滤器
        if filter_dict:
            query_params["where"] = filter_dict
        
        # 如果有嵌入模型，使用向量搜索
        if self.embedding_model:
            embedding = self.embedding_model.embed_query(query)
            query_params["query_embeddings"] = [embedding]
            del query_params["query_texts"]
        
        results = collection.query(**query_params)
        
        # 解析结果
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                document = Document(
                    page_content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    id=doc_id
                )
                # ChromaDB 返回的是距离，转换为相似度分数
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - distance  # 转换为相似度
                
                search_results.append(SearchResult(document=document, score=score))
        
        return search_results
    
    def delete(self, ids: List[str]) -> bool:
        """删除指定文档"""
        try:
            collection = self._get_collection()
            collection.delete(ids=ids)
            logger.info(f"已删除 {len(ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def update(self, id: str, document: Document) -> bool:
        """更新文档"""
        try:
            # 先删除旧文档
            self.delete([id])
            
            # 添加新文档
            document.id = id
            self.add_documents([document])
            return True
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    def get(self, id: str) -> Optional[Document]:
        """获取指定文档"""
        try:
            collection = self._get_collection()
            result = collection.get(ids=[id])
            
            if result["ids"] and result["ids"][0]:
                return Document(
                    page_content=result["documents"][0],
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                    id=id
                )
            return None
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        client = self._get_client()
        collections = client.list_collections()
        return [c.name for c in collections]
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            client = self._get_client()
            client.delete_collection(name=collection_name)
            
            if collection_name == self.collection_name:
                self._collection = None
            
            logger.info(f"已删除集合 '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    def count(self) -> int:
        """获取文档数量"""
        collection = self._get_collection()
        return collection.count()
    
    def save(self, path: str) -> bool:
        """ChromaDB 自动持久化，此方法仅用于兼容性"""
        # ChromaDB 的 PersistentClient 已经自动持久化
        logger.info(f"ChromaDB 数据已自动持久化到: {self.persist_path}")
        return True
    
    def load(self, path: str) -> bool:
        """加载 ChromaDB 数据"""
        try:
            self.persist_path = path
            self._client = None
            self._collection = None
            
            # 触发客户端初始化
            collection = self._get_collection()
            count = collection.count()
            
            logger.info(f"ChromaDB 已从 {path} 加载，集合 '{self.collection_name}' 包含 {count} 个文档")
            return True
        except Exception as e:
            logger.error(f"加载 ChromaDB 失败: {e}")
            return False
    
    def search_by_vector(self, vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """通过向量搜索"""
        collection = self._get_collection()
        
        results = collection.query(
            query_embeddings=[vector],
            n_results=top_k
        )
        
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                document = Document(
                    page_content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    id=doc_id
                )
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - distance
                
                search_results.append(SearchResult(document=document, score=score))
        
        return search_results
    
    def peek(self, limit: int = 10) -> List[Document]:
        """查看集合中的文档样本"""
        collection = self._get_collection()
        results = collection.peek(limit=limit)
        
        documents = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                documents.append(Document(
                    page_content=results["documents"][i],
                    metadata=results["metadatas"][i] if results["metadatas"] else {},
                    id=doc_id
                ))
        
        return documents
