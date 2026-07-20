"""Reusable console and rotating-file logging."""

import logging
from logging.handlers import RotatingFileHandler

from src.utils.paths import LOG_DIR, ensure_runtime_directories


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger without adding duplicate handlers."""
    ensure_runtime_directories()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        LOG_DIR / f"{name}.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    console_handler = logging.StreamHandler()
    for handler in (file_handler, console_handler):
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
