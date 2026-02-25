"""
Core utilities for AI-RSS-PERSON project.

This module provides shared utilities for logging, environment variable handling,
cost tracking, and constants.
"""

from .logger import setup_logger, get_logger
from .env import (
    get_required_env,
    get_optional_env,
    get_int_env,
    get_bool_env,
    get_list_env,
)
from .cost_tracker import CostTracker
from .constants import *
from core.settings import (
    get_settings,
    load_settings,
    validate_settings,
    set_settings,
    clear_settings,
    is_settings_initialized,
)

__all__ = [
    # Logger
    "setup_logger",
    "get_logger",
    # Environment
    "get_required_env",
    "get_optional_env",
    "get_int_env",
    "get_bool_env",
    "get_list_env",
    # Cost tracking
    "CostTracker",
    # Settings
    "get_settings",
    "load_settings",
    "validate_settings",
    "set_settings",
    "clear_settings",
    "is_settings_initialized",
    # Constants (all exported from constants module)
]

# 导入配置管理器（在模块级别避免循环导入）
try:
    from ..config_manager import get_config_manager, ConfigManager
    __all__.extend(["get_config_manager", "ConfigManager"])
except ImportError:
    pass
