"""
MCP 适配器
"""
from langchain_mcp_adapters.client import MultiServerMCPClient
from functools import lru_cache


class McpAdapter:

    def __init__(self):
        self.client = None

    def build(self):
        self.client = MultiServerMCPClient({
            "order-service": {
                "url": "http://localhost:8080/mcp",
                "transport": "streamable-http"
            }
        })


@lru_cache()
def get_mcp_adapter() -> McpAdapter:
    return McpAdapter()

mcp_adapter = get_mcp_adapter()
