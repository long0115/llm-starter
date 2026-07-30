"""
计算器工具

提供数学计算功能。
"""

from langchain.tools import tool
from infra.utils.log_util import logger


@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式
    
    Args:
        expression: 数学表达式字符串
        
    Returns:
        计算结果字符串
    """
    
    try:
        expression = expression.replace("x", "*").replace("÷", "/")
        
        result = eval(expression)
        logger.info(f"计算成功: {expression} = {result}")
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        logger.error(f"计算失败: {expression}, 错误: {str(e)}")
        return f"计算失败: {str(e)}"