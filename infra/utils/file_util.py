import os
import fnmatch
from typing import Generator

def scan_files(root_dir: str, supported_extensions: list[str], ignore_patterns: list[str]) -> Generator[str, None, None]:
    """
    扫描目录下所有支持的文件

    :param root_dir: 根目录
    :param supported_extensions: 支持的文件扩展名列表
    :param ignore_patterns: 忽略的模式列表
    :Returns: 生成器，返回所有符合条件的文件路径
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 过滤目录
        dirnames[:] = [d for d in dirnames if not any(
            fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns
        )]
        
        for filename in filenames:
            # 过滤文件
            if any(fnmatch.fnmatch(filename, pattern) for pattern in ignore_patterns):
                continue
            
            # 检查扩展名
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                yield os.path.abspath(os.path.join(dirpath, filename))

def get_file_hash(file_path: str) -> str:
    """
    计算文件哈希值（用于增量更新检测）

    :param file_path: 文件路径
    :Returns: MD5哈希值
    """
    import hashlib
    
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_info(file_path: str) -> dict:
    """
    获取文件信息

    :param file_path: 文件路径
    :Returns: 文件信息字典
    """
    stat = os.stat(file_path)
    return {
        "path": file_path,
        "name": os.path.basename(file_path),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "hash": get_file_hash(file_path)
    }