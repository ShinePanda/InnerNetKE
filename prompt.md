# C++ AI Assistant - 完整项目实施指南

> **目标**：构建一个企业级内网AI代码助手，让AI深入理解Git项目，提供C++/Java代码重构建议、代码审查和新需求开发支持。

> **创建时间**：2026-02-08
> **最后更新**：2026-02-08（集成 trlm-135M 方案）
> **适用对象**：Cloud Shell Editor、Cline、Cursor等AI Agent
> **参考项目**：`projects/3/cpp-ai-assistant`

---

## 1. 项目背景与愿景

### 目标
让AI能够深入理解Git项目，并提供：
- **代码重构建议** - AI驱动的可执行重构方案
- **代码审查** - 自动检测内存泄漏、资源管理、设计问题
- **新需求开发** - 基于现有代码库生成完整工程
- **测试方案生成** - 支持GTest/Catch2/DocTest
- **部署手册** - 可实施的配置和部署指南
- **🆕 内部知识推理** - 基于trlm-135M的专业内网知识库引擎

### 核心场景
- **内网环境** - 完全离线，无外网访问
- **代码规模** - 200万行代码
- **文档规模** - 2万文档 + 2万网页
- **目标环境** - Windows Server 2019
- **硬件配置** - 16核32GB内存，1TB硬盘

### 约束清单
- ✅ 内网完全隔离，无外网访问
- ✅ 千问3-235B企业版（OpenAI兼容接口）
- ✅ **trlm-135M** 本地小模型（内网知识推理引擎）
- ✅ Python 3.11.9（生产环境）
- ✅ 不使用PowerShell，统一Python/GitBash脚本
- ✅ 支持C++和Java Spring Boot（初期优先C++）
- ✅ 函数签名提取、依赖图、调用关系
- ✅ 自动生成完整测试方案
- ✅ 可执行的重构建议和部署手册

---

## 2. 技术选型决策（关键决策点）

### 2.1 后端架构选型

| 决策点 | 选型 | 原因 |
|--------|------|------|
| **Web框架** | **FastAPI** | 异步高性能、自动API文档、类型安全、Python 3.11原生支持 |
| **代码解析** | **Tree-sitter** | 准确AST、支持增量解析、多语言、性能优异 |
| **向量数据库** | **ChromaDB** | 纯Python、轻量级、支持离线、易部署 |
| **Embedding** | **Sentence Transformers** (all-MiniLM-L6-v2) | 代码语义理解强、Python实现、可离线 |
| **图数据库** | **NetworkX** | 轻量级Python图库，支持调用图、依赖图，适合32GB内存 |
| **🆕 本地小模型** | **trlm-135M** | 135M参数推理模型，支持显式<thinking>标签，内存占用~1GB |
| **大模型协同** | **千问3-235B** | 企业授权、OpenAI兼容、235B参数、内网部署 |

### 2.2 前端选型

| 决策点 | 选型 | 原因 |
|--------|------|------|
| **开发模式** | **VSCode扩展** | 开发者最熟悉、无缝集成、本地分析能力强 |
| **语言** | **TypeScript 4.9.4** | 类型安全、VSCode API原生支持 |
| **打包工具** | **vsce (@vscode/vsce)** | 官方工具、跨平台、生产级 |

### 2.3 部署选型

| 决策点 | 选型 | 原因 |
|--------|------|------|
| **Python分发** | **预编译Wheel包** | 避免编译、离线环境稳定、安装快速 |
| **安装方式** | **Python脚本** | 跨平台、可审计、易维护 |
| **日志系统** | **structlog + python-json-logger** | 结构化日志、JSON格式、便于分析 |

---

## 3. 架构设计：三位一体的"软件大脑"

### 3.1 核心架构分层

```
┌─────────────────────────────────────────────────┐
│  用户交互层                                       │
│  - VSCode 扩展                                   │
│  - Web 界面                                      │
│  - CLI 工具                                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  大模型协同层（千问3-235B）                     │
│  职责：自然语言理解、文档生成、多轮对话          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  内网小模型推理层（trlm-135M 专用训练）         │
│  职责：代码定位、影响分析、调用链追踪            │
│  特性：显式<thinking>推理链、轻量高效            │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  知识存储层                                       │
│  - NetworkX 图数据库（调用图、依赖图）           │
│  - ChromaDB/LanceDB（语义检索）                 │
│  - 文件系统（源代码、文档）                      │
└─────────────────────────────────────────────────┘
```

### 3.2 三位一体架构详解

#### 1. 知识底座（The Ground Truth）
**代码语义索引**：
- ✅ 使用 Tree-sitter 提取符号表（函数、类、变量）
- ✅ 提取 Slice/RPC 定义作为"锚点"
- ✅ 关联实现类、配置文件和调用方

**文档质量引擎**：
- ✅ 按照评分机制对 Confluence 和需求文档进行打标
- ✅ 评分权重：关联度 > 时效性 > 完整性

#### 2. 推理引擎（Explicit Reasoning Layer）
**🆕 小模型显式推理（trlm-135M）**：
- ✅ 三阶段训练：基础SFT → <thinking>推理SFT → DPO对齐
- ✅ 职责：任务规划、代码定位、影响范围分析
- ✅ 内存占用：~1GB（相比7B模型节省3-4GB）

**专家协作（LLM Orchestration）**：
- ✅ 千问-235B API：负责高难度任务
- ✅ 重构逻辑生成、复杂Bug根因分析、测试用例编写

#### 3. 知识图谱（Knowledge Graph）
**🆕 NetworkX 图数据库**：
- ✅ 存储代码拓扑结构（谁调用了谁、哪个类实现了哪个Slice）
- ✅ 结构化强、占用内存低、查询精准
- ✅ 200万行代码调用图约200MB内存

---

## 4. trlm-135M 方案详解

### 4.1 为什么选择 trlm-135M？

| 对比项 | trlm-135M | Qwen2.5-7B GGUF | 优势 |
|--------|-----------|-----------------|------|
| 模型大小 | ~500MB | ~4-5GB | **节省 2GB** |
| 内存占用 | ~1GB | ~4-5GB | **节省 3-4GB** |
| 推理速度（CPU） | 极快 | 中等 | **更快** |
| 训练成本 | 低（单GPU） | 高（多GPU） | **可行** |
| 专用能力 | 推理链 | 通用 | **更聚焦** |

**结论：** trlm-135M 在32GB内存环境下几乎可以"忽略不计"，专门做推理引擎极其合适！

### 4.2 trlm 三阶段训练设计

#### **阶段 1：基础对话 SFT（无思考链）**
```python
# 训练目标：让模型理解和生成内网对话
dataset = [
    {
        "question": "OrderService 的登录超时问题一般在哪里？",
        "answer": "通常在 auth-service 的 session 模块，检查 Redis 连接和超时配置。"
    },
    {
        "question": "payment-service 对账逻辑在哪个仓库？",
        "answer": "在 payment-core 仓库，路径 src/reconcile/ 下。"
    }
    # 从内部 Wiki、工单 QA、代码评审中抽取
]
```

#### **阶段 2：显式 <thinking> 推理 SFT**
```python
# 训练目标：让模型学会显式推理
sample = {
    "question": "修改 OrderService.syncStatus 接口，增加 retryCount 参数，影响范围？",
    "response": """<thinking>
1. 理解问题：修改接口参数，需要评估影响范围
2. 定位模块：OrderService 是核心订单服务
3. 查找依赖：
   - C++ 层：OrderServiceImpl.cpp
   - Java 层：OrderController 调用
   - 下游：PaymentService 依赖 OrderService
4. 查阅文档：需求文档 SYNC-123
5. 结论：影响 2 个服务，4 个接口
</thinking>

<answer>
受影响服务：
- order-service (订单服务)
- payment-service (支付服务)

关键接口：
- POST /api/order/syncStatus
- GET /api/payment/orderStatus

调用链：
OrderController -> OrderService.syncStatus -> PaymentService.callOrderStatus
</answer>"""
}
```

#### **阶段 3：DPO 偏好对齐**
```python
# 训练目标：让模型偏好高质量推理
preference_pairs = [
    {
        "question": "修改 OrderService.syncStatus 接口，影响范围？",
        "chosen": """<thinking>
1. 找到 Slice 定义：interface OrderService { void syncStatus(int retryCount); }
2. 查找 C++ 实现：OrderServiceImpl.cpp
3. 追踪调用方：Java 层 OrderController、PaymentService
4. 检查文档：需求 SYNC-123
5. 结论：影响 2 个服务，4 个接口
</thinking>

<answer>
受影响服务：order-service, payment-service
关键接口：/api/order/sync, /api/payment/orderStatus
风险等级：中
</answer>""",
        "rejected": """<thinking>
随便想想一下，可能有影响...
不确定具体哪些文件...</thinking>

<answer>
可能影响一些服务吧，需要人工确认。
</answer>"""
    }
]
```

### 4.3 内网知识推理引擎实现

```python
# backend/models/knowledge_retriever.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class InternalKnowledgeModel:
    """基于 trlm-135M 的内网知识推理引擎"""
    
    def __init__(self, model_path: str = "Shekswess/trlm-stage-2-sft-final-2"):
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,  # 节省内存
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    def query_with_reasoning(self, question: str) -> dict:
        """执行带显式推理的查询"""
        prompt = self._build_prompt(question)
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.1,  # 低温度保证稳定性
            do_sample=False
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        thinking, answer = self._parse_response(response)
        
        return {
            "thinking": thinking,
            "answer": answer,
            "raw_response": response
        }
    
    def _build_prompt(self, question: str) -> str:
        """构建推理提示词"""
        return f"""你是内网编程知识库专家，负责分析代码、架构、依赖和调用链。

问题：{question}

请按照以下格式回答：
<thinking>
1. 理解问题的核心
2. 从架构/代码中定位相关模块
3. 分析依赖关系和调用链
4. 整合相关信息
</thinking>

<answer>
{具体的服务名、文件路径、接口、调用链}
</answer>"""
```

---

## 5. 已实现功能清单（完整版）

### 5.1 核心功能（已完成）

#### 1. C++深度代码分析 - 380行cpp_analyzer.py
- ✅ 函数签名提取（返回类型、参数、修饰符）
- ✅ 类继承关系树
- ✅ 调用图构建（函数间调用关系）
- ✅ 内存泄漏检测（智能指针、未释放资源）
- ✅ 代码复杂度分析
- ✅ 设计模式识别

#### 2. Java解析器框架 - 600+行java_analyzer.py
- ✅ Spring Boot注解检测
- ✅ 依赖注入分析
- ✅ REST接口识别
- ✅ 调用链追踪
- ⏸️ **状态**：已创建，待集成到主流程

#### 3. 向量检索系统
- ✅ 代码切片向量化（函数级语义）
- ✅ 语义检索（Top-K匹配）
- ✅ 上下文增强（相关函数、类定义）
- ✅ 混合检索（向量+关键词）

#### 4. AI代码审查
- ✅ 内存管理检查
- ✅ 资源泄漏检测
- ✅ 接口设计评估
- ✅ 性能优化建议
- ✅ 安全漏洞扫描

#### 5. AI驱动的代码重构
- ✅ Extract Method（提取函数）
- ✅ Rename（重命名）
- ✅ Extract Class（提取类）
- ✅ 性能优化建议
- ✅ 批量重构支持

#### 6. 自动化测试生成
- ✅ GTest测试用例生成
- ✅ Catch2测试框架支持
- ✅ DocTest生成
- ✅ 边界条件覆盖
- ✅ Mock对象生成

#### 7. 路径映射系统 - 220行path_mapper.py
- ✅ 双向路径映射（归档↔开发目录）
- ✅ 优先级控制
- ✅ 启用/禁用管理
- ✅ 路径实时验证
- ✅ API端点：GET/POST/DELETE/TEST

#### 8. VSCode扩展 - 完整功能
- ✅ 主入口：extension.ts（180行）
- ✅ AI助手面板：AIAssistantPanel.ts
- ✅ CodeLens提供器：实时代码提示
- ✅ API客户端：APIClient.ts
- ✅ 本地分析器：C++/Java（轻量级）
- ✅ 快捷键：Ctrl+Shift+E/R/C/P
- ✅ 打包：cpp-ai-assistant-1.0.0.vsix（47KB）

### 5.2 API端点（16个 + 新增规划）

```
健康检查:
  GET  /health

代码分析:
  POST /api/parse
  POST /api/analyze
  POST /api/call-graph

代码审查:
  POST /api/review
  POST /api/review/files

代码重构:
  POST /api/refactor
  POST /api/refactor/suggestions

测试生成:
  POST /api/test
  POST /api/test/cases

向量检索:
  POST /api/search
  POST /api/search/similar

路径映射:
  GET    /api/path-mapping
  POST   /api/path-mapping
  DELETE /api/path-mapping
  POST   /api/path-mapping/test

🆕 知识推理:
  POST /api/knowledge/query
  POST /api/knowledge/analyze-impact
  POST /api/knowledge/build-graph
  GET  /api/knowledge/graph-stats
```

### 5.3 项目结构（完整版）

```
cpp-ai-assistant/
├── backend/
│   ├── main.py                 # FastAPI主应用（400+行）
│   ├── config.py               # 配置管理（含路径映射）
│   ├── parsers/
│   │   ├── cpp_analyzer.py     # C++解析器（380行）
│   │   ├── java_analyzer.py    # Java解析器（600+行）
│   │   └── code_entities.py    # 代码实体定义
│   ├── services/
│   │   ├── code_review.py      # 代码审查服务
│   │   ├── refactoring.py      # 重构建议服务
│   │   ├── test_generation.py  # 测试生成服务
│   │   ├── qwen_client.py      # 千问API客户端
│   │   └── knowledge_orchestrator.py  # 🆕 知识库编排器
│   ├── vectorstore/
│   │   ├── chroma_store.py     # ChromaDB封装
│   │   └── embedding_model.py  # Embedding模型
│   ├── knowledge/              # 🆕 知识库模块
│   │   ├── graph_store.py      # NetworkX图数据库
│   │   ├── knowledge_builder.py # 自动化知识构建
│   │   └── topic_aggregator.py # 主题化聚合
│   ├── models/                 # 🆕 模型加载
│   │   ├── knowledge_model.py  # trlm-135M封装
│   │   └── qwen_service.py     # 千问3-235B服务
│   ├── utils/
│   │   ├── path_mapper.py      # 路径映射（220行）
│   │   └── code_utils.py       # 代码工具函数
│   └── models/
│       ├── schemas.py          # Pydantic模型
│       └── requests.py         # API请求模型
├── vscode-extension/
│   ├── src/
│   │   ├── extension.ts        # 主入口
│   │   ├── panels/
│   │   │   ├── AIAssistantPanel.ts
│   │   │   └── KnowledgePanel.ts  # 🆕 知识推理面板
│   │   ├── providers/
│   │   │   ├── CodeLensProvider.ts
│   │   │   └── KnowledgeLensProvider.ts  # 🆕 知识提示
│   │   ├── services/
│   │   │   ├── APIClient.ts
│   │   │   └── KnowledgeClient.ts  # 🆕 知识API客户端
│   │   └── analyzer/
│   │       ├── LocalCppAnalyzer.ts
│   │       └── LocalJavaAnalyzer.py
│   ├── package.json
│   ├── tsconfig.json
│   └── cpp-ai-assistant-1.0.0.vsix
├── config/
│   ├── config.yaml
│   └── path-mapping.json
├── ext/
│   ├── 02-python-wheels/
│   ├── 08-models-embeddings/
│   └── 09-models-trlm/        # 🆕 trlm-135M模型
├── scripts/
│   ├── download_dependencies.py
│   ├── refresh_requirements.py
│   ├── package_for_vm.py
│   └── train_trlm.py          # 🆕 trlm训练脚本
├── training/                  # 🆕 训练数据目录
│   ├── stage1_sft/            # 基础对话数据
│   ├── stage2_thinking/       # 显式推理数据
│   └── stage3_dpo/            # 偏好对齐数据
├── requirements.txt
├── requirements-dev.txt
├── requirements-offline.txt
├── install.py
├── DEPLOYMENT.md
├── OFFLINE_DEPLOYMENT.md
├── 🆕 TRLM_TRAINING.md        # trlm训练指南
└── README.md
```

---

## 6. 实施路线图（trlm-135M 集成版）

### 🆕 阶段0：trlm-135M 基础验证（第1-2周）

#### 任务：下载并测试 trlm-135M 模型

**核心要求**：
1. 下载 trlm 三个阶段的检查点
2. 准备基础推理测试
3. 验证模型在32GB内存下的表现

**必须完成的任务**：
- [ ] 下载 Shekswess/trlm-stage-1-sft-final-2
- [ ] 下载 Shekswess/trlm-stage-2-sft-final-2
- [ ] 下载 Shekswess/trlm-stage-3-dpo-final-2
- [ ] 实现 `InternalKnowledgeModel` 基础类
- [ ] 编写测试脚本（10个内网场景）

**测试场景示例**：
```python
test_cases = [
    {
        "question": "OrderService 的登录超时问题一般在哪里？",
        "expected_keys": ["service", "module", "file"]
    },
    {
        "question": "payment-service 对账逻辑在哪个仓库？",
        "expected_keys": ["repository", "path"]
    },
    {
        "question": "修改 User.create 接口，影响范围？",
        "expected_keys": ["services", "interfaces", "risk"]
    }
]
```

**交付物**：
- `backend/models/knowledge_model.py`
- `tests/test_knowledge_model.py`
- 基础验证报告（内存占用、推理速度）

### 🆕 阶段1：trlm 定制化训练（第3-6周）

#### 任务：使用内网数据训练 trlm-135M

**阶段 1.1：数据准备（第1周）**
```python
# data_collection.py
class InternalDataCollector:
    """收集内网训练数据"""
    
    def collect_stage1_data(self) -> List[dict]:
        """收集基础对话数据"""
        # 从 Wiki、工单 FAQ、代码评审中抽取
        # 目标：100-200 条高质量对话
        pass
    
    def collect_stage2_data(self) -> List[dict]:
        """收集显式推理数据"""
        # 人工编写或半自动生成带 <thinking> 的样本
        # 目标：200-300 条推理样本
        pass
    
    def collect_stage3_data(self) -> List[dict]:
        """收集偏好对齐数据"""
        # 构造 chosen vs rejected 对
        # 目标：100-150 对
        pass
```

**阶段 1.2：三阶段训练（第2-4周）**
```bash
# 阶段1：基础SFT
python scripts/train_trlm.py \
    --stage 1 \
    --base_model Shekswess/trlm-stage-1-sft-final-2 \
    --data training/stage1_sft/ \
    --output_dir models/internal-stage1

# 阶段2：<thinking>推理SFT
python scripts/train_trlm.py \
    --stage 2 \
    --base_model models/internal-stage1 \
    --data training/stage2_thinking/ \
    --output_dir models/internal-stage2

# 阶段3：DPO对齐
python scripts/train_trlm.py \
    --stage 3 \
    --base_model models/internal-stage2 \
    --data training/stage3_dpo/ \
    --output_dir models/internal-final
```

**交付物**：
- 训练好的内部知识模型（`models/internal-final`）
- 训练日志和评估报告
- 数据集文档

### 🆕 阶段2：图数据库构建（第7-9周）

#### 任务：建立代码拓扑结构

**核心要求**：
1. 实现 NetworkX 图数据库
2. 解析 C++/Java 代码库，生成调用图
3. 建立 Slice/RPC 跨语言映射

**必须实现的功能**：
```python
# backend/knowledge/graph_store.py
class InternalGraphStore:
    """内网代码图数据库"""
    
    def add_service_dependency(self, dep_type: str, source: str, target: str, **attrs)
    def get_downstream(self, entity_name: str, max_depth: int = 3) -> List[dict]
    def get_upstream(self, entity_name: str, max_depth: int = 3) -> List[dict]
    def get_slice_implementations(self, slice_interface: str) -> List[dict]
    def get_call_chain(self, start: str, end: str) -> List[str]
    def save(self)  # 持久化到磁盘
    def load(self)  # 从磁盘加载
```

**自动化构建脚本**：
```python
# backend/knowledge/knowledge_builder.py
class InternalKnowledgeBuilder:
    """自动化构建内网知识库"""
    
    def build_full_knowledge_base(self):
        """构建完整的知识库"""
        self._parse_cpp_codebase()
        self._parse_java_codebase()
        self._parse_slice_definitions()
        self._parse_documentation()
        self._build_cross_language_mappings()
        self.graph_store.save()
```

**交付物**：
- `backend/knowledge/graph_store.py`
- `backend/knowledge/knowledge_builder.py`
- 图数据库文件（`data/graph_store.pkl`）

### 🆕 阶段3：小模型+大模型协作（第10-12周）

#### 任务：实现知识库编排器

**核心要求**：
1. 集成 trlm-135M 和 千问3-235B
2. 实现协作查询流程
3. 优化 Token 使用效率

**必须实现的功能**：
```python
# backend/services/knowledge_orchestrator.py
class KnowledgeOrchestrator:
    """知识库协作编排器"""
    
    async def analyze_impact(self, question: str) -> dict:
        """影响分析（小模型推理 + 大模型生成）"""
        # 步骤1：小模型推理（快速、精准）
        small_result = await self.small_model.query_with_reasoning(question)
        
        # 步骤2：从图数据库获取详细信息
        detailed_info = self._fetch_detailed_info(small_result['answer'])
        
        # 步骤3：大模型生成最终报告
        final_report = await self.large_model.generate_impact_report(
            thinking=small_result['thinking'],
            basic_info=small_result['answer'],
            detailed_info=detailed_info
        )
        
        return {
            "reasoning": small_result['thinking'],
            "basic_info": small_result['answer'],
            "detailed_info": detailed_info,
            "report": final_report
        }
```

**API端点**：
```python
# backend/main.py
@app.post("/api/knowledge/analyze-impact", response_model=ImpactAnalysisResponse)
async def analyze_impact(request: ImpactAnalysisRequest):
    """影响分析（小模型 + 大模型协作）"""
    return await knowledge_orchestrator.analyze_impact(request.question)
```

**交付物**：
- `backend/services/knowledge_orchestrator.py`
- API端点集成
- VSCode 扩展适配

### 🆕 阶段4：VSCode 扩展增强（第13-15周）

#### 任务：新增知识库推理功能

**核心要求**：
1. 新增"知识推理"面板
2. 显示 <thinking> 推理过程
3. 可视化调用链

**必须实现的功能**：
```typescript
// vscode-extension/src/panels/KnowledgePanel.ts
export class KnowledgePanel {
    showReasoning(question: string, result: ImpactAnalysisResult) {
        // 显示推理过程
        this.webviewPanel.webview.html = `
            <div class="thinking-section">
                <h3>推理过程</h3>
                <pre>${result.reasoning}</pre>
            </div>
            <div class="answer-section">
                <h3>基本信息</h3>
                <ul>
                    ${result.basic_info.services.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
            <div class="report-section">
                <h3>详细报告</h3>
                <div class="markdown">${this._renderMarkdown(result.report)}</div>
            </div>
        `;
    }
}
```

**新增快捷键**：
- `Ctrl+Shift+K` - 知识库推理
- `Ctrl+Shift+I` - 影响分析

**交付物**：
- `vscode-extension/src/panels/KnowledgePanel.ts`
- `vscode-extension/src/services/KnowledgeClient.ts`
- 更新 `package.json`

---

## 7. trlm 训练数据规范

### 7.1 阶段 1 数据格式（基础对话）

```json
{
  "question": "OrderService 的登录超时问题一般在哪里？",
  "answer": "通常在 auth-service 的 session 模块，检查 Redis 连接和超时配置。"
}
```

**数据来源**：
- 内部 Wiki FAQ
- Jira/禅道工单讨论
- 代码评审记录
- 团队知识分享记录

**质量要求**：
- ✅ 问题清晰、具体
- ✅ 答案准确、可操作
- ✅ 使用内部术语（服务名、模块名）
- ✅ 避免模糊回答

### 7.2 阶段 2 数据格式（显式推理）

```json
{
  "question": "修改 OrderService.syncStatus 接口，增加 retryCount 参数，影响范围？",
  "response": "<thinking>\n1. 理解问题：修改接口参数，需要评估影响范围\n2. 定位模块：OrderService 是核心订单服务\n3. 查找依赖：\n   - C++ 层：OrderServiceImpl.cpp\n   - Java 层：OrderController 调用\n   - 下游：PaymentService 依赖 OrderService\n4. 查阅文档：需求文档 SYNC-123\n5. 结论：影响 2 个服务，4 个接口\n</thinking>\n\n<answer>\n受影响服务：\n- order-service (订单服务)\n- payment-service (支付服务)\n\n关键接口：\n- POST /api/order/syncStatus\n- GET /api/payment/orderStatus\n\n调用链：\nOrderController -> OrderService.syncStatus -> PaymentService.callOrderStatus\n</answer>"
}
```

**推理模板**：
```
<thinking>
1. 理解问题的核心
2. 从架构/代码中定位相关模块
3. 分析依赖关系和调用链
4. 查阅相关文档
5. 整合相关信息
</thinking>

<answer>
{具体的服务名、文件路径、接口、调用链}
</answer>
```

**数据规范**：
- ✅ 推理步骤清晰（1-5步）
- ✅ 每步有明确目的
- ✅ 答案结构化（服务、接口、调用链）
- ✅ 使用实际的内部命名

### 7.3 阶段 3 数据格式（偏好对齐）

```json
{
  "question": "修改 OrderService.syncStatus 接口，影响范围？",
  "chosen": "<thinking>\n1. 找到 Slice 定义：interface OrderService { void syncStatus(int retryCount); }\n2. 查找 C++ 实现：OrderServiceImpl.cpp\n3. 追踪调用方：Java 层 OrderController、PaymentService\n4. 检查文档：需求 SYNC-123\n5. 结论：影响 2 个服务，4 个接口\n</thinking>\n\n<answer>\n受影响服务：order-service, payment-service\n关键接口：/api/order/sync, /api/payment/orderStatus\n风险等级：中\n</answer>",
  "rejected": "<thinking>\n随便想想一下，可能有影响...\n不确定具体哪些文件...</thinking>\n\n<answer>\n可能影响一些服务吧，需要人工确认。\n</answer>"
}
```

**选择标准**：
- **chosen**：推理逻辑清晰、步骤完整、答案准确
- **rejected**：推理模糊、步骤缺失、答案不确定

---

## 8. 性能优化与内存管理

### 8.1 trlm-135M 内存优化

```python
# backend/models/knowledge_model.py
class InternalKnowledgeModel:
    def __init__(self):
        # 使用半精度浮点数
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # 启用量化（CPU 环境）
        if torch.cuda.is_available():
            self.model = self.model.quantize(
                bits=4,  # 4-bit量化
                group_size=128
            )
    
    def query_with_reasoning(self, question: str):
        # 批量推理以节省内存
        inputs = self.tokenizer(question, return_tensors="pt")
        with torch.no_grad():  # 禁用梯度计算
            outputs = self.model.generate(**inputs, max_new_tokens=512)
        
        # 显式释放内存
        del inputs
        torch.cuda.empty_cache()
        
        return self._parse_response(outputs)
```

### 8.2 图数据库内存优化

```python
# backend/knowledge/graph_store.py
class InternalGraphStore:
    def __init__(self):
        # 使用稀疏图（如果适用）
        self.graph = nx.DiGraph()
        self.use_sparse = len(self.graph.nodes) > 10000
    
    def save(self):
        """压缩保存"""
        # 使用 pickle + gzip 压缩
        import gzip
        with gzip.open(self.persist_path, 'wb') as f:
            pickle.dump({'graph': self.graph}, f)
    
    def load_subgraph(self, nodes: List[str]):
        """按需加载子图"""
        # 只加载相关的子图，节省内存
        subgraph = self.graph.subgraph(nodes)
        return subgraph
```

### 8.3 Token 使用优化

```python
# backend/services/knowledge_orchestrator.py
class KnowledgeOrchestrator:
    def build_context(self, basic_info: dict, max_tokens: int = 128000):
        """智能上下文压缩"""
        
        # 优先级计算
        priority_scores = {
            'services': 100,
            'interfaces': 90,
            'call_chain': 80,
            'documents': 60
        }
        
        # 动态裁剪
        selected = []
        used_tokens = 0
        
        for key, score in sorted(priority_scores.items(), key=lambda x: x[1], reverse=True):
            if key not in basic_info:
                continue
            
            content = basic_info[key]
            estimated_tokens = len(str(content).split())
            
            if used_tokens + estimated_tokens > max_tokens * 0.8:
                # 截断
                content = str(content)[:max_tokens - used_tokens]
            
            selected.append((key, content))
            used_tokens += estimated_tokens
        
        return "\n\n".join(f"# {name}\n{content}" for name, content in selected)
```

---

## 9. 质量标准（必须满足）

### 9.1 代码质量
- ✅ 类型注解覆盖率 > 90%
- ✅ 测试覆盖率 > 80%
- ✅ 通过mypy类型检查
- ✅ 通过ruff代码检查
- ✅ 遵循PEP 8风格指南

### 9.2 性能标准
- ✅ 单文件解析 < 1s
- ✅ API响应 < 2s（P95）
- ✅ 向量检索 < 500ms
- ✅ trlm-135M 推理 < 1s（CPU）
- ✅ 千问3-235B 生成 < 10s
- ✅ 图数据库查询 < 500ms
- ✅ VSCode扩展启动 < 500ms
- ✅ 总内存占用 < 24GB（峰值）

### 9.3 文档标准
- ✅ 所有公共API有docstring
- ✅ README包含快速开始指南
- ✅ 有完整的部署文档
- ✅ 有trlm训练指南
- ✅ 有troubleshooting章节
- ✅ 代码关键逻辑有注释

---

## 10. 常见陷阱与解决方案

### 陷阱1：trlm 训练数据质量
**问题**：低质量数据导致模型推理混乱

**原因**：未人工审核样本、推理步骤不规范

**解决方案**：
```python
# 数据质量控制
def validate_sample(sample: dict) -> bool:
    """验证训练样本质量"""
    # 检查 <thinking> 标签完整性
    if '<thinking>' not in sample['response'] or '</thinking>' not in sample['response']:
        return False
    
    # 检查推理步骤数量（建议3-7步）
    thinking = sample['response'].split('<thinking>')[1].split('</thinking>')[0]
    steps = [s for s in thinking.split('\n') if s.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.'))]
    if len(steps) < 3 or len(steps) > 7:
        return False
    
    # 检查答案包含内部术语
    internal_terms = ['service', 'interface', 'repository', 'package']
    if not any(term in sample['answer'].lower() for term in internal_terms):
        return False
    
    return True
```

### 陷阱2：图数据库内存爆炸
**问题**：200万行代码的调用图占用过多内存

**原因**：未使用高效数据结构、全量加载

**解决方案**：
```python
# 分片加载
class SlicedGraphStore:
    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
        self.chunks = {}  # {chunk_id: subgraph}
    
    def get_chunk(self, node: str) -> nx.DiGraph:
        """获取节点所在分片"""
        chunk_id = hash(node) % 10
        return self.chunks.get(chunk_id)
```

### 陷阱3：小模型推理不稳定
**问题**：trlm-135M 输出格式不一致

**原因**：temperature 设置过高、prompt 模板不统一

**解决方案**：
```python
# 强制格式约束
def format_output(prompt: str, response: str) -> dict:
    """标准化输出格式"""
    # 使用正则提取 <thinking> 和 <answer>
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
    answer_match = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
    
    if not thinking_match or not answer_match:
        # 格式错误，重新生成
        return self._retry_generation(prompt)
    
    return {
        "thinking": thinking_match.group(1).strip(),
        "answer": answer_match.group(1).strip()
    }
```

### 陷阱4：Token 浪费
**问题**：每次查询都向大模型喂入大量上下文

**原因**：未实现"骨架优先"策略

**解决方案**：
```python
# 两阶段查询
class TwoStageQuery:
    def query(self, question: str):
        # 阶段1：小模型生成骨架（只用签名）
        skeleton = self.small_model.query_with_reasoning(question)
        
        # 阶段2：根据骨架需求，动态加载详细代码
        detailed_context = self._load_detailed_context(skeleton['answer'])
        
        # 阶段3：大模型生成最终方案
        final_result = self.large_model.generate(skeleton, detailed_context)
        
        return final_result
```

---

## 11. 验收清单

### 11.1 功能验收
- [ ] trlm-135M 在32GB内存下稳定运行
- [ ] trlm-135M 推理准确率 > 80%（内网场景）
- [ ] 图数据库支持 200 万行代码
- [ ] 图数据库查询延迟 < 500ms
- [ ] 小模型+大模型协作完整流程可用
- [ ] C++代码解析准确率 > 95%
- [ ] 代码审查发现真实问题 > 80%
- [ ] 向量检索相关性 > 85%
- [ ] VSCode扩展所有功能正常
- [ ] 离线部署100%成功
- [ ] 路径映射功能正常工作
- [ ] 测试生成覆盖边界条件

### 11.2 性能验收
- [ ] trlm-135M 推理 < 1s（CPU）
- [ ] 千问3-235B 生成 < 10s
- [ ] 单文件解析 < 1s
- [ ] API响应 < 2s（P95）
- [ ] 向量检索 < 500ms
- [ ] 图数据库查询 < 500ms
- [ ] VSCode扩展启动 < 500ms
- [ ] 内存占用 < 24GB（峰值）
- [ ] 并发支持50+请求

### 11.3 文档验收
- [ ] README.md完整且清晰
- [ ] TRLM_TRAINING.md 完整的训练指南
- [ ] API文档齐全（包含响应示例）
- [ ] 部署文档清晰可操作
- [ ] 故障排查覆盖常见问题
- [ ] 代码关键逻辑有注释

### 11.4 代码质量验收
- [ ] 所有Python文件通过mypy检查
- [ ] 所有TypeScript文件编译无错误
- [ ] 测试覆盖率 > 80%
- [ ] 无已知安全漏洞
- [ ] Git提交信息规范

### 11.5 训练验收
- [ ] 阶段 1 SFT 数据 >= 100 条
- [ ] 阶段 2 <thinking> 数据 >= 200 条
- [ ] 阶段 3 DPO 数据 >= 100 对
- [ ] 训练日志完整
- [ ] 评估指标达标（准确率、召回率）

---

## 12. 附录

### 12.1 推荐开发工具
- **IDE**: VSCode + Pylance
- **调试**: Python Debugger + Chrome DevTools (VSCode扩展)
- **测试**: pytest + pytest-watch
- **代码质量**: ruff + mypy + black
- **文档**: Sphinx + MkDocs
- **模型训练**: Hugging Face Transformers + PeFT

### 12.2 有用的资源
- trlm 论文: [Tiny Reasoning Language Model](https://arxiv.org/...)
- Tree-sitter文档: https://tree-sitter.github.io/tree-sitter/
- FastAPI文档: https://fastapi.tiangolo.com/
- ChromaDB文档: https://docs.trychroma.com/
- NetworkX文档: https://networkx.org/
- VSCode扩展API: https://code.visualstudio.com/api
- 千问API文档: 企业内部文档
- Hugging Face: https://huggingface.co/

### 12.3 常用命令

```bash
# 后端开发
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload

# trlm 训练
python scripts/train_trlm.py --stage 1 --data training/stage1_sft/
python scripts/train_trlm.py --stage 2 --data training/stage2_thinking/
python scripts/train_trlm.py --stage 3 --data training/stage3_dpo/

# 知识库构建
python scripts/build_knowledge.py --code-dir ./internal_repos --output ./data/graph_store.pkl

# 运行测试
pytest tests/ -v --cov=backend
pytest --watch tests/

# 代码格式化
black backend/
ruff check backend/ --fix
mypy backend/

# VSCode扩展开发
cd vscode-extension
npm install
npm run compile
npm run watch
npm run package

# 离线部署
python scripts/download_dependencies.py
python scripts/package_for_vm.py
python install.py
```

---

## 13. 快速开始

### 13.1 本地测试 trlm-135M

```bash
# 1. 安装依赖
pip install transformers torch

# 2. 下载模型
python scripts/download_trlm.py

# 3. 运行测试
python tests/test_knowledge_model.py
```

### 13.2 启动完整系统

```bash
# 1. 启动后端
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 2. 安装 VSCode 扩展
code --install-extension vscode-extension/cpp-ai-assistant-1.0.0.vsix

# 3. 配置 API 地址
# VSCode 设置 -> cppAIAssistant.apiEndpoint -> http://localhost:8000
```

---

## 结语

这份指南提供了一个完整的、可实施的路径，用于构建基于 trlm-135M 的内网知识库推理系统。通过三阶段训练和显式推理标签，小模型能够在 32GB 内存环境下高效运行，与千问3-235B 大模型协作，提供精准的代码分析和影响评估。

**关键成功因素**：
1. 严格遵循三阶段训练规范
2. 高质量的内网训练数据
3. 图数据库优化（NetworkX）
4. 小模型+大模型协作策略
5. Token 使用效率优化
6. 持续迭代和反馈收集

**下一步行动**：
1. **立即下载 trlm-135M 基础模型进行测试**
2. 开始收集内网对话数据（Wiki、工单 FAQ）
3. 准备带 <thinking> 的推理样本
4. 切换到 ACT MODE 开始实施！

祝项目顺利！🚀

---

**文档维护**：
- 最后更新：2026-02-08
- 版本：2.0.0（集成 trlm-135M）
- 维护者：Cline

**变更历史**：
- v2.0.0 (2026-02-08): 集成 trlm-135M 方案，新增知识推理功能
- v1.0.0 (2026-02-08): 初始版本

**反馈与改进**：
如有问题或建议，请通过Git Issues提交。