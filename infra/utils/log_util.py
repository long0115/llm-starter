import logging
import os
import glob
from functools import lru_cache
from datetime import datetime
from infra.settings import settings


class LevelDateSizeFileHandler(logging.Handler):
    """
    自定义日志处理器
    
    按照日期+大小切割
    每个级别一个目录，仅写入对应级别日志
    文件名格式：logs/error/2023-07-14_1.log
    """
    def __init__(self, log_dir: str, level: int, max_bytes: int, encoding: str = "utf-8"):
        super().__init__()
        self.log_dir = log_dir
        self.level = level
        self.max_bytes = max_bytes
        self.encoding = encoding

        # 文件句柄缓存
        self.stream = None
        self.baseFilename = None

    def _get_level_dir(self) -> str:
        # 获取当前级别对应的目录
        level_name = logging.getLevelName(self.level).lower()
        return os.path.join(self.log_dir, level_name)

    def _get_current_filename(self) -> str:
        # 获取当前应该写入的日志文件名
        today = datetime.now().strftime("%Y-%m-%d")
        level_dir = self._get_level_dir()

        # 查找当天已存在的日志文件
        pattern = os.path.join(level_dir, f"{today}_*.log")
        existing_files = glob.glob(pattern)

        if not existing_files:
            return os.path.join(level_dir, f"{today}_1.log")

        max_num = 0
        for file in existing_files:
            try:
                basename = os.path.basename(file)
                num_part = basename.split('_')[-1].replace('.log', '')
                max_num = max(max_num, int(num_part))
            except (IndexError, ValueError):
                continue

        current_file = os.path.join(level_dir, f"{today}_{max_num}.log")
        if os.path.exists(current_file) and os.path.getsize(current_file) >= self.max_bytes:
            return os.path.join(level_dir, f"{today}_{max_num + 1}.log")
        return current_file

    def _open(self):
        # 动态打开文件，不存在目录先创建
        target_file = self._get_current_filename()
        target_dir = os.path.dirname(target_file)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.baseFilename = target_file
        self.stream = open(self.baseFilename, mode='a', encoding=self.encoding)

    def _close(self):
        # 关闭文件流
        if self.stream:
            self.stream.close()
            self.stream = None
        super().close()

    def emit(self, record):
        # 核心修复：仅完全匹配当前handler绑定级别才输出，杜绝串流
        if record.levelno != self.level:
            return

        # 检查是否需要切换文件
        new_file = self._get_current_filename()
        # 文件不存在 / 文件变更 / 流未打开，则重新打开
        if self.stream is None or self.baseFilename != new_file or not os.path.exists(new_file):
            self._close()
            self._open()

        # 写入日志
        msg = self.format(record)
        self.stream.write(msg + "\n")
        self.stream.flush()

def setup_logger() -> logging.Logger:
    """
    创建按级别分离、日期+大小双重切割的日志记录器

    :Returns: logger实例
    """
    
    logger = logging.getLogger(settings.LOG_NAME)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    logger.propagate = False    # 防止日志冒泡，仅在当前logger处理
    logger.handlers.clear()     # 清空所有已绑定的handler
    # 日志格式化器
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 每个级别独立Handler，仅接收对应等级日志
    levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    for level in levels:
        handler = LevelDateSizeFileHandler(
            log_dir=settings.LOG_DIR,
            level=level,
            max_bytes=settings.LOG_MAX_BYTES
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


@lru_cache()
def get_logger() -> logging.Logger:
    return setup_logger()

logger = setup_logger()
