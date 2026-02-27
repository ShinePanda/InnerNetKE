# C++ AI Assistant - Backend Services
# C++代码解析、向量检索和AI推理服务

## 服务架构

```
backend/
├── main.py                    # FastAPI主入口
├── config.py                  # 配置管理
├── app.py                     # 应用工厂
├── parsers/
│   ├── __init__.py
│   ├── cpp_parser.py         # C++语法解析器
│   ├── cpp_analyzer.py       # C++语义分析器
│   └── code_entities.py      # 代码实体定义
├── models/
│   ├── __init__.py
│   ├── schemas.py            # Pydantic模型
│   └── code_structures.py    # 代码结构定义
├── services/
│   ├── __init__.py
│   ├── qwen_service.py       # 千问模型集成
│   ├── refactoring_service.py # 重构服务
│   ├── review_service.py     # 代码审查服务
│   ├── vector_service.py     # 向量检索服务
│   └── knowledge_service.py   # 知识库服务
├── vectorstore/
│   ├── __init__.py
│   ├── chroma_store.py       # ChromaDB向量存储
│   └── hybrid_retriever.py   # 混合检索器
└── utils/
    ├── __init__.py
    ├── tree_sitter_utils.py  # Tree-sitter工具
    └── logger.py             # 日志配置
```

## 核心功能

### 1. C++代码解析
- 使用Tree-sitter进行语法解析
- 提取类、函数、变量等实体
- 分析继承关系和调用图
- 检测代码异味和潜在问题

### 2. 向量检索
- 基于代码语义的向量索引
- 混合检索策略（稠密+稀疏）
- 相关性排序和重排序
- 增量索引更新

### 3. AI推理
- 千问模型集成
- 专用Prompt模板
- 代码审查建议
- 重构方案生成
