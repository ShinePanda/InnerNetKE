#!/bin/bash

###############################################################################
# TRLM-135M 完整验证测试流程
#
# 目的：自动化完成所有验证步骤
#       下载模型 -> 基础验证 -> 内网场景测试 -> 生成报告
#
# 使用方法：
#   bash scripts/run_full_validation.sh
#
# 输出：
#   - 日志文件: validation_full.log
#   - 测试报告: scripts/trlm_validation_*.json
#   - 场景报告: tests/trlm_baseline_*.md
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_info() {
    echo -e "${GREEN}[信息]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查Python环境
check_python() {
    print_info "检查 Python 环境..."
    
    if ! command -v python &> /dev/null; then
        print_error "未找到 Python"
        exit 1
    fi
    
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    print_info "Python 版本: $PYTHON_VERSION"
    
    # 检查必需的包
    print_info "检查必需的 Python 包..."
    
    python -c "import torch" 2>/dev/null || {
        print_error "torch 未安装"
        print_info "运行: pip install torch"
        exit 1
    }
    
    python -c "import transformers" 2>/dev/null || {
        print_error "transformers 未安装"
        print_info "运行: pip install transformers"
        exit 1
    }
    
    python -c "import huggingface_hub" 2>/dev/null || {
        print_error "huggingface-hub 未安装"
        print_info "运行: pip install huggingface-hub"
        exit 1
    }
    
    # 可选包
    python -c "import psutil" 2>/dev/null && print_info "✓ psutil 已安装（可选）" || \
        print_warning "psutil 未安装（可选），将无法监控内存使用"
    
    echo ""
}

# 主流程
main() {
    print_header "TRLM-135M 完整验证测试流程"
    echo ""
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 检查环境
    check_python
    
    # 步骤 1: 下载模型
    print_header "步骤 1: 下载 TRLM 模型"
    print_info "这可能需要 10-30 分钟，取决于网络速度..."
    echo ""
    
    if python scripts/download_trlm.py --stage all; then
        print_info "✓ 模型下载完成"
    else
        print_error "✗ 模型下载失败"
        print_info "请检查网络连接和磁盘空间"
        exit 1
    fi
    echo ""
    
    # 步骤 2: 验证下载
    print_header "步骤 2: 验证模型下载"
    echo ""
    
    if python scripts/download_trlm.py --verify; then
        print_info "✓ 模型验证通过"
    else
        print_error "✗ 模型验证失败"
        print_info "请检查下载的文件完整性"
        exit 1
    fi
    echo ""
    
    # 步骤 3: 基础验证测试
    print_header "步骤 3: 运行基础验证测试"
    print_info "测试 Stage 1（基础SFT）..."
    echo ""
    
    if python scripts/validate_trlm.py --stage stage1; then
        STAGE1_RESULT="✓"
    else
        STAGE1_RESULT="✗"
        print_warning "Stage 1 测试失败，继续..."
    fi
    echo ""
    
    print_info "测试 Stage 2（<thinking>推理SFT）..."
    echo ""
    
    if python scripts/validate_trlm.py --stage stage2; then
        STAGE2_RESULT="✓"
    else
        STAGE2_RESULT="✗"
        print_warning "Stage 2 测试失败，继续..."
    fi
    echo ""
    
    print_info "测试 Stage 3（DPO偏好对齐）..."
    echo ""
    
    if python scripts/validate_trlm.py --stage stage3; then
        STAGE3_RESULT="✓"
    else
        STAGE3_RESULT="✗"
        print_warning "Stage 3 测试失败，继续..."
    fi
    echo ""
    
    # 步骤 4: 内网场景测试
    print_header "步骤 4: 运行内网场景测试"
    print_info "测试 Stage 2（推荐用于内网场景）..."
    print_info "这可能需要 10-20 分钟..."
    echo ""
    
    if python tests/test_trlm_baseline.py --stage stage2; then
        BASELINE_RESULT="✓"
    else
        BASELINE_RESULT="✗"
        print_warning "内网场景测试失败"
    fi
    echo ""
    
    # 完成总结
    print_header "测试完成！"
    echo ""
    echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "测试结果总结:"
    echo "  模型下载: ✓"
    echo "  模型验证: ✓"
    echo "  Stage 1 基础验证: $STAGE1_RESULT"
    echo "  Stage 2 基础验证: $STAGE2_RESULT"
    echo "  Stage 3 基础验证: $STAGE3_RESULT"
    echo "  内网场景测试: $BASELINE_RESULT"
    echo ""
    echo "生成的报告文件:"
    echo "  - 基础验证报告: scripts/trlm_validation_*.json"
    echo "  - 内网场景报告: tests/trlm_baseline_*.json"
    echo "  - 内网场景报告(MD): tests/trlm_baseline_*.md"
    echo ""
    
    # 下一步建议
    print_header "下一步建议"
    echo ""
    echo "1. 查看测试报告:"
    echo "   - 打开 tests/trlm_baseline_*.md 查看详细的测试结果"
    echo ""
    echo "2. 根据测试结果决定下一步:"
    echo "   - 如果通过率 > 70%: 可以开始准备训练数据"
    echo "   - 如果通过率 50%-70%: 需要更高质量的训练数据"
    echo "   - 如果通过率 < 50%: 重新评估方案（参考 TRLM_QUICKSTART.md）"
    echo ""
    echo "3. 详细指南请参考:"
    echo "   - 快速入门: TRLM_QUICKSTART.md"
    echo "   - 完整方案: prompt.md"
    echo ""
    
    # 检查是否有失败
    if [[ "$BASELINE_RESULT" == "✗" ]]; then
        print_warning "部分测试失败，请查看日志排查问题"
        print_info "日志文件: validation_full.log"
        exit 1
    else
        print_info "所有测试完成！"
        exit 0
    fi
}

# 运行主流程
main