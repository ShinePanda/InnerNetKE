"""
Java代码解析器
支持Java语法分析和实体提取（包括Java Spring Boot代码）
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import tree_sitter
from tree_sitter import Node, Parser, Tree
from tree_sitter_languages import get_language

from .code_entities import (
    EntityType, Location, CodeEntity, CodeIssue, IssueSeverity,
    IssueCategory, CallGraph, InheritanceGraph, AccessSpecifier
)
from ..utils.tree_sitter_utils import (
    node_to_string, get_node_text, find_child_by_type,
    find_children_by_type, traverse_tree, get_node_range
)

logger = logging.getLogger(__name__)


class JavaParser:
    """Java代码解析器"""
    
    def __init__(self):
        self.parser: Optional[Parser] = None
        self.language = None
        self._initialize_parser()
    
    def _initialize_parser(self) -> None:
        """初始化解析器"""
        try:
            self.language = get_language("java")
            self.parser = Parser()
            self.parser.set_language(self.language)
            logger.info("Java parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Java parser: {e}")
            raise
    
    def parse_file(self, file_path: str) -> Tuple[Tree, str]:
        """解析Java文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        content = path.read_text(encoding="utf-8")
        tree = self.parser.parse(bytes(content, "utf-8"))
        return tree, content
    
    def parse_content(self, content: str) -> Tree:
        """解析Java代码内容"""
        return self.parser.parse(bytes(content, "utf-8"))
    
    def generate_entity_id(self, file_path: str, entity_name: str, line: int) -> str:
        """生成唯一实体ID"""
        unique_str = f"{file_path}:{entity_name}:{line}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]


class JavaCodeAnalyzer:
    """Java代码分析器"""
    
    def __init__(self, parser: JavaParser):
        self.parser = parser
        self.entity_counter = 0
    
    def analyze_file(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析Java文件"""
        if content is None:
            tree, content = self.parser.parse_file(file_path)
        else:
            tree = self.parser.parse_content(content)
        
        entities = []
        issues = []
        call_graph = CallGraph()
        inheritance_graph = InheritanceGraph()
        
        # 解析所有实体
        self._extract_entities(tree, content, file_path, entities)
        
        # 构建调用图
        self._build_call_graph(tree, content, entities, call_graph)
        
        # 检测代码问题
        self._detect_issues(tree, content, file_path, issues)
        
        return {
            "file_path": file_path,
            "entities": entities,
            "issues": issues,
            "call_graph": call_graph,
            "inheritance_graph": inheritance_graph,
            "content": content,
            "tree": tree
        }
    
    def _extract_entities(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        entities: List[CodeEntity]
    ) -> None:
        """提取代码实体"""
        def process_node(node: Node, depth: int = 0):
            if depth > 50:  # 防止无限递归
                return
            entity = self._node_to_entity(node, content, file_path)
            if entity:
                entities.append(entity)
            for child in node.children:
                process_node(child, depth + 1)
        
        process_node(tree.root_node)
    
    def _node_to_entity(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """将Tree-sitter节点转换为代码实体"""
        node_type = node.type
        
        if node_type == "class_declaration":
            return self._parse_class(node, content, file_path)
        elif node_type == "interface_declaration":
            return self._parse_interface(node, content, file_path)
        elif node_type == "method_declaration":
            return self._parse_method(node, content, file_path)
        elif node_type == "field_declaration":
            return self._parse_field(node, content, file_path)
        elif node_type == "enum_declaration":
            return self._parse_enum(node, content, file_path)
        
        return None
    
    def _parse_class(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析类定义"""
        name_node = find_child_by_type(node, "identifier")
        if not name_node:
            return None
        
        name = get_node_text(name_node, content)
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # 查找父类和接口
        superclasses = []
        implemented_interfaces = []
        
        super_class_node = find_child_by_type(node, "superclass")
        if super_class_node:
            superclasses.append(get_node_text(super_class_node, content))
        
        super_interfaces_node = find_child_by_type(node, "super_interfaces")
        if super_interfaces_node:
            interfaces = find_children_by_type(super_interfaces_node, "type_identifier")
            implemented_interfaces = [get_node_text(i, content) for i in interfaces]
        
        # 计算圈复杂度
        complexity = self._calculate_complexity(node, content)
        
        # 检测Spring注解
        annotations = self._extract_annotations(node, content)
        is_spring_controller = any("@Controller" in ann or "@RestController" in ann for ann in annotations)
        is_spring_service = any("@Service" in ann for ann in annotations)
        is_spring_component = any("@Component" in ann for ann in annotations)
        
        metadata = {
            "superclasses": superclasses,
            "implemented_interfaces": implemented_interfaces,
            "annotations": annotations,
            "is_spring_controller": is_spring_controller,
            "is_spring_service": is_spring_service,
            "is_spring_component": is_spring_component
        }
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.CLASS,
            name=name,
            location=Location(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_column=node.start_point[1],
                end_column=node.end_point[1]
            ),
            file_path=file_path,
            content=get_node_text(node, content),
            signature=get_node_text(node, content),
            cyclomatic_complexity=complexity,
            line_count=end_line - start_line,
            metadata=metadata
        )
    
    def _parse_interface(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析接口定义"""
        name_node = find_child_by_type(node, "identifier")
        if not name_node:
            return None
        
        name = get_node_text(name_node, content)
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.CLASS,
            name=name,
            location=Location(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_column=node.start_point[1],
                end_column=node.end_point[1]
            ),
            file_path=file_path,
            content=get_node_text(node, content),
            signature=f"interface {name}",
            cyclomatic_complexity=1,
            line_count=end_line - start_line
        )
    
    def _parse_method(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析方法定义"""
        name_node = find_child_by_type(node, "identifier")
        if not name_node:
            return None
        
        name = get_node_text(name_node, content)
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # 解析返回类型
        type_node = node.child_by_field_name("type")
        return_type = get_node_text(type_node, content) if type_node else "void"
        
        # 解析参数
        params_node = find_child_by_type(node, "formal_parameters")
        parameters = []
        if params_node:
            param_decls = find_children_by_type(params_node, "formal_parameter")
            for param in param_decls:
                param_type_node = param.child_by_field_name("type")
                param_name_node = find_child_by_type(param, "identifier")
                if param_type_node and param_name_node:
                    param_type = get_node_text(param_type_node, content)
                    param_name = get_node_text(param_name_node, content)
                    parameters.append(f"{param_type} {param_name}")
        
        # 构建方法签名
        param_str = ", ".join(parameters)
        signature = f"{return_type} {name}({param_str})"
        
        # 确定访问修饰符
        access = self._determine_access(node)
        
        # 确定其他修饰符
        is_static = self._has_modifier(node, "static")
        
        # 检测Spring注解
        annotations = self._extract_annotations(node, content)
        is_rest_mapping = any(ann.startswith("@") and "Mapping" in ann for ann in annotations)
        
        # 计算圈复杂度
        body = find_child_by_type(node, "block")
        complexity = self._calculate_complexity(body, content) if body else 1
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.METHOD,
            name=name,
            location=Location(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_column=node.start_point[1],
                end_column=node.end_point[1]
            ),
            file_path=file_path,
            content=get_node_text(node, content),
            signature=signature,
            return_type=return_type,
            parameters=parameters,
            access_specifier=access,
            is_static=is_static,
            cyclomatic_complexity=complexity,
            line_count=end_line - start_line,
            metadata={
                "annotations": annotations,
                "is_rest_mapping": is_rest_mapping
            }
        )
    
    def _parse_field(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析字段声明"""
        declarators = find_children_by_type(node, "variable_declarator")
        if not declarators:
            return None
        
        type_node = node.child_by_field_name("type")
        field_type = get_node_text(type_node, content) if type_node else "Object"
        
        entities = []
        for declarator in declarators:
            name_node = find_child_by_type(declarator, "identifier")
            if not name_node:
                continue
            
            name = get_node_text(name_node, content)
            entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
            
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # 检测Spring注解
            annotations = self._extract_annotations(node, content)
            is_autowired = any("@Autowired" in ann for ann in annotations)
            
            entities.append(CodeEntity(
                entity_id=entity_id,
                entity_type=EntityType.MEMBER,
                name=name,
                location=Location(
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1]
                ),
                file_path=file_path,
                content=get_node_text(node, content),
                signature=f"{field_type} {name}",
                cyclomatic_complexity=1,
                line_count=1,
                metadata={
                    "annotations": annotations,
                    "is_autowired": is_autowired
                }
            ))
        
        return entities[0] if entities else None
    
    def _parse_enum(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析枚举定义"""
        name_node = find_child_by_type(node, "identifier")
        name = get_node_text(name_node, content) if name_node else "anonymous"
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.CLASS,
            name=name,
            location=Location(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_column=node.start_point[1],
                end_column=node.end_point[1]
            ),
            file_path=file_path,
            content=get_node_text(node, content),
            signature=f"enum {name}",
            line_count=end_line - start_line
        )
    
    def _determine_access(self, node: Node) -> AccessSpecifier:
        """确定访问修饰符"""
        modifiers = find_child_by_type(node, "modifiers")
        if modifiers:
            for child in modifiers.children:
                text = get_node_text(child, content="")
                if text in ["public", "protected", "private"]:
                    if text == "public":
                        return AccessSpecifier.PUBLIC
                    elif text == "protected":
                        return AccessSpecifier.PROTECTED
                    elif text == "private":
                        return AccessSpecifier.PRIVATE
        return AccessSpecifier.PUBLIC
    
    def _has_modifier(self, node: Node, modifier: str) -> bool:
        """检查是否有特定修饰符"""
        modifiers = find_child_by_type(node, "modifiers")
        if modifiers:
            for child in modifiers.children:
                if get_node_text(child, content="") == modifier:
                    return True
        return False
    
    def _extract_annotations(self, node: Node, content: str) -> List[str]:
        """提取注解"""
        annotations = []
        modifiers = find_child_by_type(node, "modifiers")
        if modifiers:
            for child in modifiers.children:
                if child.type == "marker_annotation" or child.type == "annotation":
                    annotations.append(get_node_text(child, content))
        return annotations
    
    def _calculate_complexity(self, node: Optional[Node], content: str) -> int:
        """计算圈复杂度"""
        if not node:
            return 1
        complexity = 1
        decision_types = {
            "if_statement", "else_clause", "conditional_expression",
            "for_statement", "enhanced_for_statement", "while_statement",
            "do_statement", "switch_expression", "catch_clause"
        }
        for child in traverse_tree(node):
            if child.type in decision_types:
                complexity += 1
        return complexity
    
    def _build_call_graph(
        self,
        tree: Tree,
        content: str,
        entities: List[CodeEntity],
        call_graph: CallGraph
    ) -> None:
        """构建调用图"""
        for entity in entities:
            call_graph.add_entity(entity)
        
        call_nodes = find_children_by_type(tree.root_node, "method_invocation")
        for call_node in call_nodes:
            name_node = find_child_by_type(call_node, "identifier")
            if not name_node:
                continue
            callee_name = get_node_text(name_node, content)
            caller = self._find_enclosing_method(call_node, entities)
            if caller:
                for entity in entities:
                    if entity.name == callee_name and entity.entity_type == EntityType.METHOD:
                        call_graph.add_call(caller.entity_id, entity.entity_id)
                        break
    
    def _find_enclosing_method(
        self,
        node: Node,
        entities: List[CodeEntity]
    ) -> Optional[CodeEntity]:
        """查找包含给定节点的方法"""
        for entity in entities:
            if entity.entity_type == EntityType.METHOD:
                entity_start = entity.location.start_line - 1
                entity_end = entity.location.end_line - 1
                node_start = node.start_point[0]
                if entity_start <= node_start <= entity_end:
                    return entity
        return None
    
    def _detect_issues(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        issues: List[CodeIssue]
    ) -> None:
        """检测代码问题"""
        self._detect_spring_issues(tree, content, file_path, issues)
        self.__detect_exception_issues(tree, content, file_path, issues)
        self._detect_design_issues(tree, content, file_path, issues)
    
    def _detect_spring_issues(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        issues: List[CodeIssue]
    ) -> None:
        """检测Spring框架相关问题"""
        method_nodes = find_children_by_type(tree.root_node, "method_declaration")
        for method_node in method_nodes:
            annotations = self._extract_annotations(method_node, content)
            has_transactional = any("@Transactional" in ann for ann in annotations)
            
            method_content = get_node_text(method_node, content)
            has_db_operation = any(
                keyword in method_content 
                for keyword in ["repository.insert", "repository.update", "repository.delete"]
            )
            
            if has_db_operation and not has_transactional:
                issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.CORRECTNESS,
                    message="Database operation without @Transactional annotation",
                    location=Location(
                        file_path=file_path,
                        start_line=method_node.start_point[0] + 1,
                        end_line=method_node.end_point[0] + 1
                    ),
                    suggestion="Consider adding @Transactional annotation",
                    rule_id="spring-missing-transactional"
                ))
    
    def _detect_exception_issues(self, tree, content, file_path, issues):
        """检测异常处理问题（空catch块）"""
        try_nodes = find_children_by_type(tree.root_node, "try_statement")
        for try_node in try_nodes:
            catch_clauses = find_children_by_type(try_node, "catch_clause")
            for catch_node in catch_clauses:
                block = find_child_by_type(catch_node, "block")
                if block and len(block.children) <= 2:
                    issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        severity=IssueSeverity.ERROR,
                        category=IssueCategory.CORRECTNESS,
                        message="Empty catch block",
                        location=Location(
                            file_path=file_path,
                            start_line=catch_node.start_point[0] + 1,
                            end_line=catch_node.end_point[0] + 1
                        ),
                        suggestion="Never leave catch blocks empty",
                        rule_id="java-empty-catch"
                    ))
    
    def _detect_design_issues(self, tree, content, file_path, issues):
        """检测设计问题（过长方法）"""
        method_nodes = find_children_by_type(tree.root_node, "method_declaration")
        for method_node in method_nodes:
            func_lines = method_node.end_point[0] - method_node.start_point[0]
            if func_lines > 50:
                func_name = "unknown"
                name_node = find_child_by_type(method_node, "identifier")
                if name_node:
                    func_name = get_node_text(name_node, content)
                issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.DESIGN,
                    message=f"Method '{func_name}' is {func_lines} lines",
                    location=Location(
                        file_path=file_path,
                        start_line=method_node.start_point[0] + 1,
                        end_line=method_node.end_point[0] + 1
                    ),
                    suggestion="Consider splitting into smaller methods",
                    rule_id="java-long-method"
                ))
    
    def _generate_issue_id(self) -> str:
        """生成问题ID"""
        import uuid
        return f"issue-{uuid.uuid4().hex[:8]}"


    # ====================== 新增 RAG 专用方法 ======================
    def get_rag_chunks(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        专为 Chroma RAG 设计的语义 chunk 方法
        返回格式：[{"content": str, "metadata": dict}]
        """
        if content is None:
            tree, content = self.parser.parse_file(file_path)
        else:
            tree = self.parser.parse_content(content)

        chunks: List[Dict[str, Any]] = []

        # Tree-sitter 查询提取类、方法、字段等
        query = self.parser.language.query("""
            (class_declaration) @class
            (method_declaration) @method
            (field_declaration) @field
            (interface_declaration) @interface
        """)
        
        captures = query.captures(tree.root_node)
        
        for node, capture_name in captures:
            chunk_text = node.text.decode("utf-8").strip()
            if not chunk_text or len(chunk_text) < 10:
                continue

            start_line = node.start_point[0] + 1
            end_line   = node.end_point[0] + 1

            entity_type = {
                "class": EntityType.CLASS,
                "method": EntityType.METHOD,
                "field": EntityType.FIELD,
                "interface": EntityType.INTERFACE
            }.get(capture_name, EntityType.UNKNOWN)

            entity = CodeEntity(
                entity_id=hashlib.md5(f"{file_path}:{capture_name}:{start_line}".encode()).hexdigest()[:16],
                entity_type=entity_type,
                name=chunk_text.split(maxsplit=2)[1] if len(chunk_text.split()) > 1 else "anonymous",
                location=Location(file_path=file_path, start_line=start_line, end_line=end_line),
                file_path=file_path,
                content=chunk_text,
                signature=chunk_text[:300],
                doc_comment="",
                language="java"
            )
            
            chunks.append({
                "content": chunk_text,
                "metadata": entity.to_dict()
            })

        # 兜底整文件
        if not chunks:
            chunks.append({
                "content": content[:8000],
                "metadata": {
                    "file_path": file_path,
                    "entity_type": "file",
                    "language": "java",
                    "name": Path(file_path).name
                }
            })
        
        return chunks