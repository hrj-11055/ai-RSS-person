import feedparser
import requests
import os
import smtplib
import datetime
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, parsedate_to_datetime # 引入时间解析工具
from openai import OpenAI

# ================= 🔧 用户配置区域 =================

# 1. DeepSeek 配置
DEEPSEEK_API_KEY = "sk-ce0851ae8faa4f29a3ecc7281e05b81d"  # 替换这里
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 2. 邮箱发送配置 (SMTP)
SMTP_SERVER = "smtp.qq.com"      # 例如: smtp.qq.com, smtp.163.com, smtp.gmail.com
SMTP_PORT = 465                  # SSL端口通常是 465
SENDER_EMAIL = "1415994589@qq.com"   # 发件人邮箱
SENDER_PASSWORD = "rhxqbetoaoqwbacf"       # ⚠️ 注意：这里填授权码，不是登录密码
RECEIVER_EMAIL = "19927570442@139.com" # 收件人邮箱 (可以是同一个)

# 3. 网络代理
PROXY_URL = "http://127.0.0.1:7897"

# 4. RSSHub配置（用于Twitter等需要RSSHub的源）
RSSHUB_HOST = "http://localhost:1200"  # 你的 Docker RSSHub 地址

# 5. 抓取设置
MAX_ITEMS_PER_SOURCE = 1

# 6. 本地保存目录配置
OUTPUT_DIR = "reports"  # HTML 报告保存目录 

# ================= 💰 计费模块 =================
class CostTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.price_input = 2.0   # 输入: ¥2/百万tokens (约 $0.28)
        self.price_output = 3.0  # 输出: ¥3/百万tokens (约 $0.42) 

    def add(self, usage):
        if usage:
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens

    def report(self):
        cost = (self.total_input_tokens / 1_000_000 * self.price_input) + \
               (self.total_output_tokens / 1_000_000 * self.price_output)
        return f"📊 本次消耗: 输入 {self.total_input_tokens} | 输出 {self.total_output_tokens} | 费用: ¥{cost:.5f}"

# ================= 📧 邮件模块 (已修复) =================
def send_email(subject, html_content):
    print("📧 正在发送邮件...")
    try:
        message = MIMEMultipart()
        # 修复发件人格式
        message['From'] = formataddr(["AI日报助手", SENDER_EMAIL])
        message['To'] = formataddr(["订阅者", RECEIVER_EMAIL])
        message['Subject'] = Header(subject, 'utf-8')
        message.attach(MIMEText(html_content, 'html', 'utf-8'))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# ================= 🤖 核心逻辑 =================
class AI_Daily_Report:
    def __init__(self):
        self.proxies = {"http": PROXY_URL, "https": PROXY_URL}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        self.tracker = CostTracker()
        
        # 稳过的信源列表 (已移除 MIT, Ars, Gradient)
        # 数据源列表
        self.sources = [
            # --- 🐦 Twitter/X 官方机构账号 (通过RSSHub) ---
            {"name": "OpenAI Twitter",     "url": "/twitter/user/OpenAI", "strategy": "rsshub"},
            {"name": "Google DeepMind",    "url": "/twitter/user/GoogleDeepMind", "strategy": "rsshub"},
            {"name": "Anthropic AI",       "url": "/twitter/user/AnthropicAI", "strategy": "rsshub"},
            {"name": "DeepSeek AI",        "url": "/twitter/user/deepseek_ai", "strategy": "rsshub"},
            {"name": "Alibaba Qwen",       "url": "/twitter/user/Alibaba_Qwen", "strategy": "rsshub"},

            # --- 🐦 Twitter/X AI领袖账号 (通过RSSHub) ---
            {"name": "Sam Altman",         "url": "/twitter/user/sama", "strategy": "rsshub"},
            {"name": "Geoffrey Hinton",    "url": "/twitter/user/geoffreyhinton", "strategy": "rsshub"},
            {"name": "Yann LeCun",         "url": "/twitter/user/ylecun", "strategy": "rsshub"},
            {"name": "Yoshua Bengio",      "url": "/twitter/user/Yoshua_Bengio", "strategy": "rsshub"},
            {"name": "Demis Hassabis",     "url": "/twitter/user/demishassabis", "strategy": "rsshub"},
            {"name": "Andrew Ng",          "url": "/twitter/user/AndrewYNg", "strategy": "rsshub"},
            {"name": "Jim Fan",            "url": "/twitter/user/drjimfan", "strategy": "rsshub"},
            {"name": "Lex Fridman",        "url": "/twitter/user/lexfridman", "strategy": "rsshub"},

            # --- 📰 MIT/学术 (通过RSSHub) ---
            {"name": "MIT AI News",        "url": "/mit/news/AI", "strategy": "rsshub"},

            # --- 📰 传统RSS源 ---
            {"name": "OpenAI Blog",        "url": "https://openai.com/news/rss.xml", "strategy": "direct"},
            {"name": "Google AI Blog",     "url": "https://blog.google/technology/ai/rss/", "strategy": "direct"},
            {"name": "Google DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "strategy": "direct"},
            {"name": "Google Research",    "url": "https://research.google/blog/rss", "strategy": "direct"},
            {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed", "strategy": "direct"},
            {"name": "Hugging Face",       "url": "https://huggingface.co/blog/feed.xml", "strategy": "direct"},
            {"name": "NVIDIA Research",    "url": "https://blogs.nvidia.com/blog/category/nvidia-research/feed", "strategy": "direct"},
            {"name": "NVIDIA Blog",        "url": "https://blogs.nvidia.com/feed", "strategy": "direct"},
            {"name": "AWS ML Blog",        "url": "https://aws.amazon.com/blogs/machine-learning/feed", "strategy": "direct"},
            {"name": "TechCrunch AI",      "url": "https://techcrunch.com/category/artificial-intelligence/feed", "strategy": "direct"},
            {"name": "TechCrunch",         "url": "https://techcrunch.com/feed", "strategy": "direct"},
            {"name": "The Verge AI",       "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "strategy": "direct"},
            {"name": "The Verge",          "url": "https://www.theverge.com/rss/index.xml", "strategy": "direct"},
            {"name": "Wired",              "url": "https://www.wired.com/feed/rss", "strategy": "direct"},
            {"name": "Digital Trends",     "url": "https://www.digitaltrends.com/feed", "strategy": "direct"},
            {"name": "Gizmodo",            "url": "https://gizmodo.com/feed", "strategy": "cffi"},  # 需要cffi
            {"name": "Science Daily AI",   "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "strategy": "direct"},
            {"name": "Towards AI",         "url": "https://towardsai.net/feed", "strategy": "direct"},
            {"name": "Jack Clark",         "url": "https://jack-clark.net/feed", "strategy": "direct"},
            {"name": "AI News",            "url": "https://www.artificialintelligence-news.com/feed", "strategy": "cffi"},
            {"name": "AI Business",        "url": "https://aibusiness.com/rss.xml", "strategy": "direct"},
            {"name": "AI Weekly",          "url": "https://aiweekly.co/issues.rss", "strategy": "direct"},
            {"name": "Beehiiv AI",         "url": "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml", "strategy": "direct"},
            {"name": "The Gradient",       "url": "https://thegradient.pub/rss", "strategy": "direct"},

            # --- 🎓 学术网站 (不走代理) ---
            {"name": "Arxiv AI",           "url": "https://arxiv.org/rss/cs.AI", "strategy": "noproxy"},

            # --- 📰 中文RSS源 (通过RSSHub) ---
            {"name": "36氪 AI",            "url": "/36kr/information/AI", "strategy": "rsshub"},
            {"name": "InfoQ AI",           "url": "/infoq/topic/AI&LLM", "strategy": "rsshub"},

            # --- 📱 微信公众号 (通过 wewe-rss) ---
            {"name": "机器之心",           "url": "http://localhost:4000/feeds/MP_WXS_3073282833.atom", "strategy": "direct"},
            {"name": "数字生命卡兹克",     "url": "http://localhost:4000/feeds/MP_WXS_3223096120.atom", "strategy": "direct"},
            {"name": "夕小瑶科技说",       "url": "http://localhost:4000/feeds/MP_WXS_3207765945.atom", "strategy": "direct"},
            {"name": "新智元",             "url": "http://localhost:4000/feeds/MP_WXS_3271041950.atom", "strategy": "direct"},
            {"name": "AI前线",             "url": "http://localhost:4000/feeds/MP_WXS_3554086560.atom", "strategy": "direct"},
            {"name": "APPSO",              "url": "http://localhost:4000/feeds/MP_WXS_2392024520.atom", "strategy": "direct"},
            {"name": "智东西",             "url": "http://localhost:4000/feeds/MP_WXS_3081486433.atom", "strategy": "direct"},
            {"name": "量子位",             "url": "http://localhost:4000/feeds/MP_WXS_3236757533.atom", "strategy": "direct"},
            {"name": "Founder Park",       "url": "http://localhost:4000/feeds/MP_WXS_3895742803.atom", "strategy": "direct"},
            {"name": "赛博禅心",           "url": "http://localhost:4000/feeds/MP_WXS_3934419561.atom", "strategy": "direct"},
            {"name": "GitHubDaily",        "url": "http://localhost:4000/feeds/MP_WXS_3019715205.atom", "strategy": "direct"},
            {"name": "阿里技术",           "url": "http://localhost:4000/feeds/MP_WXS_3885737868.atom", "strategy": "direct"},
            {"name": "特工宇宙",           "url": "http://localhost:4000/feeds/MP_WXS_3621654047.atom", "strategy": "direct"},
            {"name": "AI科技评论",         "url": "http://localhost:4000/feeds/MP_WXS_3098132220.atom", "strategy": "direct"},
            {"name": "深科技",             "url": "http://localhost:4000/feeds/MP_WXS_3218265689.atom", "strategy": "direct"},
        ]

        # 导入 curl_cffi
        try:
            from curl_cffi import requests as cffi_requests
            self.cffi_requests = cffi_requests
        except ImportError:
            self.cffi_requests = None

    def is_within_24h(self, entry):
        """判断新闻是否在过去24小时内发布"""
        try:
            # feedparser 通常会提供 published_parsed (struct_time)
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                # 转换为 datetime 对象
                pub_time = datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed))
                # 获取当前时间
                now = datetime.datetime.now()
                # 计算差值
                delta = now - pub_time
                # 如果时间差在 0 到 24 小时之间 (防止时区导致的未来时间，以及过滤掉太旧的)
                if delta.total_seconds() <= 24 * 3600 and delta.total_seconds() >= -3600: 
                    return True
                else:
                    return False
            
            # 如果没有标准时间字段，尝试兜底 (有些源可能结构不同，这里简单处理：默认保留)
            # 或者你可以选择默认不保留：return False
            return True 
        except Exception:
            return True # 解析失败时，为了不漏消息，通常选择保留

    def fetch_rss(self):
        print(f"🚀 启动采集 (过去24小时) ...")
        collected_items = []
        for source in self.sources:
            print(f"📡 扫描: {source['name']} ... ", end="", flush=True)
            try:
                url = source['url']
                strategy = source.get('strategy', 'direct')  # 默认 direct

                # 根据策略选择请求方式
                if strategy == "rsshub":
                    # RSSHub路由
                    url = f"{RSSHUB_HOST}{url}"
                    resp = requests.get(url, timeout=30)
                elif strategy == "cffi" and self.cffi_requests:
                    # 使用 curl_cffi 模拟浏览器
                    resp = self.cffi_requests.get(
                        url,
                        proxies=self.proxies,
                        impersonate="edge101",
                        timeout=30
                    )
                    # 转换为标准 requests.Response 对象
                    class MockResponse:
                        def __init__(self, content):
                            self.content = content
                            self.status_code = 200
                    resp = MockResponse(resp.content)
                elif strategy == "noproxy":
                    # 不走代理直连
                    resp = requests.get(url, headers=self.headers, timeout=15)
                else:
                    # 默认走代理
                    resp = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=15)

                feed = feedparser.parse(resp.content)

                if len(feed.entries) > 0:
                    # 获取前 N 条候选
                    candidates = feed.entries[:MAX_ITEMS_PER_SOURCE]
                    valid_count = 0

                    for entry in candidates:
                        # --- 核心过滤逻辑 ---
                        if self.is_within_24h(entry):
                            collected_items.append({
                                "source": source['name'],
                                "title": entry.title,
                                "link": entry.link,
                                "summary": entry.get('summary', entry.get('description', ''))[:1000]
                            })
                            valid_count += 1

                    print(f"✅ 发现 {len(candidates)} 条，入选 {valid_count} 条 (24h内)")
                else:
                    print(f"⚠️ 源为空")
            except Exception as e:
                print(f"❌ 错: {str(e)[:20]}")
        return collected_items

    def analyze_with_ai(self, item):
        prompt = f"""
        你是一份《全球AI内参》的主编。请将以下新闻改写为中文快讯。

        来源：{item['source']}
        标题：{item['title']}
        摘要：{item['summary']}

        要求：
        1. 【中文标题】：吸引人且准确。
        2. 【摘要】：150字以内，总结文章内容，在结尾一针见血指出影响或价值。不需要任何说明文字。
        3. 格式：HTML格式，使用 <h3> 标题，<p> 正文。
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            self.tracker.add(response.usage)
            return response.choices[0].message.content
        except Exception as e:
            return f"<p>❌ AI 分析失败: {e}</p>"

    def save_to_local(self, html_content, date_str, digest_text):
        """保存 HTML 内容到本地文件"""
        try:
            # 确保输出目录存在
            os.makedirs(OUTPUT_DIR, exist_ok=True)

            # 生成文件名
            html_filename = f"{OUTPUT_DIR}/AI_Daily_{date_str}_email.html"
            txt_filename = f"{OUTPUT_DIR}/AI_Daily_{date_str}_digest.txt"

            # 保存 HTML 文件
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML 已保存到: {html_filename}")

            # 保存纯文本摘要
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"全球AI日报 | {date_str}\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"摘要:\n{digest_text}\n\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(f"✅ 摘要已保存到: {txt_filename}")

            return True
        except Exception as e:
            print(f"❌ 保存本地文件失败: {e}")
            return False

    def run(self):
        # 1. 采集 (带时间过滤)
        items = self.fetch_rss()
        if not items:
            print("❌ 过去24小时内没有新资讯，任务结束。")
            return

        # 2. AI 处理
        print(f"\n🤖 开始 AI 分析 ({len(items)} 条)...")
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

        # 邮件专用 HTML 样式
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif;">
            <h1 style="color: #333;">🌍 全球AI日报 | {date_str}</h1>
            <p style="color: #666;">DeepSeek 智能筛选与点评 - 精选过去24小时高价值资讯</p>
            <hr>
        </div>
        """

        digest_text = ""  # 摘要文本

        for i, item in enumerate(items, 1):
            print(f"[{i}/{len(items)}] 处理: {item['title'][:30]}...")
            ai_result = self.analyze_with_ai(item)

            # 拼接摘要 (取前两条新闻的标题作为摘要)
            if i <= 2:
                digest_text += f"{i}. {item['title']}\n"

            html_body += f"""
            <div style='margin-bottom: 25px; padding: 20px; background-color: #f7f7f7; border-radius: 10px;'>
                {ai_result}
                <div style='margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0;'>
                    <p style='font-size: 12px; color: #666; margin: 0 0 8px 0;'>📰 来源: {item['source']}</p>
                    <a href='{item['link']}' target='_blank' style='display: inline-block; padding: 8px 16px; background-color: #007AFF; color: white; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 500;'>📖 阅读原文 →</a>
                </div>
            </div>
            """
            time.sleep(1)

        # 添加计费信息
        usage_report = self.tracker.report()
        html_body += f"<hr><p style='color: gray; font-size: 12px;'>{usage_report}</p>"

        print("\n" + "="*50)
        print(usage_report)
        print("="*50)

        # 3. 保存到本地文件
        print("\n💾 正在保存到本地文件...")
        self.save_to_local(html_body, date_str, digest_text)

        # 4. 发送邮件
        print("\n📧 正在发送邮件...")
        send_email(f"🚀 AI日报 ({date_str}) - {len(items)}条精选", html_body)

if __name__ == "__main__":
    bot = AI_Daily_Report()
    bot.run()