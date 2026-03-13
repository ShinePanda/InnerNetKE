"""
向量存储服务 - ChromaDB集成
兼容 chromadb 1.5.x 版本
"""
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib
import uuid

import chromadb
from chromadb.utils import embedding_functions
import numpy as np

from ..config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储基类"""
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: Optional[np.ndarray] = None
    ) -> List[str]:
        """添加文档"""
        raise NotImplementedError
    
    async def search(
        self,
        query: str,
        query_embedding: Optional[np.ndarray] = None,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """搜索"""
        raise NotImplementedError
    
    async def delete(self, ids: List[str]) -> None:
        """删除"""
        raise NotImplementedError
    
    async def update(self, id: str, document: Dict[str, Any]) -> None:
        """更新"""
        raise NotImplementedError
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    """ChromaDB向量存储实现 - 兼容 1.5.x 版本"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_config = self.settings.knowledge_base.vector_db
        
        # 初始化ChromaDB客户端 (1.5.x API)
        persist_dir = Path(self.vector_config.persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(persist_dir)
        )
        
        # 获取或创建集合 (1.5.x API - metadata简化)
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.vector_config.collection_name,
                metadata={
                    "hnsw:space": self.vector_config.hnsw_space
                }
            )
        except Exception as e:
            logger.warning(f"Failed to get_or_create_collection with : {e}")
            # 如果metadata格式不支持，使用简化版本
            self.collection = self.client.get_or_create_collection(
                name=self.vector_config.collection_name
            )
        
        # 初始化嵌入函数
        self._init_embedding_function()
    
    def _init_embedding_function(self) -> None:
        model_name = self.vector_config.embedding_model  # 可能是 "all-MiniLM-L6-v2"
        local_path = self.vector_config.local_embedding_path
        if local_path and Path(local_path).exists():
            model_name = local_path
        
        try:
            # 尝试使用sentence-transformers
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_name,
                device="cpu"
            )
            logger.info(f"Using SentenceTransformer with model: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}")
            # 使用默认嵌入函数
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
    
    def _generate_id(self, content: str, source: str) -> str:
        """生成唯一ID"""
        unique_str = f"{source}:{hashlib.md5(content.encode()).hexdigest()}"
        return f"doc_{uuid.uuid4().hex[:8]}"
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: Optional[np.ndarray] = None
    ) -> List[str]:
        """添加文档到向量库"""
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            doc_id = self._generate_id(doc["content"], doc.get("source", ""))
            ids.append(doc_id)
            texts.append(doc["content"])
            
            metadata = {
                "source": doc.get("source", ""),
                "source_type": doc.get("source_type", "code"),
                # 新增：支持 path_mapper 关键字段
                "dev_path": doc.get("dev_path", doc.get("file_path", "")),
                "archive_path": doc.get("archive_path", ""),
                "repo": doc.get("repo", ""),
                "language": doc.get("language", "cpp"),
                "entity_type": doc.get("entity_type", ""),
                "entity_name": doc.get("entity_name", ""),
                "line_start": doc.get("line_start", doc.get("location", {}).get("start_line", 0)),
                "line_end": doc.get("line_end", doc.get("location", {}).get("end_line", 0)),
                "file_path": doc.get("file_path", ""),
                "line_start": doc.get("line_start", 0),
                "line_end": doc.get("line_end", 0),
                "chunk_index": doc.get("chunk_index", 0),
                "created_at": datetime.now().isoformat()
            }
            metadatas.append(metadata)
        
        # 如果没有提供嵌入，使用自动嵌入
        if embeddings is None:
            try:
                embeddings = self.embedding_function(texts)
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                embeddings = None
        
        # 添加到ChromaDB
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Added {len(ids)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise
        
        return ids
    
    async def search(
        self,
        query: str,
        query_embedding: Optional[np.ndarray] = None,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """搜索向量库"""
        # 生成查询嵌入
        if query_embedding is None:
            try:
                query_embedding = self.embedding_function([query])[0]
            except Exception as e:
                logger.error(f"Query embedding failed: {e}")
                query_embedding = None
        
        # 构建where过滤条件
        where_filter = None
        if filters:
            where_filter = {}
            for key, value in filters.items():
                if isinstance(value, list):
                    where_filter[key] = {"$in": value}
                else:
                    where_filter[key] = value
        
        # 执行搜索
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding] if query_embedding is not None else None,
                query_texts=[query] if query_embedding is None else None,
                n_results=top_k,
                where=where_filter,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None,
                    "score": 1 - results["distances"][0][i] if "distances" in results else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    async def delete(self, ids: List[str]) -> None:
        """删除文档"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    async def update(
        self,
        id: str,
        document: Dict[str, Any]
    ) -> None:
        """更新文档"""
        try:
            self.collection.update(
                ids=[id],
                documents=[document["content"]],
                metadatas=[{
                    "source": document.get("source", ""),
                    "source_type": document.get("source_type", "code"),
                    "updated_at": datetime.now().isoformat()
                }]
            )
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.vector_config.collection_name,
                "embedding_model": self.vector_config.embedding_model
            }
        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return {"error": str(e)}
    
    async def reset(self) -> None:
        """重置集合"""
        try:
            self.client.delete_collection(self.vector_config.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.vector_config.collection_name
            )
            logger.info("Collection reset successful")
        except Exception as e:
            logger.error(f"Reset failed: {e}")
            raise
    
    async def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        """获取指定来源的所有文档"""
        try:
            results = self.collection.get(
                where={"source": source},
                include=["documents", "metadatas"]
            )
            
            return [
                {
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                for i in range(len(results["ids"]))
            ]
        except Exception as e:
            logger.error(f"Get by source failed: {e}")
            return []
    
    async def delete_by_source(self, source: str) -> int:
        """删除指定来源的所有文档"""
        try:
            results = self.collection.get(
                where={"source": source},
                ids_only=True
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} documents from {source}")
                return len(results["ids"])
            
            return 0
        except Exception as e:
            logger.error(f"Delete by source failed: {e}")
            raise
