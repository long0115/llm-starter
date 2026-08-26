"""
技能执行器（Skill Executor）

负责执行知识驱动的技能（基于 SKILL.md 文件）。
与 SkillRegistry 配合工作：
- SkillRegistry 负责"发现"技能（启动时扫描、生成目录）
- SkillExecutor 负责"执行"技能（加载完整指令 + 外部引用，调用 LLM）

核心流程：
1. 接收用户输入和匹配到的技能名称
2. 从 SkillRegistry 加载完整 SKILL.md 指令
3. 根据技能指令中的引用声明，按需加载外部参考文档
4. 构建完整的系统提示词
5. 调用 LLM 执行技能，返回结果
"""

import re
from pathlib import Path
from typing import Optional
from langchain_core.messages import BaseMessage
from application.ports.llm_client_port import LlmClientPort
from application.skills.skill_registry import SkillRegistry
from infra.utils.log_util import logger


class SkillExecutor:
    """
    技能执行器：加载完整指令 + 外部引用，调用 LLM 执行技能
    
    类比 Java 中的 Service 实现类：
    - 依赖 SkillRegistry（类似依赖注入）
    - 对外提供统一的 execute() 接口
    - 内部处理指令加载、引用解析、提示词构建
    """

    def __init__(self, llm_client: LlmClientPort, registry: SkillRegistry):
        self.llm_client = llm_client
        self.registry = registry

    def execute(
        self,
        skill_name: str,
        user_input: str,
        messages: Optional[list[BaseMessage]] = None
    ) -> str:
        """
        执行指定技能
        
        Args:
            skill_name: 要执行的技能名称（如 'meeting-summarizer'）
            user_input: 用户输入内容
            messages: 历史消息列表（可选）
            
        Returns:
            技能执行结果文本
        """
        # 1. 加载完整技能指令
        system_prompt = self.registry.load_full_instruction(skill_name)
        if system_prompt is None:
            error_msg = f"技能 '{skill_name}' 不存在或加载失败"
            logger.error(error_msg)
            return error_msg

        logger.info(f"📄 加载技能指令: {skill_name}")

        # 3. 调用 LLM 执行技能
        response = self.llm_client.invoke(
            question=user_input,
            system_content=system_prompt,
            messages=messages
        )

        return response.content

    async def aexecute(
        self,
        skill_name: str,
        user_input: str,
        messages: Optional[list[BaseMessage]] = None
    ) -> str:
        """
        异步执行指定技能
        
        Args:
            skill_name: 要执行的技能名称
            user_input: 用户输入内容
            messages: 历史消息列表（可选）
            
        Returns:
            技能执行结果文本
        """
        # 1. 加载完整技能指令
        system_prompt = self.registry.load_full_instruction(skill_name)
        if system_prompt is None:
            error_msg = f"技能 '{skill_name}' 不存在或加载失败"
            logger.error(error_msg)
            return error_msg

        logger.info(f" 加载技能指令: {skill_name}")

        # 3. 异步调用 LLM 执行技能
        response = await self.llm_client.ainvoke(
            question=user_input,
            system_content=system_prompt,
            messages=messages
        )

        return response.content
