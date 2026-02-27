#!/usr/bin/env python3
"""
TRLM-135M 内网场景基础测试

目的:
1. 测试 trlm-135M 在内网编程知识场景下的基础表现
2. 评估模型的推理能力（无需训练）
3. 判断是否值得投入资源进行定制化训练

测试场景:
- 代码问题排查
- 架构定位
- 依赖关系分析
- 接口影响评估

使用方法:
    python tests/test_trlm_baseline.py --stage stage2
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/trlm_baseline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 内网场景测试用例（模拟真实的内部开发问题）
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
    },
    {
        'category': '调用链',
        'question': '从 API 网关到数据库的完整调用链是什么？',
        'expected_elements': ['gateway', 'service', 'database', 'chain'],
        'description': '完整调用链追踪'
    },
    {
        'category': '配置管理',
        'question': 'Redis 连接配置在哪里？',
        'expected_elements': ['redis', 'config', 'configuration'],
        'description': '配置文件定位'
    },
    {
        'category': '错误处理',
        'question': '当数据库连接失败时，系统如何处理？',
        'expected_elements': ['database', 'error', 'handle', 'exception'],
        'description': '错误处理机制'
    },
    {
        'category': '测试用例',
        'question': 'OrderService 需要哪些测试用例？',
        'expected_elements': ['test', 'service', 'order', 'case'],
        'description': '测试覆盖分析'
    },
    {
        'category': '性能优化',
        'question': '如何优化 queryOrder 查询性能？',
        'expected_elements': ['performance', 'query', 'optimize', 'index'],
        'description': '性能优化建议'
    }
]


def evaluate_response(question: str, response: str, expected_elements: List[str]) -> Dict[str, Any]:
    """
    评估模型回答质量
    
    Args:
        question: 问题
        response: 模型回答
        expected_elements: 期望包含的元素
        
    Returns:
        dict: 评估结果
    """
    response_lower = response.lower()
    
    # 检查期望元素
    found_elements = [elem for elem in expected_elements 
                     if elem.lower() in response_lower]
    element_coverage = len(found_elements) / len(expected_elements)
    
    # 检查回答长度
    response_length = len(response.split())
    
    # 检查是否有结构化回答（列表、编号）
    has_structure = any(marker in response for marker in ['1.', '-', '*', ':', '->'])
    
    # 检查是否提到具体的服务名/类名（模拟内部术语）
    mentions_service = any(term in response_lower for term in 
                          ['service', 'repository', 'class', 'function', 'method'])
    
    # 综合评分
    structure_score = 0.3 if has_structure else 0
    coverage_score = element_coverage * 0.5
    terminology_score = 0.2 if mentions_service else 0
    total_score = structure_score + coverage_score + terminology_score
    
    return {
        'response_length': response_length,
        'found_elements': found_elements,
        'element_coverage': element_coverage,
        'has_structure': has_structure,
        'mentions_service': mentions_service,
        'total_score': total_score,
        'quality': 'good' if total_score >= 0.7 else 'medium' if total_score >= 0.4 else 'poor'
    }


class InternalScenarioTester:
    """内网场景测试器"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        
    def load_model(self) -> bool:
        """加载模型"""
        try:
            logger.info(f"加载模型: {self.model_path}")
            
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map='cpu'
            )
            self.model.eval()
            logger.info("✓ 模型加载完成")
            return True
            
        except Exception as e:
            logger.error(f"✗ 模型加载失败: {e}")
            return False
    
    def query(self, question: str, use_thinking: bool = False) -> str:
        """
        查询模型
        
        Args:
            question: 问题
            use_thinking: 是否使用thinking模式
            
        Returns:
            str: 回答
        """
        try:
            if use_thinking:
                prompt = f"""You are an internal software engineering expert. Answer the following question with clear reasoning.

Question: {question}

<thinking>
Think step by step about the problem.
1. Understand what the user is asking
2. Identify the relevant services or components
3. Consider the dependencies and relationships
4. Provide a structured answer
</thinking>

Answer:"""
            else:
                prompt = f"""You are an internal software engineering expert.

Question: {question}

Answer:"""
            
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 提取回答部分
            if 'Answer:' in response:
                response = response.split('Answer:')[-1].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return f"Error: {str(e)}"
    
    def test_scenario(self, test_case: Dict[str, Any], use_thinking: bool = False) -> Dict[str, Any]:
        """
        测试单个场景
        
        Args:
            test_case: 测试用例
            use_thinking: 是否使用thinking模式
            
        Returns:
            dict: 测试结果
        """
        question = test_case['question']
        expected_elements = test_case['expected_elements']
        category = test_case['category']
        description = test_case['description']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"类别: {category} - {description}")
        logger.info(f"问题: {question}")
        
        # 查询模型
        thinking_mode_str = "[Thinking模式]" if use_thinking else "[直接回答]"
        logger.info(f"模式: {thinking_mode_str}")
        
        response = self.query(question, use_thinking=use_thinking)
        
        logger.info(f"\n回答:\n{response}")
        
        # 评估回答
        evaluation = evaluate_response(question, response, expected_elements)
        
        logger.info(f"\n评估:")
        logger.info(f"  质量评分: {evaluation['total_score']*100:.1f}% ({evaluation['quality']})")
        logger.info(f"  元素覆盖率: {evaluation['element_coverage']*100:.1f}%")
        logger.info(f"  结构化: {'是' if evaluation['has_structure'] else '否'}")
        logger.info(f"  回答长度: {evaluation['response_length']} tokens")
        
        result = {
            'category': category,
            'description': description,
            'question': question,
            'response': response,
            'expected_elements': expected_elements,
            'found_elements': evaluation['found_elements'],
            'use_thinking': use_thinking,
            **evaluation
        }
        
        return result
    
    def run_baseline_test(self) -> Dict[str, Any]:
        """
        运行基础测试（对比thinking模式vs直接回答）
        
        Returns:
            dict: 测试结果
        """
        if not self.load_model():
            return {'success': False, 'error': 'Model loading failed'}
        
        all_results = []
        
        # 对每个测试用例，运行两种模式
        for i, test_case in enumerate(INTERNAL_TEST_CASES, 1):
            logger.info(f"\n\n{'#'*60}")
            logger.info(f"测试 {i}/{len(INTERNAL_TEST_CASES)}")
            logger.info(f"{'#'*60}")
            
            # 直接回答模式
            result_direct = self.test_scenario(test_case, use_thinking=False)
            all_results.append(result_direct)
            
            # Thinking模式
            result_thinking = self.test_scenario(test_case, use_thinking=True)
            all_results.append(result_thinking)
        
        # 统计分析
        direct_results = [r for r in all_results if not r['use_thinking']]
        thinking_results = [r for r in all_results if r['use_thinking']]
        
        direct_avg_score = sum(r['total_score'] for r in direct_results) / len(direct_results)
        thinking_avg_score = sum(r['total_score'] for r in thinking_results) / len(thinking_results)
        
        # 按类别统计
        category_performance = {}
        for result in all_results:
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
            'model_path': str(self.model_path),
            'total_tests': len(all_results),
            'direct_avg_score': direct_avg_score,
            'thinking_avg_score': thinking_avg_score,
            'improvement': thinking_avg_score - direct_avg_score,
            'improvement_pct': (thinking_avg_score - direct_avg_score) / direct_avg_score * 100 if direct_avg_score > 0 else 0,
            'category_performance': category_performance,
            'results': all_results
        }
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='TRLM-135M 内网场景基础测试')
    parser.add_argument(
        '--stage',
        type=str,
        default='stage2',
        choices=['stage1', 'stage2', 'stage3'],
        help='要测试的阶段 (默认: stage2)'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        help='自定义模型路径'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速测试模式（只测试前3个场景）'
    )
    
    args = parser.parse_args()
    
    global INTERNAL_TEST_CASES
    if args.quick:
        INTERNAL_TEST_CASES = INTERNAL_TEST_CASES[:3]
        logger.info("快速测试模式：仅测试前3个场景")
    
    # 确定模型路径
    if args.model_path:
        model_path = args.model_path
    else:
        model_paths = {
            'stage1': 'ext/09-models-trlm/stage1-sft-final-2',
            'stage2': 'ext/09-models-trlm/stage2-sft-final-2',
            'stage3': 'ext/09-models-trlm/stage3-dpo-final-2'
        }
        model_path = model_paths[args.stage]
    
    logger.info("=" * 60)
    logger.info("TRLM-135M 内网场景基础测试")
    logger.info("=" * 60)
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"阶段: {args.stage}")
    logger.info(f"测试场景数: {len(INTERNAL_TEST_CASES)}")
    logger.info(f"模型路径: {model_path}")
    logger.info("")
    
    # 检查模型路径
    if not Path(model_path).exists():
        logger.error(f"模型路径不存在: {model_path}")
        logger.info("请先运行: python scripts/download_trlm.py --stage " + args.stage)
        return
    
    # 运行测试
    tester = InternalScenarioTester(model_path)
    summary = tester.run_baseline_test()
    
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
            logger.info("  - 模型能够回答内网相关的问题")
            logger.info("  - Thinking模式有明显提升效果" if summary['improvement'] > 0.1 else "")
            logger.info("  - 建议: 可以开始准备定制化训练数据")
        elif summary['thinking_avg_score'] >= 0.4:
            logger.info("⚠ 基础表现中等")
            logger.info("  - 模型有一定理解能力，但不够精准")
            if summary['improvement'] > 0.1:
                logger.info("  - Thinking模式有明显提升，证明了显式推理的价值")
            logger.info("  - 建议: 需要高质量的微调数据")
        else:
            logger.info("✗ 基础表现较差")
            logger.info("  - 模型难以理解内网场景")
            logger.info("  - 建议:")
            logger.info("    1. 尝试Stage 3 (DPO)模型")
            logger.info("    2. 准备大量高质量的训练数据")
            logger.info("    3. 考虑使用更大的基础模型")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_suffix = "_quick" if args.quick else "_full"
        output_file = f'tests/trlm_baseline_{args.stage}{mode_suffix}_{timestamp}.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"\n详细结果已保存到: {output_file}")
        
        # 生成Markdown报告
        md_file = output_file.replace('.json', '.md')
        generate_markdown_report(summary, md_file)
        logger.info(f"Markdown报告已保存到: {md_file}")
        
    else:
        logger.error(f"测试失败: {summary.get('error', 'Unknown error')}")


def generate_markdown_report(summary: Dict[str, Any], output_file: str):
    """生成Markdown格式的测试报告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# TRLM-135M 内网场景基础测试报告\n\n")
        f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**模型路径**: {summary['model_path']}\n")
        f.write(f"**测试数量**: {summary['total_tests']}\n\n")
        
        f.write("## 测试总结\n\n")
        f.write(f"- **直接回答平均分**: {summary['direct_avg_score']*100:.1f}%\n")
        f.write(f"- **Thinking模式平均分**: {summary['thinking_avg_score']*100:.1f}%\n")
        f.write(f"- **提升**: {summary['improvement']*100:.1f}%\n\n")
        
        f.write("## 按类别表现\n\n")
        f.write("| 类别 | 平均分 | 最高分 | 最低分 |\n")
        f.write("|------|--------|--------|--------|\n")
        for category, perf in summary['category_performance'].items():
            f.write(f"| {category} | {perf['avg']*100:.1f}% | {perf['max']*100:.1f}% | {perf['min']*100:.1f}% |\n")
        
        f.write("\n## 详细测试结果\n\n")
        for i, result in enumerate(summary['results'], 1):
            mode = "Thinking模式" if result['use_thinking'] else "直接回答"
            quality_emoji = {"good": "✓", "medium": "⚠", "poor": "✗"}
            f.write(f"### {i}. {result['category']} - {result['description']}\n\n")
            f.write(f"**模式**: {mode}\n")
            f.write(f"**评分**: {result['total_score']*100:.1f}% ({quality_emoji.get(result['quality'], '?')}) \n")
            f.write(f"**问题**: {result['question']}\n\n")
            f.write(f"**回答**:\n```\n{result['response']}\n```\n\n")
            f.write(f"**期望元素**: {result['expected_elements']}\n")
            f.write(f"**找到元素**: {result['found_elements']}\n")
            f.write(f"**覆盖率**: {result['element_coverage']*100:.1f}%\n\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n测试被用户中断")
    except Exception as e:
        logger.error(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()