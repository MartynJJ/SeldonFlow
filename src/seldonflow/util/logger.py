from seldonflow.util.env import Environment

import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from pathlib import Path
from datetime import datetime
import os
import platform

TEST_LOG_FILE = Path("seldonflow_test")
PROD_LOG_FILE = Path("seldonflow")
LOG_DIR = Path("logs")
EXTERNAL_LOG_DIR = Path("src/seldonflow/data/shared/logs/SeldonFlow/")


def get_log_file_path(env: Environment) -> Path:
    if env == Environment.PRODUCTION:
        return LOG_DIR / PROD_LOG_FILE
    elif env == Environment.TESTING:
        return LOG_DIR / TEST_LOG_FILE
    else:
        raise ValueError(f"Unknown environment: {env}. Cannot determine log file path.")


class LoggingMixin:
    """Mixin class to provide consistent logging functionality across all classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger(f"SeldonFlow.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance for this class."""
        return self._logger


def setup_logging(log_file: str, log_level: str):
    """Configure unified logging for the entire platform."""

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    today = datetime.now().strftime("%Y%m%d")
    extension = ".log"
    daily_log_file = f"{log_file}{extension}"
    file_handler = TimedRotatingFileHandler(
        filename=daily_log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        delay=False,
        utc=False,
    )
    file_handler.suffix = "%Y-%m-%d"
    # file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    os.makedirs(EXTERNAL_LOG_DIR, exist_ok=True)  # Ensure external log directory exists
    computer_name = platform.node().replace(" ", "_")
    external_log_file = (
        EXTERNAL_LOG_DIR / f"{computer_name}_{Path(log_file).name}{extension}"
    )
    external_file_handler = TimedRotatingFileHandler(
        filename=external_log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        delay=False,
        utc=False,
    )
    external_file_handler.suffix = "%Y-%m-%d"
    external_file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger("SeldonFlow")
    root_logger.setLevel(getattr(logging, log_level.upper()))

    root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(external_file_handler)
    root_logger.addHandler(console_handler)

    root_logger.propagate = False
