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

_deprecation_warned = False


def _warn_deprecated_fallback():
    global _deprecation_warned
    if not _deprecation_warned:
        print("⚠️ [DEPRECATED] 直接使用 core.utils.env 读取配置将在下一版本移除，请改为 core.settings")
        _deprecation_warned = True


def _try_get_from_settings(key: str):
    try:
        from core.settings import get_settings, is_settings_initialized
    except Exception:
        return None

    if not is_settings_initialized():
        return None

    s = get_settings()
    mapping = {
        "DEEPSEEK_API_KEY": s.ai.api_key,
        "DEEPSEEK_BASE_URL": s.ai.base_url,
        "AI_MODEL": s.ai.model,
        "RSSHUB_HOST": s.rss.rsshub_host,
        "PROXY_URL": s.rss.proxy_url,
        "MAX_ITEMS_PER_SOURCE": str(s.rss.max_items_per_source),
        "TIME_WINDOW_HOURS": str(s.rss.time_window_hours),
        "ENABLE_PROXY_IP_UPDATE": str(s.rss.enable_proxy_ip_update).lower(),
        "MAX_ARTICLES_IN_REPORT": str(s.report.max_articles_in_report),
        "OUTPUT_DIR": s.report.output_dir,
        "LOG_LEVEL": s.logging.level,
        "UPLOAD_ENABLED": str(s.cloud.enabled).lower(),
        "CLOUD_SERVER_HOST": s.cloud.host,
        "CLOUD_SERVER_PORT": str(s.cloud.port),
        "CLOUD_SERVER_USER": s.cloud.user,
        "CLOUD_SERVER_PASSWORD": s.cloud.password,
        "CLOUD_SERVER_KEY_PATH": s.cloud.key_path,
        "CLOUD_SERVER_REMOTE_PATH": s.cloud.remote_path,
        "CLOUD_SERVER_JSON_REMOTE_PATH": s.cloud.json_remote_path,
        "UPLOAD_METHOD": s.cloud.upload_method,
        "HTTP_UPLOAD_URL": s.cloud.http_upload_url,
        "HTTP_UPLOAD_TOKEN": s.cloud.http_upload_token,
        "EMAIL_ENABLED": str(s.email.enabled).lower(),
        "EMAIL_WHEN_UPLOAD_FAIL": str(s.email.when_upload_fail).lower(),
        "SMTP_SERVER": s.email.smtp_server,
        "SMTP_PORT": str(s.email.smtp_port),
        "SENDER_EMAIL": s.email.sender_email,
        "SENDER_PASSWORD": s.email.sender_password,
        "RECEIVER_EMAIL": s.email.receiver_email,
        "CC_EMAIL": s.email.cc_email,
        "BCC_EMAIL": s.email.bcc_email,
        "PIPELINE_CACHE_DIR": s.pipeline.cache_dir,
        "RESUME_FROM_CACHE": str(s.pipeline.resume_from_cache).lower(),
        "STAGE_RETRY_COUNT": str(s.pipeline.retry_count),
        "STAGE_RETRY_DELAY_SECONDS": str(s.pipeline.retry_delay_seconds),
        "PIPELINE_LOCK_FILE": str(s.pipeline.lock_file),
        "SOURCES_YAML_PATH": str(s.sources_path),
        "WEIGHTS_YAML_PATH": str(s.weights_path),
    }
    return mapping.get(key)


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
    value = _try_get_from_settings(key)
    if value is None:
        _warn_deprecated_fallback()
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
    value = _try_get_from_settings(key)
    if value is not None:
        return str(value)
    _warn_deprecated_fallback()
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
    value = _try_get_from_settings(key)
    if value is None:
        _warn_deprecated_fallback()
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
    value = _try_get_from_settings(key)
    if value is None:
        _warn_deprecated_fallback()
        value = os.getenv(key, "")
    value = str(value).lower()
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
    value = _try_get_from_settings(key)
    if value is None:
        _warn_deprecated_fallback()
        value = os.getenv(key)
    if value:
        return [item.strip() for item in value.split(separator)]
    return default
