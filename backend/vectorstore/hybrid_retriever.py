"""
混合检索器 - 结合向量检索和关键词检索
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import get_settings
from .chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器"""
    
    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store
        self.settings = get_settings()
        self.vector_config = self.settings.vector_search
        
        # TF-IDF索引
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True
        )
        
        # 文档缓存
        self._doc_cache = {}
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        search_type: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """混合搜索"""
        if search_type == "vector":
            return await self._vector_search(query, top_k, filters)
        elif search_type == "keyword":
            return await self._keyword_search(query, top_k, filters)
        else:
            return await self._hybrid_search(query, top_k, filters)
    
    async def _vector_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        return await self.vector_store.search(
            query=query,
            top_k=top_k,
            filters=filters
        )
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """关键词检索（TF-IDF）"""
        # 预处理查询
        query_tokens = self._preprocess_text(query)
        
        # 获取所有文档进行检索
        all_docs = await self._get_all_documents(filters)
        
        if not all_docs:
            return []
        
        # 提取文档文本
        doc_texts = [doc["content"] for doc in all_docs]
        doc_ids = [doc["id"] for doc in all_docs]
        
        # 构建TF-IDF矩阵
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(doc_texts)
            query_vector = self.tfidf_vectorizer.transform([query_tokens])
        except Exception as e:
            logger.error(f"TF-IDF computation failed: {e}")
            return []
        
        # 计算相似度
        similarities = cosine_similarity(query_vector, tfidf_matrix)[0]
        
        # 排序获取top_k
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                doc = all_docs[idx]
                results.append({
                    "id": doc_ids[idx],
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {}),
                    "score": float(similarities[idx]),
                    "search_type": "keyword"
                })
        
        return results
    
    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """混合检索"""
        # 并行执行向量检索和关键词检索
        vector_results, keyword_results = await Promise.all([
            self._vector_search(query, top_k * 2, filters),
            self._keyword_search(query, top_k * 2, filters)
        ])
        
        # 合并结果
        merged = self._merge_results(vector_results, keyword_results)
        
        # 重排序
        reranked = self._rerank(query, merged)
        
        return reranked[:top_k]
    
    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并检索结果"""
        # 使用字典去重，保留最高分
        merged_map = {}
        
        for result in vector_results:
            doc_id = result["id"]
            if doc_id not in merged_map:
                merged_map[doc_id] = {
                    **result,
                    "vector_score": result.get("score", 0),
                    "keyword_score": 0,
                    "final_score": result.get("score", 0)
                }
        
        for result in keyword_results:
            doc_id = result["id"]
            if doc_id in merged_map:
                merged_map[doc_id]["keyword_score"] = result.get("score", 0)
                # 融合分数
                merged_map[doc_id]["final_score"] = (
                    0.6 * merged_map[doc_id]["vector_score"] +
                    0.4 * merged_map[doc_id]["keyword_score"]
                )
            else:
                merged_map[doc_id] = {
                    **result,
                    "vector_score": 0,
                    "keyword_score": result.get("score", 0),
                    "final_score": result.get("score", 0)
                }
        
        # 按融合分数排序
        results = list(merged_map.values())
        results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return results
    
    def _rerank(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """重排序"""
if not results:
            return []
        
        # 计算查询特征
        query_features = self._extract_query_features(query)
        
        for result in results:
            content = result["content"]
            metadata = result.get("metadata", {})
            
            # 基础分数
            base_score = result.get("final_score", 0)
            
            # 新鲜度权重
            freshness_score = self._calculate_freshness(metadata)
            
            # 位置权重（代码定义位置优先）
            position_score = self._calculate_position(metadata)
            
            # 类型权重
            type_score = self._calculate_type_score(metadata)
            
            # 综合分数
            final_score = (
                0.4 * base_score +
                0.2 * freshness_score +
                0.2 * position_score +
                0.2 * type_score
            )
            
            result["rerank_score"] = final_score
        
        # 按重排序分数排序
        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        return results
    
    def _extract_query_features(self, query: str) -> Dict[str, Any]:
        """提取查询特征"""
        features = {
            "length": len(query),
            "has_code_markers": bool(re.search(r'[`\'"]', query)),
            "has_question": "?" in query,
            "has_verbs": bool(re.search(r'\b(write|create|fix|refactor|explain)\b', query.lower())),
            "word_count": len(query.split())
        }
        return features
    
    def _calculate_freshness(self, metadata: Dict) -> float:
        """计算新鲜度分数"""
        try:
            created_at = metadata.get("created_at", "")
            if created_at:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at)
                days_old = (datetime.now() - dt).days
                # 30天内的文档获得满分，之后递减
                freshness = max(0, 1 - days_old / 30)
                return freshness
        except Exception:
            pass
        return 0.5
    
    def _calculate_position(self, metadata: Dict) -> float:
        """计算位置分数"""
        # 类定义和函数定义优先
        entity_type = metadata.get("entity_type", "")
        if entity_type in ["class", "function", "method"]:
            return 1.0
        elif entity_type in ["member", "variable"]:
            return 0.6
        else:
            return 0.8
    
    def _calculate_type_score(self, metadata: Dict) -> float:
        """计算类型分数"""
        source_type = metadata.get("source_type", "code")
        language = metadata.get("language", "cpp")
        
        # C++代码优先
        if source_type == "code" and language == "cpp":
            return 1.0
        elif source_type == "documentation":
            return 0.7
        else:
            return 0.8
    
    async def _get_all_documents(
        self,
        filters: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """获取所有文档"""
        # 简化实现：实际应该使用分页获取
        # 这里假设文档数量在可控范围内
        try:
            stats = await self.vector_store.get_stats()
            count = stats.get("document_count", 0)
            
            if count == 0:
                return []
            
            # 批量获取
            batch_size = 1000
            all_docs = []
            
            for i in range(0, count, batch_size):
                # 获取一批文档
                # 注意：ChromaDB API可能需要调整
                pass
            
            return all_docs[:5000]  # 限制数量
            
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 转小写
        text = text.lower()
        
        # 移除特殊字符，保留字母数字和空格
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def index_code_entities(
        self,
        entities: List[Dict[str, Any]]
    ) -> None:
        """索引代码实体"""
        documents = []
        
        for entity in entities:
            # 构建文档内容
            doc_content = self._entity_to_document(entity)
            
            documents.append({
                "content": doc_content["text"],
                "source": entity.get("file_path", ""),
                "source_type": "code",
                "language": entity.get("language", "cpp"),
                "entity_type": entity.get("entity_type", ""),
                "entity_name": entity.get("name", ""),
                "file_path": entity.get("file_path", ""),
                "line_start": entity.get("line_start", 0),
                "line_end": entity.get("line_end", 0)
            })
        
        # 添加到向量库
        if documents:
            await self.vector_store.add_documents(documents)
    
    def _entity_to_document(self, entity: Dict) -> Dict[str, str]:
        """将代码实体转换为文档"""
        parts = []
        
        # 实体名称
        name = entity.get("name", "")
        entity_type = entity.get("entity_type", "")
        parts.append(f"Entity: {name} ({entity_type})")
        
        # 签名
        signature = entity.get("signature", "")
        if signature:
            parts.append(f"Signature: {signature}")
        
        # 返回类型
        return_type = entity.get("return_type", "")
        if return_type:
            parts.append(f"Returns: {return_type}")
        
        # 参数
        parameters = entity.get("parameters", [])
        if parameters:
            parts.append(f"Parameters: {', '.join(parameters)}")
        
        # 文档注释
        doc_comment = entity.get("doc_comment", "")
        if doc_comment:
            parts.append(f"Documentation: {doc_comment}")
        
        # 代码内容
        content = entity.get("content", "")
        if content:
            parts.append(f"Code: {content}")
        
        return {
            "text": "\n".join(parts)
        }


class AsyncHelper:
    """异步辅助类"""
    
    @staticmethod
    async def all(tasks):
        """并行执行多个异步任务"""
        import asyncio
        return await asyncio.gather(*tasks)
