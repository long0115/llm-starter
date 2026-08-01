"""
时间工具

提供获取当前时间的功能。
"""

from datetime import datetime
from langchain.tools import tool
from infra.utils.log_util import logger


@tool(return_direct=True)
def get_current_time() -> str:
    """
    获取当前时间
    
    Returns:
        当前时间字符串
    """
    
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return f"当前时间: {time_str}"