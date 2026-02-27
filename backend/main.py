"""
C++ AI Assistant - 主FastAPI应用
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import get_settings
from .models.schemas import (
    QueryRequest, QueryResponse,
    CodeReviewRequest, CodeReviewResponse,
    RefactorRequest, RefactorResponse,
    TestGenerationRequest, TestGenerationResponse,
    HealthStatus, TaskInfo, TaskStatus
)
from .parsers import CppParser, CppCodeAnalyzer
from .services.qwen_service import QwenService
from .vectorstore import ChromaVectorStore, HybridRetriever
from .utils.path_mapper import get_path_mapper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 全局实例
qwen_service: QwenService = None
vector_store: ChromaVectorStore = None
hybrid_retriever: HybridRetriever = None
cpp_parser: CppParser = None
cpp_analyzer: CppCodeAnalyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理"""
    global qwen_service, vector_store, hybrid_retriever, cpp_parser, cpp_analyzer
    
    logger.info("Starting C++ AI Assistant...")
    
    # 初始化服务
    try:
        qwen_service = QwenService()
        logger.info("Qwen service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Qwen service: {e}")
    
    try:
        vector_store = ChromaVectorStore()
        hybrid_retriever = HybridRetriever(vector_store)
        logger.info("Vector store initialized")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        raise
    
    try:
        cpp_parser = CppParser()
        cpp_analyzer = CppCodeAnalyzer(cpp_parser)
        logger.info("C++ parser initialized")
    except Exception as e:
        logger.error(f"Failed to initialize C++ parser: {e}")
        raise
    
    logger.info("C++ AI Assistant started successfully")
    
    yield
    
    # 关闭服务
    logger.info("Shutting down C++ AI Assistant...")
    if qwen_service:
        await qwen_service.close()
    logger.info("Shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title="C++ AI Assistant API",
    description="AI-powered C++ code refactoring and programming assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 依赖注入
async def get_services():
    """获取服务实例"""
    return {
        "qwen": qwen_service,
        "vector_store": vector_store,
        "hybrid_retriever": hybrid_retriever,
        "cpp_analyzer": cpp_analyzer
    }


# 健康检查端点
@app.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check():
    """健康检查"""
    return HealthStatus(
        status="healthy",
        version="1.0.0",
        components={
            "qwen": qwen_service is not None,
            "vector_store": vector_store is not None,
            "cpp_parser": cpp_parser is not None
        },
        timestamp=datetime.now()
    )


# API端点
@app.post("/api/query", response_model=QueryResponse, tags=["AI"])
async def handle_query(request: QueryRequest, services=Depends(get_services)):
    """处理用户查询"""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # 检索相关上下文
        context = []
        if hybrid_retriever and request.context_files:
            for file_path in request.context_files:
                docs = await hybrid_retriever.vector_store.get_by_source(file_path)
                context.extend(docs)
        
        # 生成回答
        if qwen_service:
            answer = await qwen_service.explain_code(
                code="",  # 需要从上下文获取
                context=request.query,
                language=request.language
            )
        else:
            answer = "Qwen service not available. Please check configuration."
        
        return QueryResponse(
            answer=answer,
            references=context,
            metadata={
                "task_type": request.task_type.value,
                "language": request.language
            }
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review", response_model=CodeReviewResponse, tags=["AI"])
async def review_code(request: CodeReviewRequest, services=Depends(get_services)):
    """代码审查"""
    if not request.code:
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        if qwen_service:
            result = await qwen_service.review_code(
                code=request.code,
                file_path=request.file_path,
                review_scope=request.review_scope
            )
            
            # 解析结果
            summary = result.get("summary", "")
            score = result.get("score", 50)
            issues = result.get("issues", [])
            metrics_data = result.get("metrics", {})
            
            # 构建响应
            return CodeReviewResponse(
                summary=summary,
                score=score,
                issues=[
CodeIssue(
                        issue_id=f"issue-{i}",
                        severity=issue.get("severity", "info"),
                        category=issue.get("category", "correctness"),
                        message=issue.get("message", ""),
                        location=Location(
                            file_path=request.file_path or "",
                            start_line=issue.get("line", 1),
                            end_line=issue.get("line", 1)
                        ),
                        suggestion=issue.get("suggestion")
                    )
                    for i, issue in enumerate(issues)
                ],
                metrics=ReviewMetrics(
                    total_issues=len(issues),
                    critical_count=sum(1 for i in issues if i.get("severity") == "critical"),
                    error_count=sum(1 for i in issues if i.get("severity") == "error"),
                    warning_count=sum(1 for i in issues if i.get("severity") == "warning"),
                    info_count=sum(1 for i in issues if i.get("severity") == "info"),
                    complexity_score=0.0,
                    maintainability_score=score
                ),
                suggestions=[s.get("suggestion", "") for s in issues if s.get("suggestion")]
            )
        else:
            return CodeReviewResponse(
                summary="Qwen service not available",
                score=0,
                issues=[],
                metrics=ReviewMetrics(
                    total_issues=0, critical_count=0, error_count=0,
                    warning_count=0, info_count=0
                ),
                suggestions=["Please configure Qwen API access"]
            )
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refactor", response_model=RefactorResponse, tags=["AI"])
async def refactor_code(request: RefactorRequest, services=Depends(get_services)):
    """代码重构"""
    if not request.code:
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        if qwen_service:
            result = await qwen_service.suggest_refactoring(
                code=request.code,
                refactor_type=request.refactor_type,
                constraints=request.constraints
            )
            
            return RefactorResponse(
                current_state=result.get("current_state", ""),
                issues_identified=result.get("issues", []),
                suggestions=[
                    RefactoringSuggestion(
                        pattern_name=s.get("pattern", ""),
                        description=s.get("description", ""),
                        benefits=s.get("benefits", []),
                        risks=s.get("risks", []),
                        effort_estimate=s.get("effort", "medium"),
                        before_code=s.get("before_code"),
                        after_code=s.get("after_code"),
                        steps=s.get("steps", [])
                    )
                    for s in result.get("suggestions", [])
                ],
                estimated_improvements=result.get("estimated_improvements", {})
            )
        else:
            return RefactorResponse(
                current_state="Qwen service not available",
                issues_identified=[],
                suggestions=[],
                estimated_improvements={}
            )
    except Exception as e:
        logger.error(f"Refactoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test", response_model=TestGenerationResponse, tags=["AI"])
async def generate_tests(request: TestGenerationRequest, services=Depends(get_services)):
    """生成测试"""
    if not request.code:
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        if qwen_service:
            result = await qwen_service.generate_tests(
                code=request.code,
                test_framework=request.test_framework,
                coverage_level=request.coverage_level
            )
            
            return TestGenerationResponse(
                test_cases=[
                    TestCase(
                        name=t.get("name", ""),
                        description=t.get("description", ""),
                        test_code=t.get("test_code", ""),
                        expected_behavior=t.get("expected_behavior", ""),
                        edge_cases=t.get("edge_cases", [])
                    )
                    for t in result.get("test_cases", [])
                ],
                total_cases=len(result.get("test_cases", [])),
                framework=request.test_framework,
                coverage_notes=result.get("coverage_notes", [])
            )
        else:
            return TestGenerationResponse(
                test_cases=[],
                total_cases=0,
                framework=request.test_framework,
                coverage_notes=["Qwen service not available"]
            )
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index/stats", tags=["Index"])
async def get_index_stats(services=Depends(get_services)):
    """获取索引统计"""
    if vector_store:
        stats = await vector_store.get_stats()
        return stats
    return {"error": "Vector store not available"}


@app.post("/api/index/rebuild", tags=["Index"])
async def rebuild_index(background_tasks: BackgroundTasks, services=Depends(get_services)):
    """重建索引"""
    if not cpp_analyzer:
        raise HTTPException(status_code=500, detail="C++ analyzer not available")
    
    # 启动后台任务
    background_tasks.add_task(_rebuild_index_task)
    
    return {"status": "Index rebuild started"}


async def _rebuild_index_task():
    """重建索引任务"""
    global hybrid_retriever
    
    if not vector_store:
        logger.error("Vector store not available for rebuild")
        return
    
    try:
        # 重置索引
        await vector_store.reset()
        
        # 重新索引代码仓库
        settings = get_settings()
        repos_dir = Path(settings.knowledge_base.repos_dir)
        
        if repos_dir.exists():
            cpp_files = list(repos_dir.rglob("*.cpp")) + list(repos_dir.rglob("*.h"))
            
            for cpp_file in cpp_files[:100]:  # 限制数量
                try:
                    # 解析C++文件
                    analysis_result = cpp_analyzer.analyze_file(str(cpp_file))
                    
                    # 提取实体
                    entities = analysis_result["entities"]
                    
                    # 索引实体
                    if hybrid_retriever and entities:
                        entity_dicts = [e.to_dict() for e in entities]
                        await hybrid_retriever.index_code_entities(entity_dicts)
                        
                except Exception as e:
                    logger.warning(f"Failed to process {cpp_file}: {e}")
        
        logger.info("Index rebuild completed")
        
    except Exception as e:
        logger.error(f"Index rebuild failed: {e}")


# 路径映射端点
class PathMappingRequest(BaseModel):
    """路径映射请求"""
    archive_root: str
    dev_root: str
    priority: int = 0
    description: str = ""


class PathMappingTestRequest(BaseModel):
    """路径映射测试请求"""
    path: str


@app.get("/api/path-mapping", tags=["Path Mapping"])
async def get_path_mappings():
    """获取所有路径映射"""
    try:
        path_mapper = get_path_mapper()
        mappings = path_mapper.get_mappings()
        return {
            "success": True,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"Failed to get path mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/path-mapping", tags=["Path Mapping"])
async def add_path_mapping(request: PathMappingRequest):
    """添加路径映射"""
    try:
        path_mapper = get_path_mapper()
        path_mapper.add_mapping(
            archive_root=request.archive_root,
            dev_root=request.dev_root,
            priority=request.priority,
            description=request.description
        )
        return {
            "success": True,
            "message": f"Path mapping added: {request.archive_root} -> {request.dev_root}"
        }
    except Exception as e:
        logger.error(f"Failed to add path mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/path-mapping", tags=["Path Mapping"])
async def remove_path_mapping(archive_root: str):
    """删除路径映射"""
    try:
        path_mapper = get_path_mapper()
        success = path_mapper.remove_mapping(archive_root)
        
        if success:
            return {
                "success": True,
                "message": f"Path mapping removed: {archive_root}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Path mapping not found: {archive_root}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove path mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/path-mapping/test", tags=["Path Mapping"])
async def test_path_mapping(request: PathMappingTestRequest):
    """测试路径映射"""
    try:
        path_mapper = get_path_mapper()
        result = path_mapper.test_mapping(request.path)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to test path mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 导入需要的类
from datetime import datetime
from .models.schemas import (
    Location, CodeIssue as CodeIssueSchema,
    ReviewMetrics, RefactoringSuggestion, TestCase
)
