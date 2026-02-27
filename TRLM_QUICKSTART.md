# TRLM-135M 快速入门指南

> **目的**：在投入大量资源训练之前，先验证 trlm-135M 基础模型的复现效果

---

## 📋 目录

1. [前置要求](#前置要求)
2. [快速安装依赖](#快速安装依赖)
3. [下载模型](#下载模型)
4. [运行基础验证测试](#运行基础验证测试)
5. [运行内网场景测试](#运行内网场景测试)
6. [解读测试结果](#解读测试结果)
7. [下一步决策](#下一步决策)

---

## 前置要求

### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **CPU** | 4核 | 8核+ |
| **内存** | 8GB | 16GB+ |
| **磁盘** | 2GB 可用空间 | 5GB+ 可用空间 |
| **GPU** | 不需要 | 不需要（CPU推理） |

### 软件要求

- **Python**: 3.8+
- **操作系统**: Windows/Linux/macOS
- **网络**: 需要访问 Hugging Face（下载模型）

---

## 快速安装依赖

### 步骤 1: 创建虚拟环境（推荐）

```bash
cd projects/3/cpp-ai-assistant

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 步骤 2: 安装必需的依赖

```bash
pip install torch transformers huggingface-hub
```

**可选依赖**（用于内存监控）：
```bash
pip install psutil
```

---

## 下载模型

### 方式一：下载所有三个阶段（推荐）

```bash
python scripts/download_trlm.py --stage all
```

### 方式二：逐个下载

```bash
# Stage 1: 基础SFT（无思考链）
python scripts/download_trlm.py --stage stage1

# Stage 2: <thinking>推理SFT（推荐测试）
python scripts/download_trlm.py --stage stage2

# Stage 3: DPO偏好对齐
python scripts/download_trlm.py --stage stage3
```

### 验证下载

```bash
python scripts/download_trlm.py --verify
```

**预期输出**：
```
验证结果:
  ✓ stage1: 基础SFT模型（无思考链）
      目录: ext/09-models-trlm/stage1-sft-final-2
  ✓ stage2: <thinking>推理SFT模型
      目录: ext/09-models-trlm/stage2-sft-final-2
  ✓ stage3: DPO偏好对齐模型
      目录: ext/09-models-trlm/stage3-dpo-final-2
```

---

## 运行基础验证测试

### 目的

测试模型的基本能力：
- 模型能否正常加载
- 推理速度如何
- 内存占用是否合理
- 三个阶段的性能对比

### 运行测试

```bash
# 测试 Stage 2（推荐）
python scripts/validate_trlm.py --stage stage2

# 测试 Stage 3
python scripts/validate_trlm.py --stage stage3

# 测试所有阶段
for stage in stage1 stage2 stage3; do
    echo "Testing $stage..."
    python scripts/validate_trlm.py --stage $stage
done
```

### 测试内容

测试涵盖三个类别：

1. **基础问答**（Basic）
   - 简单算术
   - 编程概念解释
   - 常识问答

2. **推理能力**（Reasoning）
   - 多步推理
   - 应用题

3. **内部知识**（Internal Knowledge）
   - 系统命令
   - 构建工具

### 预期结果

```
验证总结
============================================================
总测试数: 7
通过数: 5
通过率: 71.4%
平均生成时间: 3.45s
平均内存占用: 1024.5 MB

按类别统计:
  简单算术: 1/1 (100.0%)
  编程概念解释: 1/1 (100.0%)
  常识问答: 1/1 (100.0%)
  多步推理: 1/1 (100.0%)
  应用题: 0/1 (0.0%)
  系统命令: 1/1 (100.0%)
  构建工具: 0/1 (0.0%)

详细结果已保存到: scripts/trlm_validation_stage2_20260208_040000.json
```

---

## 运行内网场景测试

### 目的

测试模型在内网编程知识场景下的表现：
- 代码问题排查
- 架构定位
- 依赖关系分析
- 接口影响评估

### 快速测试（3个场景，~5分钟）

```bash
python tests/test_trlm_baseline.py --stage stage2 --quick
```

### 完整测试（10个场景，~15分钟）

```bash
python tests/test_trlm_baseline.py --stage stage2
```

### 测试场景

| 类别 | 问题 | 评估重点 |
|------|------|---------|
| 代码定位 | OrderService 的登录超时问题一般在哪里？ | 服务、模块定位 |
| 仓库定位 | payment-service 对账逻辑在哪个仓库？ | 代码组织结构 |
| 接口分析 | User.create 接口需要哪些参数？ | API 接口理解 |
| 依赖关系 | OrderService 依赖哪些其他服务？ | 服务依赖分析 |
| 影响范围 | 修改 OrderService.syncStatus 接口，增加一个参数，会影响哪些地方？ | 变更影响评估 |
| 调用链 | 从 API 网关到数据库的完整调用链是什么？ | 完整调用链追踪 |
| 配置管理 | Redis 连接配置在哪里？ | 配置文件定位 |
| 错误处理 | 当数据库连接失败时，系统如何处理？ | 错误处理机制 |
| 测试用例 | OrderService 需要哪些测试用例？ | 测试覆盖分析 |
| 性能优化 | 如何优化 queryOrder 查询性能？ | 性能优化建议 |

### 模式对比

每个测试用例会运行两种模式：

1. **直接回答模式**：直接回答问题
2. **Thinking模式**：使用 `<thinking>` 标签显式推理

这样可以评估显式推理标签的价值。

### 预期输出

```
测试总结
============================================================
总测试数: 20
直接回答平均分: 45.0%
Thinking模式平均分: 58.0%
提升: 13.0%

按类别表现:
  代码定位: 50.0% (min: 40.0%, max: 60.0%)
  仓库定位: 45.0% (min: 35.0%, max: 55.0%)
  接口分析: 40.0% (min: 30.0%, max: 50.0%)
  ...
```

---

## 解读测试结果

### 评分标准

| 分数范围 | 质量评级 | 说明 |
|---------|---------|------|
| **70%+** | ✓ 良好 | 模型表现优秀，适合作为内网知识推理引擎 |
| **50%-70%** | ⚠ 中等 | 模型有一定能力，需要高质量的微调数据 |
| **<50%** | ✗ 较差 | 模型难以理解内网场景，需要重新考虑方案 |

### 关键指标

1. **通过率**：测试用例通过的比例
   - 基础验证：目标 > 70%
   - 内网场景：目标 > 60%（考虑到模型未经过训练）

2. **Thinking模式提升**：显式推理标签带来的改进
   - 正常范围：5%-15%
   - 如果 > 15%，说明显式推理非常有效
   - 如果 < 5%，说明模型已经能够隐式推理

3. **内存占用**：模型运行时的内存使用
   - 正常范围：800MB - 1500MB
   - 如果 > 2GB，可能需要优化或考虑更大内存

4. **推理速度**：单次问答的响应时间
   - 正常范围：2-5秒（CPU）
   - 如果 > 10秒，说明性能需要优化

### 按类别表现分析

- **代码定位/仓库定位**：如果表现好，说明模型理解代码组织结构
- **接口分析/依赖关系**：如果表现好，说明模型理解架构层面
- **影响范围/调用链**：这是核心能力，如果表现好，价值很高
- **配置管理/错误处理**：基础能力，应该达到及格线
- **测试用例/性能优化**：高级能力，低分可以接受

---

## 下一步决策

### 场景 1：测试结果良好（通过率 > 70%）

**建议**：✅ 继续推进定制化训练

**下一步**：
1. 开始收集内网训练数据（参考 `prompt.md` 第 7 节）
2. 准备阶段 1 数据（100+ 条基础对话）
3. 准备阶段 2 数据（200+ 条带 `<thinking>` 的推理样本）
4. 开始三阶段训练流程

**预期**：经过训练后，内网场景表现可达 80%+

---

### 场景 2：测试结果中等（通过率 50%-70%）

**建议**：⚠ 有条件推进，需谨慎

**下一步**：
1. 先尝试 Stage 3 (DPO) 模型，看是否有改善
2. 调整推理参数（temperature, max_tokens）
3. 准备**更高质量**的微调数据
4. 考虑数据增强技术

**预期**：需要 3-5 倍的训练数据才能达到良好效果

---

### 场景 3：测试结果较差（通过率 < 50%）

**建议**：✗ 暂停，重新评估方案

**可选方案**：

**方案 A**：更换更大的基础模型
- 尝试 Qwen2.5-0.5B 或 1B
- 内存占用会增加，但能力更强
- 训练成本也会增加

**方案 B**：改变策略
- 不使用小模型推理
- 直接使用大模型（千问3-235B）+ 检索增强（RAG）
- 成本更高，但效果更有保障

**方案 C**：简化目标
- 不追求通用推理能力
- 仅专注于特定场景（如代码搜索、依赖分析）
- 使用规则引擎 + 简单模型组合

---

## 常见问题

### Q1: 下载模型失败怎么办？

**A**: 检查以下几点：

1. 网络连接是否正常：
   ```bash
   ping huggingface.co
   ```

2. Hugging Face Hub 是否配置：
   ```bash
   huggingface-cli login
   ```

3. 防火墙/代理设置：
   ```bash
   export HF_ENDPOINT=https://hf-mirror.com  # 使用镜像
   ```

### Q2: 内存不足怎么办？

**A**: 尝试以下优化：

1. 使用量化模型（需要重新下载）：
   ```python
   model = AutoModelForCausalLM.from_pretrained(
       model_path,
       torch_dtype=torch.float16,
       quantization_config=BitsAndBytesConfig(
           load_in_8bit=True  # or load_in_4bit=True
       )
   )
   ```

2. 关闭其他程序释放内存

3. 使用更大的机器进行测试

### Q3: 推理速度太慢怎么办？

**A**: 优化策略：

1. 减少生成的 token 数：
   ```python
   outputs = model.generate(**inputs, max_new_tokens=128)  # 从256减到128
   ```

2. 使用 GPU（如果可用）：
   ```python
   model = AutoModelForCausalLM.from_pretrained(
       model_path,
       device_map='cuda'  # 使用GPU
   )
   ```

3. 批量推理（适合生产环境）

### Q4: 测试结果波动很大怎么办？

**A**: 原因和解决方案：

1. **原因**：小模型对随机种子敏感
2. **解决方案**：
   ```python
   torch.manual_seed(42)
   np.random.seed(42)
   ```
3. 运行多次测试取平均值

---

## 附录：完整测试流程

### 完整的自动化测试脚本

```bash
#!/bin/bash

# TRLM-135M 完整测试流程

echo "========================================"
echo "TRLM-135M 完整验证测试流程"
echo "========================================"

# 步骤 1: 下载模型
echo ""
echo "步骤 1: 下载模型..."
python scripts/download_trlm.py --stage all

if [ $? -ne 0 ]; then
    echo "✗ 模型下载失败"
    exit 1
fi

# 步骤 2: 验证下载
echo ""
echo "步骤 2: 验证下载..."
python scripts/download_trlm.py --verify

# 步骤 3: 基础验证测试（所有阶段）
echo ""
echo "步骤 3: 基础验证测试..."
for stage in stage1 stage2 stage3; do
    echo "测试 $stage..."
    python scripts/validate_trlm.py --stage $stage
done

# 步骤 4: 内网场景测试
echo ""
echo "步骤 4: 内网场景测试..."
python tests/test_trlm_baseline.py --stage stage2

echo ""
echo "========================================"
echo "测试完成！"
echo "========================================"
echo ""
echo "请查看测试报告并决定下一步行动："
echo "  - 基础验证报告: scripts/trlm_validation_*.json"
echo "  - 内网场景报告: tests/trlm_baseline_*.md"
```

保存为 `scripts/run_full_validation.sh`，然后运行：

```bash
bash scripts/run_full_validation.sh > validation_full.log 2>&1
```

---

## 联系与支持

- **项目文档**: `prompt.md`
- **问题反馈**: 通过 Git Issues
- **技术讨论**: 参考项目 Wiki

---

**最后更新**: 2026-02-08
**版本**: 1.0.0