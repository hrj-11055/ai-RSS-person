"""
Environment variable utility for AI-RSS-PERSON project.

Extracted from daily_report_PRO_cloud.py to provide consistent
environment variable loading across all modules and scripts.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file on import
load_dotenv()


def get_required_env(key: str) -> str:
    """
    Get a required environment variable.

    Args:
        key: Environment variable name

    Returns:
        Environment variable value

    Raises:
        ValueError: If the environment variable is not set

    Example:
        >>> api_key = get_required_env("API_KEY")
        >>> print(api_key)
        'sk-xxxxx'
    """
    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"❌ 缺少必需的环境变量: {key}\n"
            f"请在 .env 文件中设置 {key}=your_value_here"
        )
    return value


def get_optional_env(key: str, default: str = "") -> str:
    """
    Get an optional environment variable with a default value.

    Args:
        key: Environment variable name
        default: Default value if not set (defaults to empty string)

    Returns:
        Environment variable value or default

    Example:
        >>> port = get_optional_env("PORT", "8080")
        >>> print(port)
        '8080'
    """
    return os.getenv(key, default)


def get_int_env(key: str, default: int = 0) -> int:
    """
    Get an environment variable as an integer.

    Args:
        key: Environment variable name
        default: Default value if not set or invalid

    Returns:
        Integer value

    Example:
        >>> max_items = get_int_env("MAX_ITEMS", 10)
        >>> print(max_items)
        10
    """
    value = os.getenv(key)
    if value:
        try:
            return int(value)
        except ValueError:
            return default
    return default


def get_bool_env(key: str, default: bool = False) -> bool:
    """
    Get an environment variable as a boolean.

    Accepts: true, yes, 1, on (case-insensitive)

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Boolean value

    Example:
        >>> debug = get_bool_env("DEBUG", False)
        >>> print(debug)
        True
    """
    value = os.getenv(key, "").lower()
    if value in ("true", "yes", "1", "on"):
        return True
    elif value in ("false", "no", "0", "off"):
        return False
    return default


def get_list_env(key: str, default: Optional[list] = None, separator: str = ",") -> list:
    """
    Get an environment variable as a list.

    Args:
        key: Environment variable name
        default: Default value if not set
        separator: String to split on (defaults to comma)

    Returns:
        List of strings

    Example:
        >>> hosts = get_list_env("ALLOWED_HOSTS", ["localhost"])
        >>> print(hosts)
        ['localhost', 'example.com']
    """
    if default is None:
        default = []
    value = os.getenv(key)
    if value:
        return [item.strip() for item in value.split(separator)]
    return default
