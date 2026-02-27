# C++ AI Assistant - 内网离线部署清单

> 生成时间: 2026-02-07 20:10
> Python版本: 3.11.9
> Node.js版本: 18.19.0
> 总大小: ~2.6 GB

---

## 📦 已下载的完整依赖清单

### 1. Python Wheel包 (63个)

**位置**: `ext/02-python-wheels/`

**核心依赖**:
- `fastapi-0.128.4-py3-none-any.whl` - Web框架
- `uvicorn-0.40.0-py3-none-any.whl` - ASGI服务器
- `pydantic-2.12.5-py3-none-any.whl` - 数据验证
- `torch-2.10.0-cp311-cp311-win_amd64.whl` - 深度学习框架
- `transformers-5.1.0-py3-none-any.whl` - 千问兼容接口
- `sentence_transformers-5.2.2-py3-none-any.whl` - 嵌入模型

**数据处理**:
- `pandas-3.0.0-cp311-cp311-win_amd64.whl` - 数据分析
- `numpy-2.4.2-cp311-cp311-win_amd64.whl` - 数值计算
- `lxml-6.0.2-cp311-cp311-win_amd64.whl` - XML/HTML解析

**其他工具**:
- `apscheduler-3.11.2-py3-none-any.whl` - 定时任务
- `watchdog-6.0.0-py3-none-win_amd64.whl` - 文件监控
- `httpx-0.28.1-py3-none-any.whl` - HTTP客户端

### 2. NPM包 (9个)

**位置**: `ext/03-nodejs-npm/`

**TypeScript工具**:
- `typescript-5.3.3.tgz`
- `types-node-20.11.0.tgz`
- `types-vscode-1.85.0.tgz`
- `vsce-2.15.0.tgz`

**MCP服务器** (6个):
1. ✅ `modelcontextprotocol-server-memory-x.x.x.tgz` - 内存存储
2. ✅ `modelcontextprotocol-server-sequential-thinking-x.x.x.tgz` - 顺序推理
3. ✅ `modelcontextprotocol-server-filesystem-x.x.x.tgz` - 文件系统
4. ✅ `modelcontextprotocol-server-puppeteer-x.x.x.tgz` - 浏览器自动化
5. ✅ `arabold-docs-mcp-server-x.x.x.tgz` - 文档处理
6. ✅ `buger-docs-mcp-x.x.x.tgz` - 文档搜索

### 3. 嵌入模型

**位置**: `ext/08-models-embeddings/sentence-transformers-all-MiniLM-L6-v2/`

**模型文件**:
- `model.safetensors` (87.3 MB) - 模型权重
- `tokenizer.json` (711 KB) - 分词器
- `config.json` (774 B) - 配置文件
- `1_Pooling/` - 池化层
- `2_Normalize/` - 归一化层

**模型规格**:
- 向量维度: 384
- 最大序列长度: 512
- 适用场景: 代码检索、相似性匹配

### 4. 运行时

**位置**:
- Python: `ext/05-runtime-python/python-3.11.9-amd64.exe`
- Node.js: `ext/06-runtime-nodejs/node-v18.19.0-x64.msi`

### 5. Tree-sitter

**安装方式**: 通过Python包 `pip install tree-sitter`
**支持语言**: C++, Java, Python, JavaScript, TypeScript等

---

## 🚀 内网部署步骤

### 准备阶段（在外网环境）

1. **打包项目**
```powershell
# 方法1: PowerShell压缩
Compress-Archive -Path "projects\3\cpp-ai-assistant" -DestinationPath "cpp-ai-assistant-offline.zip" -Force

# 方法2: 7-Zip（推荐，更快）
7z a cpp-ai-assistant-offline.zip projects\3\cpp-ai-assistant\
```

2. **传输到内网**
- 使用U盘、内网共享或其他安全方式
- 确保完整传输 `cpp-ai-assistant-offline.zip`

### 部署阶段（在内网环境）

#### 步骤1: 解压项目

```powershell
# 解压到D盘根目录
Expand-Archive -Path "cpp-ai-assistant-offline.zip" -DestinationPath "D:\" -Force

# 进入项目目录
cd D:\cpp-ai-assistant
```

#### 步骤2: 安装Python运行时

```powershell
# 安装Python 3.11.9
.\ext\05-runtime-python\python-3.11.9-amd64.exe /passive InstallAllUsers=0 PrependPath=1 Include_test=0

# 验证安装
python --version
# 应显示: Python 3.11.9
```

#### 步骤3: 安装Node.js运行时

```powershell
# 安装Node.js 18.19.0
msiexec /i .\ext\06-runtime-nodejs\node-v18.19.0-x64.msi /passive

# 验证安装
node --version
# 应显示: v18.19.0
npm --version
# 应显示某个版本号
```

#### 步骤4: 安装Python依赖

```powershell
# 运行安装脚本
python install.py

# 或手动安装wheel包
cd ext\02-python-wheels
pip install *.whl --no-index
```

#### 步骤5: 配置环境

创建 `.env` 文件:

```env
# 千问企业版API配置
QWEN_API_BASE=http://internal-qwen.example.com/v1
QWEN_API_KEY=your-api-key-here
QWEN_MODEL=qwen-3-235b

# 嵌入模型路径（本地）
EMBEDDING_MODEL_PATH=./ext/08-models-embeddings/sentence-transformers-all-MiniLM-L6-v2

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO

# 代码库配置
CODE_REPOSITORIES=D:/repos
MAX_FILE_SIZE=10485760  # 10MB
```

#### 步骤6: 配置MCP服务器

创建 `.config/mcp.json`:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "D:/repos"]
    },
    "arabold-docs": {
      "command": "npx",
      "args": ["-y", "@arabold/docs-mcp-server"],
      "env": {
        "DOCS_PATH": "./docs"
      }
    }
  }
}
```

#### 步骤7: 启动服务

```powershell
# 启动FastAPI服务器
python backend/main.py

# 或使用uvicorn直接启动
uvicorn server_main:app --host 0.0.0.0 --port 8000
```

服务启动后:
- API地址: `http://localhost:8000`
- 文档地址: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/health`

---

## 🔍 部署验证

### 1. 验证Python包

```powershell
python -c "import fastapi; import torch; import transformers; import sentence_transformers; print('✓ 所有Python包安装成功')"
```

### 2. 验证嵌入模型

```powershell
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('./ext/08-models-embeddings/sentence-transformers-all-MiniLM-L6-v2'); embeddings = model.encode(['测试文本']); print(f'✓ 模型加载成功，向量维度: {embeddings.shape[1]}')"
```

### 3. 验证MCP服务器

```powershell
# 测试Memory服务器
npx -y @modelcontextprotocol/server-memory --help

# 测试文件系统服务器
npx -y @modelcontextprotocol/server-filesystem --help
```

### 4. 验证API服务

```powershell
# 健康检查
curl http://localhost:8000/health

# 测试分析接口
curl -X POST http://localhost:8000/analyze/code -H "Content-Type: application/json" -d '{"code": "int main() { return 0; }", "language": "cpp"}'
```

---

## 📊 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4核 | 16核 |
| 内存 | 16 GB | 32 GB |
| 硬盘 | 5 GB可用 | 1 TB |
| 网络 | 内网 | 内网 |

### 软件要求

- **操作系统**: Windows Server 2019 或更高
- **Python**: 3.11.9（离线安装）
- **Node.js**: 18.19.0（离线安装）
- **Git**: 用于代码仓库版本控制

---

## 📁 目录结构

```
cpp-ai-assistant/
├── ext/                                        # 离线资源
│   ├── 01-python-pip/                          # Python源码包
│   ├── 02-python-wheels/                       # 63个wheel文件
│   ├── 03-nodejs-npm/                          # 9个npm包
│   ├── 05-runtime-python/                      # Python安装程序
│   ├── 06-runtime-nodejs/                      # Node.js安装程序
│   ├── 07-tools-tree-sitter/                   # Tree-sitter（Python包）
│   ├── 08-models-embeddings/                   # 嵌入模型
│   │   └── sentence-transformers-all-MiniLM-L6-v2/
│   │       ├── model.safetensors               # 87.3 MB
│   │       ├── tokenizer.json                  # 711 KB
│   │       └── ...
│   └── manifest.json                           # 依赖清单
├── server_main.py                              # 服务器主程序
├── install.py                                  # 安装脚本
├── download_dependencies.py                    # 下载脚本
├── requirements-py3-universal.txt              # Python依赖清单
├── .env                                        # 环境配置（创建）
├── .config/mcp.json                            # MCP配置（创建）
└── docs/                                       # 文档
    ├── MCP_SERVERS_SETUP.md
    └── API_REFERENCE.md
```

---

## ⚠️ 常见问题

### Q1: pip安装时提示"已存在但版本不对"

```powershell
# 强制重新安装
pip install --force-reinstall --no-index --no-deps <package-name>.whl
```

### Q2: Node.js安装后npm命令找不到

```powershell
# 重启PowerShell或添加环境变量
$env:Path += ";C:\Program Files\nodejs"
```

### Q3: 嵌入模型加载失败

```powershell
# 检查模型路径是否正确
Get-ChildItem .\ext\08-models-embeddings\ -Recurse

# 确保所有文件完整
```

### Q4: MCP服务器无法启动

```powershell
# 检查npm包是否正确安装
cd ext\03-nodejs-npm
npm pack <package-name> --pack-destination ../temp

# 或直接测试
npx -y <package-name> --help
```

### Q5: 服务启动后无法访问

```powershell
# 检查防火墙规则
New-NetFirewallRule -DisplayName "C++ AI Assistant" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# 检查服务状态
Get-Process python
```

---

## ✅ 部署检查清单

- [ ] 解压项目到目标目录
- [ ] 安装Python 3.11.9
- [ ] 安装Node.js 18.19.0
- [ ] 安装所有Python wheel包
- [ ] 配置.env文件（千问API、模型路径）
- [ ] 配置MCP服务器
- [ ] 验证嵌入模型加载
- [ ] 启动服务
- [ ] 测试API接口
- [ ] 配置文件监控
- [ ] 配置定时任务（可选）

---

## 🎉 部署完成

恭喜！C++ AI Assistant已成功部署到内网环境。

现在可以:
- 使用千问大模型进行代码分析
- 进行C++/Java代码重构
- 执行自动化代码审查
- 查询代码知识库
- 使用MCP服务器扩展功能

享受内网私有化AI代码助手！