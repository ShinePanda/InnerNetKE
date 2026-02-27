"""
C++ AI Assistant - 代码实体定义
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


class EntityType(str, Enum):
    """代码实体类型"""
    FILE = "file"
    CLASS = "class"
    STRUCT = "struct"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    MEMBER = "member"
    CONSTANT = "constant"
    TYPEDEF = "typedef"
    ENUM = "enum"
    NAMESPACE = "namespace"
    TEMPLATE = "template"
    MACRO = "macro"


class AccessSpecifier(str, Enum):
    """访问修饰符"""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"


class IssueSeverity(str, Enum):
    """问题严重程度"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    """问题类别"""
    MEMORY_SAFETY = "memory_safety"
    RESOURCE_MANAGEMENT = "resource_management"
    EXCEPTION_SAFETY = "exception_safety"
    CONCURRENCY = "concurrency"
    PERFORMANCE = "performance"
    MODERN_CPP = "modern_cpp"
    DESIGN = "design"
    READABILITY = "readability"
    CORRECTNESS = "correctness"


@dataclass
class Location:
    """代码位置"""
    file_path: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    
    def __str__(self) -> str:
        if self.start_line == self.end_line:
            return f"{self.file_path}:{self.start_line}"
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


@dataclass
class CodeEntity:
    """代码实体"""
    entity_id: str
    entity_type: EntityType
    name: str
    location: Location
    file_path: str
    content: str
    
    # 语义信息
    signature: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    
    # 关系信息
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    caller_ids: List[str] = field(default_factory=list)
    callee_ids: List[str] = field(default_factory=list)
    
    # 访问控制
    access_specifier: Optional[AccessSpecifier] = None
    is_static: bool = False
    is_constexpr: bool = False
    is_virtual: bool = False
    is_template: bool = False
    
    # 文档和注释
    doc_comment: Optional[str] = None
    comments: List[str] = field(default_factory=list)
    
    # 度量信息
    cyclomatic_complexity: int = 1
    line_count: int = 0
    
    # 元数据
    language: str = "cpp"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "location": {
                "file_path": self.location.file_path,
                "start_line": self.location.start_line,
                "end_line": self.location.end_line,
            },
            "signature": self.signature,
            "return_type": self.return_type,
            "parameters": self.parameters,
            "parent_id": self.parent_id,
            "access_specifier": self.access_specifier.value if self.access_specifier else None,
            "is_static": self.is_static,
            "is_virtual": self.is_virtual,
            "is_template": self.is_template,
            "doc_comment": self.doc_comment,
            "complexity": self.cyclomatic_complexity,
        }


@dataclass
class CodeIssue:
    """代码问题"""
    issue_id: str
    severity: IssueSeverity
    category: IssueCategory
    message: str
    location: Location
    
    # 修复信息
    suggestion: Optional[str] = None
    fix_code: Optional[str] = None
    
    # 规则信息
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    
    # 元数据
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "location": {
                "file_path": self.location.file_path,
                "start_line": self.location.start_line,
                "end_line": self.location.end_line,
            },
            "suggestion": self.suggestion,
            "fix_code": self.fix_code,
            "rule_id": self.rule_id,
            "confidence": self.confidence,
        }


@dataclass
class RefactoringOpportunity:
    """重构机会"""
    opportunity_id: str
    pattern_name: str
    description: str
    location: Location
    
    # 重构详情
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    effort_estimate: str = "medium"
    
    # 代码示例
    before_code: Optional[str] = None
    after_code: Optional[str] = None
    
    # 步骤
    steps: List[str] = field(default_factory=list)
    
    # 元数据
    impact_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "pattern_name": self.pattern_name,
            "description": self.description,
            "location": {
                "file_path": self.location.file_path,
                "start_line": self.location.start_line,
                "end_line": self.location.end_line,
},
            "benefits": self.benefits,
            "risks": self.risks,
            "effort_estimate": self.effort_estimate,
            "before_code": self.before_code,
            "after_code": self.after_code,
            "steps": self.steps,
            "impact_score": self.impact_score,
        }


@dataclass
class CallGraph:
    """调用图"""
    nodes: Dict[str, CodeEntity] = field(default_factory=dict)
    edges: Dict[str, List[str]] = field(default_factory=dict)  # caller -> [callees]
    reverse_edges: Dict[str, List[str]] = field(default_factory=dict)  # callee -> [callers]
    
    def add_entity(self, entity: CodeEntity) -> None:
        self.nodes[entity.entity_id] = entity
        self.edges[entity.entity_id] = []
        self.reverse_edges[entity.entity_id] = []
    
    def add_call(self, caller_id: str, callee_id: str) -> None:
        if caller_id in self.edges and callee_id not in self.edges[caller_id]:
            self.edges[caller_id].append(callee_id)
        if callee_id in self.reverse_edges:
            self.reverse_edges[callee_id].append(caller_id)
    
    def get_callers(self, entity_id: str) -> List[str]:
        return self.reverse_edges.get(entity_id, [])
    
    def get_callees(self, entity_id: str) -> List[str]:
        return self.edges.get(entity_id, [])
    
    def find_reachable(self, start_id: str) -> set:
        """查找从起始实体可达的所有实体"""
        reachable = set()
        stack = [start_id]
        
        while stack:
            current = stack.pop()
            if current not in reachable:
                reachable.add(current)
                stack.extend(self.get_callees(current))
        
        return reachable
    
    def find_cycles(self) -> List[List[str]]:
        """检测调用图中的循环"""
        cycles = []
        visited = set()
        recursion_stack = set()
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            recursion_stack.add(node)
            path.append(node)
            
            for callee in self.get_callees(node):
                if callee not in visited:
                    dfs(callee, path)
                elif callee in recursion_stack:
                    # 找到循环
                    cycle_start = path.index(callee)
                    cycles.append(path[cycle_start:])
            
            recursion_stack.remove(node)
            path.pop()
        
        for node in self.nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles


@dataclass
class InheritanceGraph:
    """继承图"""
    nodes: Dict[str, CodeEntity] = field(default_factory=dict)
    edges: Dict[str, List[str]] = field(default_factory=dict)  # derived -> [base]
    
    def add_entity(self, entity: CodeEntity, base_classes: List[str] = None) -> None:
        self.nodes[entity.entity_id] = entity
        self.edges[entity.entity_id] = base_classes or []
    
    def get_base_classes(self, entity_id: str) -> List[str]:
        return self.edges.get(entity_id, [])
    
    def get_derived_classes(self, entity_id: str) -> List[str]:
        derived = []
        for derived_id, bases in self.edges.items():
            if entity_id in bases:
                derived.append(derived_id)
        return derived
    
    def get_inheritance_chain(self, entity_id: str) -> List[str]:
        """获取继承链"""
        chain = []
        current = entity_id
        
        while current:
            chain.append(current)
            bases = self.get_base_classes(current)
            current = bases[0] if bases else None
        
        return chain
    
    def detect_diamond_problem(self) -> List[str]:
        """检测菱形继承问题"""
        problematic = []
        
        for entity_id, bases in self.edges.items():
            if len(bases) >= 2:
                # 检查是否有共同基类
                for i, base1 in enumerate(bases):
                    for base2 in bases[i+1:]:
                        # 检查base1和base2是否有共同基类
                        base1_chain = set(self.get_inheritance_chain(base1))
                        base2_chain = set(self.get_inheritance_chain(base2))
                        common = base1_chain & base2_chain
                        if common and entity_id not in problematic:
                            problematic.append(entity_id)
                            break
        
        return problematic
