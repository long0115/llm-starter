"""
应用配置类

使用 Pydantic Settings 自动从环境变量和 .env 文件加载配置。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):

    # 环境标识
    APP_ENV: str = "dev"

    # 项目配置
    PROJECT_NAME: str = "MultiAgentFlow"
    PROJECT_DESC: str = "AI大模型 - 多 Agent 协作工作流框架"
    PROJECT_VERSION: str = "1.0.0"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite:///sqlite_db/llm_app.db"

    # 知识库配置
    RAG_ROOT_DIR: str = "./docs"                                                        # 知识库根目录
    RAG_SUPPORTED_EXTENSIONS: List[str] = [".md", ".txt", ".pdf", ".docx", ".doc"]      # 支持的文件扩展名
    RAG_IGNORE_PATTERNS: List[str] = ["__pycache__", ".git", "node_modules", "*.log"]   # 忽略的文件模式
    RAG_VECTOR_TOP_K: int = 10                                                          # 向量检索结果数
    RAG_BM25_TOP_K: int = 10                                                            # BM25检索结果数
    RAG_RERANK_TOP_K: int = 3                                                           # 重排序检索结果数
    RAG_HYBRID_WEIGHTS: List[float] = [0.6, 0.4]                                        # 混合权重 [向量权重, BM25 权重]

    # 向量数据库配置
    CHROMA_STORE_DIR: str = "./chroma_db"
    CHROMA_STORE_COLLECTION: str = "llm_app_docs"

    # 认证配置
    SECRET_KEY: str = "your-secret-key-for-jwt"     # JWT 密钥
    ALGORITHM: str = "HS256"                        # JWT 算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30           # 访问令牌过期时间，单位分钟

    # 日志配置
    LOG_NAME: str = "app"                   # 日志名称，默认 app
    LOG_LEVEL: str = "INFO"                 # 日志最低级别
    LOG_DIR: str = "./logs"                 # 日志所在目录
    LOG_MAX_BYTES: int = 10485760           # 日志文件最大大小，单位字节
    LOG_FILE_PATH: str = "logs"             # 日志文件路径，相对于 LOG_DIR 目录

    # 速率限制配置
    RATE_LIMIT_MAX_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # CORS 配置
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    # LLM 配置 - 豆包（.env文件读取，默认None）
    DOUBAO_API_KEY: Optional[str] = None
    DOUBAO_BASE_URL: Optional[str] = None
    DOUBAO_CHAT_MODEL: Optional[str] = None
    DOUBAO_EMBEDDING_MODEL: Optional[str] = None

    # LLM 配置 - 阿里云（.env文件读取，默认None）
    ALIYUN_API_KEY: Optional[str] = None
    ALIYUN_BASE_URL: Optional[str] = None
    ALIYUN_CHAT_MODEL: Optional[str] = None
    ALIYUN_EMBEDDING_MODEL: Optional[str] = None

    # 天气配置 - 和风天气（.env文件读取，默认None）
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_HOST: Optional[str] = None

    # 新增：默认 LLM 提供商
    DEFAULT_LLM_PROVIDER: str = "aliyun"

    @property
    def llm_config(self) -> dict:
        """根据 DEFAULT_LLM_PROVIDER 返回对应的 LLM 配置"""
        if self.DEFAULT_LLM_PROVIDER == "doubao":
            return {
                "api_key": self.DOUBAO_API_KEY,
                "base_url": self.DOUBAO_BASE_URL,
                "chat_model": self.DOUBAO_CHAT_MODEL,
                "embedding_model": self.DOUBAO_EMBEDDING_MODEL,
            }
        else:  # 默认 aliyun
            return {
                "api_key": self.ALIYUN_API_KEY,
                "base_url": self.ALIYUN_BASE_URL,
                "chat_model": self.ALIYUN_CHAT_MODEL,
                "embedding_model": self.ALIYUN_EMBEDDING_MODEL,
            }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",  # 编码格式 UTF-8
        case_sensitive=False,       # 不区分大小写
        extra="allow"               # 允许额外的环境变量    
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "prod"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()