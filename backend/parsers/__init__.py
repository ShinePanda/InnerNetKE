"""
C++ Code Parser Module
"""
from .cpp_analyzer import CppParser, CppCodeAnalyzer, CppRefactoringAnalyzer
from .ice_analyzer import IceParser, IceAnalyzer
from .java_analyzer import JavaParser, JavaCodeAnalyzer
from .code_entities import (
    EntityType,
    AccessSpecifier,
    IssueSeverity,
    IssueCategory,
    Location,
    CodeEntity,
    CodeIssue,
    RefactoringOpportunity,
    CallGraph,
    InheritanceGraph,
)

# Factory function to get analyzer by language
def get_analyzer(language: str):
    """
    统一获取对应语言的 analyzer 实例
    """
    if language == "cpp":
        return CppCodeAnalyzer(CppParser())
    elif language == "java":
        return JavaCodeAnalyzer(JavaParser())
    elif language == "ice":
        # ·µ»Ø IceAnalyzer ÒÔ±£³ÖÓëÆäËûÓïÑÔµÄÒ»ÖÂ½Ó¿Ú£¨analyze_file ºÍ get_rag_chunks£©
        return IceAnalyzer()
    else:
        raise ValueError(f"不支持的语言: {language}")

__all__ = [
    # C++ parser
    "CppParser",
    "CppCodeAnalyzer",
    "CppRefactoringAnalyzer",
    # ICE Slice parser
    "IceParser",
    "IceAnalyzer",
    # Java parser
    "JavaParser",
    "JavaCodeAnalyzer",
    # Code entities
    "EntityType",
    "AccessSpecifier",
    "IssueSeverity",
    "IssueCategory",
    "Location",
    "CodeEntity",
    "CodeIssue",
    "RefactoringOpportunity",
    "CallGraph",
    "InheritanceGraph",
    # Factory function
    "get_analyzer",
]
