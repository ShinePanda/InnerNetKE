"""
C++ AI Assistant - C++语法解析器
"""
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime

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
        
        # 预编译的查询
        self._build_queries()
    
    def _build_queries(self) -> None:
        """构建Tree-sitter查询"""
        # 类/结构体查询
        self.class_query = tree_sitter.Query(
            self.parser.language,
            """
            (class_specifier
                name: (type_identifier) @class_name
                body: (class_body) @class_body)
            """
        )
        
        # 函数定义查询
        self.function_query = tree_sitter.Query(
            self.parser.language,
            """
            (function_definition
                declarator: (function_declarator
                    declarator: (identifier) @func_name
                    parameters: (parameter_list) @params)
                body: (compound_statement) @body)
            """
        )
        
        # 方法定义查询
        self.method_query = tree_sitter.Query(
            self.parser.language,
            """
            (function_definition
                declarator: (qualified_identifier) @qualified_name
                parameters: (parameter_list) @params
                body: (compound_statement) @body)
            """
        )
        
        # 变量声明查询
        self.variable_query = tree_sitter.Query(
            self.parser.language,
            """
            (declaration
                declarator: (init_declarator
                    declarator: (identifier) @var_name)
                type: (primitive_type) @type
                value: (call_expression)? @init)
            """
        )
        
        # 调用表达式查询
        self.call_query = tree_sitter.Query(
            self.parser.language,
            """
            (call_expression
                function: (identifier) @callee
                arguments: (argument_list) @args)
            """
        )
    
    def analyze_file(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析C++文件"""
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
        cursor = tree.walk()
        
        def process_node(node: Node, depth: int = 0):
            if depth > 50:  # 防止无限递归
                return
            
            entity = self._node_to_entity(node, content, file_path)
            if entity:
                entities.append(entity)
            
            for child in node.children:
                process_node(child,depth + 1)
        
        process_node(tree.root_node)
    
    def _node_to_entity(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """将Tree-sitter节点转换为代码实体"""
        node_type = node.type
        
        if node_type == "class_specifier":
            return self._parse_class(node, content, file_path)
        elif node_type == "struct_specifier":
            return self._parse_struct(node, content, file_file)
        elif node_type == "function_definition":
            return self._parse_function(node, content, file_path)
        elif node_type == "method_definition":
            return self._parse_method(node, content, file_path)
        elif node_type == "declaration":
            return self._parse_declaration(node, content, file_path)
        elif node_type == "namespace_definition":
            return self._parse_namespace(node, content, file_path)
        elif node_typeifier":
            return == "enum_spec self._parse_enum(node, content, file_path)
        
        return None
    
    def _parse_class(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析类定义"""
        name_node = find_child_by_type(node, "type_identifier")
        if not name_node:
            return None
        
        name = get_node_text(name_node, content)
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # 查找类成员
        class_body = find_child_by_type(node, "class_body")
        members = []
        if class_body:
            members = find_children_by_type(
                class_body,
                ["function_definition", "field_declaration", "access_specifier"]
            )
        
        # 查找基类
        base_classes = []
        base_clause = find_child_by_type(node, "base_class_clause")
        if base_clause:
            for child in base_clause.children:
                if child.type == "base_class":
                    base_name_node = find_child_by_type(child, "type_identifier")
                    if base_name_node:
                        base_classes.append(get_node_text(base_name_node, content))
        
        # 确定访问修饰符
        access = self._determine_access(node)
        
        # 计算圈复杂度
        complexity = self._calculate_complexity(node, content)
        
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
            signature=name,
            parameters=[],
            parent_id=None,
            access_specifier=access,
            is_static=False,
            cyclomatic_complexity=complexity,
            line_count=end_line - start_line,
            metadata={"base_classes": base_classes, "member_count": len(members)}
        )
    
    def _parse_struct(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析结构体定义"""
        name_node = find_child_by_type(node, "type_identifier")
        if not name_node:
            return None
        
        name = get_node_text(name_node, content)
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # 结构体默认为public
        access = AccessSpecifier.PUBLIC
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.STRUCT,
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
            signature=name,
            access_specifier=access,
            cyclomatic_complexity=1,
            line_count=end_line - start_line,
        )
    
    def _parse_function(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析函数定义"""
        declarator = find_child_by_type(node, "function_declarator")
        if not declarator:
            return None
        
        name_node = find_child_by_type(declarator, "identifier")
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
        params_node = find_child_by_type(declarator, "parameter_list")
        parameters = []
        if params_node:
            for child in params_node.children:
                if child.type == "parameter_declaration":
                    param_name = find_child_by_type(child, "identifier")
                    if param_name:
                        param_type = child.child_by_field_name("type")
                        param_str = get_node_text(param_type, content) + " " + get_node_text(param_name, content)
                        parameters.append(param_str)
        
        # 构建函数签名
        param_str = ", ".join(parameters)
        signature = f"{return_type} {name}({param_str})"
        
        # 确定是否为静态/constexpr
        is_static = False
        is_constexpr = False
        for sibling in node.children:
            if sibling.type == "storage_class_specifier":
                if get_node_text(sibling, content) == "static":
                    is_static = True
                elif get_node_text(sibling, content) == "constexpr":
                    is_constexpr = True
        
        # 计算圈复杂度
        body = find_child_by_type(node, "compound_statement")
        complexity = self._calculate_complexity(body, content) if body else 1
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.FUNCTION,
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
            is_static=is_static,
            is_constexpr=is_constexpr,
            cyclomatic_complexity=complexity,
            line_count=end_line - start_line,
        )
    
    def _parse_method(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析类方法定义"""
        declarator = find_child_by_type(node, "qualified_identifier")
        if not declarator:
            return None
        
        # 获取完整的方法名（类名::方法名）
        name = get_node_text(declarator, content)
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # 解析返回类型和参数（类似函数解析）
        type_node = node.child_by_field_name("type")
        return_type = get_node_text(type_node, content) if type_node else "void"
        
        params_node = find_child_by_type(node, "parameter_list")
        parameters = []
        if params_node:
            for child in params_node.children:
                if child.type == "parameter_declaration":
                    param_name = find_child_by_type(child, "identifier")
                    if param_name:
                        param_type = child.child_by_field_name("type")
                        param_str = get_node_text(param_type, content) + " " + get_node_text(param_name, content)
                        parameters.append(param_str)
        
        # 确定是否const
        is_const = False
        for sibling in node.children:
            if sibling.type == "cv_qualifiers" and "const" in get_node_text(sibling, content):
                is_const = True
        
        # 确定访问修饰符
        access = self._determine_access(node)
        
        # 计算圈复杂度
        body = find_child_by_type(node, "compound_statement")
        complexity = self._calculate_complexity(body, content) if body else 1
        
        # 提取方法名（不带类名）
        short_name = name.split("::")[-1] if "::" in name else name
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.METHOD,
            name=short_name,
            location=Location(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_column=node.start_point[1],
                end_column=node.end_point[1]
            ),
            file_path=file_path,
            content=get_node_text(node, content),
            signature=get_node_text(declarator, content),
            return_type=return_type,
            parameters=parameters,
            access_specifier=access,
            is_virtual=False,  # 需要进一步检查
            cyclomatic_complexity=complexity,
            line_count=end_line - start_line,
            metadata={"full_name": name}
        )
    
    def _parse_declaration(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析变量/成员声明"""
        declarator = find_child_by_type(node, "init_declarator")
        if not declarator:
            return None
        
        name_node = find_child_by_type(declarator, "identifier")
        if not name_node:
            return None
        
        name = get_node_text(name_node, content)
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # 获取类型
        type_node = node.child_by_field_name("type")
        var_type = get_node_text(type_node, content) if type_node else "auto"
        
        # 确定是变量还是成员
        is_member = "class_body" in str(node.parent) if node.parent else False
        
        # 确定访问修饰符
        access = self._determine_access(node) if is_member else None
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.MEMBER if is_member else EntityType.VARIABLE,
            name=name,
            location=Location(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_column=node.start_point[1],
                end_column=node.end_point[1]
            ),
            file_path=file_path,
            content=get_node_text(node,content),
            signature=f"{var_type} {name}",
            return_type=var_type,
            access_specifier=access,
            line_count=1,
        )
    
    def _parse_namespace(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析命名空间"""
        name_node = find_child_by_type(node, "identifier")
        name = get_node_text(name_node, content) if name_node else "anonymous"
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.NAMESPACE,
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
            signature=f"namespace {name}",
            line_count=end_line - start_line,
        )
    
    def _parse_enum(
        self,
        node: Node,
        content: str,
        file_path: str
    ) -> Optional[CodeEntity]:
        """解析枚举定义"""
        name_node = find_child_by_type(node, "type_identifier")
        name = get_node_text(name_node, content) if name_node else "anonymous"
        entity_id = self.parser.generate_entity_id(file_path, name, node.start_point[0])
        
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # 提取枚举值
        values = []
        enumerator_list = find_child_by_type(node, "enumerator_list")
        if enumerator_list:
            for child in enumerator_list.children:
                if child.type == "enumerator":
                    value_name = find_child_by_type(child, "identifier")
                    if value_name:
                        values.append(get_node_text(value_name, content))
        
        return CodeEntity(
            entity_id=entity_id,
            entity_type=EntityType.ENUM,
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
            line_count=end_line - start_line,
            metadata={"values": values}
        )
    
    def _determine_access(self, node: Node) -> Optional[AccessSpecifier]:
        """确定访问修饰符"""
        parent = node.parent
        if parent and parent.type in ["class_body", "access_specifier"]:
            # 向上查找访问说明符
            siblings = parent.children if hasattr(parent, 'children') else []
            for sibling in siblings:
                if sibling.type == "access_specifier":
                    text = get_node_text(sibling, "").strip()
                    if text == "public":
                        return AccessSpecifier.PUBLIC
                    elif text == "protected":
                        return AccessSpecifier.PROTECTED
                    elif text == "private":
                        return AccessSpecifier.PRIVATE
        return None
    
    def _calculate_complexity(self, node: Optional[Node], content: str) -> int:
        """计算圈复杂度"""
        if not node:
            return 1
        
        complexity = 1
        
        # 统计决策点
        decision_types = {
            "if_statement",
            "else_clause",
            "conditional_expression",
            "for_statement",
            "while_statement",
            "do_statement",
            "case_statement",
            "catch_clause"
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
        # 添加所有实体作为节点
        for entity in entities:
            call_graph.add_entity(entity)
        
        # 查找函数调用
        call_nodes = find_children_by_type(tree.root_node, "call_expression")
        
        for call_node in call_nodes:
            callee_node = find_child_by_type(call_node, "identifier")
            if not callee_node:
                continue
            
            callee_name = get_node_text(callee_node, content)
            
            # 找到调用者（当前正在解析的函数）
            caller = self._find_enclosing_function(call_node, entities)
            if caller:
                # 找到被调用者
                for entity in entities:
                    if entity.name == callee_name and entity.entity_type in [
                        EntityType.FUNCTION, EntityType.METHOD
                    ]:
                        call_graph.add_call(caller.entity_id, entity.entity_id)
                        break
    
    def _find_enclosing_function(
        self,
        node: Node,
        entities: List[CodeEntity]
    ) -> Optional[CodeEntity]:
        """查找包含给定节点的函数"""
        for entity in entities:
            if entity.entity_type in [EntityType.FUNCTION, EntityType.METHOD]:
                # 检查节点是否在函数范围内
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
        self._detect_memory_issues(tree, content, file_path, issues)
        self._detect_resource_issues(tree, content, file_path, issues)
        self._detect_null_pointer_issues(tree, content, file_path, issues)
        self._detect_modern_cpp_issues(tree, content, file_path, issues)
        self._detect_design_issues(tree, content, file_path, issues)
    
    def _detect_memory_issues(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        issues: List[CodeIssue]
    ) -> None:
        """检测内存安全问题"""
        # 检测原始new/delete使用
        new_nodes = find_children_by_type(tree.root_node, "new_expression")
        for new_node in new_nodes:
            location = get_node_range(new_node)
            
            # 检查是否有对应的delete
            delete_found = False
            for sibling in traverse_tree(tree.root_node):
                if sibling.type == "delete_expression":
                    delete_found = True
                    break
            
            if not delete_found:
                issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.MEMORY_SAFETY,
                    message="Raw new/delete detected - consider using smart pointers",
                    location=Location(
                        file_path=file_path,
                        start_line=location[0],
                        end_line=location[1],
                    ),
                    suggestion="Use std::unique_ptr or std::shared_ptr instead",
                    rule_id="memory-raw-new"
                ))
        
        # 检测delete[]使用
        delete_array_nodes = find_children_by_type(tree.root_node, "delete_expression")
        for delete_node in delete_array_nodes:
            delete_text = get_node_text(delete_node, content)
            if "delete[]" not in delete_text and "delete" in delete_text:
                issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.ERROR,
                    category=IssueCategory.MEMORY_SAFETY,
                    message="Potential mismatched delete - use delete[] for arrays",
                    location=Location(
                        file_path=file_path,
                        start_line=delete_node.start_point[0] + 1,
                        end_line=delete_node.end_point[0] + 1,
                    ),
                    suggestion="If allocating array, use delete[] instead of delete",
                    rule_id="memory-delete-array"
                ))
    
    def _detect_resource_issues(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        issues: List[CodeIssue]
    ) -> None:
        """检测资源管理问题"""
        # 检测文件操作未使用RAII
        fstream_nodes = []
        for node in traverse_tree(tree.root_node):
            if node.type == "namespace_definition":
                ns_name = get_node_text(node, content)
                if "std" in ns_name or "fstream" in content:
                    # 简化检测：查找fstream类型声明
                    pass
        
        # 检测资源获取后未释放
        malloc_nodes = find_children_by_type(tree.root_node, "call_expression")
        for malloc_node in malloc_nodes:
            func_name = get_node_text(malloc_node, content)
            if "malloc" in func_name or "fopen" in func_name:
                issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.RESOURCE_MANAGEMENT,
                    message="Raw resource allocation detected - ensure proper cleanup",
                    location=Location(
                        file_path=file_path,
                        start_line=malloc_node.start_point[0] + 1,
                        end_line=malloc_node.end_point[0] + 1,
                    ),
                    suggestion="Consider using RAII wrappers or smart pointers",
                    rule_id="resource-raw-allocation"
                ))
    
    def _detect_null_pointer_issues(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        issues: List[CodeIssue]
    ) -> None:
        """检测空指针问题"""
        # 检测NULL、0、nullptr混用
        null_usage_nodes = []
        for node in traverse_tree(tree.root_node):
            if node.type in ["null_pointer", "number_literal", "identifier"]:
                text = get_node_text(node, content)
                if text in ["NULL", "0"] and "nullptr" in content:
                    null_usage_nodes.append(node)
        
        for node in null_usage_nodes:
            issues.append(CodeIssue(
                issue_id=self._generate_issue_id(),
                severity=IssueSeverity.WARNING,
                category=IssueCategory.CORRECTNESS,
                message=f"Found NULL/0 - prefer nullptr for type safety",
                location=Location(
                    file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ),
                suggestion="Replace NULL/0 with nullptr for better type safety",
                rule_id="nullpointer-prefer-nullptr"
            ))
    
    def _detect_modern_cpp_issues(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        issues: List[CodeIssue]
    ) -> None:
        """检测现代C++问题"""
        # 检测auto_ptr使用
        autp_ptr_nodes = []
        for node in traverse_tree(tree.root_node):
            if node.type == "identifier" and get_node_text(node, content) == "auto_ptr":
                autp_ptr_nodes.append(node)
        
        for node in autp_ptr_nodes:
            issues.append(CodeIssue(
                issue_id=self._generate_issue_id(),
                severity=IssueSeverity.ERROR,
                category=IssueCategory.MODERN_CPP,
                message="auto_ptr is deprecated and dangerous - use unique_ptr instead",
                location=Location(
                    file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ),
                suggestion="Replace auto_ptr with std::unique_ptr",
                fix_code=get_node_text(node, content).replace("auto_ptr", "std::unique_ptr"),
                rule_id="moderncpp-auto-ptr"
            ))
        
        # 检测range-for可以使用的场景
        for_nodes = find_children_by_type(tree.root_node, "for_statement")
        for for_node in for_nodes:
            for_text = get_node_text(for_node, content)
            if "size_t i = 0" in for_text or "int i = 0" in for_text:
                issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.INFO,
                    category=IssueCategory.MODERN_CPP,
                    message="Consider using range-based for loop",
                    location=Location(
                        file_path=file_path,
                        start_line=for_node.start_point[0] + 1,
                        end_line=for_node.end_point[0] + 1,
                    ),
                    suggestion="Replace index-based loop with range-based for loop",
                    rule_id="moderncpp-range-for"
                ))
    
    def _detect_design_issues(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        issues: List[CodeIssue]
    ) -> None:
        """检测设计问题"""
        # 检测过长函数
        function_nodes = find_children_by_type(tree.root_node, "function_definition")
        for func_node in function_nodes:
            func_lines = func_node.end_point[0] - func_node.start_point[0]
            if func_lines > 100:
                issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.DESIGN,
                    message=f"Function is {func_lines} lines - consider splitting into smaller functions",
                    location=Location(
                        file_path=file_path,
                        start_line=func_node.start_point[0] + 1,
                        end_line=func_node.end_point[0] + 1,
                    ),
                    suggestion="Consider extracting parts of the function into smaller, focused functions",
                    rule_id="design-long-function"
                ))
        
        # 检测过多参数
        for func_node in function_nodes:
            params_node = find_child_by_type(func_node, "parameter_list")
            if params_node:
                param_count = len([c for c in params_node.children if c.type == "parameter_declaration"])
                if param_count > 7:
                    issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.DESIGN,
                        message=f"Function has {param_count} parameters - consider grouping into struct/object",
                        location=Location(
                            file_path=file_path,
                            start_line=func_node.start_point[0] + 1,
                            end_line=func_node.end_point[0] + 1,
                        ),
                        suggestion="Consider using Parameter Object pattern to reduce parameter count",
                        rule_id="design-many-parameters"
                    ))
    
    def _generate_issue_id(self) -> str:
        """生成问题ID"""
        import uuid
        return f"issue-{uuid.uuid4().hex[:8]}"


class CppRefactoringAnalyzer:
    """C++重构分析器"""
    
    def __init__(self, parser: CppParser):
        self.parser = parser
        self.analyzer = CppCodeAnalyzer(parser)
    
    def find_refactoring_opportunities(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """查找重构机会"""
        if content is None:
            tree, content = self.parser.parse_file(file_path)
        else:
            tree = self.parser.parse_content(content)
        
        opportunities = []
        
        # 查找代码重复
        self._find_code_duplication(tree, content, file_path, opportunities)
        
        # 查找长方法
        self._find_long_methods(tree, content, file_path, opportunities)
        
        # 查找大类
        self._find_large_classes(tree, content, file_path, opportunities)
        
        # 查找魔法数字
        self._find_magic_numbers(tree, content, file_path, opportunities)
        
        # 查找条件语句可以多态化的地方
        self._find_type_checks(tree, content, file_path, opportunities)
        
        return opportunities
    
    def _find_code_duplication(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        opportunities: List[Dict[str, Any]]
    ) -> None:
        """查找代码重复"""
        # 简化的重复代码检测
        # 实际实现需要更复杂的算法（如CCFinder、ConQAT等）
        code_blocks = self._extract_code_blocks(tree)
        
        # 使用简单的哈希比较
        block_hashes = {}
        for i, block in enumerate(code_blocks):
            block_text = " ".join(block.split())  # 规范化空白
            block_hash = hash(block_text)
            
            if block_hash in block_hashes:
                # 发现重复
                opportunities.append({
                    "pattern": "code-duplication",
                    "description": "Potential code duplication detected",
                    "location1": {"file": file_path, "line": block_hashes[block_hash]["line"]},
                    "location2": {"file": file_path, "line": i * 5},  # 简化行号估计
                    "severity": "warning",
                    "suggestion": "Extract duplicated code into a separate function"
                })
            else:
                block_hashes[block_hash] = {"line": i * 5}
    
    def _extract_code_blocks(self, tree: Tree) -> List[str]:
        """提取代码块（简化版）"""
        blocks = []
        for node in tree.root_node.children:
            if node.type == "compound_statement":
                blocks.append(get_node_text(node, ""))
        return blocks
    
    def _find_long_methods(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        opportunities: List[Dict[str, Any]]
    ) -> None:
        """查找长方法"""
        function_nodes = find_children_by_type(tree.root_node, "function_definition")
        
        for func_node in function_nodes:
            line_count = func_node.end_point[0] - func_node.start_point[0]
            
            if line_count > 50:  # 阈值
                func_name = "unknown"
                name_node = find_child_by_type(func_node, "identifier")
                if name_node:
                    func_name = get_node_text(name_node, content)
                
                opportunities.append({
                    "pattern": "long-method",
                    "description": f"Method '{func_name}' is {line_count} lines long",
                    "location": {
                        "file": file_path,
                        "start_line": func_node.start_point[0] + 1,
                        "end_line": func_node.end_point[0] + 1
                    },
                    "severity": "warning",
                    "metric": {"lines": line_count},
                    "suggestion": "Consider extracting parts of this method into smaller, focused methods"
                })
    
    def _find_large_classes(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        opportunities: List[Dict[str, Any]]
    ) -> None:
        """查找大类"""
        class_nodes = find_children_by_type(tree.root_node, "class_specifier")
        
        for class_node in class_nodes:
            line_count = class_node.end_point[0] - class_node.start_point[0]
            
            if line_count > 500:  # 阈值
                class_name = "unknown"
                name_node = find_child_by_type(class_node, "type_identifier")
                if name_node:
                    class_name = get_node_text(name_node, content)
                
                opportunities.append({
                    "pattern": "large-class",
                    "description": f"Class '{class_name}' is {line_count} lines long",
                    "location": {
                        "file": file_path,
                        "start_line": class_node.start_point[0] + 1,
                        "end_line": class_node.end_point[0] + 1
                    },
                    "severity": "warning",
                    "metric": {"lines": line_count},
                    "suggestion": "Consider splitting this class into smaller, focused classes"
                })
    
    def _find_magic_numbers(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        opportunities: List[Dict[str, Any]]
    ) -> None:
        """查找魔法数字"""
        number_literals = find_children_by_type(tree.root_node, "number_literal")
        
        for num_node in number_literals:
            num_text = get_node_text(num_node, content)
            
            # 排除常见的常量
            if num_text in ["0", "1", "-1", "2", "10", "100", "1000"]:
                continue
            
            # 检查是否在可接受的位置
            parent = num_node.parent
            if parent and parent.type in ["enumerator", "case_statement"]:
                continue
            
            # 检查是否已有命名常量定义
            content_lines = content.split('\n')
            line_num = num_node.start_point[0]
            
            has_constant_nearby = False
            for i in range(max(0, line_num - 10), min(len(content_lines), line_num + 10)):
                if "const" in content_lines[i] or "constexpr" in content_lines[i]:
                    has_constant_nearby = True
                    break
            
            if not has_constant_nearby:
                opportunities.append({
                    "pattern": "magic-number",
                    "description": f"Magic number '{num_text}' found",
                    "location": {
                        "file": file_path,
                        "start_line": num_node.start_point[0] + 1,
                        "end_line": num_node.end_point[0] + 1
                    },
                    "severity": "info",
                    "suggestion": "Replace magic number with a named constant for better readability"
                })
    
    def _find_type_checks(
        self,
        tree: Tree,
        content: str,
        file_path: str,
        opportunities: List[Dict[str, Any]]
    ) -> None:
        """查找类型检查可以多态化的地方"""
        # 查找dynamic_cast使用
        dynamic_cast_nodes = find_children_by_type(tree.root_node, "dynamic_cast_expression")
        
        for cast_node in dynamic_cast_nodes:
            opportunities.append({
                "pattern": "type-check-polymorphism",
                "description": "dynamic_cast detected - consider using virtual functions instead",
                "location": {
                    "file": file_path,
                    "start_line": cast_node.start_point[0] + 1,
                    "end_line": cast_node.end_point[0] + 1
                },
                "severity": "info",
                "suggestion": "Consider replacing type checking with polymorphism (virtual functions)"
            })
