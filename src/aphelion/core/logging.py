"""
Structured logging for Aphelion.

Provides consistent logging throughout the application.
"""

import logging
import sys
from typing import Final

# Configure logging format
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Create root logger for aphelion
_root_logger: logging.Logger | None = None


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance configured for Aphelion
    """
    global _root_logger

    if _root_logger is None:
        _root_logger = logging.getLogger("aphelion")
        _root_logger.setLevel(logging.INFO)

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        handler.setFormatter(formatter)
        _root_logger.addHandler(handler)

    # Return child logger
    if name.startswith("aphelion."):
        return logging.getLogger(name)
    else:
        return logging.getLogger(f"aphelion.{name}")


def set_log_level(level: int) -> None:
    """
    Set the log level for all aphelion loggers.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    global _root_logger
    if _root_logger:
        _root_logger.setLevel(level)
