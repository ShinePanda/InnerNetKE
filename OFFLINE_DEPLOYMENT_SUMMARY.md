# C++ AI Assistant - 离线部署指南

> Python版本: **3.11.9**
> 更新日期: 2025-01-22
> 作者: Matrix Agent

---

## 目录

1. [概述](#概述)
2. [系统要求](#系统要求)
3. [项目结构](#项目结构)
4. [快速部署](#快速部署)
5. [离线安装步骤](#离线安装步骤)
6. [验证部署](#验证部署)
7. [配置说明](#配置说明)
8. [API使用指南](#api使用指南)
9. [故障排除](#故障排除)
10. [维护指南](#维护指南)
11. [常见问题](#常见问题faq)

---

## 概述

本文档详细介绍如何在**完全内网（Air-gapped）环境**下部署 C++ AI Assistant。所有依赖项已预先下载到本地目录，安装过程无需互联网连接。

### 核心组件

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | **3.11.9** | 后端运行时 |
| FastAPI | 最新版 | Web 框架 |
| ChromaDB | 0.5.4 | 向量数据库 |
| tree-sitter | 0.21.3 | C++/ICE 代码解析 |
| uvicorn | 最新版 | ASGI 服务器 |

---

## 系统要求

### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|----------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 10GB | 30GB+ SSD |

### 软件要求

- **操作系统**: Windows Server 2019 / Windows 10/11 (x64)
- **Python**: 3.11.9 (推荐)
- **Node.js**: 18+ (可选，用于VSCode扩展)

---

## 项目结构

```
cpp-ai-assistant/
├── backend/                      # Python 后端
│   ├── main.py                 # 服务入口点
│   ├── config.py               # 配置加载
│   ├── api/                    # API路由
│   ├── parsers/                # 代码解析器
│   │   ├── cpp_analyzer.py     # C++ 代码分析
│   │   ├── ice_analyzer.py    # ICE Slice 协议解析
│   │   └── java_analyzer.py    # Java 代码分析
│   ├── services/               # AI 服务
│   ├── vectorstore/            # 向量存储
│   └── utils/                  # 工具函数
├── ext/                         # 离线依赖包
│   ├── 02-python-wheels/       # Python 预编译包 (.whl)
│   └── ...                     # 其他离线资源
├── data/                        # 数据目录
│   ├── repos/                  # 代码仓库
│   ├── docs/                   # 文档
│   └── indexes/                # 向量索引
├── config.yaml                 # 主配置文件
├── requirements.txt            # Python 依赖清单
└── start.bat                   # 启动脚本
```

---

## 快速部署

### 步骤1: 安装Python依赖

```bash
# 进入项目目录
cd D:\cpp-ai-assistant

# 设置PYTHONPATH
$env:PYTHONPATH = "D:\cpp-ai-assistant"

# 安装Python包 (使用预下载的whl)
pip install --no-index --find-links=ext/02-python-wheels -r requirements.txt

# 或直接安装whl
pip install ext/02-python-wheels/*.whl --no-deps
```

### 步骤2: 启动服务

```bash
# 方式1: 使用模块方式 (推荐)
python -m backend.main

# 方式2: 使用uvicorn
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 方式3: 直接运行main.py
python backend/main.py
```

> ⚠️ **注意**: 必须设置 `PYTHONPATH` 环境变量指向项目根目录

### 步骤3: 验证

```powershell
# 测试健康检查
Invoke-WebRequest -Uri "http://localhost:8000/health"

# 或使用curl
curl http://localhost:8000/health
```

---

## 离线安装步骤

### 方式A: 使用预下载的whl包 (推荐)

项目已包含预下载的依赖包在 `ext/02-python-wheels/` 目录：

```bash
# 安装所有whl
pip install ext/02-python-wheels/*.whl --no-deps

# 或使用requirements.txt (自动查找whl)
pip install --no-index --find-links=ext/02-python-wheels -r requirements.txt
```

### 方式B: 自行下载whl包

如需更新依赖，在有网络的机器上：

```bash
# 下载所有依赖到指定目录
pip download -r requirements.txt --dest ./ext/02-python-wheels --only-binary=:all:

# 下载后拷贝整个ext目录到目标机器
```

### 核心依赖包说明

| 目录 | 内容 | 说明 |
|------|------|------|
| `ext/02-python-wheels/` | Python .whl 包 | 包含 chromadb, fastapi, uvicorn 等 |
| `ext/07-tools-tree-sitter/` | tree-sitter 工具 | C++/C/Java 语法解析 |
| `ext/08-models-embeddings/` | 嵌入模型 | SentenceTransformer 模型 |

---

## 验证部署

### 1. 健康检查

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health"
```

预期响应：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "qwen": true,
    "vector_store": true,
    "cpp_parser": true,
    "ice_parser": true
  }
}
```

### 2. 验证 Python 依赖

```bash
# 检查关键模块
python -c "import fastapi, uvicorn, yaml, chromadb; print('Core OK')"

# 检查 tree-sitter
python -c "import tree_sitter; print(tree_sitter.Language.version())"
```

### 3. API 文档

访问 `http://localhost:8000/docs` 查看 Swagger UI

---

## 配置说明

### 配置文件位置

- 主配置: `config.yaml` (推荐，使用 YAML 注释方便)
- 备选: `config.json`

### 关键配置项

```yaml
# 服务配置
server:
  host: "0.0.0.0"
  port: 8000

# Qwen模型配置 (如需使用AI功能)
qwen:
  api_key: "${QWEN_API_KEY}"  # 建议使用环境变量
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-plus"

# ChromaDB 配置 (可选)
chromadb:
  persist_directory: "./data/indexes"
  collection_name: "code_entities"

# Tree-sitter 配置
tree_sitter:
  grammar_path: "./ext/07-tools-tree-sitter"
  languages: ["cpp", "c", "python", "java", "ice"]

# 日志配置
logging:
  level: "INFO"
  file: "./logs/app.log"
```

---

## API使用指南

### 核心 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger API 文档 |
| `/api/v1/analyze` | POST | C++ 代码分析 |
| `/api/v1/ice/parse` | POST | ICE Slice 文件解析 |
| `/api/v1/refactor` | POST | 代码重构 |
| `/api/v1/review` | POST | 代码审查 |
| `/api/v1/search` | GET | 向量搜索 |

### 示例请求

```bash
# 代码分析
curl -X POST http://localhost:8000/api/v1/analyze ^
  -H "Content-Type: application/json" ^
  -d "{\"code\": \"void hello() { printf(\"Hello\"); }\"}"

# ICE Slice 解析
curl -X POST http://localhost:8000/api/v1/ice/parse ^
  -H "Content-Type: application/json" ^
  -d "{\"content\": \"module Demo { interface Hello { void say(); } }\"}"

# 代码搜索
curl "http://localhost:8000/api/v1/search?query=function+definition"
```

---

## 故障排除

### 问题1: ModuleNotFoundError

**症状**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
# 使用离线whl安装缺失模块
pip install --no-index --find-links=ext/02-python-wheels xxx
```

### 问题2: chromadb 加载失败

**症状**: `Failed to load SentenceTransformer` 或 `ModuleNotFoundError: No module named 'chromadb'`

**解决**: 这是可选功能，不影响基本API使用。如需完整功能：
```bash
# 安装预下载的 chromadb
pip install ext/02-python-wheels/chromadb-*.whl --no-deps
pip install sentence-transformers
```

### 问题3: tree-sitter 版本不兼容

**症状**: `TypeError: tree_sitter.Query() takes no arguments`

**解决**: 项目已处理兼容问题，如仍有问题：
```bash
pip install tree-sitter==0.21.3
pip install tree-sitter-languages==1.10.2
```

### 问题4: ImportError: No module named 'backend'

**症状**: `ModuleNotFoundError: No module named 'backend'`

**解决**: 设置 PYTHONPATH 环境变量
```powershell
# PowerShell
$env:PYTHONPATH = "D:\cpp-ai-assistant"

# CMD
set PYTHONPATH=D:\cpp-ai-assistant

# 永久设置 (系统属性 -> 高级 -> 环境变量)
```

### 问题5: 服务启动失败 (端口占用)

**症状**: `OSError: [Errno 10048] Only one usage of each socket address`

**解决**:
```bash
# 查看端口占用
netstat -ano | findstr 8000

# 关闭占用进程
taskkill /PID <PID> /F
```

### 问题6: YAML 解析错误

**症状**: `yaml.scanner.ScannerError` 或 Import 警告

**解决**: 确保 config.yaml 格式正确，缩进使用空格

---

## 维护指南

### 更新依赖

1. 下载新版本依赖包到 `ext/02-python-wheels/` 目录
2. 重新运行安装命令
3. 重启服务

### 备份数据

```bash
# 备份向量索引
robocopy /E /ZB /R:3 /W:5 "data\indexes" "backup\indexes"

# 备份模型
robocopy /E /ZB /R:3 /W:5 "data\models" "backup\models"
```

### 日志轮转

日志文件自动生成在 `logs/` 目录，定期清理：

```bash
# 清理 7 天前的日志 (PowerShell)
Get-ChildItem -Path logs -Filter *.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
```

---

## 常见问题 (FAQ)

**Q: 支持哪些 Python 版本？**
A: 推荐 Python 3.11.9，已测试兼容性

**Q: 是否可以在 Linux/macOS 运行？**
A: 当前版本针对 Windows 优化，Linux/macOS 需调整路径分隔符

**Q: 内存不足怎么办？**
A: 减少 HNSW 索引参数，或不使用向量功能（基础API不受影响）

**Q: 首次启动很慢？**
A: 首次启动会加载嵌入模型（约1-2GB），后续启动使用缓存

**Q: 如何完全卸载？**
A: 删除安装目录即可，无系统级安装

**Q: ICE 解析器支持哪些语法？**
A: 支持 module, interface, struct, enum, sequence, dictionary, exception, const

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2025-01-20 | 初始发布 |
| 1.0.1 | 2025-01-21 | 修复安装脚本 |
| 1.0.2 | 2025-01-22 | 添加故障排除指南，整合多文档内容 |

---

## 技术支持

如遇到问题，请收集以下信息：

1. 安装/错误日志文件
2. 系统信息：`systeminfo`
3. Python 版本：`python --version`
4. 错误截图或完整错误信息

联系技术支持时，请提供以上信息及详细的故障描述。

---

*本文档整合自 DEPLOYMENT.md, DEPLOYMENT_GUIDE.md, OFFLINE_DEPLOYMENT.md*
