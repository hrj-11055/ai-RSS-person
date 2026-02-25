"""
Logging utility for AI-RSS-PERSON project.

Extracted from daily_report_PRO_cloud.py to provide consistent logging
across all modules and scripts.
"""

import logging
from typing import Optional

from .observability import get_run_id, get_stage


class ObservabilityContextFilter(logging.Filter):
    """Inject run context fields for consistent structured logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = get_run_id()
        if not hasattr(record, "stage"):
            record.stage = get_stage()
        if not hasattr(record, "error_code"):
            record.error_code = "-"
        if not hasattr(record, "severity"):
            record.severity = "-"
        return True


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
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[run_id=%(run_id)s stage=%(stage)s err=%(error_code)s sev=%(severity)s] '
            '%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        console_handler.addFilter(ObservabilityContextFilter())

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
