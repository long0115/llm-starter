"""
MCP 适配器

通过 langchain_mcp_adapters 的 MultiServerMCPClient 连接远程 MCP 服务，
获取工具列表供 Agent 使用。
"""
from typing import List, Any
from infra.utils.log_util import logger


class McpAdapter:
    """
    MCP 适配器

    负责管理 MCP 客户端和工具获取。
    类比 Java 中的 HttpClient + ToolRegistry。

    注意：langchain-mcp-adapters >= 0.1.0 不再支持上下文管理器用法，
    直接使用 client = MultiServerMCPClient(...) + await client.get_tools()。
    """

    def __init__(self):
        self.client = None
        self._tools = []

        # MCP 服务器配置（对应 Java 服务端的 MCP 配置）
        # sse-message-endpoint: /mcp/message 表示 POST 消息端点
        # SSE 连接端点默认为 /sse
        self._servers = {
            "java-user-service": {
                "url": "http://localhost:8080/sse",
                "transport": "sse"
            }
        }

    async def initialize(self):
        """
        初始化 MCP 客户端并获取工具列表
        """
        from langchain_mcp_adapters.client import MultiServerMCPClient

        if self.client is None:
            # 创建客户端实例（不再需要 async with）
            self.client = MultiServerMCPClient(self._servers)

            # 逐个服务器获取工具，便于排查问题
            for server_name, connection in self._servers.items():
                try:
                    logger.info(f"正在连接 MCP 服务器: {server_name} -> {connection}")
                    tools = await self.client.get_tools(server_name=server_name)
                    logger.info(f"服务器 {server_name} 返回 {len(tools)} 个工具")
                    self._tools.extend(tools)
                except Exception as e:
                    logger.error(f"连接 MCP 服务器 {server_name} 失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

    def get_tools(self) -> List[Any]:
        """
        获取 MCP 工具列表

        Returns:
            LangChain Tool 对象列表
        """
        return self._tools

    def close(self):
        """
        关闭 MCP 客户端连接
        """
        self.client = None
        self._tools = []
