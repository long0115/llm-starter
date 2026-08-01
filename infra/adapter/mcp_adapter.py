"""
MCP 适配器

通过 langchain_mcp_adapters 的 MultiServerMCPClient 连接远程 MCP 服务，
获取工具列表供 Agent 使用。
"""
from typing import List, Any


class McpAdapter:
    """
    MCP 适配器

    负责管理 MCP 客户端生命周期和工具获取。
    类比 Java 中的 HttpClient + ToolRegistry。

    注意：MultiServerMCPClient 是异步上下文管理器，
    必须在 async with 上下文中使用，否则工具调用会失败。
    """

    def __init__(self):
        self.client = None
        self._context = None
        self._tools = []

        # MCP 服务器配置
        self._servers = {
            "order-service": {
                "url": "http://localhost:8080/mcp",
                "transport": "streamable-http"
            }
        }

    async def initialize(self):
        """
        初始化 MCP 客户端并获取工具列表

        必须在异步上下文中调用（如 Agent 的 run 方法中）。
        内部使用 async with 管理客户端生命周期。
        """
        from langchain_mcp_adapters.client import MultiServerMCPClient

        if self.client is None:
            # 创建异步上下文管理器
            self._context = MultiServerMCPClient(self._servers)
            # 进入异步上下文，保持连接活跃
            await self._context.__aenter__()
            self.client = self._context
            # 获取所有可用工具
            self._tools = self.client.get_tools()

    def get_tools(self) -> List[Any]:
        """
        获取 MCP 工具列表

        Returns:
            LangChain Tool 对象列表
        """
        return self._tools

    async def close(self):
        """
        关闭 MCP 客户端连接

        在应用关闭或不再需要 MCP 工具时调用。
        """
        if self._context is not None:
            await self._context.__aexit__(None, None, None)
            self.client = None
            self._context = None
            self._tools = []
