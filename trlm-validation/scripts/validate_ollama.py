#!/usr/bin/env python3
"""
TRLM-135M Ollama 集成验证脚本

目的：
1. 使用 Ollama 快速验证小模型能力
2. 无需下载 Hugging Face 模型
3. 测试内网编程知识场景

使用方法：
    python scripts/validate_ollama.py --model phi-3-mini
    python scripts/validate_ollama.py --quick
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trlm-validation/ollama_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 内网场景测试用例
INTERNAL_TEST_CASES = [
    {
        'category': '代码定位',
        'question': 'OrderService 的登录超时问题一般在哪里？',
        'expected_elements': ['service', 'auth', 'session', 'timeout'],
        'description': '常见问题定位'
    },
    {
        'category': '仓库定位',
        'question': 'payment-service 对账逻辑在哪个仓库？',
        'expected_elements': ['payment', 'reconcile', 'core'],
        'description': '代码组织结构'
    },
    {
        'category': '接口分析',
        'question': 'User.create 接口需要哪些参数？',
        'expected_elements': ['parameters', 'user', 'create'],
        'description': 'API 接口分析'
    },
    {
        'category': '依赖关系',
        'question': 'OrderService 依赖哪些其他服务？',
        'expected_elements': ['service', 'payment', 'user', 'dependency'],
        'description': '服务依赖分析'
    },
    {
        'category': '影响范围',
        'question': '修改 OrderService.syncStatus 接口，增加一个参数，会影响哪些地方？',
        'expected_elements': ['service', 'interface', 'impact', 'caller'],
        'description': '接口变更影响评估'
    }
]


def find_ollama() -> str:
    """
    查找 Ollama 可执行文件
    
    Returns:
        str: Ollama 可执行文件路径
    """
    # 1. 检查环境变量
    ollama_path = os.environ.get('OLLAMA_PATH')
    if ollama_path:
        ollama_exec = os.path.join(ollama_path, 'ollama.exe' if sys.platform == 'win32' else 'ollama')
        if os.path.exists(ollama_exec):
            return ollama_exec
    
    # 2. 检查默认 Windows 路径
    default_path = r'D:\APP\Ollama\ollama.exe'
    if sys.platform == 'win32' and os.path.exists(default_path):
        return default_path
    
    # 3. 检查 PATH
    for path in os.environ.get('PATH', '').split(os.pathsep):
        ollama_exec = os.path.join(path, 'ollama.exe' if sys.platform == 'win32' else 'ollama')
        if os.path.exists(ollama_exec):
            return ollama_exec
    
    return None


def check_ollama_models() -> List[str]:
    """
    获取已安装的 Ollama 模型列表
    
    Returns:
        list: 模型名称列表
    """
    ollama_exec = find_ollama()
    if not ollama_exec:
        raise RuntimeError("未找到 Ollama 可执行文件")
    
    try:
        result = subprocess.run(
            [ollama_exec, 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # 解析输出
            models = []
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('NAME'):
                    model_name = line.split()[0].strip()
                    models.append(model_name)
            return models
        else:
            logger.error(f"Ollama list 失败: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        logger.error("Ollama 命令超时")
        return []
    except Exception as e:
        logger.error(f"获取 Ollama 模型列表失败: {e}")
        return []


def query_ollama(model: str, question: str, use_thinking: bool = False) -> Dict[str, Any]:
    """
    使用 Ollama 查询模型
    
    Args:
        model: 模型名称
        question: 问题
        use_thinking: 是否使用 thinking 模式
        
    Returns:
        dict: 包含回答和元信息
    """
    ollama_exec = find_ollama()
    if not ollama_exec:
        raise RuntimeError("未找到 Ollama 可执行文件")
    
    # 构建 prompt
    if use_thinking:
        prompt = f"""You are an internal software engineering expert with strong reasoning capabilities.

Question: {question}

Think step by step about the problem:
1. Understand what the user is asking
2. Identify the relevant services or components
3. Consider the dependencies and relationships
4. Provide a structured answer

Answer:"""
    else:
        prompt = f"""You are an internal software engineering expert.

Question: {question}

Answer:"""
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            [
                ollama_exec,
                'run',
                model,
                prompt
            ],
            capture_output=True,
            text=True,
            timeout=60  # 60秒超时
        )
        
        generation_time = time.time() - start_time
        
        if result.returncode == 0:
            response = result.stdout.strip()
            return {
                'success': True,
                'response': response,
                'generation_time': generation_time,
                'use_thinking': use_thinking
            }
        else:
            logger.error(f"Ollama 运行失败: {result.stderr}")
            return {
                'success': False,
                'error': result.stderr,
                'generation_time': generation_time,
                'use_thinking': use_thinking
            }
            
    except subprocess.TimeoutExpired:
        logger.error("Ollama 命令超时")
        return {
            'success': False,
            'error': 'Timeout',
            'generation_time': 60,
            'use_thinking': use_thinking
        }
    except Exception as e:
        logger.error(f"Ollama 查询失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'generation_time': 0,
            'use_thinking': use_thinking
        }


def evaluate_response(question: str, response: str, expected_elements: List[str]) -> Dict[str, Any]:
    """评估模型回答质量"""
    response_lower = response.lower()
    
    # 检查期望元素
    found_elements = [elem for elem in expected_elements 
                     if elem.lower() in response_lower]
    element_coverage = len(found_elements) / len(expected_elements) if expected_elements else 0
    
    # 检查回答长度
    response_length = len(response.split())
    
    # 检查是否有结构化回答
    has_structure = any(marker in response for marker in ['1.', '-', '*', ':', '->', '•'])
    
    # 综合评分
    structure_score = 0.3 if has_structure else 0
    coverage_score = element_coverage * 0.5
    length_score = 0.2 if response_length > 10 else 0.1
    total_score = min(structure_score + coverage_score + length_score, 1.0)
    
    return {
        'response_length': response_length,
        'found_elements': found_elements,
        'element_coverage': element_coverage,
        'has_structure': has_structure,
        'total_score': total_score,
        'quality': 'good' if total_score >= 0.6 else 'medium' if total_score >= 0.4 else 'poor'
    }


class OllamaValidator:
    """Ollama 验证器"""
    
    def __init__(self, model: str = 'phi-3-mini'):
        self.model = model
        self.ollama_exec = find_ollama()
        
        if not self.ollama_exec:
            raise RuntimeError("未找到 Ollama，请安装或设置 OLLAMA_PATH 环境变量")
        
        logger.info(f"找到 Ollama: {self.ollama_exec}")
        logger.info(f"使用模型: {self.model}")
    
    def check_installation(self) -> bool:
        """检查 Ollama 安装和模型"""
        try:
            # 检查 Ollama 是否可运行
            result = subprocess.run(
                [self.ollama_exec, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Ollama 版本检查失败: {result.stderr}")
                return False
            
            logger.info(f"Ollama 版本: {result.stdout.strip()}")
            
            # 检查可用模型
            models = check_ollama_models()
            logger.info(f"已安装的模型: {', '.join(models) if models else '无'}")
            
            if self.model not in models:
                logger.warning(f"模型 {self.model} 未安装")
                logger.info(f"运行: {self.ollama_exec} pull {self.model} 来安装")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查 Ollama 安装失败: {e}")
            return False
    
    def run_tests(self, test_cases: List[Dict[str, Any]], use_thinking: bool = False) -> List[Dict[str, Any]]:
        """运行测试用例"""
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            question = test_case['question']
            expected_elements = test_case['expected_elements']
            category = test_case['category']
            description = test_case['description']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"测试 {i}/{len(test_cases)}: {category} - {description}")
            logger.info(f"问题: {question}")
            logger.info(f"模式: {'Thinking' if use_thinking else '直接回答'}")
            
            # 查询模型
            result = query_ollama(self.model, question, use_thinking=use_thinking)
            
            if result['success']:
                response = result['response']
                logger.info(f"\n回答:\n{response[:500]}...")
                
                # 评估回答
                evaluation = evaluate_response(question, response, expected_elements)
                
                logger.info(f"\n评估:")
                logger.info(f"  质量评分: {evaluation['total_score']*100:.1f}% ({evaluation['quality']})")
                logger.info(f"  元素覆盖率: {evaluation['element_coverage']*100:.1f}%")
                logger.info(f"  结构化: {'是' if evaluation['has_structure'] else '否'}")
                logger.info(f"  回答长度: {evaluation['response_length']} tokens")
                logger.info(f"  生成时间: {result['generation_time']:.2f}s")
                
                results.append({
                    'category': category,
                    'description': description,
                    'question': question,
                    'response': response,
                    'expected_elements': expected_elements,
                    'found_elements': evaluation['found_elements'],
                    'use_thinking': use_thinking,
                    'generation_time': result['generation_time'],
                    **evaluation
                })
            else:
                logger.error(f"查询失败: {result.get('error', 'Unknown error')}")
                results.append({
                    'category': category,
                    'description': description,
                    'question': question,
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'use_thinking': use_thinking
                })
        
        return results
    
    def run_baseline_test(self) -> Dict[str, Any]:
        """运行基准测试（对比两种模式）"""
        logger.info("=" * 60)
        logger.info("Ollama 基准测试")
        logger.info("=" * 60)
        logger.info(f"模型: {self.model}")
        logger.info(f"测试用例数: {len(INTERNAL_TEST_CASES)}")
        logger.info("")
        
        if not self.check_installation():
            return {'success': False, 'error': 'Ollama installation check failed'}
        
        all_results = []
        
        # 直接回答模式
        logger.info(f"\n\n{'#'*60}")
        logger.info("模式 1: 直接回答")
        logger.info(f"{'#'*60}\n")
        direct_results = self.run_tests(INTERNAL_TEST_CASES, use_thinking=False)
        all_results.extend(direct_results)
        
        # Thinking模式
        logger.info(f"\n\n{'#'*60}")
        logger.info("模式 2: Thinking模式")
        logger.info(f"{'#'*60}\n")
        thinking_results = self.run_tests(INTERNAL_TEST_CASES, use_thinking=True)
        all_results.extend(thinking_results)
        
        # 统计分析
        successful_results = [r for r in all_results if r.get('success', True)]
        
        if successful_results:
            direct = [r for r in successful_results if not r['use_thinking']]
            thinking = [r for r in successful_results if r['use_thinking']]
            
            direct_avg_score = sum(r['total_score'] for r in direct) / len(direct) if direct else 0
            thinking_avg_score = sum(r['total_score'] for r in thinking) / len(thinking) if thinking else 0
            avg_time = sum(r['generation_time'] for r in successful_results) / len(successful_results)
            
            # 按类别统计
            category_performance = {}
            for result in successful_results:
                category = result['category']
                if category not in category_performance:
                    category_performance[category] = {'scores': []}
                category_performance[category]['scores'].append(result['total_score'])
            
            for category in category_performance:
                scores = category_performance[category]['scores']
                category_performance[category]['avg'] = sum(scores) / len(scores)
                category_performance[category]['max'] = max(scores)
                category_performance[category]['min'] = min(scores)
            
            summary = {
                'success': True,
                'model': self.model,
                'ollama_path': self.ollama_exec,
                'total_tests': len(successful_results),
                'direct_avg_score': direct_avg_score,
                'thinking_avg_score': thinking_avg_score,
                'improvement': thinking_avg_score - direct_avg_score,
                'improvement_pct': (thinking_avg_score - direct_avg_score) / direct_avg_score * 100 if direct_avg_score > 0 else 0,
                'avg_generation_time': avg_time,
                'category_performance': category_performance,
                'results': all_results
            }
        else:
            summary = {
                'success': False,
                'error': 'No successful tests',
                'results': all_results
            }
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='TRLM Ollama 集成验证')
    parser.add_argument(
        '--model',
        type=str,
        default='phi-3-mini',
        help='Ollama 模型名称（默认: phi-3-mini）'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速测试模式（仅前3个场景）'
    )
    parser.add_argument(
        '--ollama-path',
        type=str,
        help='Ollama 可执行文件路径（默认: 自动检测）'
    )
    
    args = parser.parse_args()
    
    # 设置 Ollama 路径
    if args.ollama_path:
        os.environ['OLLAMA_PATH'] = args.ollama_path
    
    global INTERNAL_TEST_CASES
    if args.quick:
        INTERNAL_TEST_CASES = INTERNAL_TEST_CASES[:3]
        logger.info("快速测试模式：仅测试前3个场景")
    
    logger.info("=" * 60)
    logger.info("TRLM-135M Ollama 集成验证")
    logger.info("=" * 60)
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"模型: {args.model}")
    logger.info(f"测试场景数: {len(INTERNAL_TEST_CASES)}")
    logger.info("")
    
    # 运行测试
    try:
        validator = OllamaValidator(model=args.model)
        summary = validator.run_baseline_test()
        
        # 输出总结
        logger.info("\n\n" + "=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)
        
        if summary['success']:
            logger.info(f"总测试数: {summary['total_tests']}")
            logger.info(f"\n模式对比:")
            logger.info(f"  直接回答平均分: {summary['direct_avg_score']*100:.1f}%")
            logger.info(f"  Thinking模式平均分: {summary['thinking_avg_score']*100:.1f}%")
            logger.info(f"  提升: {summary['improvement']*100:.1f}%")
            logger.info(f"  平均生成时间: {summary['avg_generation_time']:.2f}s")
            
            logger.info(f"\n按类别表现:")
            for category, perf in summary['category_performance'].items():
                logger.info(f"  {category}: {perf['avg']*100:.1f}% "
                           f"(min: {perf['min']*100:.1f}%, max: {perf['max']*100:.1f}%)")
            
            # 生成建议
            logger.info(f"\n\n{'='*60}")
            logger.info("分析与建议")
            logger.info(f"{'='*60}")
            
            if summary['thinking_avg_score'] >= 0.6:
                logger.info("✓ 基础表现良好")
                logger.info(f"  - 模型 {args.model} 能够回答内网相关的问题")
                if summary['improvement'] > 0.1:
                    logger.info("  - Thinking模式有明显提升效果")
                logger.info("  - 建议: 可以继续使用 Ollama 或考虑下载 Hugging Face 模型进行深度定制")
            elif summary['thinking_avg_score'] >= 0.4:
                logger.info("⚠ 基础表现中等")
                logger.info(f"  - 模型 {args.model} 有一定理解能力，但不够精准")
                if summary['improvement'] > 0.1:
                    logger.info("  - Thinking模式有明显提升，证明了显式推理的价值")
                logger.info("  - 建议:")
                logger.info("    1. 尝试其他 Ollama 模型（如 llama3.2）")
                logger.info("    2. 使用 Hugging Face 上的专门训练的模型")
            else:
                logger.info("✗ 基础表现较差")
                logger.info(f"  - 模型 {args.model} 难以理解内网场景")
                logger.info("  - 建议:")
                logger.info("    1. 尝试其他 Ollama 模型")
                logger.info("    2. 使用 Hugging Face 上的 trlm-135M 等专用模型")
            
            # 保存结果
            reports_dir = Path('trlm-validation/reports')
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode_suffix = "_quick" if args.quick else "_full"
            output_file = reports_dir / f'ollama_validation_{args.model}{mode_suffix}_{timestamp}.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"\n详细结果已保存到: {output_file}")
            
        else:
            logger.error(f"测试失败: {summary.get('error', 'Unknown error')}")
    
    except RuntimeError as e:
        logger.error(f"错误: {e}")
        logger.info("\n安装指南:")
        logger.info("1. 下载 Ollama: https://ollama.com/download")
        logger.info("2. 安装后通过环境变量指定路径:")
        logger.info("   Windows: set OLLAMA_PATH=D:\\APP\\Ollama")
        logger.info("   Linux/macOS: export OLLAMA_PATH=/path/to/ollama")
        logger.info("3. 拉取模型: ollama pull phi-3-mini")
    
    except Exception as e:
        logger.error(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n测试被用户中断")