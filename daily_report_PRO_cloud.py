"""
AI 日报生成器 - 云服务器版本

主要功能：
1. 从多个 RSS 源采集 AI 行业新闻
2. 使用智能排序系统筛选重要文章
3. 对文章标题进行去重
4. 通过 DeepSeek AI 分析并生成 JSON 格式报告
5. 上传到云服务器供网站集成使用
"""

import json
import sys
import datetime
import time
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

from core.utils import setup_logger, get_required_env, get_optional_env, get_int_env, CostTracker
from core.utils.constants import *

from lib.rss_collector import RSSCollector
from lib.ai_analyzer import AIAnalyzer
from lib.publishers.cloud_publisher import CloudPublisher
from lib.publishers.local_publisher import LocalPublisher
from lib.article_deduplicator import ArticleDeduplicator
from article_ranker import ArticleRanker

from core.config_manager import get_config_manager


def _env_bool(name: str, default: bool) -> bool:
    raw = get_optional_env(name, str(default).lower()).strip().lower()
    return raw in {"1", "true", "yes", "on"}


# ================= ⚙️ 配置区域 (从环境变量读取) =================
load_dotenv()

DEEPSEEK_API_KEY = get_required_env("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = get_optional_env("DEEPSEEK_BASE_URL", DEFAULT_AI_BASE_URL)

PROXY_URL = get_optional_env("PROXY_URL", "")
RSSHUB_HOST = get_optional_env("RSSHUB_HOST", DEFAULT_RSSHUB_HOST)

MAX_ITEMS_PER_SOURCE = get_int_env("MAX_ITEMS_PER_SOURCE", DEFAULT_MAX_ITEMS_PER_SOURCE)
MAX_ARTICLES_IN_REPORT = get_int_env("MAX_ARTICLES_IN_REPORT", DEFAULT_MAX_ARTICLES_IN_REPORT)

OUTPUT_DIR = get_optional_env("OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
LOG_LEVEL = get_optional_env("LOG_LEVEL", DEFAULT_LOG_LEVEL)

CLOUD_SERVER_HOST = get_optional_env("CLOUD_SERVER_HOST", DEFAULT_CLOUD_SERVER_HOST)
CLOUD_SERVER_PORT = get_int_env("CLOUD_SERVER_PORT", DEFAULT_CLOUD_SERVER_PORT)
CLOUD_SERVER_USER = get_optional_env("CLOUD_SERVER_USER", DEFAULT_CLOUD_SERVER_USER)
CLOUD_SERVER_PASSWORD = get_optional_env("CLOUD_SERVER_PASSWORD", "")
CLOUD_SERVER_KEY_PATH = get_optional_env("CLOUD_SERVER_KEY_PATH", "")
CLOUD_SERVER_REMOTE_PATH = get_optional_env("CLOUD_SERVER_REMOTE_PATH", DEFAULT_CLOUD_SERVER_REMOTE_PATH)
CLOUD_SERVER_JSON_REMOTE_PATH = get_optional_env("CLOUD_SERVER_JSON_REMOTE_PATH", DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH)

UPLOAD_METHOD = get_optional_env("UPLOAD_METHOD", DEFAULT_UPLOAD_METHOD)
HTTP_UPLOAD_URL = get_optional_env("HTTP_UPLOAD_URL", "")
HTTP_UPLOAD_TOKEN = get_optional_env("HTTP_UPLOAD_TOKEN", "")

# 流水线执行配置
PIPELINE_CACHE_DIR = get_optional_env("PIPELINE_CACHE_DIR", str(Path(OUTPUT_DIR) / ".pipeline"))
RESUME_FROM_CACHE = _env_bool("RESUME_FROM_CACHE", True)
STAGE_RETRY_COUNT = get_int_env("STAGE_RETRY_COUNT", 1)  # 总尝试次数=重试+1
STAGE_RETRY_DELAY_SECONDS = get_int_env("STAGE_RETRY_DELAY_SECONDS", 3)
UPLOAD_ENABLED = _env_bool("UPLOAD_ENABLED", True)
EMAIL_ENABLED = _env_bool("EMAIL_ENABLED", True)
EMAIL_WHEN_UPLOAD_FAIL = _env_bool("EMAIL_WHEN_UPLOAD_FAIL", False)

logger = setup_logger(level=LOG_LEVEL)


# ================= 🔧 自动更新 RSSHub 代理 IP =================
def update_rsshub_proxy_ip():
    """
    自动获取 OrbStack bridge100 IP 并更新 docker-compose.yml 中的 PROXY_URI
    这样 RSSHub 容器可以正确访问宿主机的代理服务
    """
    import subprocess
    import re

    try:
        result = subprocess.run(
            ["ifconfig", "bridge100"],
            capture_output=True,
            text=True,
            timeout=5
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

        compose_file = Path(__file__).parent / "docker-compose.yml"
        if not compose_file.exists():
            logger.warning("⚠️ docker-compose.yml 不存在，跳过代理 IP 更新")
            return False

        content = compose_file.read_text()
        current_proxy_match = re.search(r"PROXY_URI=http://(\d+\.\d+\.\d+\.\d+)", content)
        if current_proxy_match and current_proxy_match.group(1) == new_ip:
            logger.info(f"✅ 代理 IP 无需更新: {new_ip}")
            return True

        new_content = re.sub(
            r"PROXY_URI=http://\d+\.\d+\.\d+\.\d+",
            f"PROXY_URI=http://{new_ip}",
            content
        )
        compose_file.write_text(new_content)
        logger.info(f"🔄 已更新 docker-compose.yml 中的代理 IP: {new_ip}")

        try:
            subprocess.run(
                ["docker-compose", "-f", str(compose_file), "restart", "rsshub"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=compose_file.parent
            )
            logger.info("✅ RSSHub 容器已重启")
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


class AI_Daily_Report:
    """AI 日报生成器主类"""

    def __init__(self):
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY.startswith("your_"):
            raise ValueError("❌ DeepSeek API Key 未配置！请在 .env 文件中设置 DEEPSEEK_API_KEY")

        config_manager = get_config_manager()
        sources = config_manager.get_enabled_sources()
        logger.info(f"📡 已加载 {len(sources)} 个启用的 RSS 源")

        self.ranker = ArticleRanker()
        self.deduplicator = ArticleDeduplicator(config_manager=config_manager)
        self.cost_tracker = CostTracker()

        self.collector = RSSCollector(
            sources=sources,
            proxy_url=PROXY_URL,
            max_items_per_source=MAX_ITEMS_PER_SOURCE,
            time_window_hours=24,
        )

        self.analyzer = AIAnalyzer(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

        self.cloud_publisher = CloudPublisher(
            host=CLOUD_SERVER_HOST,
            port=CLOUD_SERVER_PORT,
            user=CLOUD_SERVER_USER,
            password=CLOUD_SERVER_PASSWORD,
            key_path=CLOUD_SERVER_KEY_PATH,
            remote_path=CLOUD_SERVER_REMOTE_PATH,
            method=UPLOAD_METHOD,
        )

        self.local_publisher = LocalPublisher(output_dir=OUTPUT_DIR)

        if PROXY_URL:
            logger.info(f"✅ 代理已配置: {PROXY_URL}")
        else:
            logger.info("ℹ️ 未配置代理，使用直连")

    def _run_with_retry(self, stage_name: str, fn: Callable[[], Any], retryable: bool = True) -> Any:
        attempts = STAGE_RETRY_COUNT + 1 if retryable else 1
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ 阶段 {stage_name} 失败 (attempt {attempt}/{attempts}): {str(e)[:120]}")
                if attempt < attempts:
                    time.sleep(STAGE_RETRY_DELAY_SECONDS)

        raise RuntimeError(f"阶段 {stage_name} 最终失败: {last_error}")

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
        if RESUME_FROM_CACHE and cache_path.exists():
            logger.info(f"♻️ 阶段 {stage_name}: 使用缓存 {cache_path}")
            return self._load_json(cache_path)

        result = self._run_with_retry(stage_name, runner, retryable=retryable)
        self._save_json(cache_path, result)
        logger.info(f"💾 阶段 {stage_name}: 已缓存到 {cache_path}")
        return result

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

    def _analyze_ranked_items(self, ranked_items: list[dict]) -> list[dict]:
        articles_data = []
        successful_count = 0
        failed_count = 0

        for i, item in enumerate(ranked_items, 1):
            logger.info(f"[{i}/{len(ranked_items)}] 处理: {item['title'][:30]}... (得分: {item['score']:.1f})")

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
                logger.info(f"✅ [{i}] 分析成功: {ai_result.get('title', 'N/A')[:40]}")
            else:
                failed_count += 1
                logger.warning(f"⚠️ [{i}] 分析失败，跳过此文章")

            time.sleep(1)

        logger.info(f"\n📊 AI 分析完成: 成功 {successful_count} 条，失败 {failed_count} 条")
        if successful_count == 0:
            raise RuntimeError("所有文章分析均失败")

        articles_data.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
        logger.info("📊 已按重要性评分从高到低排序")
        return articles_data

    def run(self):
        try:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            pipeline_dir = Path(PIPELINE_CACHE_DIR)
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

            logger.info(f"\n📊 开始智能排序 (共 {len(deduped_items)} 条文章)...")
            ranked_items = self._load_or_run_stage(
                "rank",
                ranked_cache,
                lambda: self.ranker.rank_articles_with_chinese_quota(
                    deduped_items,
                    top_n=MAX_ARTICLES_IN_REPORT,
                    chinese_quota=10,
                ),
                retryable=False,
            )
            self._update_pipeline_state(pipeline_state, "rank", "success", f"items={len(ranked_items)}")
            logger.info(f"\n{self.ranker.get_ranking_summary(ranked_items)}")

            logger.info(f"\n🤖 开始 AI 分析 (Top {len(ranked_items)} 条)...")
            articles_data = self._load_or_run_stage(
                "analyze",
                analyzed_cache,
                lambda: self._analyze_ranked_items(ranked_items),
                retryable=True,
            )
            self._update_pipeline_state(pipeline_state, "analyze", "success", f"items={len(articles_data)}")

            logger.info("\n💾 正在保存到本地 JSON 文件...")
            local_json_path = Path(OUTPUT_DIR) / f"{date_str}.json"
            if RESUME_FROM_CACHE and local_json_path.exists():
                local_file = str(local_json_path)
                logger.info(f"♻️ 本地 JSON 已存在，跳过重写: {local_file}")
            else:
                local_file = self.local_publisher.save_json(articles_data, date_str)

            if not local_file:
                self._update_pipeline_state(pipeline_state, "local_publish", "failed")
                logger.error("❌ 本地保存失败，任务结束")
                return
            self._update_pipeline_state(pipeline_state, "local_publish", "success", local_file)

            remote_filename = f"{date_str}.json"
            upload_success = False

            if UPLOAD_ENABLED:
                logger.info("\n☁️ 正在上传到云服务器 JSON 目录...")

                def _upload_once() -> bool:
                    if self.cloud_publisher.upload(local_file, remote_filename, CLOUD_SERVER_JSON_REMOTE_PATH):
                        return True
                    raise RuntimeError("upload() returned False")

                try:
                    self._run_with_retry("upload", _upload_once, retryable=True)
                    upload_success = True
                    self._update_pipeline_state(pipeline_state, "upload", "success", remote_filename)
                    logger.info(f"✅ JSON 报告已成功上传到云服务器: {CLOUD_SERVER_HOST}:{CLOUD_SERVER_JSON_REMOTE_PATH}/{remote_filename}")
                except Exception as e:
                    self._update_pipeline_state(pipeline_state, "upload", "failed", str(e)[:200])
                    logger.error(f"❌ 云服务器上传失败: {str(e)[:120]}")
            else:
                self._update_pipeline_state(pipeline_state, "upload", "skipped", "UPLOAD_ENABLED=false")
                logger.info("ℹ️ 已跳过上传阶段（UPLOAD_ENABLED=false）")

            can_send_email = EMAIL_ENABLED and (upload_success or EMAIL_WHEN_UPLOAD_FAIL or not UPLOAD_ENABLED)
            if can_send_email:
                logger.info("\n📧 开始发送邮件...")
                import subprocess

                email_sender_script = Path(__file__).parent / "daily_email_sender.sh"

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
                    self._run_with_retry("email", _send_once, retryable=True)
                    self._update_pipeline_state(pipeline_state, "email", "success")
                    logger.info("✅ 邮件发送成功")
                except Exception as e:
                    self._update_pipeline_state(pipeline_state, "email", "failed", str(e)[:200])
                    logger.warning(f"⚠️ 邮件发送失败: {str(e)[:120]}")
            else:
                reason = "EMAIL_ENABLED=false" if not EMAIL_ENABLED else "upload_failed_and_EMAIL_WHEN_UPLOAD_FAIL=false"
                self._update_pipeline_state(pipeline_state, "email", "skipped", reason)
                logger.info(f"ℹ️ 已跳过邮件发送阶段（{reason}）")

            logger.info(self.analyzer.get_cost_report())

        except Exception as e:
            logger.error(f"❌ 运行出错: {e}")
            raise


if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("🔍 检查并更新 RSSHub 代理 IP...")
        update_rsshub_proxy_ip()
        logger.info("=" * 60 + "\n")

        bot = AI_Daily_Report()
        bot.run()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 程序异常退出: {e}")
        sys.exit(1)
