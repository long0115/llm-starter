
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware, PIIMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from application.ports.llm_client_port import LlmClientPort
from application.tools.calculator import calculate
from application.tools.time_tool import get_current_time
from application.tools.weather import get_weather
from infra.adapter.mcp_adapter import McpAdapter
from infra.utils.log_util import logger


class SimpleAgent:
    def __init__(self, llm_adapter: LlmClientPort, mcp_adapter: McpAdapter = None):
        # agent 实例，初始化为 None，等待懒加载
        self.agent = None
        # MemorySaver 用于保存对话历史，支持多会话（通过 thread_id 区分）
        self.checkpointer = None
        # 注册可用工具列表（本地工具）
        self.tools = [calculate, get_current_time, get_weather]
        # 依赖注入
        self.llm_adapter = llm_adapter
        # MCP 适配器（可选）
        self.mcp_adapter = mcp_adapter

    async def build(self):
        """
        构建 Agent，支持异步初始化 MCP 工具

        Returns:
            LangGraph Agent 实例    
        """
        if self.checkpointer is None:
            self.checkpointer = InMemorySaver()

        if self.agent is None:
            # 初始化 MCP 工具（如果配置了 MCP 适配器）
            if self.mcp_adapter is not None:
                try:
                    await self.mcp_adapter.initialize()
                    mcp_tools = self.mcp_adapter.get_tools()
                    if mcp_tools:
                        # 合并本地工具和 MCP 工具
                        self.tools = self.tools + mcp_tools
                        logger.info(f"MCP 工具加载成功，共 {len(mcp_tools)} 个远程工具")
                except Exception as e:
                    logger.info(f"MCP 工具加载失败，仅使用本地工具: {e}")

            self.agent = create_agent(
                model=self.llm_adapter.client,
                tools=self.tools,
                system_prompt="你是一个智能助手，可以根据用户的问题，调用不同的工具来回答。",
                middleware=[
                    # PII 脱敏：检测并脱敏敏感信息
                    PIIMiddleware("credit_card", strategy="mask"),
                    # 对话摘要：当 Token 超过 4000 时自动压缩历史，保留最近 10 条消息不动
                    SummarizationMiddleware(
                        model=self.llm_adapter.client,      # 用于压缩的模型
                        trigger=("tokens", 4000),           # 触发条件：当 Token 数超过 4000
                        keep=("messages", 10),              # 保留：最近 10 条消息
                    ),
                    # 人工干预：审批高风险操作
                    HumanInTheLoopMiddleware(
                        # approve: 批准，reject: 拒绝，edit: 修改参数，respond: 直接回复
                        interrupt_on={
                            "calculator": True,    # 中断工具，并允许所有决策
                            "get_current_time": False,    # 不中断工具
                            "get_weather": {        # 中断工具，但允许审批和拒绝
                                "allowed_decisions": ["approve", "reject"]
                            }
                        }
                    )
                ],
                checkpointer=self.checkpointer,
            )

        return self.agent
