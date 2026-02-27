# C++ AI Assistant

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11.9-green.svg)](https://www.python.org)
[![VSCode Extension](https://img.shields.io/badge/vscode-1.85.0-blue.svg)](https://code.visualstudio.com)

> AI-powered C++ code analysis, refactoring, and review assistant with Qwen 3-235B LLM

## Features

### Core Capabilities
- **Deep Code Understanding** - Semantic analysis of C++ code structures and relationships
- **Intelligent Code Review** - Automatic detection of memory leaks, resource management, and design issues
- **AI-Driven Refactoring** - Executable refactoring suggestions powered by Qwen 3-235B
- **Automated Test Generation** - Support for GTest, Catch2, and DocTest
- **Code Knowledge Base** - Cross-repository semantic search and retrieval
- **VSCode Integration** - Ready-to-use VSCode extension with inline code intelligence

### Technical Highlights
- **Tree-sitter Parsing** - Accurate AST analysis for C++ code
- **ChromaDB Vector Store** - Efficient semantic code retrieval
- **Qwen 3-235B Integration** - 235B parameter enterprise-grade LLM
- **Complete Offline Support** - Deploy in air-gapped environments
- **High Performance** - Python 3.11.9 with async architecture

## Quick Start

### Prerequisites
- Python 3.11.9
- Node.js 18.19.0 (for VSCode extension)
- Git

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd cpp-ai-assistant

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configuration
cp config/config.yaml.example config/config.yaml
# Edit config.yaml to set Qwen API endpoint

# 4. Start backend service
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Install VSCode Extension

```bash
# Via VSCode command palette
Ctrl+Shift+P -> Extensions: Install from VSIX... -> Select cpp-ai-assistant-1.0.0.vsix

# Or via command line
code --install-extension vscode-extension/cpp-ai-assistant-1.0.0.vsix
```

### Configuration

**`config/config.yaml`**
```yaml
server:
  host: "0.0.0.0"
  port: 8000

qwen:
  api_base: "http://your-qwen-endpoint.com/v1"
  api_key: "${QWEN_API_KEY}"
  model_name: "qwen-3-235b"
```

**VSCode Settings**
```json
{
  "cppAIAssistant.apiEndpoint": "http://localhost:8000",
  "cppAIAssistant.modelName": "qwen-3-235b",
  "cppAIAssistant.enableCodeLens": true
}
```

## Project Structure

```
cpp-ai-assistant/
├── backend/                   # Backend API service
│   ├── parsers/              # C++/Java code parsers
│   ├── services/             # Business logic
│   ├── vectorstore/          # Vector database
│   └── utils/                # Utilities
├── vscode-extension/          # VSCode extension
│   ├── src/
│   │   ├── extension.ts      # Extension entry point
│   │   ├── analyzer/         # Local code analyzer
│   │   ├── providers/        # CodeLens provider
│   │   ├── panels/           # Webview panels
│   │   └── services/         # API client
│   └── cpp-ai-assistant-1.0.0.vsix
├── tests/                     # Test suite
├── ext/                       # External dependencies
│   ├── 01-python-pip/        # Source packages
│   ├── 02-python-wheels/     # Wheel packages
│   ├── 05-runtime-python/    # Python installer
│   └── 08-models-embeddings/ # Embedding models
├── scripts/                   # Utility scripts
├── config/                    # Configuration files
├── requirements.txt           # Main dependencies
├── requirements-dev.txt       # Development dependencies
└── requirements-offline.txt   # Offline installation
```

## API Documentation

### Health Check
```
GET /health

{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "qwen": true,
    "vector_store": true,
    "cpp_parser": true
  }
}
```

### Code Review
```
POST /api/review
Content-Type: application/json

{
  "code": "class Test {}",
  "file_path": "/src/test.cpp",
  "language": "cpp"
}

{
  "summary": "Code review completed",
  "score": 85,
  "issues": [...],
  "metrics": {...}
}
```

### Refactoring Suggestions
```
POST /api/refactor

{
  "code": "void process() {...}",
  "refactor_type": "extract-method"
}

{
  "current_state": "...",
  "suggestions": [...]
}
```

### Test Generation
```
POST /api/test

{
  "code": "int add(int a, int b) { return a + b; }",
  "test_framework": "gtest"
}

{
  "test_cases": [...],
  "framework": "gtest",
  "total_cases": 5
}
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=backend

# Code formatting
black backend/
ruff check backend/

# Type checking
mypy backend/

# Build VSCode extension
cd vscode-extension
npm install
npm run compile
npm run package
```

## Offline Installation

For complete offline deployment guide, see [OFFLINE_DEPLOYMENT.md](OFFLINE_DEPLOYMENT.md).

```bash
# Install from local wheel files
pip install -r requirements-offline.txt --no-index --find-links=ext/02-python-wheels

# Run installation script (automates all steps)
python install.py
```

## VSCode Extension Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+E` | Explain selected code |
| `Ctrl+Shift+R` | Refactor selected code |
| `Ctrl+Shift+C` | Review current file |
| `Ctrl+Shift+P` | Open AI Assistant panel |

## Requirements Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Main production dependencies |
| `requirements-dev.txt` | Development and testing tools |
| `requirements-offline.txt` | Offline deployment packages |
| `requirements-all-wheels.txt` | All wheel packages (auto-generated) |
| `requirements-cp311.txt` | Python 3.11 specific wheels (auto-generated) |
| `requirements-py3-universal.txt` | Python 3.x universal wheels (auto-generated) |

## Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [OFFLINE_DEPLOYMENT.md](OFFLINE_DEPLOYMENT.md) - Offline installation guide
- [SESSION_CONTEXT.md](SESSION_CONTEXT.md) - Project development context

## Technology Stack

- **Backend**: FastAPI + Python 3.11.9
- **Code Parsing**: Tree-sitter
- **Vector Storage**: ChromaDB + Sentence Transformers
- **AI Model**: Qwen 3-235B (OpenAI-compatible API)
- **Frontend**: VSCode Extension API + TypeScript
- **Testing**: pytest + pytest-asyncio

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Email**: support@example.com

---

**Made with ❤️ for C++ developers**