"""
报告生成模块

从分析后的文章生成 Markdown 和 JSON 报告。

Author: AI-RSS-PERSON Team
Version: 2.0.0
"""

import datetime
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Import shared utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import setup_logger, get_optional_env
from core.utils.constants import (
    DEFAULT_OUTPUT_DIR,
    DATETIME_FORMAT,
    FILENAME_DATETIME_FORMAT,
)

# Configuration
OUTPUT_DIR = get_optional_env("OUTPUT_DIR", DEFAULT_OUTPUT_DIR)

# Setup logger
logger = setup_logger(__name__, get_optional_env("LOG_LEVEL", "INFO"))


# HTML Template
DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .intro {{
            padding: 30px 40px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            margin: 30px 40px;
            border-radius: 0 8px 8px 0;
        }}
        .article {{
            padding: 30px 40px;
            border-bottom: 1px solid #eee;
        }}
        .article:last-child {{
            border-bottom: none;
        }}
        .article h3 {{
            color: #667eea;
            font-size: 22px;
            margin-bottom: 15px;
            line-height: 1.4;
        }}
        .article-meta {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            font-size: 13px;
            color: #888;
        }}
        .article-meta .badge {{
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
        }}
        .article-content {{
            color: #555;
            line-height: 1.8;
        }}
        .article-content strong {{
            color: #333;
            font-weight: 600;
        }}
        .article-footer {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px dashed #ddd;
            font-size: 13px;
            color: #888;
        }}
        .article-footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        .article-footer a:hover {{
            text-decoration: underline;
        }}
        .outro {{
            padding: 30px 40px;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            text-align: center;
            color: #555;
        }}
        @media (max-width: 768px) {{
            .container {{ margin: 0; border-radius: 0; }}
            .header, .intro, .article, .outro {{ padding: 20px; }}
        }}
        @media (prefers-color-scheme: dark) {{
            body {{ background: #1a1a2e; }}
            .container {{
                background: #16213e;
                color: #eaeaea;
            }}
            .intro {{ background: #1a1a2e; color: #ccc; }}
            .article {{ border-bottom-color: #333; }}
            .article h3 {{ color: #a29bfe; }}
            .article-content {{ color: #ccc; }}
            .article-content strong {{ color: #fff; }}
            .article-footer {{ color: #888; border-top-color: #444; }}
            .outro {{ color: #ccc; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report_title}</h1>
            <p class="subtitle">{report_subtitle} | {report_date}</p>
        </div>

        <div class="intro">
            <p><strong>📰 本期导读</strong></p>
            <p>本日报从全球150+权威信源中智能筛选出最重要的 <strong>{total_articles}</strong> 条AI行业资讯。</p>
            <p style="margin-top: 10px; font-size: 14px; color: #888;">生成时间: {generated_at}</p>
        </div>

        {articles_html}

        <div class="outro">
            <p><strong>💡 关于本日报</strong></p>
            <p>我们持续追踪全球AI领域动态，通过智能排序和AI分析，为您提炼最值得关注的行业情报。</p>
            <p style="margin-top: 15px; font-size: 13px; color: #888;">Powered by AI-RSS-PERSON v2.0</p>
        </div>
    </div>
</body>
</html>
"""


class ReportGenerator:
    """
    从分析后的文章生成报告。

    主要支持 Markdown 和 JSON 输出格式，HTML 为可选格式。

    示例：
        >>> generator = ReportGenerator()
        >>> md = generator.generate_markdown(articles)
        >>> json_path = generator.save_json(articles)
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化报告生成器。

        参数：
            output_dir: 保存报告的目录（默认为 OUTPUT_DIR 环境变量）
        """
        self.output_dir = Path(output_dir or OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html(
        self,
        articles: List[Dict],
        title: str = None,
        date_str: str = None
    ) -> str:
        """
        从分析后的文章生成 HTML 报告。

        参数：
            articles: 分析后的文章字典列表
            title: 报告标题（未提供则自动生成）
            date_str: 报告日期字符串（未提供则自动生成）

        返回：
            生成的 HTML 内容

        示例：
            >>> generator = ReportGenerator()
            >>> html = generator.generate_html(articles)
            >>> with open("report.html", "w") as f:
            ...     f.write(html)
        """
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

        if not title:
            title = f"🌍 全球AI日报 | {date_str}"

        # 生成文章 HTML
        articles_html = self._generate_articles_html(articles)

        # 构建报告
        generated_at = datetime.datetime.now().strftime(DATETIME_FORMAT)
        html = DEFAULT_HTML_TEMPLATE.format(
            report_title=title,
            report_subtitle="AI驱动的行业情报精选",
            report_date=date_str,
            total_articles=len(articles),
            generated_at=generated_at,
            articles_html=articles_html
        )

        return html

    def generate_markdown(
        self,
        articles: List[Dict],
        title: str = None,
        date_str: str = None
    ) -> str:
        """
        生成 Markdown 报告（默认主要格式）。

        参数：
            articles: 分析后的文章字典列表
            title: 报告标题（未提供则自动生成）
            date_str: 报告的日期字符串（未提供则自动生成）

        返回：
            生成的 Markdown 内容
        """
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

        if not title:
            title = f"🌍 全球AI日报 | {date_str}"

        lines = [
            f"# {title}",
            f"",
            f"**AI驱动的行业情报精选** | {date_str}",
            f"",
            f"## 📰 本期导读",
            f"",
            f"本日报从全球150+权威信源中智能筛选出最重要的 **{len(articles)}** 条AI行业资讯。",
            f"",
            f"---",
            f"",
        ]

        for i, article in enumerate(articles, 1):
            lines.extend([
                f"## {i}. {article.get('title', 'Unknown')}",
                f"",
                f"**来源**: {article.get('source_name', 'Unknown')} | ",
                f"**分类**: {article.get('category', '未分类')} / {article.get('sub_category', '未分类')} | ",
                f"**重要性**: {'⭐' * min(article.get('importance_score', 5) // 2, 5)}",
                f"",
                f"### 📌 要点",
                f"",
                article.get('key_point', 'N/A'),
                f"",
                f"### 📝 深度摘要",
                f"",
                article.get('summary', 'N/A'),
                f"",
                f"**🔗 原文链接**: [点击阅读]({article.get('source_url', '#')})",
                f"",
                f"---",
                f"",
            ])

        lines.extend([
            f"## 💡 关于本日报",
            f"",
            f"我们持续追踪全球AI领域动态，通过智能排序和AI分析，为您提炼最值得关注的行业情报。",
            f"",
            f"*Powered by AI-RSS-PERSON v2.0*",
        ])

        return "\n".join(lines)

    def _generate_articles_html(self, articles: List[Dict]) -> str:
        """
        Generate HTML for all articles.

        Args:
            articles: List of analyzed article dictionaries

        Returns:
            HTML string for all articles
        """
        html_parts = []

        for article in articles:
            html_parts.append(self._generate_article_html(article))

        return "\n".join(html_parts)

    def _generate_article_html(self, article: Dict) -> str:
        """
        Generate HTML for a single article.

        Args:
            article: Analyzed article dictionary

        Returns:
            HTML string for the article
        """
        # Escape HTML in text content
        title = self._escape_html(article.get('title', 'Unknown'))
        key_point = self._escape_html(article.get('key_point', ''))
        summary = self._escape_html(article.get('summary', ''))
        source_url = article.get('source_url', '#')
        source_name = self._escape_html(article.get('source_name', 'Unknown'))
        category = self._escape_html(article.get('category', '未分类'))
        sub_category = self._escape_html(article.get('sub_category', '未分类'))
        importance_score = article.get('importance_score', 5)

        # Format key_point with strong tags
        key_point_html = f"<strong>速览：</strong>{key_point}"

        # Format summary with paragraphs
        summary_html = summary.replace('\n\n', '</p><p>').replace('\n', '<br>')
        summary_html = f"<p><strong>深度分析：</strong>{summary_html}</p>"

        html = f"""
        <div class="article">
            <h3>{title}</h3>
            <div class="article-meta">
                <span class="badge">{category}</span>
                <span class="badge">{sub_category}</span>
                <span>重要性: {'⭐' * min(importance_score // 2, 5)}</span>
            </div>
            <div class="article-content">
                {key_point_html}
                {summary_html}
            </div>
            <div class="article-footer">
                🔗 来源: {source_name} | <a href="{source_url}" target="_blank">点击阅读原文</a>
            </div>
        </div>
        """

        return html

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def save_html(
        self,
        articles: List[Dict],
        filename: str = None
    ) -> str:
        """
        生成并保存 HTML 报告到文件（可选格式）。

        参数：
            articles: 分析后的文章字典列表
            filename: 输出文件名（自动生成如果未提供）

        返回：
            路径到保存的文件
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime(FILENAME_DATETIME_FORMAT)
            filename = f"AI_Daily_Report_{timestamp}.html"

        html = self.generate_html(articles)
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"✅ HTML report saved: {filepath}")
        return str(filepath)

    def save_markdown(
        self,
        articles: List[Dict],
        filename: str = None
    ) -> str:
        """
        生成并保存 Markdown 报告到文件（使用 YYYY-MM-DD.md 格式）。

        参数：
            articles: 分析后的文章字典列表
            filename: 输出文件名（未提供则使用 YYYY-MM-DD.md 格式）

        返回:
            路径到保存的文件
        """
        if not filename:
            # 使用 YYYY-MM-DD.md 格式
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            filename = f"{date_str}.md"

        md = self.generate_markdown(articles)
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)

        logger.info(f"✅ Markdown report saved: {filepath}")
        return str(filepath)

    def save_default(
        self,
        articles: List[Dict],
        markdown_filename: str = None,
        json_filename: str = None
    ) -> Dict[str, str]:
        """
        保存默认格式报告（Markdown + JSON）。

        参数：
            articles: 分析后的文章字典列表
            markdown_filename: Markdown 文件名（未提供则使用 YYYY-MM-DD.md 格式）
            json_filename: JSON 文件名（未提供则使用 YYYY-MM-DD.json 格式）

        返回：
            包含两个文件路径的字典：{"markdown": path, "json": path}
        """
        paths = {}

        # 保存 Markdown（主要格式）
        md_path = self.save_markdown(articles, markdown_filename)
        paths["markdown"] = md_path

        # 保存 JSON（用于网站集成）
        if not json_filename:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            json_filename = f"{date_str}.json"
        json_path = self.save_json(articles, date_str=datetime.datetime.now().strftime("%Y-%m-%d"), filename=json_filename)
        paths["json"] = json_path

        logger.info(f"✅ 默认格式保存完成: Markdown + JSON")
        return paths


if __name__ == "__main__":
    # Test mode
    print("🧪 Report Generator Test Mode")
    print("=" * 50)

    # Test articles
    test_articles = [
        {
            "title": "OpenAI 发布 GPT-5",
            "key_point": "OpenAI 发布 GPT-5，性能提升300%，API价格下调50%",
            "summary": "OpenAI 今日宣布发布 GPT-5 模型...",
            "source_name": "OpenAI Blog",
            "source_url": "https://openai.com/blog",
            "category": "技术",
            "sub_category": "大模型",
            "importance_score": 9
        },
        {
            "title": "Google DeepMind 新突破",
            "key_point": "DeepMind 在蛋白质折叠领域取得新进展",
            "summary": "Google DeepMind 宣布...",
            "source_name": "Google Blog",
            "source_url": "https://blog.google",
            "category": "研究",
            "sub_category": "学术突破",
            "importance_score": 7
        }
    ]

    generator = ReportGenerator()

    # Generate HTML
    html = generator.generate_html(test_articles)
    print(f"✅ Generated HTML: {len(html)} characters")

    # Generate Markdown
    md = generator.generate_markdown(test_articles)
    print(f"✅ Generated Markdown: {len(md)} characters")

    # Save test files
    html_path = generator.save_html(test_articles, "test_report.html")
    md_path = generator.save_markdown(test_articles, "test_report.md")

    print(f"✅ HTML saved to: {html_path}")
    print(f"✅ Markdown saved to: {md_path}")
