#!/usr/bin/env python3
"""
===============================================================================
C++ AI Assistant - 打包脚本（用于传输到虚拟机）

功能: 将ext目录和必要文件打包，方便传输到虚拟机离线安装

使用方法:
    python scripts/package_for_vm.py
    python scripts/package_for_vm.py --output ../cpp-ai-assistant-offline.zip

作者: Cline
版本: 1.0.0
日期: 2026-02-06
===============================================================================
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import logging


class PackageLogger:
    """打包日志记录器"""
    
    def __init__(self, log_file: str = "package.log"):
        self.logger = logging.getLogger("PackageGenerator")
        self.logger.setLevel(logging.INFO)
        
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


class PackageGenerator:
    """离线安装包生成器"""
    
    def __init__(self, output_file: str = None):
        # 基础路径
        self.script_dir = Path(__file__).parent.parent
        self.ext_dir = self.script_dir / "ext"
        
        # 输出文件
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.script_dir.parent / f"cpp-ai-assistant-offline-{timestamp}.zip"
        
        self.output_file = Path(output_file)
        self.log = PackageLogger(str(self.script_dir / "package.log"))
        
        # 打包统计
        self.stats = {
            "total_files": 0,
            "total_size": 0
        }
    
    def get_package_contents(self):
        """获取要打包的内容"""
        contents = []
        
        # 核心文件
        core_files = [
            "install.py",
            "requirements-pip.txt",
            "requirements-wheels.txt",
            "SESSION_CONTEXT.md",
            "README.md",
            "DEPLOYMENT.md",
            "OFFLINE_DEPLOYMENT.md",
            "IMPLEMENTATION_SUMMARY.md"
        ]
        
        for filename in core_files:
            file_path = self.script_dir / filename
            if file_path.exists():
                contents.append(("core", file_path))
        
        # backend目录
        backend_dir = self.script_dir / "backend"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                rel_path = py_file.relative_to(self.script_dir)
                contents.append(("backend", py_file))
        
        # ext目录
        if self.ext_dir.exists():
            for file_path in self.ext_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(self.script_dir)
                    contents.append(("ext", file_path))
        
        # scripts目录（下载脚本和打包脚本）
        scripts_dir = self.script_dir / "scripts"
        if scripts_dir.exists():
            for script_file in scripts_dir.rglob("*"):
                if script_file.is_file():
                    rel_path = script_file.relative_to(self.script_dir)
                    contents.append(("scripts", script_file))
        
        # config目录
        config_dir = self.script_dir / "config"
        if config_dir.exists():
            for config_file in config_dir.rglob("*"):
                if config_file.is_file():
                    rel_path = config_file.relative_to(self.script_dir)
                    contents.append(("config", config_file))
        
        return contents
    
    def create_package(self):
        """创建离线安装包"""
        self.log.section("C++ AI Assistant 离线安装包生成")
        self.log.info(f"目标文件: {self.output_file}")
        
        try:
            # 获取要打包的内容
            self.log.info("扫描文件...")
            contents = self.get_package_contents()
            
            if not contents:
                self.log.error("未找到任何文件，请先运行下载脚本")
                return False
            
            self.log.info(f"找到 {len(contents)} 个文件")
            
            # 计算总大小
            total_size = sum(f.stat().st_size for _, f in contents)
            self.log.info(f"总大小: {total_size / (1024*1024):.2f} MB")
            
            # 创建ZIP文件
            self.log.info("开始打包...")
            
            with zipfile.ZipFile(self.output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for category, file_path in contents:
                    # 添加文件到ZIP
                    arcname = file_path.relative_to(self.script_dir)
                    zipf.write(file_path, arcname)
                    self.stats["total_files"] += 1
                    self.stats["total_size"] += file_path.stat().st_size
                    
                    # 每打包100个文件输出一次进度
                    if self.stats["total_files"] % 100 == 0:
                        self.log.info(f"已打包 {self.stats['total_files']} 个文件...")
            
            self.log.success(f"打包完成!")
            self.log.info(f"输出文件: {self.output_file}")
            self.log.info(f"文件数: {self.stats['total_files']}")
            self.log.info(f"大小: {self.stats['total_size'] / (1024*1024):.2f} MB")
            
            # 创建说明文件
            self._readme_file()
            
            return True
            
        except Exception as e:
            self.log.error(f"打包失败: {str(e)}")
            import traceback
            self.log.error(traceback.format_exc())
            return False
    
    def _readme_file(self):
        """创建离线安装说明"""
        readme_content = f"""# C++ AI Assistant - 离线安装说明

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 文件清单
- 总文件数: {self.stats['total_files']}
- 总大小: {self.stats['total_size'] / (1024*1024):.2f} MB

## 安装步骤

### 1. 解压压缩包
```bash
# 将压缩包复制到虚拟机
unzip cpp-ai-assistant-offline-*.zip
# 或在Windows中使用WinRAR/7-Zip解压
```

### 2. 配置（可选）
编辑 `config.yaml` 文件，配置千问API信息：
```yaml
qwen:
  api_base: "http://your-qwen-endpoint.com/v1"
  api_key: "your-api-key"
  model_name: "qwen-3-235b"
```

### 3. 运行安装脚本
```bash
python install.py
```

安装脚本将自动：
- 安装Python虚拟环境
- 安装Python依赖包
- 安装Node.js（如果需要）
- 配置VSCode扩展

### 4. 启动服务
```bash
# Windows
start.bat

# 或使用Python
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 5. 验证安装
访问健康检查端点：
```bash
http://localhost:8000/health
```

## 常见问题

### Q: Python版本不匹配？
A: install.py会自动检测Python版本，建议使用Python 3.11.9

### Q: 依赖包安装失败？
A: 检查 ext 目录是否完整，查看 install_*.log 日志文件

### Q: 模型下载失败？
A: 模型较大（约500MB），可以跳过模型下载，首次运行时自动下载

### Q: VSCode扩展无法安装？
A: 确保已安装Node.js，或手动安装 .vsix 文件

## 日志文件
- install_*.log - 安装日志
- download.log - 下载日志（如果有）
- package.log - 打包日志

## 更多帮助
查看详细文档：
- SESSION_CONTEXT.md - 项目状态和下一步
- DEPLOYMENT.md - 完整部署指南
- OFFLINE_DEPLOYMENT.md - 离线部署指南

祝使用愉快！
"""
        
        readme_file = self.script_dir / "INSTALL Offline_README.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.log.success(f"安装说明已生成: {readme_file.name}")
    
    def run(self):
        """执行打包流程"""
        success = self.create_package()
        
        if success:
            self.log.info("")
            self.log.section("下一步")
            self.log.info("1. 将压缩包传输到虚拟机（U盘、网络共享等）")
            self.log.info("2. 在虚拟机中解压压缩包")
            self.log.info("3. 运行: python install.py")
            self.log.info("")
            self.log.success("打包完成!")
        else:
            self.log.error("打包失败")
        
        return success


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="C++ AI Assistant - 打包离线安装包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/package_for_vm.py
  python scripts/package_for_vm.py --output package.zip
  python scripts/package_for_vm.py --output ../offline-package.zip
        """
    )
    
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出文件路径（默认: cpp-ai-assistant-offline-TIMESTAMP.zip）"
    )
    
    args = parser.parse_args()
    
    packager = PackageGenerator(output_file=args.output)
    success = packager.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()