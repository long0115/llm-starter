"""
PromptManager - 提示词管理器

负责加载、管理和渲染提示词模板。
"""

import os
import yaml
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from functools import lru_cache


# Prompt 管理器
class PromptManager:
    
    def __init__(self, prompts_dir: str = None):
        self.prompts: Dict[str, ChatPromptTemplate] = {}
        # 获取当前文件所在的绝对目录 -> infra/prompt/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if prompts_dir is None:
            self.prompts_dir = os.path.join(base_dir, "template")
        else:
            self.prompts_dir = prompts_dir
    
    def load_prompt(self, name: str, version: str = "v1") -> ChatPromptTemplate:
        """
        加载 Prompt 模板，支持多版本。
        
        Args:
            name: Prompt 名称
            version: 版本号，默认 "v1"
        Returns: 
            ChatPromptTemplate 实例，用于渲染提示词模板
        """
        # 检查缓存
        file_name = f"{name}_{version}"
        if file_name in self.prompts:
            return self.prompts[file_name]
        
        # 加载 yaml 文件
        file_path = os.path.join(self.prompts_dir, f"{file_name}.yaml")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt 文件不存在: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        # 创建 Prompt
        messages = [
            (msg["role"], msg["content"]) for msg in data["messages"]
        ]
        
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # 缓存
        self.prompts[file_name] = prompt
        return prompt
    
    def list_prompts(self) -> list:
        """
        列出所有可用的 Prompt 名称。
        
        Returns: 
            所有 Prompt 名称的列表
        """
        prompts = []
        if os.path.exists(self.prompts_dir):
            for filename in os.listdir(self.prompts_dir):
                if filename.endswith(".yaml"):
                    name = os.path.splitext(filename)[0]
                    prompts.append(name)
        return prompts


@lru_cache()
def get_prompt_manager() -> PromptManager:
    return PromptManager()

prompt_manager = get_prompt_manager()