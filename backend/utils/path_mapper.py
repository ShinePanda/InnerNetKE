"""
路径映射模块
解决归档目录与开发目录的路径映射问题
从项目1集成而来，适配项目2的架构
"""

from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PathMapping:
    """路径映射配置"""
    archive_root: str      # 归档目录（如 /internal/repos）
    dev_root: str          # 开发目录（如 D:/projects）
    enabled: bool = True   # 是否启用
    priority: int = 0      # 优先级（数字越大优先级越高）
    description: str = ""  # 描述信息


class PathMapper:
    """路径映射器"""
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        初始化路径映射器
        
        参数：
        - mapping_file: 映射配置文件路径
        """
        if mapping_file is None:
            # 默认配置文件路径
            base_dir = Path(__file__).parent.parent.parent
            mapping_file = base_dir / "config" / "path-mapping.json"
        
        self.mapping_file = Path(mapping_file)
        self.mappings: List[PathMapping] = []
        self.load_mappings()
    
    def load_mappings(self) -> None:
        """加载路径映射配置"""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.mappings = [
                    PathMapping(
                        archive_root=m["archive_root"],
                        dev_root=m["dev_root"],
                        enabled=m.get("enabled", True),
                        priority=m.get("priority", 0),
                        description=m.get("description", "")
                    )
                    for m in data.get("mappings", [])
                ]
                
                # 按优先级排序
                self.mappings.sort(key=lambda x: x.priority, reverse=True)
                logger.info(f"Loaded {len(self.mappings)} path mappings from {self.mapping_file}")
                
            except Exception as e:
                logger.error(f"Failed to load path mappings from {self.mapping_file}: {e}")
                self.mappings = []
        else:
            logger.info(f"Path mapping file not found: {self.mapping_file}")
            self.mappings = []
    
    def add_mapping(
        self,
        archive_root: str,
        dev_root: str,
        priority: int = 0,
        description: str = ""
    ) -> None:
        """
        添加或更新路径映射
        
        参数：
        - archive_root: 归档目录路径
        - dev_root: 开发目录路径
        - priority: 优先级
        - description: 描述
        """
        # 规范化路径格式（使用POSIX风格，确保跨平台一致性）
        archive_root = Path(archive_root).resolve().as_posix()
        dev_root = Path(dev_root).resolve().as_posix()
        
        # 检查是否已存在相同的archive_root
        for m in self.mappings:
            if m.archive_root == archive_root:
                logger.info(f"Updating existing mapping: {archive_root}")
                m.dev_root = dev_root
                m.priority = priority
                m.description = description
                break
        else:
            logger.info(f"Adding new mapping: {archive_root} -> {dev_root}")
            self.mappings.append(PathMapping(
                archive_root=archive_root,
                dev_root=dev_root,
                priority=priority,
                description=description
            ))
        
        # 保存配置
        self.save_mappings()
    
    def remove_mapping(self, archive_root: str) -> bool:
        """
        删除路径映射
        
        参数：
        - archive_root: 要删除的归档目录
        
        返回：
        - 是否成功删除
        """
        archive_root = Path(archive_root).resolve().as_posix()
        original_count = len(self.mappings)
        
        self.mappings = [
            m for m in self.mappings 
            if m.archive_root != archive_root
        ]
        
        if len(self.mappings) < original_count:
            logger.info(f"Removed mapping: {archive_root}")
            self.save_mappings()
            return True
        
        return False
    
    def save_mappings(self) -> None:
        """保存路径映射配置到文件"""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mappings": [
                {
                    "archive_root": m.archive_root,
                    "dev_root": m.dev_root,
                    "enabled": m.enabled,
                    "priority": m.priority,
                    "description": m.description
                }
                for m in self.mappings
            ]
        }
        
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.mappings)} path mappings to {self.mapping_file}")
    
    def map_to_dev(self, archive_path: str) -> Tuple[str, bool]:
        """
        将归档路径映射到开发路径
        
        参数：
        - archive_path: 归档路径
        
        返回：
        - (mapped_path, is_mapped): 映射后的路径和是否成功映射
        """
        archive_resolved = Path(archive_path).resolve().as_posix()
        
        # 按优先级排序后查找
        sorted_mappings = sorted(self.mappings, key=lambda x: x.priority, reverse=True)
        
        for mapping in sorted_mappings:
            if not mapping.enabled:
                continue
            
            # 检查路径是否以archive_root开头
            if archive_resolved.startswith(mapping.archive_root + "/"):
                # 计算相对路径
                try:
                    rel_path = Path(archive_resolved).relative_to(Path(mapping.archive_root))
                    dev_path = Path(mapping.dev_root) / rel_path
                    return dev_path.as_posix(), True
                except ValueError:
                    logger.warning(f"Failed to compute relative path for {archive_path}")
                    continue
        
        # 未找到映射，返回原路径
        return archive_path, False
    
    def map_to_archive(self, dev_path: str) -> Tuple[str, bool]:
        """
        将开发路径映射到归档路径
        
        参数：
        - dev_path: 开发路径
        
        返回：
        - (mapped_path, is_mapped): 映射后的路径和是否成功映射
        """
        dev_resolved = Path(dev_path).resolve().as_posix()
        
        # 按优先级排序后查找
        sorted_mappings = sorted(self.mappings, key=lambda x: x.priority, reverse=True)
        
        for mapping in sorted_mappings:
            if not mapping.enabled:
                continue
            
            # 检查路径是否以dev_root开头
            if dev_resolved.startswith(mapping.dev_root + "/"):
                # 计算相对路径
                try:
                    rel_path = Path(dev_resolved).relative_to(Path(mapping.dev_root))
                    archive_path = Path(mapping.archive_root) / rel_path
                    return archive_path.as_posix(), True
                except ValueError:
                    logger.warning(f"Failed to compute relative path for {dev_path}")
                    continue
        
        # 未找到映射，返回原路径
        return dev_path, False
    
    def get_mappings(self) -> List[dict]:
        """
        获取所有路径映射
        
        返回：
        - 映射列表的字典格式
        """
        return [
            {
                "archive_root": m.archive_root,
                "dev_root": m.dev_root,
                "enabled": m.enabled,
                "priority": m.priority,
                "description": m.description
            }
            for m in self.mappings
        ]
    
    def test_mapping(self, path: str) -> dict:
        """
        测试路径映射
        
        参数：
        - path: 测试路径
        
        返回：
        - 测试结果字典
        """
        # 尝试映射到开发路径
        dev_path, dev_mapped = self.map_to_dev(path)
        
        # 尝试映射到归档路径
        archive_path, archive_mapped = self.map_to_archive(path)
        
        return {
            "original_path": path,
            "mapped_to_dev": {
                "path": dev_path,
                "is_mapped": dev_mapped
            },
            "mapped_to_archive": {
                "path": archive_path,
                "is_mapped": archive_mapped
            }
        }


# 全局单例
_mapper_instance: Optional[PathMapper] = None


def get_path_mapper(mapping_file: Optional[str] = None) -> PathMapper:
    """
    获取全局路径映射器单例
    
    参数：
    - mapping_file: 可选的映射文件路径
    
    返回：
    - PathMapper实例
    """
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = PathMapper(mapping_file)
    return _mapper_instance


def reset_path_mapper():
    """重置全局路径映射器（主要用于测试）"""
    global _mapper_instance
    _mapper_instance = None