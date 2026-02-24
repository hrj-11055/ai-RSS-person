"""
AI 日报生成器 - 云服务器版本

主要功能：
1. 从多个 RSS 源采集 AI 行业新闻
2. 使用智能排序系统筛选重要文章
3. 对文章标题进行去重
3. 通过 DeepSeek AI 分析并生成 JSON 格式报告
4. 上传到云服务器供网站集成使用
5. 将来直接在服务器上部署，就不需要上传到云服务器，本来就在云服务器上了。
Author: AI-RSS-PERSON Team
Version: 2.0.0
"""

import os
import sys
import datetime
import time
import logging
from pathlib import Path

# 导入共享工具
from dotenv import load_dotenv

# 导入 core/utils 工具
from core.utils import setup_logger, get_required_env, get_optional_env, get_int_env, CostTracker
from core.utils.constants import *

# 导入 lib 模块
from lib.rss_collector import RSSCollector
from lib.ai_analyzer import AIAnalyzer
from lib.publishers.cloud_publisher import CloudPublisher
from lib.publishers.local_publisher import LocalPublisher
from lib.article_deduplicator import ArticleDeduplicator
from article_ranker import ArticleRanker

# 导入配置管理器
from core.config_manager import get_config_manager

# ================= ⚙️ 配置区域 (从环境变量读取) =================

# 1. DeepSeek 配置 (从环境变量读取，必需)
load_dotenv()
DEEPSEEK_API_KEY = get_required_env("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = get_optional_env("DEEPSEEK_BASE_URL", DEFAULT_AI_BASE_URL)

# 2. 网络代理 (可选)
PROXY_URL = get_optional_env("PROXY_URL", "")

# 3. RSSHub配置（用于Twitter等需要RSSHub的源）
RSSHUB_HOST = get_optional_env("RSSHUB_HOST", DEFAULT_RSSHUB_HOST)

# 4. 抓取设置
MAX_ITEMS_PER_SOURCE = get_int_env("MAX_ITEMS_PER_SOURCE", DEFAULT_MAX_ITEMS_PER_SOURCE)

# 5. 报告设置
MAX_ARTICLES_IN_REPORT = get_int_env("MAX_ARTICLES_IN_REPORT", DEFAULT_MAX_ARTICLES_IN_REPORT)

# 6. 本地保存目录配置
OUTPUT_DIR = get_optional_env("OUTPUT_DIR", DEFAULT_OUTPUT_DIR)

# 7. 日志级别
LOG_LEVEL = get_optional_env("LOG_LEVEL", DEFAULT_LOG_LEVEL)

# 8. 云服务器配置
CLOUD_SERVER_HOST = get_optional_env("CLOUD_SERVER_HOST", DEFAULT_CLOUD_SERVER_HOST)
CLOUD_SERVER_PORT = get_int_env("CLOUD_SERVER_PORT", DEFAULT_CLOUD_SERVER_PORT)
CLOUD_SERVER_USER = get_optional_env("CLOUD_SERVER_USER", DEFAULT_CLOUD_SERVER_USER)
CLOUD_SERVER_PASSWORD = get_optional_env("CLOUD_SERVER_PASSWORD", "")
CLOUD_SERVER_KEY_PATH = get_optional_env("CLOUD_SERVER_KEY_PATH", "")
CLOUD_SERVER_REMOTE_PATH = get_optional_env("CLOUD_SERVER_REMOTE_PATH", DEFAULT_CLOUD_SERVER_REMOTE_PATH)
CLOUD_SERVER_JSON_REMOTE_PATH = get_optional_env("CLOUD_SERVER_JSON_REMOTE_PATH", DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH)

# 9. 上传方式
UPLOAD_METHOD = get_optional_env("UPLOAD_METHOD", DEFAULT_UPLOAD_METHOD)

# 10. HTTP上传配置（如果使用HTTP方式）
HTTP_UPLOAD_URL = get_optional_env("HTTP_UPLOAD_URL", "")
HTTP_UPLOAD_TOKEN = get_optional_env("HTTP_UPLOAD_TOKEN", "")

# 初始化日志
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
        # 方法1: 获取 bridge100 的 IP
        result = subprocess.run(
            ["ifconfig", "bridge100"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # 从 ifconfig 输出中提取 IP 地址
            match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                new_ip = match.group(1)
            else:
                logger.warning("⚠️ 无法从 bridge100 获取 IP")
                return False
        else:
            logger.warning("⚠️ bridge100 接口不存在，跳过代理 IP 更新")
            return False

        # 读取 docker-compose.yml
        compose_file = Path(__file__).parent / "docker-compose.yml"
        if not compose_file.exists():
            logger.warning("⚠️ docker-compose.yml 不存在，跳过代理 IP 更新")
            return False

        content = compose_file.read_text()

        # 检查是否需要更新
        current_proxy_match = re.search(r'PROXY_URI=http://(\d+\.\d+\.\d+\.\d+)', content)
        if current_proxy_match:
            current_ip = current_proxy_match.group(1)
            if current_ip == new_ip:
                logger.info(f"✅ 代理 IP 无需更新: {new_ip}")
                return True

        # 更新 PROXY_URI
        new_content = re.sub(
            r'PROXY_URI=http://\d+\.\d+\.\d+\.\d+',
            f'PROXY_URI=http://{new_ip}',
            content
        )

        # 写回文件
        compose_file.write_text(new_content)
        logger.info(f"🔄 已更新 docker-compose.yml 中的代理 IP: {new_ip}")

        # 重启 RSSHub 容器使新配置生效
        try:
            subprocess.run(
                ["docker-compose", "-f", str(compose_file), "restart", "rsshub"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=compose_file.parent
            )
            logger.info("✅ RSSHub 容器已重启")
            # 等待 RSSHub 启动
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


# ================= 🤖 AI 日报生成器 =================
class AI_Daily_Report:
    """AI 日报生成器主类"""

    def __init__(self):
        """初始化 AI 日报生成器"""
        # 验证 API 密钥
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY.startswith("your_"):
            raise ValueError("❌ DeepSeek API Key 未配置！请在 .env 文件中设置 DEEPSEEK_API_KEY")

        # 从 YAML 配置文件加载 RSS 源
        config_manager = get_config_manager()
        sources = config_manager.get_enabled_sources()

        logger.info(f"📡 已加载 {len(sources)} 个启用的 RSS 源")

        # 初始化组件
        self.ranker = ArticleRanker()
        self.deduplicator = ArticleDeduplicator(config_manager=config_manager)
        self.cost_tracker = CostTracker()

        # 初始化 RSS 收集器
        self.collector = RSSCollector(
            sources=sources,
            proxy_url=PROXY_URL,
            max_items_per_source=MAX_ITEMS_PER_SOURCE,
            time_window_hours=24
        )

        # 初始化 AI 分析器
        self.analyzer = AIAnalyzer(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )

        # 初始化云发布器
        self.cloud_publisher = CloudPublisher(
            host=CLOUD_SERVER_HOST,
            port=CLOUD_SERVER_PORT,
            user=CLOUD_SERVER_USER,
            password=CLOUD_SERVER_PASSWORD,
            key_path=CLOUD_SERVER_KEY_PATH,
            remote_path=CLOUD_SERVER_REMOTE_PATH,
            method=UPLOAD_METHOD
        )

        # 初始化本地发布器
        self.local_publisher = LocalPublisher(output_dir=OUTPUT_DIR)

        # 代理配置日志
        if PROXY_URL:
            logger.info(f"✅ 代理已配置: {PROXY_URL}")
        else:
            logger.info("ℹ️ 未配置代理，使用直连")

    def run(self):
        """运行日报生成流程"""
        try:
            # 1. 采集 RSS 文章
            logger.info("🚀 启动采集 (过去24小时) ...")
            items = self.collector.collect_all()

            if not items:
                logger.warning("❌ 过去24小时内没有新资讯，任务结束。")
                return

            # 2. 文章去重（基于标题语义相似度）
            logger.info(f"\n🔄 开始去重 (共 {len(items)} 条文章)...")
            items = self.deduplicator.deduplicate(items)

            # 3. 智能排序并限制数量（确保中文新闻 ≥ 10 篇）
            logger.info(f"\n📊 开始智能排序 (共 {len(items)} 条文章)...")
            ranked_items = self.ranker.rank_articles_with_chinese_quota(
                items,
                top_n=MAX_ARTICLES_IN_REPORT,
                chinese_quota=10  # 确保至少10篇中文新闻
            )

            # 打印排序统计
            logger.info(f"\n{self.ranker.get_ranking_summary(ranked_items)}")

            # 3. AI 分析
            logger.info(f"\n🤖 开始 AI 分析 (Top {len(ranked_items)} 条)...")
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

            # 收集所有 AI 分析结果
            articles_data = []
            successful_count = 0
            failed_count = 0

            for i, item in enumerate(ranked_items, 1):
                logger.info(f"[{i}/{len(ranked_items)}] 处理: {item['title'][:30]}... (得分: {item['score']:.1f})")

                # 转换为 AI 分析器需要的格式
                article_for_ai = {
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("source", "Unknown"),
                    "link": item.get("link", "")
                }

                ai_result = self.analyzer.analyze_single(article_for_ai)

                if ai_result:
                    # AI 分析成功，添加到列表
                    articles_data.append(ai_result)
                    successful_count += 1
                    logger.info(f"✅ [{i}] 分析成功: {ai_result.get('title', 'N/A')[:40]}")
                else:
                    # AI 分析失败
                    failed_count += 1
                    logger.warning(f"⚠️ [{i}] 分析失败，跳过此文章")

                time.sleep(1)  # 避免请求过快

            logger.info(f"\n📊 AI 分析完成: 成功 {successful_count} 条，失败 {failed_count} 条")

            # 按 importance_score 从高到低排序
            articles_data.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
            logger.info("📊 已按重要性评分从高到低排序")

            if successful_count == 0:
                logger.error("❌ 所有文章分析均失败，任务结束。")
                return

            # 4. 保存到本地 JSON 文件
            logger.info("\n💾 正在保存到本地 JSON 文件...")
            local_file = self.local_publisher.save_json(articles_data, date_str)

            if not local_file:
                logger.error("❌ 本地保存失败，跳过上传")
                return

            # 5. 上传到云服务器 JSON 目录
            logger.info("\n☁️ 正在上传到云服务器 JSON 目录...")
            remote_filename = f"{date_str}.json"

            if self.cloud_publisher.upload(local_file, remote_filename, CLOUD_SERVER_JSON_REMOTE_PATH):
                logger.info(f"✅ JSON 报告已成功上传到云服务器: {CLOUD_SERVER_HOST}:{CLOUD_SERVER_JSON_REMOTE_PATH}/{remote_filename}")

                # JSON 上传成功后，发送邮件（JSON→MD→邮件）
                logger.info("\n📧 开始发送邮件...")
                try:
                    import subprocess
                    result = subprocess.run(
                        ['/Users/MarkHuang/miniconda3/bin/python3', 'daily_email_sender.sh'],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        logger.info("✅ 邮件发送成功")
                    else:
                        logger.warning(f"⚠️ 邮件发送失败: {result.stdout}")
                except Exception as e:
                    logger.warning(f"⚠️ 邮件发送异常: {str(e)[:100]}")
            else:
                logger.error("❌ 云服务器上传失败（跳过邮件发送）")

            # 打印成本报告
            logger.info(self.analyzer.get_cost_report())

        except Exception as e:
            logger.error(f"❌ 运行出错: {e}")
            raise


if __name__ == "__main__":
    try:
        # 首先更新 RSSHub 代理 IP
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
