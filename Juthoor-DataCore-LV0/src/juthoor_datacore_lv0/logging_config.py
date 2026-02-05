"""
Logging configuration for Juthoor DataCore.

Usage:
    from juthoor_datacore_lv0.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Processing %d items", count)
"""
from __future__ import annotations

import logging
import os
import sys
from typing import TextIO


def setup_logging(
    level: str | None = None,
    stream: TextIO = sys.stderr,
    format_string: str | None = None,
) -> None:
    """
    Configure root logging for Juthoor.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to INFO.
               Can be overridden by JUTHOOR_LOG_LEVEL env var.
        stream: Output stream. Defaults to stderr.
        format_string: Custom format string. Defaults to timestamp | level | name | message.
    """
    # Allow environment variable override
    level = level or os.environ.get("JUTHOOR_LOG_LEVEL", "INFO")
    format_string = format_string or "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=stream,
        force=True,  # Override any existing config
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the given module name.

    Args:
        name: Usually __name__ of the calling module.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


# Initialize logging on import with default settings
setup_logging()
