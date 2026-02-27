#!/usr/bin/env python3
"""
===============================================================================
C++ AI Assistant - 一键自动下载所有依赖脚本

功能: 在有网络环境中自动下载所有安装包，用于离线部署
     包括Python包、Node.js运行时、嵌入模型、MCP服务器等

使用方法:
    python scripts/download_dependencies.py

作者: Cline
版本: 2.1.0
日期: 2026-02-07
===============================================================================
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
import shutil
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import time


class DownloadLogger:
    """下载日志记录器"""
    
    def __init__(self, log_file: str = "download.log"):
        self.logger = logging.getLogger("DependencyDownloader")
        self.logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def success(self, message: str):
        self.logger.info(f"[SUCCESS] {message}")
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def section(self, message: str):
        separator = "=" * 70
        self.logger.info("")
        self.logger.info(separator)
        self.logger.info(f"  {message}")
        self.logger.info(separator)


class DependencyDownloader:
    """依赖下载器"""
    
    def __init__(self, python_version: str = "3.11.9"):
        self.python_version = python_version
        
        # 基础路径
        self.script_dir = Path(__file__).parent.parent
        self.ext_dir = self.script_dir / "ext"
        self.log = DownloadLogger(str(self.script_dir / "download.log"))
        
        # 下载统计
        self.stats = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "total_size": 0,
            "errors": []
        }
    
    def setup_directories(self):
        """创建必要的目录"""
        self.log.section("创建下载目录")
        
        directories = [
            self.ext_dir / "01-python-pip",
            self.ext_dir / "02-python-wheels",
            self.ext_dir / "03-nodejs-npm",
            self.ext_dir / "05-runtime-python",
            self.ext_dir / "06-runtime-nodejs",
            self.ext_dir / "07-tools-tree-sitter",
            self.ext_dir / "08-models-embeddings",
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.log.info(f"✓ 创建: {directory}")
    
    def run_command(self, command: List[str], description: str = "",
                   cwd: str = None, env: dict = None, retry: int = 3) -> Tuple[bool, str, str]:
        """运行命令（支持重试）"""
        for attempt in range(retry):
            self.log.info(f"执行: {description}")
            if attempt > 0:
                self.log.info(f"重试 {attempt + 1}/{retry}...")
            
            try:
                # 合并环境变量
                run_env = os.environ.copy()
                if env:
                    run_env.update(env)
                
                # 在Windows下设置UTF-8编码
                if os.name == 'nt':
                    run_env['PYTHONUTF8'] = '1'
                    run_env['PYTHONIOENCODING'] = 'utf-8'
                
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    cwd=cwd or str(self.script_dir),
                    env=run_env,
                    timeout=1800  # 30分钟超时
                )
                
                if result.returncode == 0:
                    self.log.success(f"完成: {description}")
                    return True, result.stdout, result.stderr
                else:
                    if attempt == retry - 1:
                        self.log.error(f"失败: {description}")
                        if result.stderr:
                            self.log.error(f"错误: {result.stderr}")
                    time.sleep(2)
                    
            except subprocess.TimeoutExpired:
                if attempt == retry - 1:
                    self.log.error(f"超时: {description}")
                time.sleep(5)
            except Exception as e:
                if attempt == retry - 1:
                    self.log.error(f"异常: {description} - {str(e)}")
                time.sleep(2)
        
        return False, "", ""
    
    def download_python_packages(self):
        """下载Python包"""
        self.log.section("下载 Python 包")
        
        # 检查pip
        success, _, _ = self.run_command(
            ["pip", "--version"],
            description="检查pip"
        )
        if not success:
            self.log.error("未找到pip，请先安装Python")
            return False
        
        # 下载wheel包（设置UTF-8编码）
        self.log.info("下载Python Wheel包...")
        wheels_dir = self.ext_dir / "02-python-wheels"
        
        # 检查是否已有wheel包
        existing_wheels = list(wheels_dir.glob("*.whl"))
        if existing_wheels:
            self.log.info(f"✓ 检测到 {len(existing_wheels)} 个wheel包已存在")
            self.log.info("✓ 跳过wheel包下载（使用现有的包）")
            self.stats["total_files"] += len(existing_wheels)
            self.stats["successful"] += len(existing_wheels)
            return True
        
        # 设置环境变量确保pip使用UTF-8编码
        self.log.info("开始下载wheel包...")
        env = {'PYTHONIOENCODING': 'utf-8'}
        
        # 使用优化后的wheel文件
        wheels_files = [
            "requirements-cp311.txt",
            "requirements-py3-universal.txt"
        ]
        
        total_downloaded = 0
        for wheels_file in wheels_files:
            if not (self.script_dir / wheels_file).exists():
                self.log.warning(f"文件不存在: {wheels_file}，跳过")
                continue
            
            self.log.info(f"使用配置文件: {wheels_file}")
            success, stdout, stderr = self.run_command(
                [
                    "pip", "download",
                    "-r", wheels_file,
                    "-d", str(wheels_dir),
                    "--platform", "win_amd64",
                    "--only-binary", ":all:",
                    "--python-version", self.python_version,
                    "--exists-action", "i"  # 忽略已存在的文件
                ],
                description=f"下载wheel包 ({wheels_file})",
                env=env,
                retry=3
            )
            
            if success:
                # 统计新下载的文件
                current_wheels = list(wheels_dir.glob("*.whl"))
                new_count = len(current_wheels) - total_downloaded
                if new_count > 0:
                    self.log.success(f"✓ {wheels_file}: 下载了 {new_count} 个wheel包")
                    total_downloaded = len(current_wheels)
            else:
                self.log.warning(f"⚠️ {wheels_file} 下载失败或部分失败")
        
        # 最终统计
        final_wheels = list(wheels_dir.glob("*.whl"))
        size = sum(f.stat().st_size for f in final_wheels) / (1024 * 1024)
        self.log.success(f"✓ 总计: {len(final_wheels)} 个wheel包 ({size:.1f} MB)")
        self.stats["total_files"] += len(final_wheels)
        self.stats["successful"] += len(final_wheels)
        self.stats["total_size"] += size
        return True
    
    def download_python_runtime(self):
        """下载Python运行时"""
        self.log.section("下载 Python 运行时")
        
        python_dir = self.ext_dir / "05-runtime-python"
        installer_path = python_dir / f"python-{self.python_version}-amd64.exe"
        
        if installer_path.exists():
            self.log.info(f"Python安装包已存在: {installer_path.name}")
            return True
        
        self.log.info(f"下载Python {self.python_version}...")
        
        # Python官方下载URL
        url = f"https://www.python.org/ftp/python/{self.python_version.rstrip('.0')}/python-{self.python_version}-amd64.exe"
        
        try:
            self._download_file(url, installer_path, f"Python {self.python_version}")
            size = installer_path.stat().st_size / (1024 * 1024)
            self.log.success(f"Python运行时: {size:.1f} MB")
            self.stats["total_files"] += 1
            self.stats["successful"] += 1
            self.stats["total_size"] += size
            return True
        except Exception as e:
            self.log.error(f"Python运行时下载失败: {e}")
            self.stats["failed"] += 1
            return False
    
    def download_nodejs_runtime(self):
        """下载Node.js运行时"""
        self.log.section("下载 Node.js 运行时")
        
        nodejs_dir = self.ext_dir / "06-runtime-nodejs"
        node_version = "18.19.0"
        installer_path = nodejs_dir / f"node-v{node_version}-x64.msi"
        
        if installer_path.exists():
            self.log.info(f"Node.js安装包已存在: {installer_path.name}")
            return True
        
        self.log.info(f"下载Node.js {node_version}...")
        
        # Node.js官方下载URL
        url = f"https://nodejs.org/dist/v{node_version}/node-v{node_version}-x64.msi"
        
        try:
            self._download_file(url, installer_path, f"Node.js {node_version}")
            size = installer_path.stat().st_size / (1024 * 1024)
            self.log.success(f"Node.js运行时: {size:.1f} MB")
            self.stats["total_files"] += 1
            self.stats["successful"] += 1
            self.stats["total_size"] += size
            return True
        except Exception as e:
            self.log.error(f"Node.js运行时下载失败: {e}")
            self.stats["failed"] += 1
            return False
    
    def download_npm_packages(self):
        """下载npm包"""
        self.log.section("下载 NPM 包")
        
        # 检查npm
        npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
        success, _, _ = self.run_command(
            [npm_cmd, "--version"],
            description="检查npm"
        )
        if not success:
            self.log.warning("未找到npm，跳过npm包下载")
            return False
        
        npm_dir = self.ext_dir / "03-nodejs-npm"
        
        # TypeScript和编译工具
        typescript_packages = [
            "typescript@5.3.3",
            "@types/node@20.11.0",
            "@types/vscode@1.85.0",
            "vsce@2.15.0"
        ]
        
        # MCP服务器（仅下载，不安装）
        mcp_servers = [
            "@modelcontextprotocol/server-memory",
            "@modelcontextprotocol/server-sequential-thinking",
            "@modelcontextprotocol/server-filesystem",
            "@modelcontextprotocol/server-puppeteer",
            "@arabold/docs-mcp-server",
            "@buger/docs-mcp"
        ]
        
        # 分组下载
        self.log.info("下载TypeScript和编译工具...")
        for package in typescript_packages:
            self.log.info(f"下载: {package}")
            success, stdout, stderr = self.run_command(
                [npm_cmd, "pack", package],
                description=f"下载npm包: {package}",
                cwd=str(npm_dir),
                retry=3
            )
            
            if success:
                self.log.success(f"✓ {package}")
                self.stats["total_files"] += 1
                self.stats["successful"] += 1
            else:
                self.log.warning(f"✗ {package} 下载失败")
                self.stats["failed"] += 1
        
        self.log.info("下载MCP服务器（仅下载，不安装）...")
        for package in mcp_servers:
            self.log.info(f"下载: {package}")
            success, stdout, stderr = self.run_command(
                [npm_cmd, "pack", package],
                description=f"下载MCP服务器: {package}",
                cwd=str(npm_dir),
                retry=3
            )
            
            if success:
                self.log.success(f"✓ {package}")
                self.stats["total_files"] += 1
                self.stats["successful"] += 1
            else:
                self.log.warning(f"✗ {package} 下载失败")
                self.stats["failed"] += 1
        
        return True
    
    def download_tree_sitter(self):
        """下载Tree-sitter CLI"""
        self.log.warning("Tree-sitter CLI下载已禁用")
        self.log.info("Tree-sitter将通过Python包自动安装，无需单独下载")
        return True
    
    def download_embedding_models(self):
        """下载嵌入模型"""
        self.log.section("下载嵌入模型")
        self.log.info("下载sentence-transformers/all-MiniLM-L6-v2模型...")
        
        models_dir = self.ext_dir / "08-models-embeddings"
        
        # 检查sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.log.info(f"下载模型: {model_name}")
            
            try:
                model = SentenceTransformer(model_name)
                save_path = models_dir / model_name.replace("/", "-")
                model.save(str(save_path))
                size = sum(f.stat().st_size for f in save_path.rglob("*")) / (1024 * 1024)
                self.log.success(f"✓ {model_name} ({size:.1f} MB)")
                self.stats["total_files"] += 1
                self.stats["successful"] += 1
                self.stats["total_size"] += size
            except Exception as e:
                self.log.error(f"模型下载失败: {model_name} - {e}")
                self.stats["failed"] += 1
            
            return True
            
        except ImportError:
            self.log.warning("未安装sentence-transformers，跳过模型下载")
            self.log.info("模型将在首次运行时自动下载")
            return False
    
    def _download_file(self, url: str, dest_path: Path, description: str = ""):
        """下载单个文件（带进度）"""
        self.log.info(f"下载中: {description}")
        
        def report_progress(block_num, block_size, total_size):
            progress = block_num * block_size
            if total_size > 0:
                percent = min(progress / total_size * 100, 100)
                sys.stdout.write(f"\r  进度: {percent:.1f}% ({progress/(1024*1024):.1f}MB/{total_size/(1024*1024):.1f}MB)")
                sys.stdout.flush()
        
        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print()  # 换行
    
    def generate_report(self):
        """生成下载报告"""
        self.log.section("下载报告")
        
        report_file = self.script_dir / "download_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("C++ AI Assistant - 依赖下载报告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python版本: {self.python_version}\n\n")
            f.write("-" * 70 + "\n")
            f.write("下载统计:\n")
            f.write("-" * 70 + "\n")
            f.write(f"总文件数: {self.stats['total_files']}\n")
            f.write(f"成功: {self.stats['successful']}\n")
            f.write(f"失败: {self.stats['failed']}\n")
            f.write(f"总大小: {self.stats['total_size']:.2f} MB\n\n")
            
            if self.stats['failed'] > 0:
                f.write("-" * 70 + "\n")
                f.write("失败项目:\n")
                f.write("-" * 70 + "\n")
                for error in self.stats['errors']:
                    f.write(f"✗ {error}\n")
                f.write("\n")
            
            f.write("-" * 70 + "\n")
            f.write("目录结构:\n")
            f.write("-" * 70 + "\n")
            for subdir in sorted(self.ext_dir.iterdir()):
                if subdir.is_dir():
                    files = list(subdir.iterdir())
                    if files:
                        size = sum(f.stat().st_size for f in files) / (1024 * 1024)
                        f.write(f"{subdir.name}/\n")
                        f.write(f"  文件数: {len(files)}\n")
                        f.write(f"  大小: {size:.2f} MB\n\n")
        
        self.log.success(f"报告已生成: {report_file}")
        self.log.info("")
        self.log.info("摘要:")
        self.log.info(f"  下载文件: {self.stats['total_files']} 个")
        self.log.info(f"  成功: {self.stats['successful']}")
        self.log.info(f"  失败: {self.stats['failed']}")
        self.log.info(f"  总大小: {self.stats['total_size']:.2f} MB")
        
        if self.stats['failed'] > 0:
            self.log.warning(f"有 {self.stats['failed']} 个下载失败，请检查日志")
    
    def generate_manifest(self):
        """生成离线安装清单"""
        self.log.section("生成安装清单")
        
        manifest = {
            "version": "2.1.0",
            "python_version": self.python_version,
            "node_version": "18.19.0",
            "created_at": datetime.now().isoformat(),
            "components": {}
        }
        
        # 统计各组件
        for subdir in sorted(self.ext_dir.iterdir()):
            if subdir.is_dir():
                files = list(subdir.iterdir())
                if files:
                    size = sum(f.stat().st_size for f in files) / (1024 * 1024)
                    manifest["components"][subdir.name] = {
                        "count": len(files),
                        "size_mb": round(size, 2),
                        "files": [f.name for f in files]
                    }
        
        manifest_file = self.ext_dir / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        self.log.success(f"清单已生成: {manifest_file}")
    
    def run(self):
        """执行下载流程"""
        self.log.section("C++ AI Assistant 依赖下载")
        self.log.info(f"Python版本: {self.python_version}")
        self.log.info(f"Node.js版本: 18.19.0")
        self.log.info(f"目标目录: {self.ext_dir}")
        
        start_time = time.time()
        
        try:
            # 创建目录
            self.setup_directories()
            
            # 下载各组件
            self.download_python_runtime()
            self.download_python_packages()
            self.download_nodejs_runtime()
            self.download_npm_packages()
            self.download_tree_sitter()
            self.download_embedding_models()
            
            # 生成报告
            self.generate_report()
            self.generate_manifest()
            
            elapsed = time.time() - start_time
            self.log.success(f"\n下载完成! 耗时: {elapsed/60:.1f} 分钟")
            self.log.info(f"\n下一步: 将 ext 目录复制到虚拟机，运行 python install.py")
            
            return True
            
        except KeyboardInterrupt:
            self.log.warning("\n下载被用户中断")
            return False
        except Exception as e:
            self.log.error(f"下载失败: {str(e)}")
            import traceback
            self.log.error(traceback.format_exc())
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="C++ AI Assistant - 一键下载所有依赖",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/download_dependencies.py
  python scripts/download_dependencies.py --python-version 3.11.9
        """
    )
    
    parser.add_argument(
        "--python-version",
        default="3.11.9",
        help="目标Python版本 (默认: 3.11.9)"
    )
    
    args = parser.parse_args()
    
    downloader = DependencyDownloader(
        python_version=args.python_version
    )
    
    success = downloader.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()