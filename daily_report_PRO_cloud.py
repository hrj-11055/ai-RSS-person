"""
AI 日报生成器 - 云服务器版本
"""

import json
import sys
import datetime
import time
import os
import fcntl
import shutil
import re
from collections import Counter as CharCounter
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

from core.utils import setup_logger, CostTracker
from core.utils.observability import (
    RunMetrics,
    classify_error,
    clear_stage,
    create_run_id,
    get_run_id,
    set_run_id,
    set_stage,
)

from lib.rss_collector import RSSCollector
from lib.ai_analyzer import AIAnalyzer
from lib.publishers.cloud_publisher import CloudPublisher
from lib.publishers.local_publisher import LocalPublisher
from lib.article_deduplicator import ArticleDeduplicator
from article_ranker import ArticleRanker

from core.config_manager import get_config_manager
from core.settings import AppSettings, load_settings, validate_settings, set_settings


# 先用默认级别初始化，加载配置后会更新级别
logger = setup_logger(__name__)


def update_rsshub_proxy_ip():
    """
    自动获取 OrbStack bridge100 IP 并更新 .env 中的 PROXY_URI。
    """
    import subprocess
    import re

    try:
        result = subprocess.run(
            ["ifconfig", "bridge100"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", result.stdout)
            if match:
                new_ip = match.group(1)
            else:
                logger.warning("⚠️ 无法从 bridge100 获取 IP")
                return False
        else:
            logger.warning("⚠️ bridge100 接口不存在，跳过代理 IP 更新")
            return False

        env_file = Path(__file__).parent / ".env"
        if not env_file.exists():
            logger.warning("⚠️ .env 不存在，跳过代理 IP 更新")
            return False

        content = env_file.read_text(encoding="utf-8")
        expected = f"PROXY_URI=http://{new_ip}:7897"

        if re.search(r"^PROXY_URI=http://\d+\.\d+\.\d+\.\d+:7897$", content, flags=re.MULTILINE):
            new_content = re.sub(
                r"^PROXY_URI=http://\d+\.\d+\.\d+\.\d+:7897$",
                expected,
                content,
                flags=re.MULTILINE,
            )
        elif re.search(r"^PROXY_URI=", content, flags=re.MULTILINE):
            new_content = re.sub(
                r"^PROXY_URI=.*$",
                expected,
                content,
                flags=re.MULTILINE,
            )
        else:
            new_content = content.rstrip() + f"\n{expected}\n"

        if new_content == content:
            logger.info(f"✅ 代理 IP 无需更新: {new_ip}")
            return True

        env_file.write_text(new_content, encoding="utf-8")
        logger.info(f"🔄 已更新 .env 中的代理 IP: {new_ip}")

        try:
            restart_cmd = os.getenv("RSSHUB_RESTART_CMD", "").strip()
            service_name = os.getenv("RSSHUB_SERVICE_NAME", "").strip()
            pm2_name = os.getenv("RSSHUB_PM2_NAME", "").strip()

            if restart_cmd:
                subprocess.run(
                    ["bash", "-lc", restart_cmd],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=Path(__file__).parent,
                )
            elif service_name:
                subprocess.run(
                    ["systemctl", "restart", service_name],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            elif pm2_name:
                subprocess.run(
                    ["pm2", "restart", pm2_name],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            else:
                logger.warning("⚠️ 未配置 RSSHub 重启命令（RSSHUB_RESTART_CMD / RSSHUB_SERVICE_NAME）")
                return True

            logger.info("✅ RSSHub 服务已重启")
            time.sleep(5)
        except Exception as e:
            logger.warning(f"⚠️ RSSHub 重启失败: {e}")

        return True

    except FileNotFoundError:
        logger.warning("⚠️ ifconfig 命令不可用，跳过代理 IP 更新")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("⚠️ 获取 IP 超时，跳过代理 IP 更新")
        return False
    except Exception as e:
        logger.warning(f"⚠️ 更新代理 IP 时出错: {e}")
        return False


class FileLock:
    """Single-instance process lock based on flock."""

    def __init__(self, path: str):
        self.path = Path(path)
        self._fd = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(self.path, "w", encoding="utf-8")
        try:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            self._fd.close()
            self._fd = None
            raise RuntimeError(f"lock already held: {self.path}") from e
        self._fd.seek(0)
        self._fd.truncate()
        self._fd.write(f"{os.getpid()}\n")
        self._fd.flush()

    def release(self):
        if self._fd:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            finally:
                self._fd.close()
                self._fd = None


class AI_Daily_Report:
    """AI 日报生成器主类"""
    DAILY_SOURCE_CAP = 4
    HISTORY_DEDUP_DAYS = 3
    HISTORY_TITLE_SIM_THRESHOLD = 0.72
    HISTORY_EVENT_SIM_THRESHOLD = 0.60
    INTRADAY_TITLE_SIM_THRESHOLD_STRONG = 0.72
    INTRADAY_TITLE_SIM_THRESHOLD_NUMERIC = 0.43
    INTRADAY_COMMON_SUBSTR_MIN = 6
    FINAL_CONTENT_SIM_THRESHOLD_STRONG = 0.72
    FINAL_CONTENT_SIM_THRESHOLD_NUMERIC = 0.40
    FINAL_CONTENT_OVERLAP_THRESHOLD_NUMERIC = 0.45
    FINAL_CONTENT_COMMON_SUBSTR_MIN = 6
    FINAL_CONTENT_TITLE_SIM_GUARD = 0.42

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.metrics: RunMetrics | None = None
        self._last_ranked_items: list[dict] = []

        logger.setLevel(settings.logging.level.upper())

        self.config_manager = get_config_manager(
            sources_file=settings.sources_path,
            weights_file=settings.weights_path,
        )
        sources = self.config_manager.get_enabled_sources()
        self.enabled_source_names = [s.get("name", "") for s in sources]
        logger.info(f"📡 已加载 {len(sources)} 个启用的 RSS 源")

        self.ranker = ArticleRanker(config_manager=self.config_manager)
        self.deduplicator = ArticleDeduplicator(config_manager=self.config_manager)
        self.cost_tracker = CostTracker()

        self.collector = RSSCollector(
            sources=sources,
            proxy_url=settings.rss.proxy_url,
            rsshub_host=settings.rss.rsshub_host,
            max_items_per_source=settings.rss.max_items_per_source,
            time_window_hours=settings.rss.time_window_hours,
            log_level=settings.logging.level,
        )

        self.analyzer = AIAnalyzer(
            api_key=settings.ai.api_key,
            base_url=settings.ai.base_url,
            model=settings.ai.model,
        )

        self.cloud_publisher = CloudPublisher(
            host=settings.cloud.host,
            port=settings.cloud.port,
            user=settings.cloud.user,
            password=settings.cloud.password,
            key_path=settings.cloud.key_path,
            remote_path=settings.cloud.remote_path,
            method=settings.cloud.upload_method,
            http_upload_url=settings.cloud.http_upload_url,
            http_upload_token=settings.cloud.http_upload_token,
        )

        self.local_publisher = LocalPublisher(output_dir=settings.report.output_dir)

        # 去重阈值支持通过环境变量覆盖，便于线上快速调参
        self.INTRADAY_TITLE_SIM_THRESHOLD_STRONG = self._clamp_float(
            self._safe_float(
                os.getenv("INTRADAY_TITLE_SIM_THRESHOLD_STRONG"),
                self.INTRADAY_TITLE_SIM_THRESHOLD_STRONG,
            ),
            0.0,
            1.0,
        )
        self.INTRADAY_TITLE_SIM_THRESHOLD_NUMERIC = self._clamp_float(
            self._safe_float(
                os.getenv("INTRADAY_TITLE_SIM_THRESHOLD_NUMERIC"),
                self.INTRADAY_TITLE_SIM_THRESHOLD_NUMERIC,
            ),
            0.0,
            1.0,
        )
        self.INTRADAY_COMMON_SUBSTR_MIN = max(
            1,
            self._safe_int(
                os.getenv("INTRADAY_COMMON_SUBSTR_MIN"),
                self.INTRADAY_COMMON_SUBSTR_MIN,
            ),
        )
        self.FINAL_CONTENT_SIM_THRESHOLD_STRONG = self._clamp_float(
            self._safe_float(
                os.getenv("FINAL_CONTENT_SIM_THRESHOLD_STRONG"),
                self.FINAL_CONTENT_SIM_THRESHOLD_STRONG,
            ),
            0.0,
            1.0,
        )
        self.FINAL_CONTENT_SIM_THRESHOLD_NUMERIC = self._clamp_float(
            self._safe_float(
                os.getenv("FINAL_CONTENT_SIM_THRESHOLD_NUMERIC"),
                self.FINAL_CONTENT_SIM_THRESHOLD_NUMERIC,
            ),
            0.0,
            1.0,
        )
        self.FINAL_CONTENT_OVERLAP_THRESHOLD_NUMERIC = self._clamp_float(
            self._safe_float(
                os.getenv("FINAL_CONTENT_OVERLAP_THRESHOLD_NUMERIC"),
                self.FINAL_CONTENT_OVERLAP_THRESHOLD_NUMERIC,
            ),
            0.0,
            1.0,
        )
        self.FINAL_CONTENT_COMMON_SUBSTR_MIN = max(
            1,
            self._safe_int(
                os.getenv("FINAL_CONTENT_COMMON_SUBSTR_MIN"),
                self.FINAL_CONTENT_COMMON_SUBSTR_MIN,
            ),
        )
        self.FINAL_CONTENT_TITLE_SIM_GUARD = self._clamp_float(
            self._safe_float(
                os.getenv("FINAL_CONTENT_TITLE_SIM_GUARD"),
                self.FINAL_CONTENT_TITLE_SIM_GUARD,
            ),
            0.0,
            1.0,
        )

        if settings.rss.proxy_url:
            logger.info(f"✅ 代理已配置: {settings.rss.proxy_url}")
        else:
            logger.info("ℹ️ 未配置代理，使用直连")

        logger.info(
            "🧩 去重阈值: intraday_strong=%.2f intraday_numeric=%.2f intraday_lcs=%d "
            "final_strong=%.2f final_numeric=%.2f final_overlap=%.2f final_lcs=%d final_title_guard=%.2f",
            self.INTRADAY_TITLE_SIM_THRESHOLD_STRONG,
            self.INTRADAY_TITLE_SIM_THRESHOLD_NUMERIC,
            self.INTRADAY_COMMON_SUBSTR_MIN,
            self.FINAL_CONTENT_SIM_THRESHOLD_STRONG,
            self.FINAL_CONTENT_SIM_THRESHOLD_NUMERIC,
            self.FINAL_CONTENT_OVERLAP_THRESHOLD_NUMERIC,
            self.FINAL_CONTENT_COMMON_SUBSTR_MIN,
            self.FINAL_CONTENT_TITLE_SIM_GUARD,
        )

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp_float(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    def _build_rss_insights(self, ranked_items: list[dict]) -> dict[str, Any]:
        source_counts: Counter[str] = Counter()
        source_score_sums: defaultdict[str, float] = defaultdict(float)

        for item in ranked_items:
            source = item.get("source", "unknown")
            source_counts[source] += 1
            source_score_sums[source] += self._safe_float(item.get("score", 0))

        source_weights = getattr(self.ranker, "source_weights", {})
        top_common = []
        for source, count in source_counts.most_common(10):
            weight = int(source_weights.get(source, 60))
            avg_rank_score = round(source_score_sums[source] / count, 2) if count else 0.0
            top_common.append(
                {
                    "source": source,
                    "count": count,
                    "weight": weight,
                    "avg_rank_score": avg_rank_score,
                }
            )

        high_weight_active = [x for x in top_common if x["weight"] >= 85]

        return {
            "source_counts": dict(source_counts),
            "top_common_sources": top_common,
            "high_weight_active_sources": high_weight_active,
        }

    @staticmethod
    def _load_history_summaries(pipeline_dir: Path, max_runs: int = 30) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        files = sorted(pipeline_dir.glob("*_run_summary.json"))[-max_runs:]
        for file in files:
            try:
                with file.open("r", encoding="utf-8") as f:
                    summaries.append(json.load(f))
            except Exception:
                continue
        return summaries

    def _build_source_cleanup_recommendations(self, history_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        total_runs = len(history_summaries)
        if total_runs < 7:
            return []

        source_presence: Counter[str] = Counter()
        source_total_count: Counter[str] = Counter()
        for summary in history_summaries:
            rss = summary.get("observability_report", {}).get("rss_insights", {})
            counts = rss.get("source_counts", {})
            if not isinstance(counts, dict):
                continue
            for source, count in counts.items():
                c = int(count or 0)
                if c > 0:
                    source_presence[source] += 1
                    source_total_count[source] += c

        source_weights = getattr(self.ranker, "source_weights", {})
        suggestions = []
        for source in self.enabled_source_names:
            weight = int(source_weights.get(source, 60))
            presence = int(source_presence.get(source, 0))
            total_items = int(source_total_count.get(source, 0))
            presence_ratio = (presence / total_runs) if total_runs else 0.0

            # 长期低价值候选: 低权重 + 低出现率 + 低产出
            if weight <= 65 and presence_ratio <= 0.2 and total_items <= 3:
                suggestions.append(
                    {
                        "source": source,
                        "weight": weight,
                        "present_runs": presence,
                        "total_runs": total_runs,
                        "total_items": total_items,
                        "suggestion": "consider_disable_or_remove",
                    }
                )

        return sorted(
            suggestions,
            key=lambda x: (x["weight"], x["present_runs"], x["total_items"], x["source"]),
        )[:10]

    @staticmethod
    def _build_pipeline_history_stats(history_summaries: list[dict[str, Any]]) -> dict[str, Any]:
        if not history_summaries:
            return {
                "sample_runs": 0,
                "avg_total_duration_ms": 0,
                "stage_avg_duration_ms": {},
                "top_error_codes": [],
            }

        total_durations = []
        stage_duration: defaultdict[str, list[int]] = defaultdict(list)
        error_codes: Counter[str] = Counter()

        for summary in history_summaries:
            total_durations.append(int(summary.get("total_duration_ms", 0) or 0))
            stages = summary.get("stages", {})
            if not isinstance(stages, dict):
                continue
            for stage_name, detail in stages.items():
                duration = int(detail.get("duration_ms", 0) or 0)
                stage_duration[stage_name].append(duration)
                error_code = detail.get("error_code", "")
                if error_code:
                    error_codes[error_code] += 1

        stage_avg = {
            stage: int(sum(values) / len(values)) if values else 0
            for stage, values in stage_duration.items()
        }

        return {
            "sample_runs": len(history_summaries),
            "avg_total_duration_ms": int(sum(total_durations) / len(total_durations)) if total_durations else 0,
            "stage_avg_duration_ms": stage_avg,
            "top_error_codes": [
                {"error_code": code, "count": count}
                for code, count in error_codes.most_common(5)
            ],
        }

    def _build_observability_report(self, pipeline_dir: Path, current_summary: dict[str, Any]) -> dict[str, Any]:
        # 历史统计基于当前写盘前已经存在的 run summary（即“长期”视角）
        history = self._load_history_summaries(pipeline_dir)
        rss_insights = self._build_rss_insights(self._last_ranked_items)
        pipeline_stats = self._build_pipeline_history_stats(history + [current_summary])
        cleanup_suggestions = self._build_source_cleanup_recommendations(history)
        return {
            "rss_insights": rss_insights,
            "pipeline_stats": pipeline_stats,
            "cleanup_recommendation_basis_runs": len(history),
            "cleanup_suggestions": cleanup_suggestions,
        }

    def _run_with_retry(
        self,
        stage_name: str,
        fn: Callable[[], Any],
        retryable: bool = True,
    ) -> tuple[Any, int]:
        attempts = self.settings.pipeline.retry_count + 1 if retryable else 1
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                return fn(), attempt
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ 阶段 {stage_name} 失败 (attempt {attempt}/{attempts}): {str(e)[:120]}")
                if attempt < attempts:
                    time.sleep(self.settings.pipeline.retry_delay_seconds)

        raise RuntimeError(f"阶段 {stage_name} 最终失败: {last_error}") from last_error

    @staticmethod
    def _load_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _save_json(path: Path, payload: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _load_or_run_stage(
        self,
        stage_name: str,
        cache_path: Path,
        runner: Callable[[], Any],
        retryable: bool = True,
    ) -> Any:
        if self.metrics:
            self.metrics.start_stage(stage_name)
        set_stage(stage_name)
        try:
            if self.settings.pipeline.resume_from_cache and cache_path.exists():
                logger.info(f"♻️ 阶段 {stage_name}: 使用缓存 {cache_path}")
                result = self._load_json(cache_path)
                if self.metrics:
                    self.metrics.end_stage_success(stage_name, attempts=0)
                return result

            result, attempts = self._run_with_retry(stage_name, runner, retryable=retryable)
            self._save_json(cache_path, result)
            logger.info(f"💾 阶段 {stage_name}: 已缓存到 {cache_path}")
            if self.metrics:
                self.metrics.end_stage_success(stage_name, attempts=attempts)
            return result
        except Exception as e:
            severity, error_code = classify_error(stage_name, e)
            if self.metrics:
                attempts = self.settings.pipeline.retry_count + 1 if retryable else 1
                self.metrics.end_stage_failure(
                    stage_name,
                    attempts=attempts,
                    error_code=error_code,
                    severity=severity,
                    message=str(e),
                )
            logger.error(
                f"❌ 阶段 {stage_name} 失败: {str(e)[:160]}",
                extra={"error_code": error_code, "severity": severity},
            )
            raise
        finally:
            clear_stage()

    def _update_pipeline_state(self, state_path: Path, stage: str, status: str, detail: str = ""):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state = {}
        if state_path.exists():
            try:
                state = self._load_json(state_path)
            except Exception:
                state = {}

        state[stage] = {"status": status, "time": now, "detail": detail}
        self._save_json(state_path, state)

    def _copy_report_to_local_target(self, local_file: str, date_str: str) -> str:
        target_dir = (self.settings.report.local_target_dir or "").strip()
        if not target_dir:
            return ""

        dst_dir = Path(target_dir)
        dst_dir.mkdir(parents=True, exist_ok=True)

        src_json = Path(local_file)
        dst_json = dst_dir / f"{date_str}.json"
        shutil.copy2(src_json, dst_json)
        return str(dst_json)

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text.strip().lower())

    @classmethod
    def _extract_fact_signature(cls, title: str, summary: str) -> tuple[str, set[str], set[str]]:
        text = cls._normalize_text(f"{title} {summary}")
        if not text:
            return "", set(), set()

        tokens: set[str] = set()
        for word in re.findall(r"[a-z]{3,}", text):
            tokens.add(word)

        for chunk in re.findall(r"[\u4e00-\u9fff]{2,8}", text):
            if len(chunk) == 2:
                tokens.add(chunk)
                continue
            for i in range(len(chunk) - 1):
                tokens.add(chunk[i : i + 2])

        numbers = set(re.findall(r"\d+(?:\.\d+)?(?:亿|万|%|美元|元|年)?", text))
        return text, tokens, numbers

    @staticmethod
    def _jaccard_similarity(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    def _load_recent_report_articles(self, date_str: str, days: int) -> list[dict[str, Any]]:
        output_dir = Path(self.settings.report.output_dir)
        today = datetime.date.fromisoformat(date_str)
        history: list[dict[str, Any]] = []

        for offset in range(1, days + 1):
            target_day = today - datetime.timedelta(days=offset)
            report_file = output_dir / f"{target_day.isoformat()}.json"
            if not report_file.exists():
                continue
            try:
                payload = self._load_json(report_file)
            except Exception as e:
                logger.warning(f"⚠️ 历史日报读取失败: {report_file} ({str(e)[:100]})")
                continue

            for article in payload.get("articles", []):
                title = article.get("title", "")
                summary = article.get("summary", "")
                normalized, tokens, numbers = self._extract_fact_signature(title, summary)
                if not normalized:
                    continue
                history.append(
                    {
                        "title": title,
                        "summary": summary,
                        "source": article.get("source_name", article.get("source", "unknown")),
                        "report_date": target_day.isoformat(),
                        "normalized": normalized,
                        "tokens": tokens,
                        "numbers": numbers,
                    }
                )

        return history

    def _is_history_duplicate(
        self,
        candidate: dict[str, Any],
        history_item: dict[str, Any],
    ) -> tuple[bool, float, float]:
        cand_title = self._normalize_text(candidate.get("title", ""))
        cand_text, cand_tokens, cand_numbers = self._extract_fact_signature(
            candidate.get("title", ""),
            candidate.get("summary", ""),
        )
        hist_title = self._normalize_text(history_item.get("title", ""))
        hist_text = history_item.get("normalized", "")
        hist_tokens = history_item.get("tokens", set())
        hist_numbers = history_item.get("numbers", set())

        if not cand_text or not hist_text:
            return False, 0.0, 0.0

        title_sim = SequenceMatcher(None, cand_title, hist_title).ratio()
        token_sim = self._jaccard_similarity(cand_tokens, hist_tokens)
        has_number_overlap = bool(cand_numbers and hist_numbers and (cand_numbers & hist_numbers))

        duplicate = (
            title_sim >= self.HISTORY_TITLE_SIM_THRESHOLD
            or (title_sim >= self.HISTORY_EVENT_SIM_THRESHOLD and token_sim >= 0.20)
            or (token_sim >= 0.42 and has_number_overlap)
        )
        return duplicate, title_sim, token_sim

    def _filter_history_duplicates(
        self,
        ranked_items: list[dict[str, Any]],
        date_str: str,
        history_days: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        history = self._load_recent_report_articles(date_str, days=history_days)
        if not history:
            return ranked_items, []

        kept: list[dict[str, Any]] = []
        dropped: list[dict[str, Any]] = []

        for item in ranked_items:
            matched = None
            best_title_sim = 0.0
            best_token_sim = 0.0
            for history_item in history:
                is_dup, title_sim, token_sim = self._is_history_duplicate(item, history_item)
                if is_dup:
                    matched = history_item
                    best_title_sim = title_sim
                    best_token_sim = token_sim
                    break
            if matched:
                dropped.append(
                    {
                        "title": item.get("title", ""),
                        "source": item.get("source", "unknown"),
                        "matched_date": matched.get("report_date", ""),
                        "matched_source": matched.get("source", "unknown"),
                        "matched_title": matched.get("title", ""),
                        "title_sim": round(best_title_sim, 3),
                        "token_sim": round(best_token_sim, 3),
                    }
                )
            else:
                kept.append(item)

        if dropped:
            logger.info(f"🧹 历史去重: 过滤 {len(dropped)} 条（对比近 {history_days} 天日报）")
            for row in dropped[:3]:
                logger.info(
                    "  - 过滤: [{source}] {title} -> 命中 {matched_date} [{matched_source}] {matched_title}".format(
                        **row
                    )
                )

        return kept, dropped

    @staticmethod
    def _apply_source_cap(
        ranked_items: list[dict[str, Any]],
        cap: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        kept: list[dict[str, Any]] = []
        dropped: list[dict[str, Any]] = []
        source_count: Counter[str] = Counter()

        for item in ranked_items:
            source = item.get("source", "unknown")
            if source_count[source] >= cap:
                dropped.append(item)
                continue
            source_count[source] += 1
            kept.append(item)

        return kept, dropped

    @staticmethod
    def _normalize_title_for_char_sim(title: str) -> str:
        text = (title or "").lower().strip()
        text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
        return text

    @staticmethod
    def _extract_numbers_from_title(title: str) -> set[str]:
        return set(re.findall(r"\d+(?:\.\d+)?", title or ""))

    def _is_intra_day_similar_event(self, left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, float]:
        left_title = self._normalize_title_for_char_sim(left.get("title", ""))
        right_title = self._normalize_title_for_char_sim(right.get("title", ""))
        if not left_title or not right_title:
            return False, 0.0

        title_sim = SequenceMatcher(None, left_title, right_title).ratio()
        left_nums = self._extract_numbers_from_title(left_title)
        right_nums = self._extract_numbers_from_title(right_title)
        has_number_overlap = bool(left_nums and right_nums and (left_nums & right_nums))
        no_numbers = not left_nums and not right_nums
        common_len = SequenceMatcher(None, left_title, right_title).find_longest_match(
            0, len(left_title), 0, len(right_title)
        ).size

        strong_match = title_sim >= self.INTRADAY_TITLE_SIM_THRESHOLD_STRONG and (has_number_overlap or no_numbers)
        numeric_match = (
            title_sim >= self.INTRADAY_TITLE_SIM_THRESHOLD_NUMERIC
            and has_number_overlap
            and common_len >= self.INTRADAY_COMMON_SUBSTR_MIN
        )
        return (strong_match or numeric_match), title_sim

    def _filter_intra_day_similar_events(
        self,
        ranked_items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        kept: list[dict[str, Any]] = []
        dropped: list[dict[str, Any]] = []

        for item in ranked_items:
            matched = None
            best_title_sim = 0.0
            for kept_item in kept:
                is_dup, title_sim = self._is_intra_day_similar_event(item, kept_item)
                if is_dup:
                    matched = kept_item
                    best_title_sim = title_sim
                    break

            if matched:
                dropped.append(
                    {
                        "title": item.get("title", ""),
                        "source": item.get("source", "unknown"),
                        "matched_source": matched.get("source", "unknown"),
                        "matched_title": matched.get("title", ""),
                        "title_sim": round(best_title_sim, 3),
                    }
                )
            else:
                kept.append(item)

        if dropped:
            logger.info(f"🧹 同日去重: 过滤 {len(dropped)} 条（字符相似度规则）")
            for row in dropped[:3]:
                logger.info(
                    "  - 过滤: [{source}] {title} -> 命中 [{matched_source}] {matched_title} (title_sim={title_sim})".format(
                        **row
                    )
                )

        return kept, dropped

    @staticmethod
    def _char_overlap_ratio(left: str, right: str) -> float:
        if not left or not right:
            return 0.0
        lc = CharCounter(left)
        rc = CharCounter(right)
        inter = sum((lc & rc).values())
        base = min(len(left), len(right))
        if base == 0:
            return 0.0
        return inter / base

    def _filter_final_content_duplicates(
        self,
        analyzed_items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        kept: list[dict[str, Any]] = []
        dropped: list[dict[str, Any]] = []

        def content_text(item: dict[str, Any]) -> str:
            title = item.get("title", "")
            summary = item.get("summary", "")
            return self._normalize_title_for_char_sim(f"{title} {summary}")

        def title_text(item: dict[str, Any]) -> str:
            return self._normalize_title_for_char_sim(item.get("title", ""))

        for item in analyzed_items:
            curr_text = content_text(item)
            curr_title = title_text(item)
            curr_nums = self._extract_numbers_from_title(curr_text)
            matched = None
            best_sim = 0.0
            best_title_sim = 0.0

            for kept_item in kept:
                kept_text = content_text(kept_item)
                kept_title = title_text(kept_item)
                sim = SequenceMatcher(None, curr_text, kept_text).ratio()
                overlap = self._char_overlap_ratio(curr_text, kept_text)
                kept_nums = self._extract_numbers_from_title(kept_text)
                has_number_overlap = bool(curr_nums and kept_nums and (curr_nums & kept_nums))
                common_len = SequenceMatcher(None, curr_text, kept_text).find_longest_match(
                    0, len(curr_text), 0, len(kept_text)
                ).size
                title_sim = SequenceMatcher(None, curr_title, kept_title).ratio() if curr_title and kept_title else 0.0
                title_common_len = SequenceMatcher(None, curr_title, kept_title).find_longest_match(
                    0, len(curr_title), 0, len(kept_title)
                ).size if curr_title and kept_title else 0

                # 标题层面的“同事件”兜底：同数字 + 中高标题相似度，避免摘要改写导致漏去重。
                title_numeric_match = (
                    has_number_overlap
                    and title_common_len >= self.FINAL_CONTENT_COMMON_SUBSTR_MIN
                    and title_sim >= max(self.FINAL_CONTENT_TITLE_SIM_GUARD, 0.45)
                )

                is_dup = (
                    sim >= self.FINAL_CONTENT_SIM_THRESHOLD_STRONG
                    or overlap >= self.FINAL_CONTENT_SIM_THRESHOLD_STRONG
                    or title_numeric_match
                    or (
                        has_number_overlap
                        and common_len >= self.FINAL_CONTENT_COMMON_SUBSTR_MIN
                        and (
                            title_sim >= self.FINAL_CONTENT_TITLE_SIM_GUARD
                            or title_common_len >= max(4, self.FINAL_CONTENT_COMMON_SUBSTR_MIN - 1)
                        )
                        and (
                            sim >= self.FINAL_CONTENT_SIM_THRESHOLD_NUMERIC
                            or overlap >= self.FINAL_CONTENT_OVERLAP_THRESHOLD_NUMERIC
                        )
                    )
                )
                if is_dup:
                    matched = kept_item
                    best_sim = max(sim, overlap)
                    best_title_sim = title_sim
                    break

            if matched:
                dropped.append(
                    {
                        "title": item.get("title", ""),
                        "source": item.get("source_name", item.get("source", "unknown")),
                        "matched_source": matched.get("source_name", matched.get("source", "unknown")),
                        "matched_title": matched.get("title", ""),
                        "sim": round(best_sim, 3),
                        "title_sim": round(best_title_sim, 3),
                    }
                )
            else:
                kept.append(item)

        if dropped:
            logger.info(f"🧹 结果去重: 过滤 {len(dropped)} 条（按标题+摘要字符相似度）")
            for row in dropped[:5]:
                logger.info(
                    "  - 过滤: [{source}] {title} -> 命中 [{matched_source}] {matched_title} "
                    "(sim={sim}, title_sim={title_sim})".format(
                        **row
                    )
                )

        return kept, dropped

    def _post_process_ranked_items(
        self,
        ranked_candidates: list[dict[str, Any]],
        date_str: str,
    ) -> tuple[list[dict[str, Any]], int, int]:
        history_filtered, history_dropped = self._filter_history_duplicates(
            ranked_candidates,
            date_str=date_str,
            history_days=self.HISTORY_DEDUP_DAYS,
        )
        intraday_filtered, intraday_dropped = self._filter_intra_day_similar_events(history_filtered)
        source_capped, source_dropped = self._apply_source_cap(
            intraday_filtered,
            cap=self.DAILY_SOURCE_CAP,
        )

        final_items = source_capped[: self.settings.report.max_articles_in_report]
        logger.info(
            "📉 排序后过滤: 候选=%d, 历史去重移除=%d, 同日去重移除=%d, 来源上限移除=%d, 最终=%d",
            len(ranked_candidates),
            len(history_dropped),
            len(intraday_dropped),
            len(source_dropped),
            len(final_items),
        )
        return final_items, len(history_dropped), len(source_dropped) + len(intraday_dropped)

    def _analyze_single_item(self, item: dict, index: int, total: int) -> tuple[int, dict | None, dict | None]:
        """分析单篇文章，用于并发执行"""
        logger.info(f"[{index}/{total}] 处理: {item['title'][:30]}... (得分: {item['score']:.1f})")

        article_for_ai = {
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "source": item.get("source", "Unknown"),
            "link": item.get("link", ""),
        }

        try:
            ai_result = self.analyzer.analyze_single(article_for_ai)
            if ai_result:
                logger.info(f"✅ [{index}] 分析成功: {ai_result.get('title', 'N/A')[:40]}")
                return index, ai_result, None
            else:
                logger.warning(f"⚠️ [{index}] 分析失败，跳过此文章")
                return index, None, item
        except Exception as e:
            logger.warning(f"⚠️ [{index}] 分析异常: {str(e)[:50]}")
            return index, None, item

    def _analyze_ranked_items(self, ranked_items: list[dict]) -> list[dict]:
        # 并发数配置，默认5个线程
        max_workers = int(os.getenv("AI_ANALYZER_CONCURRENCY", "5"))

        articles_data = []
        successful_count = 0
        failed_count = 0
        failed_items = []

        logger.info(f"🚀 开始并发 AI 分析 (并发数: {max_workers}, 文章数: {len(ranked_items)})...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(self._analyze_single_item, item, i, len(ranked_items)): i
                for i, item in enumerate(ranked_items, 1)
            }

            # 收集结果
            for future in as_completed(futures):
                try:
                    index, result, failed_item = future.result()
                    if result:
                        articles_data.append(result)
                        successful_count += 1
                    elif failed_item:
                        failed_count += 1
                        failed_items.append(failed_item)
                except Exception as e:
                    logger.error(f"❌ 并发任务异常: {e}")

        # 对失败的重试（串行，最多重试一次）
        if failed_items and successful_count > 0:
            logger.info(f"🔄 重试失败的 {len(failed_items)} 篇文章...")
            for item in failed_items:
                try:
                    article_for_ai = {
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "source": item.get("source", "Unknown"),
                        "link": item.get("link", ""),
                    }
                    ai_result = self.analyzer.analyze_single(article_for_ai)
                    if ai_result:
                        articles_data.append(ai_result)
                        successful_count += 1
                        failed_count -= 1
                        time.sleep(1)
                except Exception:
                    pass

        logger.info(f"\n📊 AI 分析完成: 成功 {successful_count} 条，失败 {failed_count} 条")
        if successful_count == 0:
            raise RuntimeError("所有文章分析均失败")

        articles_data.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
        logger.info("📊 已按重要性评分从高到低排序")
        return articles_data

    def run(self):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        run_id = get_run_id()
        if run_id == "-":
            run_id = create_run_id()
            set_run_id(run_id)

        self.metrics = RunMetrics(run_id=run_id)
        set_stage("run")

        try:
            pipeline_dir = Path(self.settings.pipeline.cache_dir)
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            pipeline_state = pipeline_dir / f"{date_str}_state.json"
            collected_cache = pipeline_dir / f"{date_str}_collected.json"
            deduped_cache = pipeline_dir / f"{date_str}_deduped.json"
            ranked_cache = pipeline_dir / f"{date_str}_ranked.json"
            analyzed_cache = pipeline_dir / f"{date_str}_analyzed.json"

            logger.info("🚀 启动采集 (过去24小时) ...")
            items = self._load_or_run_stage(
                "collect",
                collected_cache,
                lambda: self.collector.collect_all(),
                retryable=True,
            )
            self._update_pipeline_state(pipeline_state, "collect", "success", f"items={len(items)}")
            self.metrics.set_counter("collected_items", len(items))

            if not items:
                logger.warning("❌ 过去24小时内没有新资讯，任务结束。")
                self._update_pipeline_state(pipeline_state, "collect", "empty")
                return

            logger.info(f"\n🔄 开始去重 (共 {len(items)} 条文章)...")
            deduped_items = self._load_or_run_stage(
                "deduplicate",
                deduped_cache,
                lambda: self.deduplicator.deduplicate(items, source_name_key="source"),
                retryable=False,
            )
            self._update_pipeline_state(pipeline_state, "deduplicate", "success", f"items={len(deduped_items)}")
            self.metrics.set_counter("deduplicated_items", len(deduped_items))

            logger.info(f"\n📊 开始智能排序 (共 {len(deduped_items)} 条文章)...")
            candidate_top_n = max(self.settings.report.max_articles_in_report * 4, self.settings.report.max_articles_in_report)
            ranked_candidates = self._load_or_run_stage(
                "rank",
                ranked_cache,
                lambda: self.ranker.rank_articles_with_chinese_quota(
                    deduped_items,
                    top_n=candidate_top_n,
                    chinese_quota=10,
                ),
                retryable=False,
            )
            ranked_items, history_dropped_count, source_cap_dropped_count = self._post_process_ranked_items(
                ranked_candidates,
                date_str=date_str,
            )
            self._save_json(ranked_cache, ranked_items)
            self.metrics.set_counter("history_deduplicated_items", history_dropped_count)
            self.metrics.set_counter("source_capped_items", source_cap_dropped_count)
            self._last_ranked_items = ranked_items
            self._update_pipeline_state(
                pipeline_state,
                "rank",
                "success",
                f"items={len(ranked_items)},history_dropped={history_dropped_count},source_cap_dropped={source_cap_dropped_count}",
            )
            self.metrics.set_counter("ranked_items", len(ranked_items))
            logger.info(f"\n{self.ranker.get_ranking_summary(ranked_items)}")

            if not ranked_items:
                logger.warning("❌ 排序后无可用文章（可能被历史去重全部过滤），任务结束。")
                return

            logger.info(f"\n🤖 开始 AI 分析 (Top {len(ranked_items)} 条)...")
            articles_data = self._load_or_run_stage(
                "analyze",
                analyzed_cache,
                lambda: self._analyze_ranked_items(ranked_items),
                retryable=True,
            )
            self._update_pipeline_state(pipeline_state, "analyze", "success", f"items={len(articles_data)}")
            self.metrics.set_counter("analyzed_items", len(articles_data))

            # 最终按内容做一次字符相似度去重，避免同一事件在不同来源重复出现在成品日报
            articles_data, final_dropped = self._filter_final_content_duplicates(articles_data)
            self.metrics.set_counter("final_content_dedup_dropped", len(final_dropped))
            self.metrics.set_counter("analyzed_items_after_final_dedup", len(articles_data))

            logger.info("\n💾 正在保存到本地 JSON 文件...")
            if self.metrics:
                self.metrics.start_stage("local_publish")
            set_stage("local_publish")
            try:
                local_json_path = Path(self.settings.report.output_dir) / f"{date_str}.json"
                if self.settings.pipeline.resume_from_cache and local_json_path.exists():
                    local_file = str(local_json_path)
                    logger.info(f"♻️ 本地 JSON 已存在，跳过重写: {local_file}")
                    if self.metrics:
                        self.metrics.end_stage_success("local_publish", attempts=0)
                else:
                    local_file = self.local_publisher.save_json(articles_data, date_str)
                    if self.metrics:
                        self.metrics.end_stage_success("local_publish", attempts=1)
            except Exception as e:
                severity, error_code = classify_error("local_publish", e)
                if self.metrics:
                    self.metrics.end_stage_failure(
                        "local_publish",
                        attempts=1,
                        error_code=error_code,
                        severity=severity,
                        message=str(e),
                    )
                logger.error(
                    f"❌ 本地保存异常: {str(e)[:120]}",
                    extra={"error_code": error_code, "severity": severity},
                )
                raise
            finally:
                clear_stage()

            if not local_file:
                self._update_pipeline_state(pipeline_state, "local_publish", "failed")
                logger.error("❌ 本地保存失败，任务结束")
                return
            self._update_pipeline_state(pipeline_state, "local_publish", "success", local_file)

            local_target = (self.settings.report.local_target_dir or "").strip()
            if local_target:
                if self.metrics:
                    self.metrics.start_stage("local_copy")
                set_stage("local_copy")
                try:
                    copied_to = self._copy_report_to_local_target(local_file, date_str)
                    self._update_pipeline_state(pipeline_state, "local_copy", "success", copied_to)
                    if self.metrics:
                        self.metrics.end_stage_success("local_copy", attempts=1)
                    logger.info(f"✅ 已复制报告到目标目录: {copied_to}")
                except Exception as e:
                    severity, error_code = classify_error("local_copy", e)
                    self._update_pipeline_state(pipeline_state, "local_copy", "failed", str(e)[:200])
                    if self.metrics:
                        self.metrics.end_stage_failure(
                            "local_copy",
                            attempts=1,
                            error_code=error_code,
                            severity=severity,
                            message=str(e),
                        )
                    logger.error(
                        f"❌ 复制报告到目标目录失败: {str(e)[:120]}",
                        extra={"error_code": error_code, "severity": severity},
                    )
                    raise
                finally:
                    clear_stage()
            else:
                self._update_pipeline_state(pipeline_state, "local_copy", "skipped", "LOCAL_TARGET_DIR empty")
                if self.metrics:
                    self.metrics.start_stage("local_copy")
                    self.metrics.end_stage_success("local_copy", attempts=0)

            remote_filename = f"{date_str}.json"
            upload_success = False

            if self.settings.cloud.enabled:
                logger.info("\n☁️ 正在上传到云服务器 JSON 目录...")
                if self.metrics:
                    self.metrics.start_stage("upload")
                set_stage("upload")

                def _upload_once() -> bool:
                    if self.cloud_publisher.upload(local_file, remote_filename, self.settings.cloud.json_remote_path):
                        return True
                    raise RuntimeError("upload() returned False")

                try:
                    _, attempts = self._run_with_retry("upload", _upload_once, retryable=True)
                    upload_success = True
                    if self.metrics:
                        self.metrics.end_stage_success("upload", attempts=attempts)
                    self._update_pipeline_state(pipeline_state, "upload", "success", remote_filename)
                    logger.info(
                        f"✅ JSON 报告已成功上传到云服务器: "
                        f"{self.settings.cloud.host}:{self.settings.cloud.json_remote_path}/{remote_filename}"
                    )
                except Exception as e:
                    severity, error_code = classify_error("upload", e)
                    if self.metrics:
                        self.metrics.end_stage_failure(
                            "upload",
                            attempts=self.settings.pipeline.retry_count + 1,
                            error_code=error_code,
                            severity=severity,
                            message=str(e),
                        )
                    self._update_pipeline_state(pipeline_state, "upload", "failed", str(e)[:200])
                    logger.error(
                        f"❌ 云服务器上传失败: {str(e)[:120]}",
                        extra={"error_code": error_code, "severity": severity},
                    )
                finally:
                    clear_stage()
            else:
                if self.metrics:
                    self.metrics.start_stage("upload")
                    self.metrics.end_stage_success("upload", attempts=0)
                self._update_pipeline_state(pipeline_state, "upload", "skipped", "cloud.enabled=false")
                logger.info("ℹ️ 已跳过上传阶段（cloud.enabled=false）")

            can_send_email = self.settings.email.enabled and (
                upload_success or self.settings.email.when_upload_fail or not self.settings.cloud.enabled
            )
            if can_send_email:
                logger.info("\n📧 开始发送邮件...")
                import subprocess
                if self.metrics:
                    self.metrics.start_stage("email")
                set_stage("email")

                email_sender_script = Path(__file__).parent / "daily_email_sender.py"

                def _send_once() -> bool:
                    result = subprocess.run(
                        [sys.executable, str(email_sender_script)],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    if result.returncode == 0:
                        return True
                    raise RuntimeError(result.stdout or result.stderr or "unknown email error")

                try:
                    _, attempts = self._run_with_retry("email", _send_once, retryable=True)
                    if self.metrics:
                        self.metrics.end_stage_success("email", attempts=attempts)
                    self._update_pipeline_state(pipeline_state, "email", "success")
                    logger.info("✅ 邮件发送成功")
                except Exception as e:
                    severity, error_code = classify_error("email", e)
                    if self.metrics:
                        self.metrics.end_stage_failure(
                            "email",
                            attempts=self.settings.pipeline.retry_count + 1,
                            error_code=error_code,
                            severity=severity,
                            message=str(e),
                        )
                    self._update_pipeline_state(pipeline_state, "email", "failed", str(e)[:200])
                    logger.warning(
                        f"⚠️ 邮件发送失败: {str(e)[:120]}",
                        extra={"error_code": error_code, "severity": severity},
                    )
                finally:
                    clear_stage()
            else:
                reason = "email.disabled" if not self.settings.email.enabled else "upload_failed_and_email_when_upload_fail=false"
                if self.metrics:
                    self.metrics.start_stage("email")
                    self.metrics.end_stage_success("email", attempts=0)
                self._update_pipeline_state(pipeline_state, "email", "skipped", reason)
                logger.info(f"ℹ️ 已跳过邮件发送阶段（{reason}）")

            logger.info(self.analyzer.get_cost_report())

        except Exception as e:
            severity, error_code = classify_error("run", e)
            logger.error(
                f"❌ 运行出错: {e}",
                extra={"error_code": error_code, "severity": severity},
            )
            raise
        finally:
            if self.metrics:
                summary_path = Path(self.settings.pipeline.cache_dir) / f"{date_str}_run_summary.json"
                summary = self.metrics.summary()
                summary["observability_report"] = self._build_observability_report(
                    Path(self.settings.pipeline.cache_dir),
                    summary,
                )
                self._save_json(summary_path, summary)
                logger.info(f"📈 运行统计已写入: {summary_path}")
            clear_stage()


if __name__ == "__main__":
    try:
        settings = load_settings()
        validate_settings(settings)
        set_settings(settings)
        set_run_id(create_run_id())

        logger.setLevel(settings.logging.level.upper())

        lock = FileLock(settings.pipeline.lock_file)
        try:
            lock.acquire()
        except RuntimeError:
            logger.warning(
                f"⚠️ 检测到已有运行实例，跳过本次执行: {settings.pipeline.lock_file}",
                extra={"error_code": "E_ALREADY_RUNNING", "severity": "LOW"},
            )
            sys.exit(0)

        try:
            if settings.rss.enable_proxy_ip_update:
                logger.info("=" * 60)
                logger.info("🔍 检查并更新 RSSHub 代理 IP...")
                update_rsshub_proxy_ip()
                logger.info("=" * 60 + "\n")
            else:
                logger.info("ℹ️ 已跳过代理 IP 自动更新（ENABLE_PROXY_IP_UPDATE=false）")

            bot = AI_Daily_Report(settings)
            bot.run()
        finally:
            lock.release()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 程序异常退出: {e}")
        sys.exit(1)
