"""
计算器工具

提供数学计算功能。
"""
import ast
import operator
from langchain.tools import tool
from infra.utils.log_util import logger


# 安全的运算符白名单（只允许数学运算，禁止函数调用、属性访问等）
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

@tool(return_direct=True)
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
        
        result = safe_eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        logger.error(f"计算失败: {expression}, 错误: {str(e)}")
        return f"计算失败：请检查表达式是否正确。"

def safe_eval(expr: str) -> float:
    """
    安全计算数学表达式
    
    只允许数字和基本运算符（+、-、*、/、**、//、%），
    禁止函数调用、变量访问、属性访问等危险操作。
    
    原理：用 ast.parse 将字符串解析为 AST 语法树，
    然后递归遍历节点，只允许白名单内的运算类型。
    类比 Java：类似于用 ANTLR 定义一个只允许数学表达式的语法。
    """
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body)
    except (SyntaxError, TypeError, KeyError, ZeroDivisionError) as e:
        raise ValueError(f"表达式无效: {expr}, 原因: {e}")


def _eval_node(node):
    """递归遍历 AST 节点，只允许安全的运算"""
    # 数字字面量
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    # 二元运算（如 1+2, 3*4）
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](left, right)
    # 一元运算（如 -5）
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](operand)
    else:
        raise ValueError(f"不允许的表达式类型: {type(node).__name__}")