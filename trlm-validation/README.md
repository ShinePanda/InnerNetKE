# TRLM-135M 验证套件

> 独立的验证环境，用于测试 trlm-135M 模型在内网编程知识场景下的表现

---

## 📁 目录结构

```
trlm-validation/
├── scripts/                 # 验证脚本
│   ├── download_trlm.py    # 下载模型
│   ├── validate_trlm.py    # 基础验证
│   └── validate_ollama.py  # Ollama 集成验证（新增）
├── tests/                   # 测试脚本
│   └── test_trlm_baseline.py # 内网场景测试
├── reports/                 # 测试报告输出目录
├── models/                  # 下载的模型存储目录
├── QUICKSTART.md           # 快速入门指南
└── run_all.sh              # 一键运行所有验证
```

---

## 🚀 快速开始

### 方式一：使用 Ollama（推荐，已安装）

如果您的系统已安装 Ollama（`D:\APP\Ollama`），可以直接使用 Ollama 运行小模型：

```bash
# 1. 拉取一个小模型（可选）
ollama pull phi-3-mini

# 2. 运行 Ollama 集成验证
cd projects/3/cpp-ai-assistant/trlm-validation
python scripts/validate_ollama.py
```

### 方式二：使用 Hugging Face 模型

```bash
# 1. 下载模型
python scripts/download_trlm.py --stage stage2

# 2. 运行基础验证
python scripts/validate_trlm.py --stage stage2

# 3. 运行内网场景测试
python tests/test_trlm_baseline.py --stage stage2 --quick
```

### 方式三：一键运行（自动化）

```bash
# Linux/macOS
bash run_all.sh

# Windows PowerShell
.\run_all.ps1
```

---

## 📋 验证内容

### 1. 基础能力验证（validate_trlm.py）
- ✓ 模型加载测试
- ✓ 推理速度测试
- ✓ 内存占用测试
- ✓ 7个基础测试用例

### 2. 内网场景测试（test_trlm_baseline.py）
- ✓ 10个内网编程知识场景
- ✓ 对比直接回答 vs Thinking模式
- ✓ 自动生成详细报告

### 3. Ollama 集成验证（validate_ollama.py）
- ✓ 使用 Ollama 运行小模型
- ✓ 无需下载模型文件
- ✓ 快速验证可行性

---

## 📊 评估标准

| 通过率 | 决策 | 说明 |
|--------|------|------|
| **≥70%** | ✅ 继续推进 | 模型表现良好，可以开始准备训练数据 |
| **50%-70%** | ⚠️ 谨慎推进 | 需要更高质量的训练数据 |
| **<50%** | ✗ 暂停 | 重新评估方案 |

---

## 🔧 配置

### Ollama 配置

如果使用 Ollama，脚本会自动检测 `D:\APP\Ollama` 或通过环境变量 `OLLAMA_PATH` 指定：

```bash
# Windows
set OLLAMA_PATH=D:\APP\Ollama

# Linux/macOS
export OLLAMA_PATH=/path/to/ollama
```

### 模型存储配置

默认模型存储路径：`projects/3/cpp-ai-assistant/ext/09-models-trlm/`

可通过环境变量修改：

```bash
export TRLM_MODELS_PATH=/custom/path/models
```

---

## 📝 报告输出

所有测试报告会自动保存到 `reports/` 目录：

```
reports/
├── trlm_validation_stage1_*.json
├── trlm_validation_stage2_*.json
├── trlm_validation_stage3_*.json
├── trlm_baseline_stage2_*.json
└── trlm_baseline_stage2_*.md
```

---

## ⏱️ 预估时间

| 验证方式 | 时间 |
|---------|------|
| Ollama 快速验证 | 2-3分钟 |
| Hugging Face 下载 | 10-30分钟 |
| 基础验证 | 5-10分钟 |
| 内网场景测试（快速） | 5分钟 |
| 内网场景测试（完整） | 15-20分钟 |

---

## 🆘 常见问题

### Q1: Ollama 和 Hugging Face 模型哪个更好？

**A**: 
- **Ollama**: 无需下载，快速验证，但模型选择有限
- **Hugging Face**: 模型选择多，可直接用于后续训练，但需要下载

**建议**: 先用 Ollama 快速验证可行性，再决定是否下载 Hugging Face 模型

### Q2: 内存不足怎么办？

**A**: 
1. 使用 Ollama（内存占用更低）
2. 只下载 Stage 2 模型（最小的阶段）
3. 使用 `--quick` 模式运行测试

### Q3: 可以跳过某些验证步骤吗？

**A**: 可以，直接运行需要的测试：
```bash
# 只运行内网场景测试
python tests/test_trlm_baseline.py --stage stage2 --quick
```

---

## 📚 相关文档

- **快速入门**: `QUICKSTART.md`
- **完整方案**: `../prompt.md`
- **项目主页**: `../README.md`

---

## 🎯 下一步

完成验证后，根据结果决定：

1. **通过率 ≥70%**: 参考主项目的第6-8节，开始准备训练数据
2. **通过率 50%-70%**: 准备更高质量的训练数据
3. **通过率 <50%**: 参考备选方案

---

**最后更新**: 2026-02-08
**版本**: 1.0.0