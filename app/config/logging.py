"""
统一日志配置模块
 - 控制台彩色 + 文件按日滚动
 - 模块级独立级别配置
 - get_logger() 获取日志实例
"""

import logging
import re
import sys
import os
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv

APP_NAME = "app"
LOG_DIR_NAME = "logs"
LOG_ENCODING = "utf-8"
DEFAULT_BACKUP_DAYS = 30

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

MODULE_LOG_LEVELS = {
    "app.routers": logging.INFO,
    "app.services": logging.INFO,
    "app.middlewares": logging.DEBUG,
    "app.handlers": logging.DEBUG,
    "app.models": logging.WARNING,
}


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[34m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self._use_colors = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                self._use_colors = True
            except Exception:
                self._use_colors = False

    def format(self, record):
        message = super().format(record)
        if self._use_colors:
            color = self.COLORS.get(record.levelno, "")
            if color:
                message = f"{color}{message}{self.RESET}"
        return message


def _get_global_log_level() -> int:
    load_dotenv()
    level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG, "INFO": logging.INFO,
        "WARNING": logging.WARNING, "WARN": logging.WARNING,
        "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, logging.INFO)


_initialized = False


def setup_logging():
    global _initialized
    if _initialized:
        return
    _initialized = True

    project_root = Path(__file__).resolve().parent.parent.parent
    log_dir = project_root / LOG_DIR_NAME
    log_dir.mkdir(exist_ok=True)

    global_level = _get_global_log_level()
    root_logger = logging.getLogger()
    root_logger.setLevel(global_level)

    app_logger = logging.getLogger(APP_NAME)
    app_logger.setLevel(global_level)

    third_party = [
        "uvicorn", "uvicorn.access", "uvicorn.error",
        "sqlalchemy", "sqlalchemy.engine", "sqlalchemy.pool",
        "httpx", "httpcore", "pymysql", "bcrypt", "jose", "dotenv",
    ]
    for name in third_party:
        logging.getLogger(name).setLevel(logging.WARNING)

    for module_name, level in MODULE_LOG_LEVELS.items():
        module_logger = logging.getLogger(module_name)
        env_key = f"LOG_LEVEL_{module_name.split('.')[-1].upper()}"
        env_val = os.environ.get(env_key)
        if env_val:
            level = getattr(logging, env_val.upper(), level)
        module_logger.setLevel(level)

    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_formatter = ColorFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(global_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    app_log_path = log_dir / "app.log"
    app_file_handler = TimedRotatingFileHandler(
        filename=str(app_log_path), when="midnight", interval=1,
        backupCount=DEFAULT_BACKUP_DAYS, encoding=LOG_ENCODING,
    )
    app_file_handler.suffix = "%Y-%m-%d"
    app_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    app_file_handler.setLevel(global_level)
    app_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(app_file_handler)

    error_log_path = log_dir / "app_error.log"
    error_handler = TimedRotatingFileHandler(
        filename=str(error_log_path), when="midnight", interval=1,
        backupCount=DEFAULT_BACKUP_DAYS, encoding=LOG_ENCODING,
    )
    error_handler.suffix = "%Y-%m-%d"
    error_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    level_name = logging.getLevelName(global_level)
    logging.info(f"日志系统初始化完成 | 全局级别: {level_name}")


def get_logger(name: str = "system") -> logging.Logger:
    if not _initialized:
        setup_logging()
    if name == "system":
        return logging.getLogger(APP_NAME)
    if not name.startswith(f"{APP_NAME}."):
        logger_name = f"{APP_NAME}.{name}"
    else:
        logger_name = name
    return logging.getLogger(logger_name)
