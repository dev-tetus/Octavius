"""Module responsible for setting up logging."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Iterable, Tuple


_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


class _PrefixFilter(logging.Filter):
    """Allow only records whose logger name starts with any allowed prefix."""

    def __init__(self, allowed_prefixes: Tuple[str, ...]) -> None:
        super().__init__()
        self.allowed = allowed_prefixes

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name or ""
        return any(name.startswith(pfx) for pfx in self.allowed)


def setup_logging(
    level: str = "INFO",
    log_dir: str | Path = "./logs",
    filename: str = "octavius.log",
    max_bytes: int = 1_000_000,  # ~1 MB
    backup_count: int = 3,
    console: bool = True,
    fmt: str = _DEFAULT_FORMAT,
    datefmt: str = _DEFAULT_DATEFMT,
    *,
    # Extra options
    console_level: Optional[str] = None,                  # e.g., "INFO" (if None, uses root level)
    file_level: Optional[str] = None,                     # e.g., "DEBUG"
    console_only_prefixes: Optional[Iterable[str]] = None,  # e.g., ["octavius", "__main__"]
    module_levels: Optional[Dict[str, str]] = None,       # {"httpx":"WARNING", ...}
    disable_propagation: Optional[Iterable[str]] = None,  # ["httpx","httpcore"]
) -> Path:
    """
    Configure logging with rotating file handler and optional console handler.

    Args:
        level: Root logger level (e.g., "INFO", "DEBUG", "WARN", "ERROR").
        log_dir: Directory where the log file will be created.
        filename: Log file name.
        max_bytes: Maximum file size before rotation.
        backup_count: Number of rotated files to keep.
        console: Whether to also log to stderr (console).
        fmt: Log format string.
        datefmt: Date format.
        console_level: Specific level for the console handler (overrides root level for console).
        file_level: Specific level for the file handler (overrides root level for file).
        console_only_prefixes: If provided, only logs whose logger name starts with any of
                               these prefixes will be shown in console (e.g., "octavius", "__main__").
        module_levels: Per-module level overrides, e.g. {"httpx": "WARNING"}.
        disable_propagation: Modules for which to disable propagation to the root logger.

    Returns:
        Path: Full path to the created log file.
    """
    # Prepare paths
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / filename

    # Root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # File handler (rotating)
    f_handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    f_handler.setFormatter(formatter)
    if file_level:
        f_handler.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
    root.addHandler(f_handler)

    # Console handler
    if console:
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(formatter)
        if console_level:
            c_handler.setLevel(getattr(logging, console_level.upper(), root.level))
        if console_only_prefixes:
            c_handler.addFilter(_PrefixFilter(tuple(console_only_prefixes)))
        root.addHandler(c_handler)

    # Per-module level overrides (quiet noisy libs)
    if module_levels:
        for name, lvl in module_levels.items():
            logging.getLogger(name).setLevel(getattr(logging, lvl.upper(), logging.WARNING))

    # Disable propagation for specific modules if requested
    if disable_propagation:
        for name in disable_propagation:
            logging.getLogger(name).propagate = False

    root.debug("Logging initialized")
    return log_path
