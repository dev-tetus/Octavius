"""Module responsible of setting up logging
"""
from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

def setup_logging(
    level: str = "INFO",
    log_dir: str | Path = "./logs",
    filename: str = "octavius.log",
    max_bytes: int = 1_000_000,   # ~1 MB
    backup_count: int = 3,
    console: bool = True,
    fmt: str = _DEFAULT_FORMAT,
    datefmt: str = _DEFAULT_DATEFMT,) -> str:
    """_summary_

    Args:
        level (str, optional): Level of logging. Defaults to "INFO".
        log_dir (str | Path, optional): Logs directory. Defaults to "./logs".
        filename (str, optional): Filename to write logs. Defaults to "octavius.log".
        max_bytes (int, optional): Max file size. Defaults to 1_000_000 ~1MB.
        backup_count (int) : Number of backup files used to create when log file 
        is close to max_bytes
        console (bool, optional): Wheter logs are show in console. Defaults to True.
        fmt (str, optional): Format of logs. Defaults to _DEFAULT_FORMAT.
        datefmt (str, optional): Date format for logs. Defaults to _DEFAULT_DATEFMT.

    Returns:
        str: Return log file path
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / filename

    root = logging.getLogger()
    root.handlers.clear()

    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    f_handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    f_handler.setFormatter(formatter)
    root.addHandler(f_handler)

    if console:
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(formatter)
        root.addHandler(c_handler)

    # Silenciar librerías ruidosas si hace falta (descomenta según tu stack)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.getLogger("openai").setLevel(logging.INFO)

    root.debug("Logging initialized")
    return log_path
