#!/usr/bin/env python3
"""
TRLM-135M 基础验证测试脚本

目的:
1. 验证模型能否正常加载
2. 测试推理能力（基础对话、显式思考）
3. 评估内存占用和推理速度
4. 对比三个阶段的性能差异

使用方法:
    python scripts/validate_trlm.py --stage stage2
    python scripts/validate_trlm.py --stage all
"""

import os
import sys
import time
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
        logging.FileHandler('scripts/trlm_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 内存监控
try:
    import psutil
    def get_memory_usage_mb():
        """获取当前进程内存使用（MB）"""
        return psutil.Process().memory_info().rss / (1024 * 1024)
except ImportError:
    logger.warning("psutil 未安装，无法监控内存使用")
    def get_memory_usage_mb():
        return 0


# 测试用例
TEST_CASES = {
    'basic': [
        {
            'question': 'What is 2 + 2?',
            'expected_keywords': ['4', 'four'],
            'description': '简单算术'
        },
        {
            'question': 'Explain what recursion is.',
            'expected_keywords': ['function', 'call', 'itself', 'recursive'],
            'description': '编程概念解释'
        },
        {
            'question': 'What is the capital of France?',
            'expected_keywords': ['Paris'],
            'description': '常识问答'
        }
    ],
    'reasoning': [
        {
            'question': 'If I have 3 apples and eat 1, then buy 2 more, how many do I have?',
            'expected_keywords': ['4', 'four'],
            'description': '多步推理'
        },
        {
            'question': 'A train leaves station A at 10:00 traveling at 60 mph. Station B is 120 miles away. What time does it arrive?',
            'expected_keywords': ['12:00', '12', 'noon'],
            'description': '应用题'
        }
    ],
    'internal_knowledge': [
        {
            'question': 'How do I find a file in a Linux system?',
            'expected_keywords': ['find', 'locate', 'grep'],
            'description': '系统命令'
        },
        {
            'question': 'What is the purpose of a Makefile?',
            'expected_keywords': ['build', 'compile', 'make'],
            'description': '构建工具'
        }
    ]
}


class TRLMValidator:
    """TRLM 模型验证器"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        self.device = 'cpu'
        
    def load_model(self) -> bool:
        """加载模型"""
        try:
            logger.info(f"加载模型: {self.model_path}")
            
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # 记录加载前内存
            mem_before = get_memory_usage_mb()
            logger.info(f"加载前内存: {mem_before:.2f} MB")
            
            # 加载 tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            logger.info("✓ Tokenizer 加载完成")
            
            # 加载模型（使用CPU）
            import torch
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map='cpu'  # 强制使用CPU
            )
            self.model.eval()
            logger.info("✓ 模型加载完成")
            
            # 记录加载后内存
            mem_after = get_memory_usage_mb()
            mem_used = mem_after - mem_before
            logger.info(f"加载后内存: {mem_after:.2f} MB")
            logger.info(f"模型占用: {mem_used:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            max_new_tokens: 最大生成token数
            
        Returns:
            str: 生成的文本
        """
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            start_time = time.time()
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generation_time = time.time() - start_time
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 计算tokens/s
            generated_tokens = outputs.shape[1] - inputs['input_ids'].shape[1]
            tokens_per_sec = generated_tokens / generation_time if generation_time > 0 else 0
            
            logger.info(f"生成时间: {generation_time:.2f}s, "
                       f"生成tokens: {generated_tokens}, "
                       f"速度: {tokens_per_sec:.2f} tokens/s")
            
            return response
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            return f"Error: {str(e)}"
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个测试用例
        
        Args:
            test_case: 测试用例字典
            
        Returns:
            dict: 测试结果
        """
        question = test_case['question']
        expected_keywords = test_case['expected_keywords']
        description = test_case['description']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"测试: {description}")
        logger.info(f"问题: {question}")
        
        start_time = time.time()
        memory_before = get_memory_usage_mb()
        
        # 生成回答
        if '<thinking>' in expected_keywords or 'thinking' in test_case.get('description', '').lower():
            # 使用带 <thinking> 的提示
            prompt = f"""{question}

Please show your thinking process in <thinking> tags, then provide the answer.

<thinking>
</thinking>
"""
        else:
            prompt = f"{question}\nAnswer:"
        
        response = self.generate(prompt, max_new_tokens=256)
        
        generation_time = time.time() - start_time
        memory_after = get_memory_usage_mb()
        
        # 检查关键词
        response_lower = response.lower()
        found_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]
        keywords_matched = len(found_keywords) / len(expected_keywords)
        
        # 判断是否通过
        passed = keywords_matched >= 0.5  # 至少50%关键词匹配
        
        result = {
            'description': description,
            'question': question,
            'response': response.strip(),
            'expected_keywords': expected_keywords,
            'found_keywords': found_keywords,
            'keywords_matched': keywords_matched,
            'passed': passed,
            'generation_time': generation_time,
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'memory_used_mb': memory_after - memory_before
        }
        
        logger.info(f"回答: {response.strip()[:200]}...")
        logger.info(f"期望关键词: {expected_keywords}")
        logger.info(f"找到关键词: {found_keywords}")
        logger.info(f"匹配率: {keywords_matched*100:.1f}%")
        logger.info(f"结果: {'✓ 通过' if passed else '✗ 未通过'}")
        
        return result
    
    def validate(self) -> Dict[str, Any]:
        """
        运行完整验证
        
        Returns:
            dict: 验证结果
        """
        if not self.load_model():
            return {'success': False, 'error': 'Model loading failed'}
        
        all_results = []
        
        # 运行所有测试
        for category, cases in TEST_CASES.items():
            logger.info(f"\n\n{'#'*60}")
            logger.info(f"测试类别: {category.upper()}")
            logger.info(f"{'#'*60}")
            
            category_results = []
            for test_case in cases:
                result = self.run_test_case(test_case)
                category_results.append(result)
                all_results.append(result)
        
        # 统计结果
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r['passed'])
        avg_generation_time = sum(r['generation_time'] for r in all_results) / total_tests
        avg_memory = sum(r['memory_used_mb'] for r in all_results) / total_tests
        
        summary = {
            'success': True,
            'model_path': str(self.model_path),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': passed_tests / total_tests,
            'avg_generation_time': avg_generation_time,
            'avg_memory_mb': avg_memory,
            'results': all_results
        }
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='验证 trlm-135M 模型')
    parser.add_argument(
        '--stage',
        type=str,
        default='stage2',
        choices=['stage1', 'stage2', 'stage3'],
        help='要验证的阶段 (默认: stage2)'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        help='自定义模型路径'
    )
    
    args = parser.parse_args()
    
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
    logger.info("TRLM-135M 基础验证测试")
    logger.info("=" * 60)
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"阶段: {args.stage}")
    logger.info(f"模型路径: {model_path}")
    logger.info("")
    
    # 检查模型路径
    if not Path(model_path).exists():
        logger.error(f"模型路径不存在: {model_path}")
        logger.info("请先运行: python scripts/download_trlm.py --stage " + args.stage)
        return
    
    # 运行验证
    validator = TRLMValidator(model_path)
    summary = validator.validate()
    
    # 输出总结
    logger.info("\n\n" + "=" * 60)
    logger.info("验证总结")
    logger.info("=" * 60)
    
    if summary['success']:
        logger.info(f"总测试数: {summary['total_tests']}")
        logger.info(f"通过数: {summary['passed_tests']}")
        logger.info(f"通过率: {summary['pass_rate']*100:.1f}%")
        logger.info(f"平均生成时间: {summary['avg_generation_time']:.2f}s")
        logger.info(f"平均内存占用: {summary['avg_memory_mb']:.2f} MB")
        
        # 按类别统计
        logger.info("\n按类别统计:")
        category_stats = {}
        for result in summary['results']:
            category = result['description']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'passed': 0}
            category_stats[category]['total'] += 1
            if result['passed']:
                category_stats[category]['passed'] += 1
        
        for category, stats in category_stats.items():
            logger.info(f"  {category}: {stats['passed']}/{stats['total']} "
                       f"({stats['passed']/stats['total']*100:.1f}%)")
        
        # 保存结果
        output_file = f'scripts/trlm_validation_{args.stage}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"\n详细结果已保存到: {output_file}")
    else:
        logger.error(f"验证失败: {summary.get('error', 'Unknown error')}")
    
    logger.info("\n建议:")
    if summary['success'] and summary['pass_rate'] >= 0.7:
        logger.info("✓ 模型表现良好，适合作为内网知识推理引擎")
        logger.info("  下一步: 收集内网数据准备微调")
    elif summary['success']:
        logger.info("⚠ 模型表现一般，建议:")
        logger.info("  1. 尝试Stage 3 (DPO)模型")
        logger.info("  2. 调整推理参数(temperature, max_tokens)")
        logger.info("  3. 准备高质量的微调数据")
    else:
        logger.info("✗ 模型加载失败，请检查:")
        logger.info("  1. 模型文件完整性")
        logger.info("  2. 依赖库版本(transformers, torch)")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n测试被用户中断")
    except Exception as e:
        logger.error(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()