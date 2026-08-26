"""
技能注册中心（Skill Registry）

类比 Java 中的 ServiceRegistry / BeanFactory：
- 启动时扫描 skills/ 目录下所有子目录
- 读取每个子目录中 SKILL.md 的 frontmatter（name + description）
- 生成"技能目录"供模型在意图识别阶段做语义匹配
- 完整 SKILL.md 内容按需加载（渐进式披露，节省 Token）

目录结构约定：
    skills/
    ├── meeting-summarizer/
    │   ├── SKILL.md          # 技能定义（必须有 frontmatter）
    │   ├── references/       # 可选：外部引用文档
    │   ├── assets/           # 可选：静态资源
    │   └── scripts/          # 可选：脚本
    ── another-skill/
        └── SKILL.md
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from infra.utils.log_util import logger


@dataclass
class SkillMetadata:
    """
    技能元数据
    
    从 SKILL.md 的 YAML frontmatter 中解析而来，
    启动时加载，注入给模型做意图匹配。
    """
    name: str                          # 技能唯一标识（如 meeting-summarizer）
    description: str                   # 技能描述（用于语义匹配）
    directory: Path = field(repr=False)  # 技能所在目录路径
    _full_content: Optional[str] = field(default=None, repr=False)  # 完整正文（懒加载）
    _references: dict[str, str] = field(default_factory=dict, repr=False)  # 引用文档缓存

    @property
    def skill_id(self) -> str:
        """技能 ID，等同于 name"""
        return self.name


class SkillRegistry:
    """
    技能注册中心（类比 Java 中的 Spring Bean Registry）
    
    职责：
    1. 启动时扫描技能目录，注册所有可用技能
    2. 提供技能目录（name + description）给模型做意图匹配
    3. 按需加载完整 SKILL.md 内容和外部引用文档
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        """
        初始化技能注册中心
        
        Args:
            skills_dir: 技能根目录，默认为当前文件所在目录（application/skills/）
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent
        self.skills_dir = skills_dir
        # 已注册的技能元数据（name -> SkillMetadata）
        self._skills: dict[str, SkillMetadata] = {}
        # 启动时自动扫描注册
        self._scan_and_register()

    def _scan_and_register(self) -> None:
        """
        扫描技能目录，注册所有可用技能
        
        遍历 skills/ 下的每个子目录，查找 SKILL.md 文件，
        解析 frontmatter 后注册到 _skills 字典中。
        """
        if not self.skills_dir.exists():
            logger.warning(f"技能目录不存在: {self.skills_dir}")
            return

        for child_dir in sorted(self.skills_dir.iterdir()):
            # 只处理包含 SKILL.md 的子目录
            if not child_dir.is_dir():
                continue

            skill_file = child_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            try:
                metadata = self._parse_skill_file(skill_file, child_dir)
                self._skills[metadata.name] = metadata
                logger.info(f"✅ 注册技能: {metadata.name} - {metadata.description}")
            except Exception as e:
                logger.error(f"❌ 注册技能失败 [{child_dir.name}]: {e}")

        logger.info(f"📋 技能注册完成，共 {len(self._skills)} 个技能")

    def _parse_skill_file(self, skill_file: Path, directory: Path) -> SkillMetadata:
        """
        解析 SKILL.md 文件，提取 frontmatter 元数据
        
        Args:
            skill_file: SKILL.md 文件路径
            directory: 技能所在目录
            
        Returns:
            SkillMetadata 元数据对象
        """
        content = skill_file.read_text(encoding='utf-8')

        # 解析 YAML frontmatter（--- 包裹的部分）
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            raise ValueError(f"技能文件格式错误，缺少 frontmatter: {skill_file}")

        frontmatter_text = match.group(1)

        # 解析 frontmatter 键值对
        metadata_dict = {}
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                metadata_dict[key.strip()] = value.strip()

        name = metadata_dict.get('name', directory.name)
        description = metadata_dict.get('description', '')

        if not name:
            raise ValueError(f"技能文件缺少 name 字段: {skill_file}")

        return SkillMetadata(
            name=name,
            description=description,
            directory=directory,
            _full_content=match.group(2),  # 缓存完整正文
        )

    def get_catalog(self) -> str:
        """
        生成技能目录文本（注入给模型做意图匹配）
        
        只暴露 name + description，不暴露完整指令，节省 Token。
        
        Returns:
            格式化的技能目录文本
        """
        if not self._skills:
            return "当前没有可用的技能。"

        skills: list[dict[str, str]] = []
        for skill in self._skills.values():
            skills.append({
                "name": skill.name,
                "description": skill.description
            })

        return json.dumps(skills, ensure_ascii=False, indent=2)

    def get_skill_names(self) -> list[str]:
        """获取所有已注册技能的名称列表"""
        return list(self._skills.keys())

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """
        根据名称获取技能元数据
        
        Args:
            name: 技能名称
            
        Returns:
            SkillMetadata 或 None
        """
        return self._skills.get(name)

    def load_full_instruction(self, name: str) -> Optional[str]:
        """
        加载技能的完整指令内容（按需加载）
        
        类比 Java 中的 Lazy Loading：
        只有在模型确认需要该技能时，才加载完整 SKILL.md 正文。
        
        Args:
            name: 技能名称
            
        Returns:
            完整的 SKILL.md 正文内容，或 None
        """
        skill = self._skills.get(name)
        if skill is None:
            logger.warning(f"技能不存在: {name}")
            return None

        # 如果已经缓存了完整内容，直接返回
        if skill._full_content is not None:
            return skill._full_content

        # 否则从文件重新读取
        skill_file = skill.directory / "SKILL.md"
        if not skill_file.exists():
            logger.error(f"技能文件不存在: {skill_file}")
            return None

        content = skill_file.read_text(encoding='utf-8')
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            skill._full_content = match.group(2)
        else:
            skill._full_content = content

        return skill._full_content
