#!/usr/bin/env python3
"""
下载 trlm-135M 模型的三个阶段检查点

TRLM (Tiny Reasoning Language Model) - 135M参数推理模型
GitHub: https://github.com/Shekswess/trlm
Model Hub: https://huggingface.co/Shekswess/

三个阶段:
1. Stage 1: 基础SFT (无思考链)
2. Stage 2: <thinking>推理SFT
3. Stage 3: DPO偏好对齐

使用方法:
    python scripts/download_trlm.py --stage all
    python scripts/download_trlm.py --stage stage1
    python scripts/download_trlm.py --stage stage2
    python scripts/download_trlm.py --stage stage3
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("错误: 需要安装 huggingface-hub")
    print("运行: pip install huggingface-hub")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/trlm_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 模型配置
MODELS = {
    'stage1': {
        'repo_id': 'Shekswess/trlm-stage-1-sft-final-2',
        'description': '基础SFT模型（无思考链）',
        'local_dir': 'ext/09-models-trlm/stage1-sft-final-2'
    },
    'stage2': {
        'repo_id': 'Shekswess/trlm-stage-2-sft-final-2',
        'description': '<thinking>推理SFT模型',
        'local_dir': 'ext/09-models-trlm/stage2-sft-final-2'
    },
    'stage3': {
        'repo_id': 'Shekswess/trlm-stage-3-dpo-final-2',
        'description': 'DPO偏好对齐模型',
        'local_dir': 'ext/09-models-trlm/stage3-dpo-final-2'
    }
}


def download_model(stage_name: str) -> bool:
    """
    下载指定阶段的模型
    
    Args:
        stage_name: stage1, stage2, stage3
        
    Returns:
        bool: 下载是否成功
    """
    if stage_name not in MODELS:
        logger.error(f"未知的阶段: {stage_name}")
        logger.info(f"可用阶段: {', '.join(MODELS.keys())}")
        return False
    
    model_config = MODELS[stage_name]
    logger.info(f"开始下载 {stage_name}: {model_config['description']}")
    logger.info(f"仓库: {model_config['repo_id']}")
    
    # 确保输出目录存在
    local_dir = Path(model_config['local_dir'])
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 下载模型
        logger.info("正在下载模型文件...")
        snapshot_download(
            repo_id=model_config['repo_id'],
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        logger.info(f"✓ {stage_name} 下载成功: {local_dir}")
        
        # 检查下载的文件
        files = list(local_dir.iterdir())
        logger.info(f"下载了 {len(files)} 个文件:")
        for f in sorted(files):
            size_mb = f.stat().st_size / (1024 * 1024) if f.is_file() else 0
            logger.info(f"  - {f.name} ({size_mb:.2f} MB)" if f.is_file() else f"  - {f.name}/")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ {stage_name} 下载失败: {e}")
        return False


def verify_downloads() -> dict:
    """
    验证已下载的模型
    
    Returns:
        dict: 验证结果
    """
    results = {}
    
    for stage_name, model_config in MODELS.items():
        local_dir = Path(model_config['local_dir'])
        
        if local_dir.exists():
            # 检查关键文件
            required_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json']
            files = [f.name for f in local_dir.iterdir()]
            
            missing = [f for f in required_files if f not in files]
            results[stage_name] = {
                'exists': True,
                'complete': len(missing) == 0,
                'missing_files': missing,
                'file_count': len(files)
            }
        else:
            results[stage_name] = {
                'exists': False,
                'complete': False,
                'missing_files': [],
                'file_count': 0
            }
    
    return results


def main():
    parser = argparse.ArgumentParser(description='下载 trlm-135M 模型')
    parser.add_argument(
        '--stage',
        type=str,
        default='all',
        choices=['all', 'stage1', 'stage2', 'stage3'],
        help='要下载的阶段 (默认: all)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='仅验证已下载的模型'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("TRLM-135M 模型下载工具")
    logger.info("=" * 60)
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"项目根目录: {project_root}")
    logger.info("")
    
    # 仅验证模式
    if args.verify:
        logger.info("验证已下载的模型...")
        results = verify_downloads()
        
        logger.info("\n验证结果:")
        for stage_name, result in results.items():
            status = "✓" if result['exists'] and result['complete'] else "✗"
            logger.info(f"\n{status} {stage_name}:")
            logger.info(f"  存在: {result['exists']}")
            logger.info(f"  完整: {result['complete']}")
            logger.info(f"  文件数: {result['file_count']}")
            if result['missing_files']:
                logger.info(f"  缺失文件: {', '.join(result['missing_files'])}")
        
        return
    
    # 下载模式
    if args.stage == 'all':
        logger.info("将下载所有三个阶段的模型...")
        stages_to_download = ['stage1', 'stage2', 'stage3']
    else:
        stages_to_download = [args.stage]
    
    logger.info(f"计划下载: {', '.join(stages_to_download)}")
    logger.info("")
    
    # 执行下载
    success_count = 0
    failed_stages = []
    
    for stage_name in stages_to_download:
        if download_model(stage_name):
            success_count += 1
        else:
            failed_stages.append(stage_name)
        logger.info("")
    
    # 最终报告
    logger.info("=" * 60)
    logger.info("下载完成")
    logger.info("=" * 60)
    logger.info(f"成功: {success_count}/{len(stages_to_download)}")
    
    if failed_stages:
        logger.warning(f"失败: {', '.join(failed_stages)}")
        logger.info("可以稍后重新运行下载失败的阶段")
    
    # 显示验证结果
    logger.info("\n验证结果:")
    results = verify_downloads()
    for stage_name, result in results.items():
        status = "✓" if result['exists'] and result['complete'] else "✗"
        config = MODELS[stage_name]
        logger.info(f"  {status} {stage_name}: {config['description']}")
        if result['exists']:
            logger.info(f"      目录: {config['local_dir']}")
    
    logger.info("")
    logger.info("下一步:")
    logger.info("  运行基础验证: python scripts/validate_trlm.py")
    logger.info("  运行内网场景测试: python tests/test_trlm_baseline.py")


if __name__ == '__main__':
    main()