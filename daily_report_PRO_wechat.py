"""
AI 日报生成器 - 微信公众号版本

主要功能：
1. 从多个 RSS 源采集 AI 行业新闻
2. 使用智能排序系统筛选重要文章
3. 通过 DeepSeek AI 分析并生成 HTML 格式报告
4. 发布到微信公众号草稿箱

Author: AI-RSS-PERSON Team
Version: 2.0.0
"""

import os
import sys
import datetime
import time
import logging
from pathlib import Path
from openai import OpenAI

# 导入共享工具
from dotenv import load_dotenv

# 导入 core/utils 工具
from core.utils import setup_logger, get_required_env, get_optional_env, get_int_env, CostTracker
from core.utils.constants import *

# 导入 lib 模块
from lib.rss_collector import RSSCollector, DEFAULT_SOURCES
from lib.publishers.local_publisher import LocalPublisher
from wechat_publisher import WeChatAuto
from article_ranker import ArticleRanker

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

# 初始化日志
logger = setup_logger(level=LOG_LEVEL)


# ================= 🤖 AI 日报生成器 =================
class AI_Daily_Report:
    """AI 日报生成器主类 - 微信公众号版本"""

    # RSS 源配置
    SOURCES = [
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
        {"name": "Gizmodo",            "url": "https://gizmodo.com/feed", "strategy": "cffi"},
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

    def __init__(self):
        """初始化 AI 日报生成器"""
        # 验证 API 密钥
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY.startswith("your_"):
            raise ValueError("❌ DeepSeek API Key 未配置！请在 .env 文件中设置 DEEPSEEK_API_KEY")

        # 初始化组件
        self.ranker = ArticleRanker()
        self.cost_tracker = CostTracker()
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

        # 初始化 RSS 收集器
        self.collector = RSSCollector(
            sources=self.SOURCES,
            proxy_url=PROXY_URL,
            max_items_per_source=MAX_ITEMS_PER_SOURCE,
            time_window_hours=24
        )

        # 初始化本地发布器
        self.local_publisher = LocalPublisher(output_dir=OUTPUT_DIR)

        # 代理配置日志
        if PROXY_URL:
            logger.info(f"✅ 代理已配置: {PROXY_URL}")
        else:
            logger.info("ℹ️ 未配置代理，使用直连")

    def analyze_with_ai(self, item):
        """使用 AI 分析文章（微信专用版本，生成 HTML 格式）

        Args:
            item: 文章字典，包含 title, summary, source, link

        Returns:
            str: HTML 格式的分析结果
        """

        prompt = f"""
        你是一位服务于顶级投资机构和科技高管的【AI情报分析师】。你的任务是撰写《全球AI内参》。
        受众时间宝贵，他们不需要普通的新闻资讯，而是需要能辅助决策的【高价值情报】。

        输入信息：
        - 来源：{item['source']}
        - 标题：{item['title']}
        - 摘要：{item['summary']}

        请按照以下"内参标准"输出 HTML 格式内容：

        1.  **<h3>标题</h3>**：
            * 风格：极度冷静、专业。禁止使用感叹号。禁止使用"震惊"、"重磅"等营销词汇。
            * 结构：核心事件 + 关键数据/核心影响。
            * 字数：30字以内

        2.  **<p>【情报速递】</p>**：
            * 用最精炼的语言概括事实（Fact）。
            * 必须包含具体的数字（如参数量、融资金额、性能提升百分比），去除所有形容词。

        3.  **<p>【深度研判】（关键部分）</p>**：
            * 不要复述新闻。请分析该事件背后的**"信号"**。
            * 思考维度（任选其一）：
                * **商业竞争**：这动了谁的蛋糕？（如：对 Google 搜索广告业务的潜在威胁）
                * **技术落地**：真正的瓶颈在哪里？（如：算力成本、数据隐私合规）
                * **长期趋势**：这是泡沫还是范式转移？
            * 字数：150字左右，直击要害。

        输出示例：
        <h3>Anthropic 发布 Claude 3.5：代码能力超越 GPT-4o，价格下调 20%</h3>
        <p><strong>【情报速递】</strong>Anthropic 今日发布 Claude 3.5 Sonnet。基准测试显示，其在 HumanEval 代码生成任务中得分 92.0%，略高于 GPT-4o 的 90.2%。同时，API 调用价格较上一代 Opis 模型下调 20%，推理速度提升 2 倍。</p>
        <p><strong>【深度研判】</strong>此举标志着大模型价格战进入白热化阶段。Claude 3.5 在"代码与逻辑"细分领域的特定优势，将直接冲击 GitHub Copilot 等辅助编程工具的市场格局。对于开发者而言，目前是混合使用模型的最佳窗口期，建议在代码生成场景优先切换至 Claude 3.5 以降低 Token 成本。</p>
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                timeout=30
            )
            self.cost_tracker.add(response.usage)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI分析失败: {item['title'][:50]}..., 错误: {str(e)[:100]}")
            return f"<p>❌ AI 分析失败: {str(e)[:50]}</p>"

    def save_to_local(self, html_content, date_str, digest_text):
        """保存 HTML 内容到本地文件

        Args:
            html_content: HTML格式的内容
            date_str: 日期字符串
            digest_text: 摘要文本

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            # 保存 HTML 文件
            html_filename = f"AI_Daily_{date_str}.html"
            html_path = self.local_publisher.save_html(html_content, html_filename)

            # 保存纯文本摘要
            txt_content = f"全球AI日报 | {date_str}\n"
            txt_content += f"{'='*50}\n\n"
            txt_content += f"摘要:\n{digest_text}\n\n"
            txt_content += f"{'='*50}\n\n"
            txt_content += f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            txt_filename = f"AI_Daily_{date_str}_digest.txt"
            txt_path = self.local_publisher.save_text(txt_content, txt_filename)

            return True
        except Exception as e:
            logger.error(f"❌ 保存本地文件失败: {e}")
            return False

    def run(self):
        """运行日报生成流程"""
        try:
            # 1. 采集 RSS 文章
            logger.info("🚀 启动采集 (过去24小时) ...")
            items = self.collector.collect_all()

            if not items:
                logger.warning("❌ 过去24小时内没有新资讯，任务结束。")
                return

            # 2. 智能排序并限制数量
            logger.info(f"\n📊 开始智能排序 (共 {len(items)} 条文章)...")
            ranked_items = self.ranker.rank_articles(items, top_n=MAX_ARTICLES_IN_REPORT)

            # 打印排序统计
            logger.info(f"\n{self.ranker.get_ranking_summary(ranked_items)}")

            # 3. AI 处理 - 生成微信 HTML 格式
            logger.info(f"\n🤖 开始 AI 分析 (Top {len(ranked_items)} 条)...")
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

            # === 微信专用 HTML 样式 ===
            wechat_html = f"""
            <section style="font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif; letter-spacing: 0.544px; text-align: justify;">
                <section style="margin-bottom: 20px; text-align: center;">
                    <h1 style="font-size: 22px; font-weight: bold; color: #333;">🌍 全球AI日报 | {date_str}</h1>
                    <p style="font-size: 14px; color: #888;">AI驱动的行业情报精选</p>
                </section>

                <!-- 导读 -->
                <section style="margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border-radius: 10px; border-left: 4px solid #667eea;">
                    <p style="font-size: 15px; line-height: 1.8; color: #555; margin: 0;">
                        <strong style="color: #667eea;">📰 本期导读</strong><br><br>
                        本日报从全球150+权威信源中智能筛选出最重要的{len(ranked_items)}条AI行业资讯，涵盖技术突破、产品发布、融资动态和行业洞察。我们通过多维度评分系统（来源权威性60% + 内容相关性40%），确保您只阅读最有价值的内容。
                    </p>
                </section>
            """

            digest_text = ""  # 摘要文本

            for i, item in enumerate(ranked_items, 1):
                logger.info(f"[{i}/{len(ranked_items)}] 处理: {item['title'][:30]}... (得分: {item['score']:.1f})")
                ai_result = self.analyze_with_ai(item)

                # 拼接摘要 (取前两条新闻的标题作为封面摘要)
                if i <= 2:
                    digest_text += f"{i}. {item['title']}\n"

                # 添加原文链接
                original_link = item.get('link', '#')

                wechat_html += f"""
                <section style="margin-bottom: 30px; padding: 20px; background-color: #f7f7f7; border-radius: 10px;">
                    {ai_result}
                    <section style="margin-top: 15px; font-size: 12px; color: #999;">
                        🔗 来源: {item['source']}<br>
                        🔗 原文链接: <a href="{original_link}" style="color: #667eea;">点击阅读</a>
                    </section>
                </section>
                """
                time.sleep(1)

            # 添加结语
            wechat_html += f"""
                <!-- 结语 -->
                <section style="margin-top: 40px; padding: 20px; background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border-radius: 10px; border-right: 4px solid #667eea;">
                    <p style="font-size: 15px; line-height: 1.8; color: #555; margin: 0; text-align: center;">
                        <strong style="color: #667eea;">💡 关于本日报</strong><br><br>
                        我们持续追踪全球AI领域动态，通过智能排序和AI分析，为您提炼最值得关注的行业情报。如果您觉得有价值，欢迎分享给更多人。<br><br>
                        <span style="font-size: 13px; color: #999;">数据来源: OpenAI、Google DeepMind、Anthropic等150+权威信源 | 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                    </p>
                </section>
            """

            # 4. 保存到本地文件
            logger.info("\n💾 正在保存到本地文件...")
            self.save_to_local(wechat_html, date_str, digest_text)

            # 5. 发布到微信
            logger.info("\n🚀 正在发布到微信公众号...")
            wx = WeChatAuto()
            if wx.client:
                # 假设封面图 cover.png 在当前目录下，如果不存在需处理异常
                try:
                    mid = wx.upload_cover("cover.png")
                    if mid:
                        wx.upload_draft(
                            title=f"全球AI日报 | {date_str}",
                            author="AI助手",
                            html_content=wechat_html,
                            digest=digest_text,
                            media_id=mid
                        )
                        logger.info("✅ 微信草稿已创建")
                except Exception as e:
                    logger.error(f"❌ 微信发布失败: {e}")

            # 打印成本报告
            logger.info(self.cost_tracker.report())

        except Exception as e:
            logger.error(f"❌ 运行出错: {e}")
            raise


if __name__ == "__main__":
    try:
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
