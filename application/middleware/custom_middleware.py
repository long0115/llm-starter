"""
自定义中间件
"""
from typing import Callable
from langchain.agents.middleware import AgentMiddleware, ModelRequest
from langchain.agents.middleware.types import ModelResponse

class ExpertiseMiddleware(AgentMiddleware):

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:

        # ---- 前置处理 ----
        try:
            result = handler(request)
        except Exception as e:
            logger.error(f"工具调用失败，自动重试一次: {e}")
            result = handler(request)
        # ---- 后置处理 ----
        return result