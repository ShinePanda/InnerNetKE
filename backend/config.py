"""
C++ AI Assistant - 配置管理模块
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """应用配置"""
    name: str = "C++ AI Assistant"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    cors_origins: List[str] = Field(default_factory=list)
    max_request_size: int = 10485760


class QwenConfig(BaseModel):
    """千问模型配置"""
    api_base: str = "https://your-qwen-endpoint.com/v1"
    api_key: str = ""
    model_name: str = "qwen-3-235b"
    max_tokens: int = 8192
    temperature: float = 0.1
    timeout: int = 120
    retry_times: int = 3
    retry_delay: int = 5


class VectorDBConfig(BaseModel):
    """向量数据库配置"""
    type: str = "chroma"
    persist_directory: str = "./data/indexes/chroma"
    collection_name: str = "cpp_code_knowledge"
    embedding_model: str = "mixedbread-ai/mxbai-embed-large-v1"
    hnsw_space: str = "cosine"
    hnsw_ef_search: int = 100
    hnsw_m: int = 16


class CodeAnalysisConfig(BaseModel):
    """代码分析配置"""
    supported_languages: List[str] = Field(
        default_factory=lambda: ["cpp", "c", "h", "hpp", "cc", "cxx"]
    )
    tree_sitter_language: str = "cpp"
    max_file_size: int = 1048576
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [
            "**/build/**", "**/cmake-build-*/**", "**/.git/**",
            "**/node_modules/**", "**/third_party/**", "**/3rd_party/**"
        ]
    )


class PathMappingConfig(BaseModel):
    """路径映射配置"""
    enabled: bool = True
    mapping_file: str = "./config/path-mapping.json"


class SyncConfig(BaseModel):
    """同步配置"""
    interval: int = 3600
    auto_sync: bool = True
    max_concurrent_syncs: int = 4
    clone_timeout: int = 600


class KnowledgeBaseConfig(BaseModel):
    """知识库配置"""
    repos_dir: str = "./data/repos"
    docs_dir: str = "./data/docs"
    indexes_dir: str = "./data/indexes"
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    code_analysis: CodeAnalysisConfig = Field(default_factory=CodeAnalysisConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)


class VectorSearchConfig(BaseModel):
    """向量搜索配置"""
    default_top_k: int = 10
    max_top_k: int = 50
    similarity_threshold: float = 0.5
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    reranker_batch_size: int = 32


class TaskQueueConfig(BaseModel):
    """任务队列配置"""
    max_concurrent_tasks: int = 8
    task_timeout: int = 300
    priority_levels: int = 3


class MonitoringConfig(BaseModel):
    """监控配置"""
    enabled: bool = True
    metrics_endpoint: str = "/metrics"
    health_endpoint: str = "/health"
    log_requests: bool = True
    log_responses: bool = False


class SecurityConfig(BaseModel):
    """安全配置"""
    enable_auth: bool = False
    rate_limit_enabled: bool = True
    requests_per_minute: int = 60
    burst_size: int = 10
    max_query_length: int = 4096
    max_code_length: int = 65536


class Settings(BaseModel):
    """全局配置"""
    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    qwen: QwenConfig = Field(default_factory=QwenConfig)
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
    vector_search: VectorSearchConfig = Field(default_factory=VectorSearchConfig)
    task_queue: TaskQueueConfig = Field(default_factory=TaskQueueConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    path_mapping: PathMappingConfig = Field(default_factory=PathMappingConfig)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        config_path = os.environ.get(
            "CONFIG_PATH",
            str(Path(__file__).parent.parent / "config.yaml")
        )
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        return {}
    
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置（单例模式）"""
    config_data = load_config()
    
    # 替换环境变量
    config_data = _replace_env_vars(config_data)
    
    return Settings(**config_data)


def _replace_env_vars(obj: Any) -> Any:
    """递归替换配置中的环境变量"""
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        env_key = obj[2:-1]
        return os.environ.get(env_key, obj)
    return obj


# 全局配置实例
settings = get_settings()
