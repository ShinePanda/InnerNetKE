#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从wheel目录刷新所有requirements文件
"""
from pathlib import Path
from datetime import datetime

def parse_wheel_filename(filename):
    """解析wheel文件名，提取包名和版本"""
    # 移除.whl扩展名
    name = filename[:-4]
    
    # 分离平台标记
    parts = name.split('-')
    
    # 标准wheel命名: package-version-python-tag-abi-tag-platform-tag
    if len(parts) >= 2:
        package = parts[0]
        version = parts[1]
        return package, version
    
    return None, None

def add_version(pkg_name, version, pkg_dict):
    """添加包到字典，保留最高版本"""
    # 统一包名（将下划线转换为连字符）
    pkg_normalized = pkg_name.replace('_', '-')
    
    if pkg_normalized not in pkg_dict or version > pkg_dict[pkg_normalized]:
        pkg_dict[pkg_normalized] = version

def main():
    wheel_dir = Path(__file__).parent.parent / "ext" / "02-python-wheels"
    project_dir = Path(__file__).parent.parent
    
    print(f"扫描wheel目录: {wheel_dir}")
    
    # 获取所有wheel文件
    wheel_files = list(wheel_dir.glob("*.whl"))
    print(f"找到 {len(wheel_files)} 个wheel文件\n")
    
    # 分类存储
    py3_universal = {}  # py3-none-any + py3-none-win_amd64
    cp311_win = {}      # cp311-win_amd64
    all_packages = set()
    
    for wheel_file in wheel_files:
        package, version = parse_wheel_filename(wheel_file.name)
        
        if package and version:
            all_packages.add(package)
            
            # 分类
            # py3-none-any 和 py3-none-win_amd64 都归为 py3_universal
            if 'py3-none-any' in wheel_file.name:
                add_version(package, version, py3_universal)
                print(f"[py3-none-any] {package}=={version}")
            elif 'py3-none-win_amd64' in wheel_file.name:
                add_version(package, version, py3_universal)
                print(f"[py3-none-win_amd64] {package}=={version}")
            elif 'cp311-cp311-win_amd64' in wheel_file.name:
                add_version(package, version, cp311_win)
                print(f"[cp311-win] {package}=={version}")
    
    print(f"\n分类统计:")
    print(f"  py3通用包: {len(py3_universal)}")
    print(f"  cp311-win包: {len(cp311_win)}")
    print(f"  总包数: {len(all_packages)}")
    
    # 生成requirements files
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. requirements-py3-universal.txt
    with open(project_dir / "requirements-py3-universal.txt", "w", encoding="utf-8") as f:
        f.write(f"# Python 3.x通用wheel包（py3-none-any 和 py3-none-win_amd64）\n")
        f.write(f"# 生成时间: {timestamp}\n")
        f.write(f"# 包数: {len(py3_universal)}\n\n")
        
        for pkg in sorted(py3_universal.keys()):
            f.write(f"{pkg}>={py3_universal[pkg]}\n")
    
    print(f"\n✓ 生成: requirements-py3-universal.txt ({len(py3_universal)}个包)")
    
    # 2. requirements-cp311.txt
    with open(project_dir / "requirements-cp311.txt", "w", encoding="utf-8") as f:
        f.write(f"# Python 3.11特定wheel包（cp311-win_amd64）\n")
        f.write(f"# 生成时间: {timestamp}\n")
        f.write(f"# 包数: {len(cp311_win)}\n\n")
        
        for pkg in sorted(cp311_win.keys()):
            f.write(f"{pkg}>={cp311_win[pkg]}\n")
    
    print(f"✓ 生成: requirements-cp311.txt ({len(cp311_win)}个包)")
    
    # 3. requirements-source-only.txt - 应该为空
    with open(project_dir / "requirements-source-only.txt", "w", encoding="utf-8") as f:
        f.write(f"# 需要从源码编译的包（无wheel）\n")
        f.write(f"# 生成时间: {timestamp}\n")
        f.write(f"# 包数: 0\n\n")
        f.write(f"# 所有包都已提供wheel文件，无需源码编译\n")
    
    print(f"✓ 生成: requirements-source-only.txt (0个包)")
    
    # 4. requirements-all-wheels.txt - 合并所有
    all_wheels = dict(zip(
        [k.replace('_', '-') for k in py3_universal.keys()],
        py3_universal.values()
    ))
    
    # 合并cp311包
    for pkg, version in cp311_win.items():
        pkg_norm = pkg.replace('_', '-')
        if pkg_norm not in all_wheels or version > all_wheels[pkg_norm]:
            all_wheels[pkg_norm] = version
    
    with open(project_dir / "requirements-all-wheels.txt", "w", encoding="utf-8") as f:
        f.write(f"# 所有wheel包（合并）\n")
        f.write(f"# 生成时间: {timestamp}\n")
        f.write(f"# 包数: {len(all_wheels)}\n\n")
        
        for pkg in sorted(all_wheels.keys()):
            f.write(f"{pkg}>={all_wheels[pkg]}\n")
    
    print(f"✓ 生成: requirements-all-wheels.txt ({len(all_wheels)}个包)")
    
    print(f"\n✅ 所有requirements文件已更新！")

if __name__ == "__main__":
    main()