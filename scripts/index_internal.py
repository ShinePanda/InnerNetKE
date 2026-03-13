#!/usr/bin/env python
"""
InnerNetKE 内网仓库索引脚本（大机器 96核专用）
自动使用 50% CPU 核心 + path_mapper + get_rag_chunks
"""
import argparse
import multiprocessing as mp
from pathlib import Path
import sys
import time
from typing import List
import psutil
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.path_mapper import get_path_mapper
from backend.vectorstore.chroma_store import ChromaVectorStore
from backend.parsers import get_analyzer


def process_parse_only(args):
    """解析专用函数（子进程用，不加载模型）"""
    start_time = time.time()
    process = psutil.Process()
    mem_start = process.memory_info().rss / (1024**2)  # MB
    
    file_path, repo_name, mapper = args
    ext = Path(file_path).suffix.lower()
    if ext not in (".cpp", ".h", ".hpp", ".c"):
        return []
    
    language = "cpp"
    analyzer = get_analyzer("cpp")
    
    try:
        dev_path, _ = mapper.map_to_dev(file_path)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        chunks = analyzer.get_rag_chunks(file_path, content)
        for chunk in chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"].update({
                "dev_path": dev_path,
                "archive_path": file_path,
                "repo": repo_name,
                "language": language
            })
        
        duration = time.time() - start_time
        mem_end = process.memory_info().rss / (1024**2)
        mem_diff = mem_end - mem_start
        
        print(f"[{repo_name}] {Path(file_path).name} 处理耗时: {duration:.2f}s, "
              f"内存变化: +{mem_diff:.1f} MB (当前 {mem_end:.1f} MB)")
        
        return chunks
    except Exception as e:
        duration = time.time() - start_time
        print(f"解析失败 {file_path}: {e} (耗时: {duration:.2f}s)")
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos", nargs="*", default=["nbi", "pub", "otn", "ptn", "sdk-platform-mcp"])
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    workers = args.workers or (lambda: max(2, mp.cpu_count() // 2))()
    print(f"🔧 CPU 核心数: {mp.cpu_count()} → 使用 {workers} 个工作进程 (50%)")
    
    start_time = time.time()
    total_files = 0
    
    # 主进程预加载 embedding 模型（只加载一次）
    print("主进程预加载 embedding 模型...")
    vector_store = ChromaVectorStore()  # 这里加载模型
    embedding_func = vector_store.embedding_function  # 获取函数
    
    all_chunks = []  # 全局收集 chunks
    mapper = get_path_mapper()  # 主进程创建一次 path_mapper
    
    for repo_name in args.repos:
        archive_root_repo = f"./data/repos/{repo_name}"
        print(f"调试：ARCHIVE_ROOT = ./data/repos")
        print(f"调试：目标完整路径 = {archive_root_repo}")
        print(f"调试：是否存在 = {Path(archive_root_repo).exists()}")
        print(f"调试：是否是目录 = {Path(archive_root_repo).is_dir()}")
        
        files = []
        for ext in ["*.cpp", "*.h", "*.hpp", "*.c"]:
            files.extend([str(p) for p in Path(archive_root_repo).rglob(ext)])
        
        print(f"找到 {len(files)} 个文件")
        
        # 多进程只解析 chunk（不加载模型）
        with mp.Pool(workers) as pool:
            results = pool.map(process_parse_only, [(f, repo_name, mapper) for f in files])
        
        # 收集所有 chunks
        for chunks in results:
            all_chunks.extend(chunks)
        
        total_files += len(files)
    
    # 主进程统一 embedding + 写入
    print(f"总收集 {len(all_chunks)} chunks，开始 embedding 和写入...")
    start_embed = time.time()
    
    if all_chunks:
        contents = [c["content"] for c in all_chunks]
        embeddings = embedding_func(contents)  # 批量 embedding
        
        # 添加 embedding 到 chunks 中
        for i, chunk in enumerate(all_chunks):
            chunk["embedding"] = embeddings[i]
        
        # 使用预计算的 embedding 添加文档
        ids = vector_store.add_documents(all_chunks, embeddings=np.array(embeddings))
        
        print(f"成功添加 {len(ids)} 个文档到向量库")
    
    embed_duration = time.time() - start_embed
    total_duration = time.time() - start_time
    
    print(f"Embedding + 写入耗时: {embed_duration:.2f} 秒")
    print(f"总耗时: {total_duration:.2f} 秒")
    print(f"总内存峰值约: {psutil.Process().memory_info().rss / (1024**2):.1f} MB")
    print("现在可以复制 chroma_db 到内网服务器了！")


if __name__ == "__main__":
    main()