"""
装饰器中间件
"""
from collections.abc import Callable
from langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from infra.utils.log_util import logger


@wrap_tool_call
def wrap_middleware(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:

    # ---- 前置处理 ----
    try:
        result = handler(request)
    except Exception as e:
        logger.error(f"工具调用失败，自动重试一次: {e}")
        result = handler(request)
    # ---- 后置处理 ----
    return result