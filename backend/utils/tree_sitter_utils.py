"""
Tree-sitter utilities for C++ parsing
"""
from typing import List, Optional, Any
from tree_sitter import Node


def node_to_string(node: Node) -> str:
    """将节点转换为字符串"""
    return node.text.decode("utf-8") if isinstance(node.text, bytes) else node.text


def get_node_text(node: Node, content: str) -> str:
    """获取节点的文本内容"""
    if node.start_byte >= len(content) or node.end_byte > len(content):
        return ""
    
    if isinstance(content, str):
        return content[node.start_byte:node.end_byte]
    return content.decode("utf-8")[node.start_byte:node.end_byte]


def find_child_by_type(node: Node, child_type: str) -> Optional[Node]:
    """查找指定类型的第一个子节点"""
    for child in node.children:
        if child.type == child_type:
            return child
    return None


def find_children_by_type(node: Node, child_types: List[str]) -> List[Node]:
    """查找所有指定类型的子节点"""
    result = []
    for child in node.children:
        if child.type in child_types:
            result.append(child)
    return result


def find_descendant_by_type(node: Node, child_type: str) -> Optional[Node]:
    """递归查找指定类型的子孙节点"""
    for child in node.children:
        if child.type == child_type:
            return child
        result = find_descendant_by_type(child, child_type)
        if result:
            return result
    return None


def find_descendants_by_type(node: Node, child_type: str) -> List[Node]:
    """递归查找所有指定类型的子孙节点"""
    result = []
    for child in node.children:
        if child.type == child_type:
            result.append(child)
        result.extend(find_descendants_by_type(child, child_type))
    return result


def traverse_tree(node: Node, depth: int = 0) -> List[Node]:
    """遍历树的所有节点"""
    result = [node]
    for child in node.children:
        result.extend(traverse_tree(child, depth + 1))
    return result


def get_node_range(node: Node) -> tuple:
    """获取节点的范围"""
    return (
        node.start_point[0] + 1,  # 1-indexed start line
        node.start_point[1] + 1,  # 1-indexed start column
        node.end_point[0] + 1,    # 1-indexed end line
        node.end_point[1] + 1,    # 1-indexed end column
    )


def get_node_line_range(node: Node) -> tuple:
    """获取节点的行范围"""
    return (node.start_point[0] + 1, node.end_point[0] + 1)


def is_leaf_node(node: Node) -> bool:
    """检查是否为叶子节点"""
    return len(node.children) == 0


def is_named_node(node: Node) -> bool:
    """检查是否为命名节点"""
    return bool(node.is_named)


def get_node_depth(node: Node, root: Node) -> int:
    """获取节点在树中的深度"""
    depth = 0
    current = node
    while current.parent != root:
        if current.parent is None:
            break
        depth += 1
        current = current.parent
    return depth


def get_siblings(node: Node) -> List[Node]:
    """获取兄弟节点"""
    if node.parent is None:
        return []
    return [child for child in node.parent.children if child != node]


def get_next_sibling(node: Node) -> Optional[Node]:
    """获取下一个兄弟节点"""
    if node.parent is None:
        return None
    siblings = node.parent.children
    for i, child in enumerate(siblings):
        if child == node and i + 1 < len(siblings):
            return siblings[i + 1]
    return None


def get_previous_sibling(node: Node) -> Optional[Node]:
    """获取前一个兄弟节点"""
    if node.parent is None:
        return None
    siblings = node.parent.children
    for i, child in enumerate(siblings):
        if child == node and i > 0:
            return siblings[i - 1]
    return None


def contains_node(parent: Node, child: Node) -> bool:
    """检查父节点是否包含子节点"""
    if child.start_byte >= parent.start_byte and child.end_byte <= parent.end_byte:
        return True
    return False


def get_common_ancestor(node1: Node, node2: Node) -> Optional[Node]:
    """获取两个节点的最近公共祖先"""
    ancestors1 = set()
    current = node1
    while current:
        ancestors1.add(current)
        current = current.parent
    
    current = node2
    while current:
        if current in ancestors1:
            return current
        current = current.parent
    
    return None


def get_first_named_child(node: Node) -> Optional[Node]:
    """获取第一个命名子节点"""
    for child in node.children:
        if child.is_named:
            return child
    return None


def skip_unnamed_nodes(node: Optional[Node]) -> Optional[Node]:
    """跳过未命名的节点"""
    while node and not node.is_named:
        if node.children:
            node = node.children[0]
        else:
            node = None
    return node
