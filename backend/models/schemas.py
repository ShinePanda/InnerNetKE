"""
Pydantic schemas for API requests and responses
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """任务类型"""
    CODE_UNDERSTANDING = "understanding"
    CODE_REVIEW = "review"
    REFACTORING = "refactoring"
    TEST_GENERATION = "test_generation"
    CODE_COMPLETION = "completion"


class Severity(str, Enum):
    """问题严重程度"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Category(str, Enum):
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


# Request schemas
class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="用户查询内容", min_length=1, max_length=4096)
    task_type: TaskType = Field(..., description="任务类型")
    context_files: Optional[List[str]] = Field(default=None, description="相关文件列表")
    project_id: Optional[str] = Field(default=None, description="项目ID")
    language: str = Field(default="cpp", description="编程语言")
    options: Optional[Dict[str, Any]] = Field(default=None, description="额外选项")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Explain the User class and its responsibilities",
                "task_type": "understanding",
                "language": "cpp",
                "context_files": ["/src/user.h", "/src/user.cpp"]
            }
        }


class CodeReviewRequest(BaseModel):
    """代码审查请求"""
    code: str = Field(..., description="待审查的代码", min_length=1, max_length=65536)
    file_path: Optional[str] = Field(default=None, description="文件路径")
    language: str = Field(default="cpp", description="编程语言")
    review_scope: str = Field(default="full", description="审查范围: full/security/performance/style")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "class User { ... }",
                "file_path": "/src/user.h",
                "language": "cpp",
                "review_scope": "full"
            }
        }


class RefactorRequest(BaseModel):
    """重构请求"""
    code: str = Field(..., description="待重构的代码", min_length=1, max_length=65536)
    file_path: Optional[str] = Field(default=None, description="文件路径")
    refactor_type: str = Field(..., description="重构类型")
    constraints: Optional[List[str]] = Field(default=None, description="约束条件")
    target_pattern: Optional[str] = Field(default=None, description="目标模式")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "void process() { ... }",
                "file_path": "/src/processor.cpp",
                "refactor_type": "extract-method"
            }
        }


class TestGenerationRequest(BaseModel):
    """测试生成请求"""
    code: str = Field(..., description="待测试的代码", min_length=1, max_length=65536)
    file_path: Optional[str] = Field(default=None, description="文件路径")
    test_framework: str = Field(default="gtest", description="测试框架")
    coverage_level: str = Field(default="basic", description="覆盖级别: basic/normal/comprehensive")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "int add(int a, int b) { return a + b; }",
                "test_framework": "gtest",
                "coverage_level": "comprehensive"
            }
        }


# Response schemas
class Location(BaseModel):
    """代码位置"""
    file_path: str
    start_line: int
    end_line: int
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    
    def __str__(self) -> str:
        if self.start_line == self.end_line:
            return f"{self.file_path}:{self.start_line}"
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


class CodeIssue(BaseModel):
    """代码问题"""
    issue_id: str
    severity: Severity
    category: Category
    message: str
    location: Location
    suggestion: Optional[str] = None
    fix_code: Optional[str] = None
    rule_id: Optional[str] = None
    confidence: float = 1.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "issue_id": "issue-001",
                "severity": "warning",
                "category": "memory_safety",
                "message": "Memory leak detected",
                "location": {
                    "file_path": "/src/memory.cpp",
                    "start_line": 42,
                    "end_line": 42
                },
                "suggestion": "Use smart pointers"
            }
        }


class ReviewMetrics(BaseModel):
    """审查指标"""
    total_issues: int
    critical_count: int
    error_count: int
    warning_count: int
    info_count: int
    complexity_score: float = 0.0
    maintainability_score: float = 0.0


class CodeReviewResponse(BaseModel):
    """代码审查响应"""
    summary: str
    score: int = Field(..., ge=0, le=100, description="代码评分")
    issues: List[CodeIssue]
    metrics:ReviewMetrics
    suggestions: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Code review completed with 3 issues found",
                "score": 85,
                "issues": [],
                "metrics": {
                    "total_issues": 3,
                    "critical_count": 0,
                    "error_count": 1,
                    "warning_count": 2,
                    "info_count": 0
                },
                "suggestions": ["Consider using smart pointers", "Add error handling"]
            }
        }


class RefactoringSuggestion(BaseModel):
    """重构建议"""
    pattern_name: str
    description: str
    benefits: List[str]
    risks: List[str]
    effort_estimate: str
    before_code: Optional[str] = None
    after_code: Optional[str] = None
    steps: List[str]
    impact_score: float = 0.0


class RefactorResponse(BaseModel):
    """重构响应"""
    current_state: str
    issues_identified: List[Dict[str, Any]]
    suggestions: List[RefactoringSuggestion]
    estimated_improvements: Dict[str, str]


class TestCase(BaseModel):
    """测试用例"""
    name: str
    description: str
    test_code: str
    expected_behavior: str
    edge_cases: List[str] = Field(default_factory=list)


class TestGenerationResponse(BaseModel):
    """测试生成响应"""
    test_cases: List[TestCase]
    total_cases: int
    framework: str
    coverage_notes: List[str]


class QueryResponse(BaseModel):
    """查询响应"""
    answer: str
    references: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ExplanationResponse(BaseModel):
    """代码解释响应"""
    summary: str
    key_concepts: List[str]
    detailed_explanation: str
    related_topics: List[str]


# Repository management schemas
class RepositoryConfig(BaseModel):
    """仓库配置"""
    url: str
    local_path: str
    branch: str = "main"
    sync_interval: int = 3600
    auto_sync: bool = True


class RepositoryInfo(BaseModel):
    """仓库信息"""
    id: str
    name: str
    url: str
    local_path: str
    language: str = "cpp"
    file_count: int = 0
    line_count: int = 0
    last_sync: Optional[datetime] = None
    status: str = "pending"


# Task management schemas
class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: str
    task_type: str
    status: TaskStatus
    progress: float = 0.0
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Health check schemas
class HealthStatus(BaseModel):
    """健康状态"""
    status: str
    version: str
    components: Dict[str, Any]
    timestamp: datetime


# Statistics schemas
class Statistics(BaseModel):
    """统计数据"""
    total_repositories: int
    total_files: int
    total_lines: int
    total_entities: int
    total_issues: int
    last_updated: Optional[datetime] = None
