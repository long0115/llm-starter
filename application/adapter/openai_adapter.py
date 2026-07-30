"""
ChatOpenAI 适配器

    - 初始化 ChatOpenAI 客户端
    - invoke 方法：同步调用
    - ainvoke 方法：异步调用
    - astream 方法：异步流式输出
    - invoke_with_messages 方法：直接传入消息列表
    - with_structured_output 方法：结构化输出
"""

from typing import List, Dict, AsyncIterator
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from infra.utils.log_util import logger
from infra.settings import settings
from functools import lru_cache
from pydantic import BaseModel


class OpenAIAdapter:
    def __init__(self):
        self._client = None
        self._embedding = None
        self.temperature: float = 0.6           # 温度参数，控制输出的随机性
        self.top_p: float = 0.9                 # Top-p 参数，控制输出的多样性
        self.timeout: int = 60                  # 超时时间，单位秒
        self.max_tokens: int = 4096             # 最大输出令牌数
        self.presence_penalty: float = 0.0      # 存在惩罚参数，控制输出的唯一性
        self.frequency_penalty: float = 0.0     # 频率惩罚参数，控制输出的重复性
        self.thinking_enabled: bool = False     # 是否启用思考模式

    @property
    def client(self):
        """
        初始化 Chat 客户端实例
        """
        if self._client is None:
            config = settings.llm_config
            self._client = ChatOpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
                model=config["chat_model"],
                temperature=self.temperature,
                top_p=self.top_p,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                extra_body={
                    "thinking": {"type": "enabled" if self.thinking_enabled else "disabled"}
                },
            )
            logger.info("ChatOpenAI 客户端初始化完成")
        return self._client

    @property
    def embedding(self):
        """
        初始化 Chat 向量模型
        """
        if self._embedding is None:
            config = settings.llm_config
            self._embedding = OpenAIEmbeddings(
                base_url=config["base_url"],
                api_key=config["api_key"],
                model=config["embedding_model"],
                check_embedding_ctx_length=False  # 禁止 LangChain 对文本做 token 化预处理
            )
            logger.info(f"Embedding模型初始化完成：{config['embedding_model']}")
        return self._embedding

    def _build_messages(self, question: str, system_content: str = None, messages: List[BaseMessage] = None) -> List[BaseMessage]:
        """
        构建 LangChain 消息列表
        
        Args:
            question: 用户输入的问题
            system_content: 系统提示词
            messages: 历史消息列表
        
        Returns:
            LangChain BaseMessage 列表
        """
        langchain_messages = []

        if system_content:
            langchain_messages.append(SystemMessage(content=system_content))

        if messages:
            for msg in messages:
                langchain_messages.append(msg)

        langchain_messages.append(HumanMessage(content=question))
        return langchain_messages

    def invoke(self, question: str, system_content: str = None, messages: List[BaseMessage] = None) -> AIMessage:
        """
        同步对话接口
        
        Args:
            question: 用户输入
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
        
        Returns:
            LLM 返回的文本内容
        """
        langchain_messages = self._build_messages(question, system_content, messages)
        response = self.client.invoke(langchain_messages)
        return response

    async def ainvoke(self, question: str, system_content: str = None, messages: List[BaseMessage] = None) -> AIMessage:
        """
        异步对话接口
        
        Args:
            question: 用户输入的问题
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
        
        Returns:
            LLM 返回的文本内容
        """
        langchain_messages = self._build_messages(question, system_content, messages)
        response = await self.client.ainvoke(langchain_messages)
        return response

    def astream(self, question: str, system_content: str = None, messages: List[BaseMessage] = None) -> AsyncIterator[str]:
        """
        异步流式对话接口
        
        Args:
            question: 用户输入的问题
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
        
        Returns:
            异步迭代器，每次返回一个文本块
        """
        langchain_messages = self._build_messages(question, system_content, messages)
        
        async def generate():
            async for chunk in self.client.astream(langchain_messages):
                yield chunk.content

        return generate()

    def invoke_with_messages(self, messages: List[BaseMessage]) -> AIMessage:
        """
        使用消息列表调用 LLM
        
        Args:
            messages: 消息列表
        
        Returns:
            LLM 返回的消息
        """
        response = self.client.invoke(messages)
        return response         

    def invoke_with_structure(self, question: str, system_content: str, messages: List[BaseMessage], schema: type[BaseModel]) -> BaseModel:
        """
        调用 LLM 模型并返回结构化输出
        
        Args:
            question: 用户输入的问题
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
            schema: 结构化模型输出的结构
        
        Returns:
            LLM 返回的结构化输出
        """
        langchain_messages = self._build_messages(question, system_content, messages)
        structured_client = self.client.with_structured_output(schema)
        response = structured_client.invoke(langchain_messages)
        return response

    def invoke_with_tools(self, question: str, system_content: str, messages: List[BaseMessage], tools: List[BaseTool]) -> AIMessage:
        """
        调用 LLM 模型并绑定工具
        
        Args:
            question: 用户输入的问题
            system_content: 系统提示词（可选）
            messages: 历史消息列表（可选）
            tools: 要绑定的工具列表
        
        Returns:
            LLM 返回的文本内容
        """
        langchain_messages = self._build_messages(question, system_content, messages)
        response = self.client.bind_tools(tools).invoke(langchain_messages)
        return response         


@lru_cache()
def get_openai_adapter() -> OpenAIAdapter:
    return OpenAIAdapter()

openai_adapter = get_openai_adapter()
