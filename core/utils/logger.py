"""
Logging utility for AI-RSS-PERSON project.

Extracted from daily_report_PRO_cloud.py to provide consistent logging
across all modules and scripts.
"""

import logging
from typing import Optional


def setup_logger(name: str = __name__, level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name (defaults to module name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("my_module", "DEBUG")
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get an existing logger or create a new one with INFO level.

    This is a convenience function for getting a logger without
    specifying the log level.

    Args:
        name: Logger name (defaults to module name)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
