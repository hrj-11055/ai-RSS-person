"""
RSS 文章收集模块

从 daily_report_PRO_cloud.py 重构而来，提供清晰、模块化的
RSS 收集系统，支持多种抓取策略（rsshub、cffi、direct、noproxy）。

Author: AI-RSS-PERSON Team
Version: 2.0.0
"""

import feedparser
import requests
import datetime
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import timezone, timedelta

# 导入共享工具
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import setup_logger, get_optional_env
from core.utils.constants import (
    DEFAULT_RSSHUB_HOST,
    DEFAULT_FETCH_TIMEOUT,
    DEFAULT_MAX_ITEMS_PER_SOURCE,
    STRATEGY_RSSHUB,
    STRATEGY_CFFI,
    STRATEGY_DIRECT,
    STRATEGY_NOPROXY,
)

# 配置
RSSHUB_HOST = get_optional_env("RSSHUB_HOST", DEFAULT_RSSHUB_HOST)
PROXY_URL = get_optional_env("PROXY_URL", "")

# 设置日志
logger = setup_logger(__name__, get_optional_env("LOG_LEVEL", "INFO"))

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# 默认 RSS 源列表（未来将移至 YAML 配置文件）
DEFAULT_SOURCES = [    # --- 🤖 AI 研究与博客 (从 awesome-AI-feeds 添加) ---
    # --- 🐦 Twitter/X 官方机构账号 (通过RSSHub) ---
    # --- 🐦 Twitter/X --- (因代理问题暂时禁用)
    # {"name": "OpenAI Twitter", "url": "/twitter/user/OpenAI", "strategy": STRATEGY_RSSHUB},
    # {"name": "Google DeepMind", "url": "/twitter/user/GoogleDeepMind", "strategy": STRATEGY_RSSHUB},
    # {"name": "Anthropic AI", "url": "/twitter/user/AnthropicAI", "strategy": STRATEGY_RSSHUB},
    # {"name": "DeepSeek AI", "url": "/twitter/user/deepseek_ai", "strategy": STRATEGY_RSSHUB},
    # {"name": "Sam Altman", "url": "/twitter/user/sama", "strategy": STRATEGY_RSSHUB},
    # {"name": "Geoffrey Hinton", "url": "/twitter/user/geoffreyhinton", "strategy": STRATEGY_RSSHUB},
    # {"name": "Yann LeCun", "url": "/twitter/user/ylecun", "strategy": STRATEGY_RSSHUB},
    # {"name": "Andrew Ng", "url": "/twitter/user/AndrewYNg", "strategy": STRATEGY_RSSHUB},

    # --- 📰 国际科技博客 ---
    {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "strategy": STRATEGY_DIRECT},
    {"name": "Google DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "Stability AI", "url": "https://stability.ai/news?format=rss", "strategy": STRATEGY_DIRECT},
    {"name": "NVIDIA Blog", "url": "https://blogs.nvidia.com/feed", "strategy": STRATEGY_DIRECT},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed", "strategy": STRATEGY_DIRECT},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "strategy": STRATEGY_DIRECT},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "Arxiv AI", "url": "https://arxiv.org/rss/cs.AI", "strategy": STRATEGY_NOPROXY},

    # --- 🤖 AI 社区 & 讨论 ---
    {"name": "Hacker News AI", "url": "https://hnrss.org/newest?q=AI", "strategy": STRATEGY_DIRECT},
    {"name": "Hacker News LLM", "url": "https://hnrss.org/newest?q=LLM", "strategy": STRATEGY_DIRECT},

    # --- 🤖 awesome-AI-feeds (测试可用) ---
    {"name": "Machine Learning Mastery", "url": "https://machinelearningmastery.com/blog/feed", "strategy": STRATEGY_DIRECT},
    {"name": "AI Roadmap Institute", "url": "https://medium.com/feed/ai-roadmap-institute", "strategy": STRATEGY_DIRECT},
    {"name": "AITopics", "url": "https://aitopics.org/feed", "strategy": STRATEGY_DIRECT},
    {"name": "AWS ML Blog", "url": "https://aws.amazon.com/blogs/ai/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Microsoft ML Blog", "url": "https://blogs.technet.microsoft.com/machinelearning/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Archie.AI Medium", "url": "https://medium.com/feed/archieai", "strategy": STRATEGY_DIRECT},
    {"name": "Singularity Weblog", "url": "https://www.singularityweblog.com/blog/feed", "strategy": STRATEGY_DIRECT},
    {"name": "DataRobot AI", "url": "https://www.datarobot.com/blog/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Iris.ai Science Assistant", "url": "https://iris.ai/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Datumbox ML Blog", "url": "http://blog.datumbox.com/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Marketing AI Institute", "url": "https://www.marketingaiinstitute.com/blog/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "Yseop AI", "url": "https://yseop.com/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Quertle AI", "url": "http://quertle.com/blog/feed", "strategy": STRATEGY_DIRECT},
    {"name": "AI Resources Blog", "url": "http://airesources.blogspot.com/feeds/posts/default?alt=rss", "strategy": STRATEGY_DIRECT},
    {"name": "AI Weekly Newsletter", "url": "http://aiweekly.co/issues.rss", "strategy": STRATEGY_DIRECT},
    {"name": "Computational Intelligence", "url": "http://computational-intelligence.blogspot.com/feeds/posts/default", "strategy": STRATEGY_DIRECT},
    {"name": "Becoming Human AI", "url": "https://becominghuman.ai/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Sony AI Neural Network", "url": "https://support.dl.sony.com/blogs/feed", "strategy": STRATEGY_DIRECT},
    {"name": "KDnuggets Neural Networks", "url": "https://www.kdnuggets.com/tag/recurrent-neural-networks/feed", "strategy": STRATEGY_DIRECT},
    {"name": "Hackaday Neural Network", "url": "https://hackaday.com/tag/neural-network/feed", "strategy": STRATEGY_DIRECT},
    {"name": "AI Weirdness", "url": "http://aiweirdness.com/rss", "strategy": STRATEGY_DIRECT},

    # --- 📰 中文 RSS ---
    {"name": "阮一峰博客", "url": "https://www.ruanyifeng.com/blog/atom.xml", "strategy": STRATEGY_DIRECT},
    {"name": "少数派", "url": "https://sspai.com/feed", "strategy": STRATEGY_DIRECT},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "strategy": STRATEGY_DIRECT},
    # {"name": "36氪 AI", "url": "/36kr/information/AI", "strategy": STRATEGY_RSSHUB},  # 因代理问题暂时禁用
    # {"name": "InfoQ AI", "url": "/infoq/topic/AI&LLM", "strategy": STRATEGY_RSSHUB},  # 因代理问题暂时禁用

    # --- 📝 博客 RSS (从 OPML 添加) ---
    {"name": "abortretry.fail", "url": "https://www.abortretry.fail/feed", "strategy": STRATEGY_DIRECT},
    {"name": "anildash.com", "url": "https://anildash.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "antirez.com", "url": "http://antirez.com/rss", "strategy": STRATEGY_DIRECT},
    {"name": "aresluna.org", "url": "https://aresluna.org/main.rss", "strategy": STRATEGY_DIRECT},
    {"name": "beej.us", "url": "https://beej.us/blog/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "bernsteinbear.com", "url": "https://bernsteinbear.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "berthub.eu", "url": "https://berthub.eu/articles/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "blog.jim-nielsen.com", "url": "https://blog.jim-nielsen.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "blog.pixelmelt.dev", "url": "https://blog.pixelmelt.dev/rss/", "strategy": STRATEGY_DIRECT},
    {"name": "bogdanthegeek.github.io", "url": "https://bogdanthegeek.github.io/blog/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "borretti.me", "url": "https://borretti.me/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "brutecat.com", "url": "https://brutecat.com/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "chadnauseam.com", "url": "https://chadnauseam.com/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "chiark.greenend.org.uk/~sgtatham", "url": "https://www.chiark.greenend.org.uk/~sgtatham/quasiblog/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "computer.rip", "url": "https://computer.rip/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "construction-physics.com", "url": "https://www.construction-physics.com/feed", "strategy": STRATEGY_DIRECT},
    {"name": "danielchasehooper.com", "url": "https://danielchasehooper.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "danieldelaney.net", "url": "https://danieldelaney.net/feed", "strategy": STRATEGY_DIRECT},
    {"name": "danielwirtz.com", "url": "https://danielwirtz.com/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "daringfireball.net", "url": "https://daringfireball.net/feeds/main", "strategy": STRATEGY_DIRECT},
    {"name": "devblogs.microsoft.com/oldnewthing", "url": "https://devblogs.microsoft.com/oldnewthing/feed", "strategy": STRATEGY_DIRECT},
    {"name": "dfarq.homeip.net", "url": "https://dfarq.homeip.net/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "downtowndougbrown.com", "url": "https://www.downtowndougbrown.com/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "dynomight.net", "url": "https://dynomight.net/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "eli.thegreenplace.net", "url": "https://eli.thegreenplace.net/feeds/all.atom.xml", "strategy": STRATEGY_DIRECT},
    {"name": "entropicthoughts.com", "url": "https://entropicthoughts.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "ericmigi.com", "url": "https://ericmigi.com/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "evanhahn.com", "url": "https://evanhahn.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "experimental-history.com", "url": "https://www.experimental-history.com/feed", "strategy": STRATEGY_DIRECT},
    {"name": "fabiensanglard.net", "url": "https://fabiensanglard.net/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "filfre.net", "url": "https://www.filfre.net/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "geoffreylitt.com", "url": "https://www.geoffreylitt.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "geohot.github.io", "url": "https://geohot.github.io/blog/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "gilesthomas.com", "url": "https://gilesthomas.com/feed/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "grantslatton.com", "url": "https://grantslatton.com/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "herman.bearblog.dev", "url": "https://herman.bearblog.dev/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "hey.paris", "url": "https://hey.paris/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "hugotunius.se", "url": "https://hugotunius.se/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "idiallo.com", "url": "https://idiallo.com/feed.rss", "strategy": STRATEGY_DIRECT},
    {"name": "it-notes.dragas.net", "url": "https://it-notes.dragas.net/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "jayd.ml", "url": "https://jayd.ml/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "jeffgeerling.com", "url": "https://www.jeffgeerling.com/blog.xml", "strategy": STRATEGY_DIRECT},
    {"name": "joanwestenberg.com", "url": "https://joanwestenberg.com/rss", "strategy": STRATEGY_DIRECT},
    {"name": "johndcook.com", "url": "https://www.johndcook.com/blog/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "jyn.dev", "url": "https://jyn.dev/atom.xml", "strategy": STRATEGY_DIRECT},
    {"name": "keygen.sh", "url": "https://keygen.sh/blog/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "krebsonsecurity.com", "url": "https://krebsonsecurity.com/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "lucumr.pocoo.org", "url": "https://lucumr.pocoo.org/feed.atom", "strategy": STRATEGY_DIRECT},
    {"name": "martinalderson.com", "url": "https://martinalderson.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "matduggan.com", "url": "https://matduggan.com/rss/", "strategy": STRATEGY_DIRECT},
    {"name": "matklad.github.io", "url": "https://matklad.github.io/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "maurycyz.com", "url": "https://maurycyz.com/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "micahflee.com", "url": "https://micahflee.com/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "michael.stapelberg.ch", "url": "https://michael.stapelberg.ch/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "miguelgrinberg.com", "url": "https://blog.miguelgrinberg.com/feed", "strategy": STRATEGY_DIRECT},
    {"name": "minimaxir.com", "url": "https://minimaxir.com/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "mitchellh.com", "url": "https://mitchellh.com/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "mjg59.dreamwidth.org", "url": "https://mjg59.dreamwidth.org/data/rss", "strategy": STRATEGY_DIRECT},
    {"name": "nesbitt.io", "url": "https://nesbitt.io/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "overreacted.io", "url": "https://overreacted.io/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "paulgraham.com", "url": "http://www.aaronsw.com/2002/feeds/pgessays.rss", "strategy": STRATEGY_DIRECT},
    {"name": "philiplaine.com", "url": "https://philiplaine.com/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "pluralistic.net", "url": "https://pluralistic.net/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "rakhim.exotext.com", "url": "https://rakhim.exotext.com/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "refactoringenglish.com", "url": "https://refactoringenglish.com/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "righto.com", "url": "https://www.righto.com/feeds/posts/default", "strategy": STRATEGY_DIRECT},
    {"name": "seangoedecke.com", "url": "https://www.seangoedecke.com/rss.xml", "strategy": STRATEGY_DIRECT},
    {"name": "shkspr.mobi", "url": "https://shkspr.mobi/blog/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "simone.org", "url": "https://simone.org/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "simonwillison.net", "url": "https://simonwillison.net/atom/everything/", "strategy": STRATEGY_DIRECT},
    {"name": "steveblank.com", "url": "https://steveblank.com/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "susam.net", "url": "https://susam.net/feed.xml", "strategy": STRATEGY_DIRECT},
    {"name": "tedium.co", "url": "https://feed.tedium.co/", "strategy": STRATEGY_DIRECT},
    {"name": "terriblesoftware.org", "url": "https://terriblesoftware.org/feed/", "strategy": STRATEGY_DIRECT},
    {"name": "timsh.org", "url": "https://timsh.org/rss/", "strategy": STRATEGY_DIRECT},
    {"name": "tomrenner.com", "url": "https://tomrenner.com/index.xml", "strategy": STRATEGY_DIRECT},
    {"name": "troyhunt.com", "url": "https://www.troyhunt.com/rss/", "strategy": STRATEGY_DIRECT},
    {"name": "utcc.utoronto.ca/~cks", "url": "https://utcc.utoronto.ca/~cks/space/blog/?atom", "strategy": STRATEGY_DIRECT},
    {"name": "wheresyoured.at", "url": "https://www.wheresyoured.at/rss/", "strategy": STRATEGY_DIRECT},
    {"name": "xania.org", "url": "https://xania.org/feed", "strategy": STRATEGY_DIRECT},
    {"name": "xeiaso.net", "url": "https://xeiaso.net/blog.rss", "strategy": STRATEGY_DIRECT},
]


class RSSCollector:
    """
    RSS 文章收集器，支持多种抓取策略。

    该类提供清晰的接口，用于从多个 RSS 源收集文章，
    支持不同的抓取策略（rsshub、cffi、direct、noproxy）。

    示例：
        >>> collector = RSSCollector()
        >>> articles = collector.collect_all()
        >>> print(f"收集了 {len(articles)} 篇文章")
    """

    def __init__(
        self,
        sources: Optional[List[Dict]] = None,
        proxy_url: Optional[str] = None,
        max_items_per_source: int = DEFAULT_MAX_ITEMS_PER_SOURCE,
        time_window_hours: int = 24
    ):
        """
        初始化 RSS 收集器。

        参数：
            sources: 源字典列表（默认为 DEFAULT_SOURCES）
            proxy_url: 请求代理 URL（默认为 PROXY_URL 环境变量）
            max_items_per_source: 每个源最多收集的文章数
            time_window_hours: 只收集这么多小时内的文章
        """
        self.sources = sources or DEFAULT_SOURCES
        self.proxy_url = proxy_url or PROXY_URL
        self.max_items_per_source = max_items_per_source
        self.time_window_hours = time_window_hours

        # 设置代理
        self.proxies = {"http": self.proxy_url, "https": self.proxy_url} if self.proxy_url else {}

        # 设置请求头
        self.headers = DEFAULT_HEADERS.copy()

        # URL 去重集合（防止重复文章）
        self.seen_urls = set()

        # 如果可用，导入 curl_cffi
        self.cffi_requests = None
        try:
            from curl_cffi import requests as cffi_requests
            self.cffi_requests = cffi_requests
            logger.debug("curl_cffi 可用")
        except ImportError:
            logger.debug("curl_cffi 不可用，cffi 策略将失败")

    def collect_all(self) -> List[Dict]:
        """
        从所有配置的源收集文章。

        返回：
            文章字典列表，每个字典包含：source、title、link、summary

        示例：
            >>> collector = RSSCollector()
            >>> articles = collector.collect_all()
            >>> for article in articles:
            ...     print(f"{article['source']}: {article['title']}")
        """
        logger.info(f"🚀 启动采集 (过去{self.time_window_hours}小时) ...")
        collected_items = []

        for source in self.sources:
            logger.info(f"📡 扫描: {source['name']} ...")
            try:
                articles = self._fetch_source(source)
                collected_items.extend(articles)
            except Exception as e:
                logger.error(f"❌ {source['name']}: 未知错误: {str(e)[:100]}")
                continue

        logger.info(f"📊 采集完成: 共收集 {len(collected_items)} 篇文章")
        return collected_items

    def _fetch_source(self, source: Dict) -> List[Dict]:
        """
        使用配置的策略从单个源抓取文章。

        参数：
            source: 源字典，包含 'name'、'url' 和 'strategy' 键

        返回：
            文章字典列表
        """
        url = source['url']
        strategy = source.get('strategy', STRATEGY_DIRECT)

        # 使用适当的策略抓取
        response = self._fetch_with_strategy(url, strategy, source['name'])

        if not response:
            return []

        # 解析和过滤文章
        return self._parse_feed(response, source)

    def _fetch_with_strategy(self, url: str, strategy: str, source_name: str) -> Optional[bytes]:
        """
        使用指定策略抓取 RSS feed 内容。

        参数：
            url: RSS feed URL
            strategy: 抓取策略（rsshub、cffi、direct、noproxy）
            source_name: 源名称（用于日志）

        返回：
            Feed 内容（字节），如果抓取失败则返回 None
        """
        try:
            if strategy == STRATEGY_RSSHUB:
                return self._fetch_rsshub(url)
            elif strategy == STRATEGY_CFFI:
                return self._fetch_cffi(url)
            elif strategy == STRATEGY_NOPROXY:
                return self._fetch_noproxy(url)
            else:  # STRATEGY_DIRECT
                return self._fetch_direct(url)
        except requests.exceptions.Timeout:
            logger.error(f"❌ {source_name}: 请求超时")
        except requests.exceptions.SSLError as e:
            logger.error(f"❌ {source_name}: SSL错误: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {source_name}: 请求失败: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"❌ {source_name}: 未知错误: {str(e)[:100]}")

        return None

    def _fetch_rsshub(self, route: str) -> Optional[bytes]:
        """
        策略 A: 通过 RSSHub 抓取（支持本地或公开实例）。

        参数：
            route: RSSHub 路由（例如 /twitter/user/OpenAI）

        返回：
            Feed 内容或 None
        """
        url = f"{RSSHUB_HOST}{route}"
        logger.debug(f"  使用 RSSHub 策略: {url}")

        # 判断是否为本地 RSSHub，如果是则不使用代理
        is_local_rsshub = (
            "localhost" in RSSHUB_HOST or
            "127.0.0.1" in RSSHUB_HOST or
            RSSHUB_HOST.startswith("http://192.168.") or
            RSSHUB_HOST.startswith("http://10.") or
            RSSHUB_HOST.startswith("http://172.")
        )

        proxies = None if is_local_rsshub else (self.proxies if self.proxies else None)

        resp = requests.get(url, proxies=proxies, timeout=DEFAULT_FETCH_TIMEOUT)
        if resp.status_code == 200:
            return resp.content
        return None

    def _fetch_cffi(self, url: str) -> Optional[bytes]:
        """
        策略 B: 使用 curl_cffi 绕过 403 阻止。

        参数：
            url: 要抓取的完整 URL

        返回：
            Feed 内容或 None
        """
        if not self.cffi_requests:
            raise ImportError("curl_cffi 不可用")

        logger.debug(f"  使用 CFFI 策略: {url}")
        resp = self.cffi_requests.get(
            url,
            proxies=self.proxies if self.proxies else None,
            impersonate="edge101",
            timeout=DEFAULT_FETCH_TIMEOUT
        )
        if resp.status_code == 200:
            return resp.content
        return None

    def _fetch_direct(self, url: str) -> Optional[bytes]:
        """
        策略 C: 通过代理直接连接。

        参数：
            url: 要抓取的完整 URL

        返回：
            Feed 内容或 None
        """
        logger.debug(f"  使用 Direct 策略: {url}")
        resp = requests.get(
            url,
            headers=self.headers,
            proxies=self.proxies if self.proxies else None,
            timeout=DEFAULT_FETCH_TIMEOUT
        )
        if resp.status_code == 200:
            return resp.content
        elif resp.status_code == 403:
            # 自动回退到 cffi（如果可用），失败时优雅降级
            logger.debug(f"  收到 403，尝试 cffi 回退...")
            try:
                return self._fetch_cffi(url)
            except Exception as e:
                logger.warning(f"  cffi 回退失败: {str(e)[:120]}")
                return None
        return None

    def _fetch_noproxy(self, url: str) -> Optional[bytes]:
        """
        策略 D: 不通过代理直接连接。

        参数：
            url: 要抓取的完整 URL

        返回：
            Feed 内容或 None
        """
        logger.debug(f"  使用 NoProxy 策略: {url}")
        resp = requests.get(url, headers=self.headers, timeout=15)
        if resp.status_code == 200:
            return resp.content
        return None

    def _parse_feed(self, content: bytes, source: Dict) -> List[Dict]:
        """
        解析 RSS feed 内容并按时间窗口过滤文章。

        参数：
            content: 原始 RSS feed 内容
            source: 源字典

        返回：
            过滤后的文章字典列表
        """
        feed = feedparser.parse(content)

        if len(feed.entries) == 0:
            logger.warning(f"⚠️ {source['name']}: 源为空")
            return []

        # 获取前 N 个候选文章
        candidates = feed.entries[:self.max_items_per_source]
        valid_articles = []

        for entry in candidates:
            # 验证标题和链接
            if not entry.title or not entry.link:
                logger.warning(f"文章缺少标题或链接，跳过")
                continue

            # URL 去重检查
            if entry.link in self.seen_urls:
                logger.debug(f"跳过重复链接: {entry.link[:60]}")
                continue

            self.seen_urls.add(entry.link)

            # 时间过滤
            if not self._is_within_time_window(entry):
                continue

            # 安全获取摘要
            summary_value = entry.get('summary', entry.get('description', '')) or ''
            if not isinstance(summary_value, str):
                summary_value = str(summary_value)
            summary_value = summary_value[:1000]

            valid_articles.append({
                "source": source['name'],
                "title": entry.title,
                "link": entry.link,
                "summary": summary_value
            })

        logger.info(f"✅ {source['name']}: 发现 {len(candidates)} 条，入选 {len(valid_articles)} 条 ({self.time_window_hours}h内)")
        return valid_articles

    def _is_within_time_window(self, entry) -> bool:
        """
        检查文章是否在配置的时间窗口内。

        增强版：添加额外验证以过滤旧内容，特别是针对 Twitter/RSSHub 源。

        参数：
            entry: Feedparser entry 对象

        返回：
            如果文章在时间窗口内则返回 True，否则返回 False
        """
        # 1. 尝试获取发布日期
        published = entry.get('published_parsed') or entry.get('updated_parsed')

        if not published:
            # 关键变更：没有日期时不再假设是最近的，而是跳过
            title = entry.get('title') or 'Unknown'
            logger.debug(f"文章缺少时间戳，跳过: {str(title)[:40]}")
            return False

        # 2. 转换为北京时间并比较
        try:
            # published_parsed 返回的是 UTC 时间元组
            # 创建带 UTC 时区的 datetime 对象
            entry_time_utc = datetime.datetime(*published[:6], tzinfo=timezone.utc)

            # 转换为北京时间 (UTC+8)
            BEIJING_TZ = timezone(timedelta(hours=8))
            entry_time_beijing = entry_time_utc.astimezone(BEIJING_TZ)

            # 获取当前北京时间
            now_beijing = datetime.datetime.now(BEIJING_TZ)
            cutoff_time_beijing = now_beijing - datetime.timedelta(hours=self.time_window_hours)

            # 额外检查：如果时间戳明显不合理
            if entry_time_beijing > now_beijing:
                title = entry.get('title') or 'Unknown'
                logger.debug(f"文章时间戳在未来，跳过: {str(title)[:40]}")
                return False

            # 如果时间戳是2024年或之前的，跳过
            # 注意：这个检查捕获 RSSHub 返回错误时间戳的情况
            if entry_time_beijing.year < 2025:
                title = entry.get('title') or 'Unknown'
                logger.debug(f"文章时间戳过旧 ({entry_time_beijing.year})，跳过: {str(title)[:40]}")
                return False

            # 使用北京时间进行比较
            return entry_time_beijing > cutoff_time_beijing
        except (ValueError, TypeError) as e:
            logger.warning(f"时间戳解析失败: {e}")
            return False


# 独立测试/验证函数（保持原 rss_collector.py 的功能）
def validate_sources(sources: Optional[List[Dict]] = None) -> Dict:
    """
    验证所有 RSS 源并返回统计信息。

    该函数可作为独立工具用于测试 RSS 源可用性。

    参数：
        sources: 源字典列表（默认为 DEFAULT_SOURCES）

    返回：
            包含验证统计的字典
    """
    collector = RSSCollector(sources=sources)
    results = {
        "total": len(collector.sources),
        "success": 0,
        "failed": 0,
        "empty": 0,
        "details": []
    }

    for source in collector.sources:
        try:
            response = collector._fetch_with_strategy(
                source['url'],
                source.get('strategy', STRATEGY_DIRECT),
                source['name']
            )

            if response:
                feed = feedparser.parse(response)
                count = len(feed.entries)
                if count > 0:
                    results["success"] += 1
                    results["details"].append({
                        "name": source['name'],
                        "status": "SUCCESS",
                        "count": count
                    })
                else:
                    results["empty"] += 1
                    results["details"].append({
                        "name": source['name'],
                        "status": "EMPTY",
                        "count": 0
                    })
            else:
                results["failed"] += 1
                results["details"].append({
                    "name": source['name'],
                    "status": "FAILED",
                    "count": 0
                })
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "name": source['name'],
                "status": "ERROR",
                "error": str(e)[:100]
            })

    return results


if __name__ == "__main__":
    # 测试/验证模式
    print("🧪 RSS Collector 测试模式")
    print("=" * 50)

    results = validate_sources()

    print(f"总计: {results['total']} 个源")
    print(f"✅ 成功: {results['success']} 个")
    print(f"⚠️  为空: {results['empty']} 个")
    print(f"❌ 失败: {results['failed']} 个")
    print()

    for detail in results['details']:
        status_emoji = "✅" if detail['status'] == "SUCCESS" else "⚠️" if detail['status'] == "EMPTY" else "❌"
        count_str = f" ({detail['count']}条)" if 'count' in detail else ""
        print(f"{status_emoji} {detail['name']}{count_str}")
