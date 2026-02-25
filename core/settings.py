"""
Unified application settings.

Configuration precedence:
1) Environment variables (highest)
2) core/config.yaml (selected scalar settings)
3) constants.py defaults (lowest)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

from core.utils.constants import (
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_MODEL,
    DEFAULT_CLOUD_SERVER_HOST,
    DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH,
    DEFAULT_CLOUD_SERVER_PORT,
    DEFAULT_CLOUD_SERVER_REMOTE_PATH,
    DEFAULT_CLOUD_SERVER_USER,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_ARTICLES_IN_REPORT,
    DEFAULT_MAX_ITEMS_PER_SOURCE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RSSHUB_HOST,
    DEFAULT_UPLOAD_METHOD,
)


@dataclass
class AISettings:
    api_key: str
    base_url: str = DEFAULT_AI_BASE_URL
    model: str = DEFAULT_AI_MODEL


@dataclass
class RSSSettings:
    rsshub_host: str = DEFAULT_RSSHUB_HOST
    proxy_url: str = ""
    max_items_per_source: int = DEFAULT_MAX_ITEMS_PER_SOURCE
    time_window_hours: int = 24


@dataclass
class ReportSettings:
    output_dir: str = DEFAULT_OUTPUT_DIR
    max_articles_in_report: int = DEFAULT_MAX_ARTICLES_IN_REPORT


@dataclass
class CloudSettings:
    enabled: bool = True
    host: str = DEFAULT_CLOUD_SERVER_HOST
    port: int = DEFAULT_CLOUD_SERVER_PORT
    user: str = DEFAULT_CLOUD_SERVER_USER
    password: str = ""
    key_path: str = ""
    remote_path: str = DEFAULT_CLOUD_SERVER_REMOTE_PATH
    json_remote_path: str = DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH
    upload_method: str = DEFAULT_UPLOAD_METHOD
    http_upload_url: str = ""
    http_upload_token: str = ""


@dataclass
class EmailSettings:
    enabled: bool = True
    when_upload_fail: bool = False
    smtp_server: str = ""
    smtp_port: int = 465
    sender_email: str = ""
    sender_password: str = ""
    receiver_email: str = ""
    cc_email: str = ""
    bcc_email: str = ""


@dataclass
class PipelineSettings:
    cache_dir: str = str(Path(DEFAULT_OUTPUT_DIR) / ".pipeline")
    resume_from_cache: bool = True
    retry_count: int = 1
    retry_delay_seconds: int = 3


@dataclass
class LoggingSettings:
    level: str = DEFAULT_LOG_LEVEL


@dataclass
class AppSettings:
    ai: AISettings
    rss: RSSSettings
    report: ReportSettings
    cloud: CloudSettings
    email: EmailSettings
    pipeline: PipelineSettings
    logging: LoggingSettings
    sources_path: Path
    weights_path: Path


_settings_instance: Optional[AppSettings] = None


def _to_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    if s in {"0", "false", "no", "off"}:
        return False
    return default


def _get_cfg(cfg: dict, path: str, default: Any = None) -> Any:
    node: Any = cfg
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def _load_core_yaml(project_root: Path) -> dict:
    core_yaml = project_root / "core" / "config.yaml"
    if not core_yaml.exists():
        return {}
    with core_yaml.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings() -> AppSettings:
    load_dotenv()

    project_root = Path(__file__).resolve().parent.parent
    yaml_cfg = _load_core_yaml(project_root)

    # constants -> YAML -> ENV
    ai_base_url = os.getenv("DEEPSEEK_BASE_URL", _get_cfg(yaml_cfg, "ai.base_url", DEFAULT_AI_BASE_URL))
    ai_model = os.getenv("AI_MODEL", _get_cfg(yaml_cfg, "ai.model", DEFAULT_AI_MODEL))
    ai_api_key = os.getenv("DEEPSEEK_API_KEY", "")

    rsshub_host = os.getenv("RSSHUB_HOST", _get_cfg(yaml_cfg, "rss.rsshub_host", DEFAULT_RSSHUB_HOST))
    proxy_url = os.getenv("PROXY_URL", "")
    max_items = _to_int(os.getenv("MAX_ITEMS_PER_SOURCE"), _to_int(_get_cfg(yaml_cfg, "rss.max_items_per_source"), DEFAULT_MAX_ITEMS_PER_SOURCE))
    time_window = _to_int(os.getenv("TIME_WINDOW_HOURS"), _to_int(_get_cfg(yaml_cfg, "rss.time_window_hours"), 24))

    output_dir = os.getenv("OUTPUT_DIR", _get_cfg(yaml_cfg, "directories.output_dir", DEFAULT_OUTPUT_DIR))
    max_articles = _to_int(
        os.getenv("MAX_ARTICLES_IN_REPORT"),
        _to_int(_get_cfg(yaml_cfg, "ranking.max_articles_in_report"), DEFAULT_MAX_ARTICLES_IN_REPORT),
    )

    cloud_enabled = _to_bool(os.getenv("UPLOAD_ENABLED"), _to_bool(_get_cfg(yaml_cfg, "publishing.cloud.enabled"), True))
    cloud_host = os.getenv("CLOUD_SERVER_HOST", _get_cfg(yaml_cfg, "publishing.cloud.host", DEFAULT_CLOUD_SERVER_HOST))
    cloud_port = _to_int(os.getenv("CLOUD_SERVER_PORT"), _to_int(_get_cfg(yaml_cfg, "publishing.cloud.port"), DEFAULT_CLOUD_SERVER_PORT))
    cloud_user = os.getenv("CLOUD_SERVER_USER", _get_cfg(yaml_cfg, "publishing.cloud.user", DEFAULT_CLOUD_SERVER_USER))
    cloud_password = os.getenv("CLOUD_SERVER_PASSWORD", "")
    cloud_key_path = os.getenv("CLOUD_SERVER_KEY_PATH", "")
    cloud_remote_path = os.getenv("CLOUD_SERVER_REMOTE_PATH", _get_cfg(yaml_cfg, "publishing.cloud.remote_path", DEFAULT_CLOUD_SERVER_REMOTE_PATH))
    cloud_json_remote = os.getenv("CLOUD_SERVER_JSON_REMOTE_PATH", DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH)
    upload_method = os.getenv("UPLOAD_METHOD", _get_cfg(yaml_cfg, "publishing.cloud.method", DEFAULT_UPLOAD_METHOD))
    http_upload_url = os.getenv("HTTP_UPLOAD_URL", "")
    http_upload_token = os.getenv("HTTP_UPLOAD_TOKEN", "")

    email_enabled = _to_bool(os.getenv("EMAIL_ENABLED"), True)
    email_when_upload_fail = _to_bool(os.getenv("EMAIL_WHEN_UPLOAD_FAIL"), False)

    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = _to_int(os.getenv("SMTP_PORT"), 465)
    sender_email = os.getenv("SENDER_EMAIL", "")
    sender_password = os.getenv("SENDER_PASSWORD", "")
    receiver_email = os.getenv("RECEIVER_EMAIL", "")
    cc_email = os.getenv("CC_EMAIL", "")
    bcc_email = os.getenv("BCC_EMAIL", "")

    pipeline_cache_dir = os.getenv("PIPELINE_CACHE_DIR", str(Path(output_dir) / ".pipeline"))
    resume_from_cache = _to_bool(os.getenv("RESUME_FROM_CACHE"), True)
    retry_count = _to_int(os.getenv("STAGE_RETRY_COUNT"), 1)
    retry_delay = _to_int(os.getenv("STAGE_RETRY_DELAY_SECONDS"), 3)

    log_level = os.getenv("LOG_LEVEL", _get_cfg(yaml_cfg, "logging.level", DEFAULT_LOG_LEVEL))

    sources_path = Path(os.getenv("SOURCES_YAML_PATH", str(project_root / "config" / "sources.yaml")))
    weights_path = Path(os.getenv("WEIGHTS_YAML_PATH", str(project_root / "config" / "weights.yaml")))

    settings = AppSettings(
        ai=AISettings(api_key=ai_api_key, base_url=ai_base_url, model=ai_model),
        rss=RSSSettings(
            rsshub_host=rsshub_host,
            proxy_url=proxy_url,
            max_items_per_source=max_items,
            time_window_hours=time_window,
        ),
        report=ReportSettings(output_dir=output_dir, max_articles_in_report=max_articles),
        cloud=CloudSettings(
            enabled=cloud_enabled,
            host=cloud_host,
            port=cloud_port,
            user=cloud_user,
            password=cloud_password,
            key_path=cloud_key_path,
            remote_path=cloud_remote_path,
            json_remote_path=cloud_json_remote,
            upload_method=upload_method,
            http_upload_url=http_upload_url,
            http_upload_token=http_upload_token,
        ),
        email=EmailSettings(
            enabled=email_enabled,
            when_upload_fail=email_when_upload_fail,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            sender_email=sender_email,
            sender_password=sender_password,
            receiver_email=receiver_email,
            cc_email=cc_email,
            bcc_email=bcc_email,
        ),
        pipeline=PipelineSettings(
            cache_dir=pipeline_cache_dir,
            resume_from_cache=resume_from_cache,
            retry_count=retry_count,
            retry_delay_seconds=retry_delay,
        ),
        logging=LoggingSettings(level=log_level),
        sources_path=sources_path,
        weights_path=weights_path,
    )
    return settings


def validate_settings(settings: AppSettings) -> None:
    if not settings.ai.api_key:
        raise ValueError("❌ 缺少 DEEPSEEK_API_KEY")

    if not settings.sources_path.exists():
        raise ValueError(f"❌ sources 配置文件不存在: {settings.sources_path}")
    if not settings.weights_path.exists():
        raise ValueError(f"❌ weights 配置文件不存在: {settings.weights_path}")

    if settings.cloud.enabled:
        if settings.cloud.upload_method not in {"sftp", "http", "ftp"}:
            raise ValueError(f"❌ 不支持的上传方式: {settings.cloud.upload_method}")
        if settings.cloud.upload_method in {"sftp", "ftp"}:
            if not settings.cloud.host or not settings.cloud.user:
                raise ValueError("❌ 启用上传后，SFTP/FTP 需要 CLOUD_SERVER_HOST 和 CLOUD_SERVER_USER")
        if settings.cloud.upload_method == "http" and not settings.cloud.http_upload_url:
            raise ValueError("❌ UPLOAD_METHOD=http 时必须配置 HTTP_UPLOAD_URL")

    if settings.email.enabled:
        required = {
            "SMTP_SERVER": settings.email.smtp_server,
            "SENDER_EMAIL": settings.email.sender_email,
            "SENDER_PASSWORD": settings.email.sender_password,
            "RECEIVER_EMAIL": settings.email.receiver_email,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"❌ 启用邮件后缺少配置: {', '.join(missing)}")

    if settings.report.max_articles_in_report <= 0:
        raise ValueError("❌ MAX_ARTICLES_IN_REPORT 必须 > 0")
    if settings.rss.max_items_per_source <= 0:
        raise ValueError("❌ MAX_ITEMS_PER_SOURCE 必须 > 0")
    if settings.pipeline.retry_count < 0:
        raise ValueError("❌ STAGE_RETRY_COUNT 不能为负数")
    if settings.pipeline.retry_delay_seconds < 0:
        raise ValueError("❌ STAGE_RETRY_DELAY_SECONDS 不能为负数")


def set_settings(settings: AppSettings) -> None:
    global _settings_instance
    _settings_instance = settings


def clear_settings() -> None:
    global _settings_instance
    _settings_instance = None


def is_settings_initialized() -> bool:
    return _settings_instance is not None


def get_settings() -> AppSettings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = load_settings()
    return _settings_instance
