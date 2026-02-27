#!/usr/bin/env python3
"""
===============================================================================
C++ AI Assistant - PyPI Wheel可用性智能检查脚本

功能:
  1. 查询PyPI API检查每个包的wheel可用性
  2. 检查本地已下载的wheel文件
  3. 生成优化的requirements文件
  4. 生成详细的Markdown报告

使用方法:
    python scripts/check_wheel_availability.py

作者: Matrix Agent
版本: 1.0.0
日期: 2026-02-06
===============================================================================
"""

import os
import sys
import json
import requests
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from packaging.requirements import Requirement
from packaging.version import parse
from dateutil import parser as date_parser


class WheelChecker:
    """Wheel可用性检查器"""
    
    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path(__file__).parent.parent
        self.wheels_dir = self.project_dir / "ext" / "02-python-wheels"
        self.source_dir = self.project_dir / "ext" / "01-python-pip"
        self.reports_dir = self.project_dir / "reports"
        
        # 创建reports目录
        self.reports_dir.mkdir(exist_ok=True)
        
        # 结果存储
        self.packages_info = {}
        
        # 目标环境
        self.target_python = "3.11"
        self.target_arch = "win_amd64"
        
        print("=" * 70)
        print("  PyPI Wheel可用性智能检查")
        print("=" * 70)
        print(f"项目目录: {self.project_dir}")
        print(f"目标Python: {self.target_python}")
        print(f"目标平台: {self.target_arch}")
        print()
    
    def parse_requirements(self, file_path: Path) -> List[str]:
        """解析requirements文件"""
        packages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                packages.append(line)
        return packages
    
    def get_package_name(self, requirement_line: str) -> str:
        """从requirements行提取包名"""
        req = Requirement(requirement_line)
        # 将包名规范化（e.g., 'Python-Dotenv' -> 'python-dotenv'）
        return req.name.lower().replace('_', '-')
    
    def query_pypi(self, package_name: str) -> Optional[Dict]:
        """查询PyPI API获取包信息"""
        url = f"https://pypi.org/pypi/{package_name}/json"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  ⚠ {package_name}: PyPI返回状态码 {response.status_code}")
                return None
        except Exception as e:
            print(f"  ⚠ {package_name}: 查询失败 - {e}")
            return None
    
    def analyze_wheels(self, package_info: Dict) -> Dict:
        """分析包的wheel可用性"""
        if not package_info or 'releases' not in package_info:
            return {
                'cp311_wheel': None,
                'py3_universal_wheel': None,
                'cp313_wheel': None,
                'has_wheel': False,
                'has_source': False,
                'best_wheel': None,
                'wheel_type': 'none'
            }
        
        releases = package_info['releases']
        wheels = {
            'cp311_wheel': None,
            'py3_universal_wheel': None,
            'cp313_wheel': None,
            'best_wheel': None
        }
        
        has_wheel = False
        has_source = False
        
        # 分析所有版本的文件
        for version, files in releases.items():
            for file_info in files:
                filename = file_info.get('filename', '')
                
                # 检查是否为wheel文件
                if filename.endswith('.whl'):
                    has_wheel = True
                    
                    # 解析wheel文件名
                    # 格式: {package}-{version}-{python_tag}-{abi_tag}-{platform_tag}.whl
                    match = re.match(r'(?P<pkg>.+)-(?P<ver>.+)-(?P<python>.+)-(?P<abi>.+)-(?P<platform>.+)\.whl$', filename)
                    
                    if match:
                        python_tag = match.group('python')
                        ab_tag = match.group('abi')
                        platform_tag = match.group('platform')
                        
                        # 1. Python 3.11专用wheel（最优）
                        if (python_tag == 'cp311' and 
                            platform_tag == self.target_arch and
                            'abi3' not in ab_tag):
                            if wheels['cp311_wheel'] is None:
                                wheels['cp311_wheel'] = file_info
                                wheels['best_wheel'] = file_info
                            else:
                                # 比较上传时间，选最新的
                                try:
                                    current_time = date_parser.parse(file_info.get('upload_time', ''))
                                    existing_time = date_parser.parse(wheels['cp311_wheel'].get('upload_time', ''))
                                    if current_time > existing_time:
                                        wheels['cp311_wheel'] = file_info
                                        wheels['best_wheel'] = file_info
                                except:
                                    pass
                        
                        # 2. Python 3.11 + abi3（次优）
                        elif (python_tag == 'cp311' and 
                              platform_tag == self.target_arch and
                              'abi3' in ab_tag):
                            if wheels['cp311_wheel'] is None:
                                wheels['cp311_wheel'] = file_info
                                if wheels['best_wheel'] is None:
                                    wheels['best_wheel'] = file_info
                        
                        # 3. py3-none-any通用wheel（第三优）
                        elif python_tag == 'py3' and platform_tag == 'any' and ab_tag == 'none':
                            if wheels['py3_universal_wheel'] is None:
                                wheels['py3_universal_wheel'] = file_info
                                if wheels['best_wheel'] is None:
                                    wheels['best_wheel'] = file_info
                            else:
                                # 比较上传时间，选最新的
                                try:
                                    current_time = date_parser.parse(file_info.get('upload_time', ''))
                                    existing_time = date_parser.parse(wheels['py3_universal_wheel'].get('upload_time', ''))
                                    if current_time > existing_time:
                                        wheels['py3_universal_wheel'] = file_info
                                        if wheels['best_wheel'] is None:
                                            wheels['best_wheel'] = file_info
                                except:
                                    pass
                        
                        # 4. Python 3.13专用wheel（用于开发环境）
                        elif python_tag == 'cp313' and platform_tag == self.target_arch:
                            if wheels['cp313_wheel'] is None:
                                wheels['cp313_wheel'] = file_info
                
                # 检查是否有源码包
                elif filename.endswith('.tar.gz') or filename.endswith('.zip'):
                    has_source = True
        
        # 确定wheel类型
        if wheels['cp311_wheel']:
            wheel_type = 'cp311'
        elif wheels['py3_universal_wheel']:
            wheel_type = 'py3_universal'
        elif wheels['cp313_wheel']:
            wheel_type = 'cp313'
        elif has_wheel:
            wheel_type = 'other'
        else:
            wheel_type = 'none'
        
        return {
            'cp311_wheel': wheels['cp311_wheel'],
            'py3_universal_wheel': wheels['py3_universal_wheel'],
            'cp313_wheel': wheels['cp313_wheel'],
            'has_wheel': has_wheel,
            'has_source': has_source,
            'best_wheel': wheels['best_wheel'],
            'wheel_type': wheel_type
        }
    
    def check_local_downloads(self, package_name: str) -> Tuple[List, List]:
        """检查本地已下载的文件"""
        downloaded_wheels = []
        downloaded_sources = []
        
        # 检查wheel目录
        if self.wheels_dir.exists():
            # 使用更宽松的匹配：连字符、下划线都匹配
            for wheel_file in self.wheels_dir.glob("*.whl"):
                # 规范化文件名和包名（连字符和下划线等价）
                file_pkg = wheel_file.stem.split('-')[0]
                # 规范化：连字符和下划线都转换为下划线
                file_pkg_norm = file_pkg.lower().replace('-', '_')
                pkg_name_norm = package_name.lower().replace('-', '_')
                
                if file_pkg_norm == pkg_name_norm or file_pkg == package_name:
                    downloaded_wheels.append(wheel_file)
        
        # 检查源码目录
        if self.source_dir.exists():
            for source_file in self.source_dir.glob("*.tar.gz"):
                file_pkg = source_file.stem.split('-')[0]
                file_pkg_norm = file_pkg.lower().replace('-', '_')
                pkg_name_norm = package_name.lower().replace('-', '_')
                
                if file_pkg_norm == pkg_name_norm or file_pkg == package_name:
                    downloaded_sources.append(source_file)
            
            for source_file in self.source_dir.glob("*.zip"):
                file_pkg = source_file.stem.split('-')[0]
                file_pkg_norm = file_pkg.lower().replace('-', '_')
                pkg_name_norm = package_name.lower().replace('-', '_')
                
                if file_pkg_norm == pkg_name_norm or file_pkg == package_name:
                    downloaded_sources.append(source_file)
        
        return downloaded_wheels, downloaded_sources
    
    def check_packages(self, requirements_file: Path) -> Dict:
        """检查所有包的wheel可用性"""
        print(f"读取requirements文件: {requirements_file.name}")
        packages = self.parse_requirements(requirements_file)
        print(f"找到 {len(packages)} 个包")
        print()
        
        results = {}
        
        for i, req_line in enumerate(packages, 1):
            package_name = self.get_package_name(req_line)
            print(f"[{i}/{len(packages)}] 检查 {package_name}...")
            
            # 查询PyPI
            pypi_info = self.query_pypi(package_name)
            
            # 分析wheel
            wheel_info = self.analyze_wheels(pypi_info)
            
            # 检查本地下载
            local_wheels, local_sources = self.check_local_downloads(package_name)
            
            # 存储结果
            results[package_name] = {
                'requirement': req_line,
                'package_name': package_name,
                'pypi_info': pypi_info,
                'wheel_info': wheel_info,
                'local_wheels': [str(f) for f in local_wheels],
                'local_sources': [str(f) for f in local_sources],
                'has_local_wheel': len(local_wheels) > 0,
                'has_local_source': len(local_sources) > 0,
                'needs_download': (wheel_info['best_wheel'] is not None and 
                                 len(local_wheels) == 0 and 
                                 wheel_info['best_wheel'].get('filename', '').endswith('.whl'))
            }
            
            # 打印简短结果
            self._print_package_summary(package_name, wheel_info, local_wheels)
        
        return results
    
    def _print_package_summary(self, package_name: str, wheel_info: Dict, local_wheels: List):
        """打印包检查摘要"""
        if wheel_info['cp311_wheel']:
            status = "✅ cp311-wheel"
        elif wheel_info['py3_universal_wheel']:
            status = "✅ py3-universal"
        elif wheel_info['cp313_wheel']:
            status = "⚠ cp313-only"
        elif wheel_info['has_wheel']:
            status = "⚠ other-wheel"
        elif wheel_info['has_source']:
            status = "⚠ source-only"
        else:
            status = "❌ no-wheel"
        
        local_status = ""
        if len(local_wheels) > 0:
            local_status = f"[已下载 {len(local_wheels)}]"
        
        print(f"      {status} {local_status}")
    
    def generate_optimized_requirements(self, results: Dict):
        """生成优化的requirements文件"""
        print()
        print("=" * 70)
        print("  生成优化的requirements文件")
        print("=" * 70)
        print()
        
        # 分类包
        cp311_packages = []
        py3_universal_packages = []
        source_packages = []
        
        for package_name, info in results.items():
            if info['wheel_info']['cp311_wheel']:
                cp311_packages.append(info['requirement'])
            elif info['wheel_info']['py3_universal_wheel']:
                py3_universal_packages.append(info['requirement'])
            else:
                source_packages.append(info['requirement'])
        
        # 写入cp311专用requirements
        cp311_file = self.project_dir / "requirements-cp311.txt"
        with open(cp311_file, 'w', encoding='utf-8') as f:
            f.write("# Python 3.11 + Windows x64 专用wheel包\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 包数: {len(cp311_packages)}\n\n")
            for req in sorted(cp311_packages):
                f.write(f"{req}\n")
        print(f"✅ 生成: {cp311_file.name} ({len(cp311_packages)} 个包)")
        
        # 写入通用requirements
        universal_file = self.project_dir / "requirements-py3-universal.txt"
        with open(universal_file, 'w', encoding='utf-8') as f:
            f.write("# Python 3.x通用wheel包（py3-none-any）\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 包数: {len(py3_universal_packages)}\n\n")
            for req in sorted(py3_universal_packages):
                f.write(f"{req}\n")
        print(f"✅ 生成: {universal_file.name} ({len(py3_universal_packages)} 个包)")
        
        # 写入源码requirements
        source_file = self.project_dir / "requirements-source-only.txt"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("# 需要从源码编译的包（无wheel）\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 包数: {len(source_packages)}\n\n")
            for req in sorted(source_packages):
                f.write(f"{req}\n")
        print(f"✅ 生成: {source_file.name} ({len(source_packages)} 个包)")
        
        # 写入合并的wheel requirements（cp311 + universal）
        all_wheels_file = self.project_dir / "requirements-all-wheels.txt"
        with open(all_wheels_file, 'w', encoding='utf-8') as f:
            f.write("# 所有可用wheel包（cp311 + py3-universal）\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 包数: {len(cp311_packages) + len(py3_universal_packages)}\n\n")
            f.write("# Python 3.11专用wheel\n")
            for req in sorted(cp311_packages):
                f.write(f"{req}\n")
            f.write("\n# Python 3.x通用wheel\n")
            for req in sorted(py3_universal_packages):
                f.write(f"{req}\n")
        print(f"✅ 生成: {all_wheels_file.name} ({len(cp311_packages) + len(py3_universal_packages)} 个包)")
        
        print()
        
        return {
            'cp311': cp311_packages,
            'py3_universal': py3_universal_packages,
            'source': source_packages
        }
    
    def generate_markdown_report(self, results: Dict, requirements_files: Dict):
        """生成详细的Markdown报告"""
        print("=" * 70)
        print("  生成详细报告")
        print("=" * 70)
        print()
        
        report_file = self.reports_dir / f"wheel_availability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            # 标题
            f.write("# PyPI Wheel可用性检查报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**目标环境**: Python 3.11 + Windows x64\n\n")
            
            # 摘要
            f.write("## 摘要\n\n")
            f.write("| 类别 | 数量 |\n")
            f.write("|------|------|\n")
            f.write(f"| 总包数 | {len(results)} |\n")
            f.write(f"| cp311专用wheel | {len(requirements_files['cp311'])} |\n")
            f.write(f"| py3通用wheel | {len(requirements_files['py3_universal'])} |\n")
            f.write(f"| 需要源码编译 | {len(requirements_files['source'])} |\n")
            f.write(f"| 无wheel | {len([p for p in results.values() if not p['wheel_info']['has_wheel']])} |\n\n")
            
            # 统计
            cp311_downloaded = sum(1 for r in results.values() if r['has_local_wheel'] and r['wheel_info']['cp311_wheel'])
            py3_universal_downloaded = sum(1 for r in results.values() if r['has_local_wheel'] and r['wheel_info']['py3_universal_wheel'])
            source_downloaded = sum(1 for r in results.values() if r['has_local_source'])
            needs_download = sum(1 for r in results.values() if r['needs_download'])
            
            f.write("### 下载状态\n\n")
            f.write("| 状态 | 数量 |\n")
            f.write("|------|------|\n")
            f.write(f"| 已下载cp311 wheel | {cp311_downloaded} |\n")
            f.write(f"| 已下载py3通用wheel | {py3_universal_downloaded} |\n")
            f.write(f"| 已下载源码包 | {source_downloaded} |\n")
            f.write(f"| 需要下载的包 | {needs_download} |\n\n")
            
            # cp311专用wheel列表
            f.write("## Python 3.11专用Wheel包 (✅ 可直接安装)\n\n")
            f.write("| 包名 | 版本要求 | 状态 |\n")
            f.write("|------|----------|------|\n")
            for pkg_info in sorted(results.values(), key=lambda x: x['package_name']):
                if pkg_info['wheel_info']['cp311_wheel']:
                    status = "✅ 已下载" if pkg_info['has_local_wheel'] else "⬇ 需要下载"
                    wheel = pkg_info['wheel_info']['cp311_wheel']
                    filename = wheel.get('filename', 'unknown')
                    f.write(f"| {pkg_info['package_name']} | `{pkg_info['requirement']}` | {status} `\n")
                    f.write(f"{filename}` |\n")
            f.write("\n")
            
            # py3通用wheel列表
            f.write("## Python 3.x通用Wheel包 (✅ 所有Python 3.x可用)\n\n")
            f.write("| 包名 | 版本要求 | 状态 |\n")
            f.write("|------|----------|------|\n")
            for pkg_info in sorted(results.values(), key=lambda x: x['package_name']):
                if pkg_info['wheel_info']['py3_universal_wheel'] and not pkg_info['wheel_info']['cp311_wheel']:
                    status = "✅ 已下载" if pkg_info['has_local_wheel'] else "⬇ 需要下载"
                    wheel = pkg_info['wheel_info']['py3_universal_wheel']
                    filename = wheel.get('filename', 'unknown')
                    f.write(f"| {pkg_info['package_name']} | `{pkg_info['requirement']}` | {status} `\n")
                    f.write(f"{filename}` |\n")
            f.write("\n")
            
            # 需要源码编译的包
            f.write("## 需要源码编译的包 (⚠️ 需要编译环境)\n\n")
            f.write("| 包名 | 版本要求 | 状态 | 说明 |\n")
            f.write("|------|----------|------|------|\n")
            for pkg_info in sorted(results.values(), key=lambda x: x['package_name']):
                if not pkg_info['wheel_info']['cp311_wheel'] and not pkg_info['wheel_info']['py3_universal_wheel']:
                    status = "✅ 已下载" if pkg_info['has_local_source'] else "⬇ 需要下载"
                    note = ""
                    if pkg_info['wheel_info']['cp313_wheel']:
                        note = "有Python 3.13 wheel"
                    elif pkg_info['wheel_info']['has_wheel']:
                        note = "有其他平台wheel"
                    else:
                        note = "无预编译wheel"
                    f.write(f"| {pkg_info['package_name']} | `{pkg_info['requirement']}` | {status} | {note} |\n")
            f.write("\n")
            
            # 需要下载的包
            f.write("## 需要下载的包\n\n")
            needs_download_list = [p for p in results.values() if p['needs_download']]
            if needs_download_list:
                f.write(f"共 **{len(needs_download_list)}** 个包需要下载\n\n")
                for pkg_info in sorted(needs_download_list, key=lambda x: x['package_name']):
                    wheel = pkg_info['wheel_info']['best_wheel']
                    if wheel:
                        filename = wheel.get('filename', 'unknown')
                        size_mb = wheel.get('size', 0) / (1024 * 1024)
                        f.write(f"- `{pkg_info['package_name']}`: {filename} ({size_mb:.1f} MB)\n")
            else:
                f.write("✅ 所有需要的wheel包已下载！\n\n")
            
            # 建议的下载命令
            f.write("## 建议的下载命令\n\n")
            f.write("### 下载cp311专用wheel\n")
            f.write("```bash\n")
            f.write("cd ext\\02-python-wheels\n")
            f.write("pip download -r ..\\..\\requirements-cp311.txt --platform win_amd64 --only-binary :all: --python-version 3.11\n")
            f.write("```\n\n")
            
            f.write("### 下载py3通用wheel\n")
            f.write("```bash\n")
            f.write("cd ext\\02-python-wheels\n")
            f.write("pip download -r ..\\..\\requirements-py3-universal.txt --platform win_amd64 --only-binary :all:\n")
            f.write("```\n\n")
            
            f.write("### 下载源码包（如需要）\n")
            f.write("```bash\n")
            f.write("cd ext\\01-python-pip\n")
            f.write("pip download -r ..\\..\\requirements-source-only.txt --no-binary :all:\n")
            f.write("```\n\n")
            
            # 详细包信息
            f.write("## 详细包信息\n\n")
            for pkg_info in sorted(results.values(), key=lambda x: x['package_name']):
                f.write(f"### {pkg_info['package_name']}\n\n")
                f.write(f"**Requirements**: `{pkg_info['requirement']}`\n\n")
                
                wheel_info = pkg_info['wheel_info']
                f.write("**Wheel可用性**:\n")
                f.write(f"- cp311专用: {'✅' if wheel_info['cp311_wheel'] else '❌'}\n")
                f.write(f"- py3通用: {'✅' if wheel_info['py3_universal_wheel'] else '❌'}\n")
                f.write(f"- cp313专用: {'✅' if wheel_info['cp313_wheel'] else '❌'}\n")
                f.write(f"- 源码包: {'✅' if wheel_info['has_source'] else '❌'}\n\n")
                
                f.write("**本地下载**:\n")
                f.write(f"- wheel: {len(pkg_info['local_wheels'])} 个\n")
                f.write(f"- 源码: {len(pkg_info['local_sources'])} 个\n\n")
                
                if wheel_info['best_wheel']:
                    best = wheel_info['best_wheel']
                    f.write(f"**推荐下载**: `{best.get('filename', 'unknown')}`\n")
                    f.write(f"- 上传时间: {best.get('upload_time', 'unknown')}\n")
                    f.write(f"- 大小: {best.get('size', 0) / (1024 * 1024):.1f} MB\n\n")
                
                f.write("---\n\n")
        
        print(f"✅ 生成报告: {report_file.name}")
        print(f"   路径: {report_file}")
        print()
        
        return report_file
    
    def run(self):
        """执行检查流程"""
        try:
            # 1. 读取requirements
            wheels_req = self.project_dir / "requirements-wheels-en.txt"
            
            # 2. 检查所有包
            results = self.check_packages(wheels_req)
            
            # 3. 生成优化的requirements文件
            requirements_files = self.generate_optimized_requirements(results)
            
            # 4. 生成Markdown报告
            report_file = self.generate_markdown_report(results, requirements_files)
            
            # 5. 打印摘要
            print("=" * 70)
            print("  检查完成！")
            print("=" * 70)
            print()
            print("生成的文件:")
            print("  - requirements-cp311.txt (Python 3.11专用wheel)")
            print("  - requirements-py3-universal.txt (Python 3.x通用wheel)")
            print("  - requirements-source-only.txt (需要编译的包)")
            print("  - requirements-all-wheels.txt (所有wheel合并)")
            print()
            print(f"  - {report_file.name} (详细报告)")
            print()
            
            return results, report_file
            
        except KeyboardInterrupt:
            print("\n\n⚠ 用户中断")
            return None, None
        except Exception as e:
            print(f"\n\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return None, None


def main():
    """主函数"""
    checker = WheelChecker()
    results, report_file = checker.run()
    
    if results:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()