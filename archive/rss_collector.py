import feedparser
import requests  # 普通请求
from curl_cffi import requests as cffi_requests # 强力模拟请求
import os
import urllib.parse
import datetime

# ================= 1. 基础配置 =================
PROXY_URL = "http://127.0.0.1:7897"
RSSHUB_HOST = "http://localhost:1200" # 你的 Docker RSSHub 地址
LOG_DIR = "logs"

# 确保 logs 目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 普通 requests 代理
proxies_default = { "http": PROXY_URL, "https": PROXY_URL }
# curl_cffi 代理
proxies_cffi = { "http": PROXY_URL, "https": PROXY_URL }

# 通用浏览器头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# ================= 2. 抓取函数封装 =================

def fetch_rsshub(route):
    """
    策略 A: 走本地 RSSHub
    适用: Twitter, 中文RSS, 有反爬的站
    """
    url = f"{RSSHUB_HOST}{route}"
    try:
        # RSSHub 在本地，不需要走 Clash 代理
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.content, "RSSHub", None
        else:
            return None, None, f"Status {resp.status_code}"
    except Exception as e:
        return None, None, str(e)[:100]

def fetch_cffi(url):
    """
    策略 B: curl_cffi 模拟浏览器
    适用: AI News (403 拦截)
    """
    try:
        # 换用 'edge101' 伪装，有时候比 chrome 更容易过 WAF
        resp = cffi_requests.get(
            url,
            proxies=proxies_cffi,
            impersonate="edge101",
            timeout=30
        )
        if resp.status_code == 200:
            return resp.content, "CFFI(Edge)", None
        else:
            return None, None, f"Status {resp.status_code}"
    except Exception as e:
        return None, None, str(e)[:100]

def fetch_direct(url):
    """
    策略 C: 普通直连（走代理）
    适用: Google, OpenAI 等老实网站
    """
    try:
        resp = requests.get(url, headers=HEADERS, proxies=proxies_default, timeout=15)
        if resp.status_code == 200:
            return resp.content, "Direct", None
        elif resp.status_code == 403:
            # 如果普通请求 403，自动降级尝试 cffi
            return fetch_cffi(url)
        else:
            return None, None, f"Status {resp.status_code}"
    except Exception as e:
        return None, None, str(e)[:100]

def fetch_noproxy(url):
    """
    策略 D: 直连不走代理
    适用: Arxiv 等学术网站（代理会导致超时）
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.content, "NoProxy", None
        else:
            return None, None, f"Status {resp.status_code}"
    except Exception as e:
        return None, None, str(e)[:100]

# ================= 3. 数据源定义 (精准分流) =================
# 格式: (名称, URL/Route, 策略类型)
sources = [
    # --- 🐦 Twitter/X 组 (必须走 RSSHub) ---
    ("OpenAI Twitter", "/twitter/user/OpenAI", "rsshub"),
    ("Google DeepMind", "/twitter/user/GoogleDeepMind", "rsshub"),
    ("Anthropic AI", "/twitter/user/AnthropicAI", "rsshub"),
    ("DeepSeek AI", "/twitter/user/deepseek_ai", "rsshub"),
    ("Alibaba Qwen", "/twitter/user/Alibaba_Qwen", "rsshub"),
    ("Sam Altman", "/twitter/user/sama", "rsshub"),
    ("Geoffrey Hinton", "/twitter/user/geoffreyhinton", "rsshub"),
    ("Yoshua Bengio", "/twitter/user/Yoshua_Bengio", "rsshub"),
    ("Demis Hassabis", "/twitter/user/demishassabis", "rsshub"),
    ("Andrew Ng", "/twitter/user/AndrewYNg", "rsshub"),
    ("Jim Fan", "/twitter/user/drjimfan", "rsshub"),
    ("Lex Fridman", "/twitter/user/lexfridman", "rsshub"),

    # --- 📰 MIT/学术 (通过 RSSHub) ---
    
    

    # --- 🛡️ 盾牌组 (必须用 cffi) ---
    ("AI News", "https://www.artificialintelligence-news.com/feed", "cffi"),
    

    # --- 🟢 国际科技博客 (普通直连) ---
    ("OpenAI Blog", "https://openai.com/news/rss.xml", "direct"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/", "direct"),
    ("Google DeepMind Blog", "https://deepmind.google/blog/rss.xml", "direct"),
    ("Google Research", "https://research.google/blog/rss", "direct"),
    ("Microsoft Research", "https://www.microsoft.com/en-us/research/feed", "direct"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml", "direct"),
    ("NVIDIA Research", "https://blogs.nvidia.com/blog/category/nvidia-research/feed", "direct"),
    ("NVIDIA Blog", "https://blogs.nvidia.com/feed", "direct"),
    ("AWS ML Blog", "https://aws.amazon.com/blogs/machine-learning/feed", "direct"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed", "direct"),
    ("TechCrunch", "https://techcrunch.com/feed", "direct"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "direct"),
    ("The Verge", "https://www.theverge.com/rss/index.xml", "direct"),
    ("Wired", "https://www.wired.com/feed/rss", "direct"),
    ("Digital Trends", "https://www.digitaltrends.com/feed", "direct"),
    ("Science Daily AI", "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "direct"),
    ("Towards AI", "https://towardsai.net/feed", "direct"),
    ("Jack Clark", "https://jack-clark.net/feed", "direct"),
    ("AI Business", "https://aibusiness.com/rss.xml", "direct"),
    ("AI Weekly", "https://aiweekly.co/issues.rss", "direct"),
    ("Beehiiv AI", "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml", "direct"),
    ("The Gradient", "https://thegradient.pub/rss", "direct"),

    # --- 🎓 学术网站 (不走代理) ---
    ("Arxiv AI", "https://arxiv.org/rss/cs.AI", "noproxy"),

    # --- 📰 中文RSS源 (通过RSSHub) ---
    ("36氪 AI", "/36kr/information/AI", "rsshub"),
    ("36氪", "/36kr", "rsshub"),
    ("InfoQ AI", "/infoq/topic/AI&LLM", "rsshub"),
    ("InfoQ", "/infoq", "rsshub"),
    ("虎嗅", "/huxiu", "rsshub"),
    ("钛媒体", "/tmtpost", "rsshub"),
    ("雷锋网", "/leiphone", "rsshub"),
    ("极客公园", "/geekpark", "rsshub"),
    ("钛媒体GBA", "/tmtpost/channel/gba", "rsshub"),

    # --- 📱 微信公众号 (通过 wewe-rss) ---
    ("机器之心", "http://localhost:4000/feeds/MP_WXS_3073282833.atom", "direct"),
    ("数字生命卡兹克", "http://localhost:4000/feeds/MP_WXS_3223096120.atom", "direct"),
    ("夕小瑶科技说", "http://localhost:4000/feeds/MP_WXS_3207765945.atom", "direct"),
    ("新智元", "http://localhost:4000/feeds/MP_WXS_3271041950.atom", "direct"),
    ("AI前线", "http://localhost:4000/feeds/MP_WXS_3554086560.atom", "direct"),
    ("APPSO", "http://localhost:4000/feeds/MP_WXS_2392024520.atom", "direct"),
    ("智东西", "http://localhost:4000/feeds/MP_WXS_3081486433.atom", "direct"),
    ("量子位", "http://localhost:4000/feeds/MP_WXS_3236757533.atom", "direct"),
    ("量子位官网", "https://www.qbitai.com/feed", "direct"),
    ("Founder Park", "http://localhost:4000/feeds/MP_WXS_3895742803.atom", "direct"),
    ("赛博禅心", "http://localhost:4000/feeds/MP_WXS_3934419561.atom", "direct"),
    ("GitHubDaily", "http://localhost:4000/feeds/MP_WXS_3019715205.atom", "direct"),
    ("特工宇宙", "http://localhost:4000/feeds/MP_WXS_3621654047.atom", "direct"),
    ("AI科技评论", "http://localhost:4000/feeds/MP_WXS_3098132220.atom", "direct"),
    ("深科技", "http://localhost:4000/feeds/MP_WXS_3218265689.atom", "direct"),

    # --- 🎯 中文开发者社区 ---
    ("掘金AI", "https://juejin.cn/tag/AI/rss", "direct"),
    ("掘金", "https://juejin.cn/rss", "direct"),
    ("CSDN AI", "https://rss.blog.csdn.net/rss/ai", "direct"),
    ("AI研习社", "https://www.yanxishe.com/rss", "direct"),
    ("SegmentFault", "https://segmentfault.com/feeds", "direct"),

    # --- 📰 中文科技博客 ---
    ("阮一峰", "/ruanyifeng-blog", "rsshub"),
    ("小众软件", "/appinn", "rsshub"),
]

# ================= 4. 主程序 =================
def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{LOG_DIR}/rss_validation_{timestamp}.log"

    print(f"🚀 开始 RSS 源验证...")
    print(f"🔌 代理端口: {PROXY_URL}")
    print(f"📝 日志文件: {log_file}")
    print("-" * 80)

    # 日志统计
    success_sources = []
    failed_sources = []
    empty_sources = []
    log_entries = []

    for idx, (name, target, strategy) in enumerate(sources, 1):
        print(f"[{idx}/{len(sources)}] {name:<25} | 策略: {strategy:<8} ... ", end="", flush=True)

        content = None
        method_used = ""
        error_msg = ""

        # 执行策略
        if strategy == "rsshub":
            content, method_used, error_msg = fetch_rsshub(target)
        elif strategy == "cffi":
            content, method_used, error_msg = fetch_cffi(target)
        elif strategy == "direct":
            content, method_used, error_msg = fetch_direct(target)
        elif strategy == "noproxy":
            content, method_used, error_msg = fetch_noproxy(target)

        # 解析结果
        log_entry = {
            "name": name,
            "target": target,
            "strategy": strategy,
            "status": "UNKNOWN",
            "method": method_used or "N/A",
            "count": 0,
            "error": error_msg,
            "latest_title": "",
            "latest_date": ""
        }

        if content:
            try:
                feed = feedparser.parse(content)
                count = len(feed.entries)

                if count > 0:
                    # 获取最新文章信息
                    latest = feed.entries[0]
                    latest_title = latest.get('title', 'N/A')[:60]
                    latest_date = latest.get('published', 'No date')

                    log_entry.update({
                        "status": "SUCCESS",
                        "count": count,
                        "latest_title": latest_title,
                        "latest_date": latest_date
                    })

                    print(f"✅ {count}条")
                    success_sources.append(name)
                else:
                    log_entry["status"] = "EMPTY"
                    print(f"⚠️  源为空")
                    empty_sources.append(name)
            except Exception as e:
                log_entry["status"] = "PARSE_ERROR"
                log_entry["error"] = str(e)[:100]
                print(f"❌ 解析错误: {str(e)[:30]}")
                failed_sources.append(name)
        else:
            log_entry["status"] = "FETCH_ERROR"
            print(f"❌ 失败: {error_msg[:30]}")
            failed_sources.append(name)

        log_entries.append(log_entry)

    # 生成日志文件
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"RSS 源验证报告\n")
        f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"📊 统计摘要\n")
        f.write(f"{'='*80}\n")
        f.write(f"总计源数: {len(sources)}\n")
        f.write(f"成功: {len(success_sources)} ({len(success_sources)/len(sources)*100:.1f}%)\n")
        f.write(f"失败: {len(failed_sources)} ({len(failed_sources)/len(sources)*100:.1f}%)\n")
        f.write(f"为空: {len(empty_sources)} ({len(empty_sources)/len(sources)*100:.1f}%)\n\n")

        # 成功列表
        f.write(f"✅ 成功的源 ({len(success_sources)}个)\n")
        f.write(f"{'-'*80}\n")
        for name in success_sources:
            f.write(f"  • {name}\n")
        f.write("\n")

        # 失败列表
        if failed_sources:
            f.write(f"❌ 失败的源 ({len(failed_sources)}个)\n")
            f.write(f"{'-'*80}\n")
            for name in failed_sources:
                f.write(f"  • {name}\n")
            f.write("\n")

        # 为空列表
        if empty_sources:
            f.write(f"⚠️  为空的源 ({len(empty_sources)}个)\n")
            f.write(f"{'-'*80}\n")
            for name in empty_sources:
                f.write(f"  • {name}\n")
            f.write("\n")

        # 详细结果
        f.write(f"📋 详细结果\n")
        f.write(f"{'='*80}\n\n")

        for entry in log_entries:
            f.write(f"源名称: {entry['name']}\n")
            f.write(f"  URL/路由: {entry['target']}\n")
            f.write(f"  策略: {entry['strategy']}\n")
            f.write(f"  状态: {entry['status']}\n")

            if entry['status'] == 'SUCCESS':
                f.write(f"  文章数: {entry['count']}\n")
                f.write(f"  最新标题: {entry['latest_title']}\n")
                f.write(f"  发布日期: {entry['latest_date']}\n")
            else:
                f.write(f"  错误信息: {entry['error']}\n")

            f.write("\n" + "-" * 80 + "\n\n")

    print("-" * 80)
    print(f"📊 最终统计: {len(success_sources)}/{len(sources)} 个源采集成功")
    print(f"📝 详细日志已保存到: {log_file}")

    # 按类别统计
    print("\n📈 分类统计:")
    twitter_count = sum(1 for s in sources if 'twitter' in s[2].lower() or '/twitter/' in s[1])
    blog_count = sum(1 for s in sources if s[2] in ['direct', 'cffi'] and 'localhost' not in s[1])
    wechat_count = sum(1 for s in sources if 'localhost' in s[1])
    chinese_rss = sum(1 for s in sources if s[2] == 'rsshub' and '/twitter/' not in s[1])

    print(f"  Twitter/X: {twitter_count}个")
    print(f"  国际博客: {blog_count}个")
    print(f"  中文RSS: {chinese_rss}个")
    print(f"  微信公众号: {wechat_count}个")

if __name__ == "__main__":
    main()
