"""
C++ AI Assistant - C++语法解析器 (简化版)
"""
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime

import tree_sitter
from tree_sitter import Node, Parser, Tree
from tree_sitter_languages import get_language

# 新增导入（用于统一 RAG chunk）
from .code_entities import CodeEntity, EntityType, Location

logger = logging.getLogger(__name__)


class CppParser:
    """C++代码解析器"""
    
    def __init__(self):
        self.parser: Optional[Parser] = None
        self.language = None
        self._initialize_parser()
    
    def _initialize_parser(self) -> None:
        """初始化解析器"""
        try:
            self.language = get_language("cpp")
            self.parser = Parser()
            self.parser.set_language(self.language)
            logger.info("C++ parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize C++ parser: {e}")
            raise
    
    def parse_file(self, file_path: str) -> Tuple[Tree, str]:
        """解析C++文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        content = path.read_text(encoding="utf-8")
        tree = self.parser.parse(bytes(content, "utf-8"))
        return tree, content
    
    def parse_content(self, content: str) -> Tree:
        """解析C++代码内容"""
        return self.parser.parse(bytes(content, "utf-8"))
    
    def generate_entity_id(self, file_path: str, entity_name: str, line: int) -> str:
        """生成唯一实体ID"""
        unique_str = f"{file_path}:{entity_name}:{line}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]


class CppCodeAnalyzer:
    """C++代码分析器"""
    
    def __init__(self, parser: CppParser):
        self.parser = parser
        self.entity_counter = 0
    
    def analyze_file(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """原方法保持不变（兼容旧代码）"""
        if content is None:
            tree, content = self.parser.parse_file(file_path)
        else:
            tree = self.parser.parse_content(content)
        
        return {
            "file_path": file_path,
            "entities": [],
            "issues": [],
            "call_graph": {},
            "inheritance_graph": {},
            "content": content,
            "tree": tree
        }

    # ====================== 新增 RAG 专用方法 ======================
    def get_rag_chunks(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        【核心新增】专为 Chroma RAG 设计的语义 chunk 方法
        返回格式完全兼容 chroma_store.py 的 add_documents
        """
        if content is None:
            tree, content = self.parser.parse_file(file_path)
        else:
            tree = self.parser.parse_content(content)

        chunks: List[Dict[str, Any]] = []

        # Tree-sitter 查询提取函数、类、结构体、命名空间
        query = self.parser.language.query("""
            (function_definition) @func
            (class_specifier) @class
            (struct_specifier) @struct
            (namespace_definition) @namespace
        """)
        
        captures = query.captures(tree.root_node)
        
        for node, capture_name in captures:
            chunk_text = node.text.decode("utf-8").strip()
            if not chunk_text or len(chunk_text) < 10:
                continue

            start_line = node.start_point[0] + 1
            end_line   = node.end_point[0] + 1

            entity = CodeEntity(
                entity_id=self.parser.generate_entity_id(file_path, capture_name, start_line),
                entity_type=EntityType.FUNCTION if capture_name == "func" else
                           EntityType.CLASS if capture_name == "class" else
                           EntityType.STRUCT if capture_name == "struct" else EntityType.NAMESPACE,
                name=chunk_text.split(maxsplit=2)[1] if len(chunk_text.split()) > 1 else "anonymous",
                location=Location(file_path=file_path, start_line=start_line, end_line=end_line),
                file_path=file_path,
                content=chunk_text,
                signature=chunk_text[:300],
                doc_comment="",
                language="cpp"
            )
            
            chunks.append({
                "content": chunk_text,
                "metadata": entity.to_dict()
            })

        # 兜底整文件 chunk
        if not chunks:
            chunks.append({
                "content": content[:8000],
                "metadata": {
                    "file_path": file_path,
                    "entity_type": "file",
                    "language": "cpp",
                    "name": Path(file_path).name
                }
            })
        
        return chunks
    
class CppRefactoringAnalyzer:
    """C++重构分析器"""
    
    def __init__(self, analyzer: CppCodeAnalyzer):
        self.analyzer = analyzer
    
    def analyze_refactoring_opportunities(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析重构机会"""
        analysis = self.analyzer.analyze_file(file_path, content)
        return {
            "opportunities": [],
            "analysis": analysis
        }