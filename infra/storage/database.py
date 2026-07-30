"""
数据库连接管理

使用 SQLAlchemy 管理 SQLite 连接，支持会话持久化。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from infra.settings import settings
from infra.utils.log_util import logger
from functools import lru_cache


# 创建数据库引擎
Engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # 允许多线程访问 SQLite
    echo=False  # True 时会打印 SQL 语句（调试用）
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """
    获取数据库会话（依赖注入用）
    
    Yields:
        SQLAlchemy 会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库，创建所有表
    
    在应用启动时调用一次。
    """
    # 导入所有模型，确保它们被注册
    from infra.storage.models import Session, Message, AgentState
    
    # 创建所有表
    Base.metadata.create_all(bind=Engine)
    logger.info("SQLite 数据库初始化完成")


@lru_cache()
def get_engine():
    return Engine
