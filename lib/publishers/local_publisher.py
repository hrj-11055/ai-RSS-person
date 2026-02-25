"""
本地发布器模块

处理将报告保存到本地文件系统。

Author: AI-RSS-PERSON Team
Version: 2.0.0
"""

import json
import logging
import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Import shared utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.utils import setup_logger
from core.utils.constants import (
    DEFAULT_OUTPUT_DIR,
    FILENAME_DATETIME_FORMAT,
)

# Setup logger
logger = setup_logger(__name__)


class LocalPublisher:
    """
    将报告保存到本地文件系统。

    支持保存 HTML、Markdown 和 JSON 格式。

    示例：
        >>> publisher = LocalPublisher()
        >>> path = publisher.save_html("<html>...</html>", "report.html")
        >>> print(f"Saved to: {path}")
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化本地发布器。

        参数：
            output_dir: 保存文件的目录（默认为 OUTPUT_DIR 环境变量）
        """
        self.output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_html(
        self,
        content: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save HTML content to file.

        Args:
            content: HTML content string
            filename: Output filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime(FILENAME_DATETIME_FORMAT)
            filename = f"AI_Daily_Report_{timestamp}.html"

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ HTML saved to: {filepath}")
        return str(filepath)

    def save_markdown(
        self,
        content: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save Markdown content to file.

        Args:
            content: Markdown content string
            filename: Output filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime(FILENAME_DATETIME_FORMAT)
            filename = f"AI_Daily_Report_{timestamp}.md"

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Markdown saved to: {filepath}")
        return str(filepath)

    def save_json(
        self,
        articles_data: List[Dict],
        date_str: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Save articles data as JSON file.

        Args:
            articles_data: List of article dictionaries
            date_str: Date string for the report
            filename: Output filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

        if not filename:
            filename = f"{date_str}.json"

        filepath = self.output_dir / filename

        # Validate path is within output directory
        if not str(filepath.resolve()).startswith(str(self.output_dir.resolve())):
            raise ValueError(f"❌ 文件路径不安全: {filepath}")

        # Build report data structure
        report_data = {
            "report_date": date_str,
            "report_title": f"全球AI日报 | {date_str}",
            "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "total_articles": len(articles_data),
            "articles": articles_data
        }

        # Save JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ JSON saved to: {filepath}")
        return str(filepath)

    def save_text(
        self,
        content: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save text content to file.

        Args:
            content: Text content string
            filename: Output filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime(FILENAME_DATETIME_FORMAT)
            filename = f"AI_Daily_Digest_{timestamp}.txt"

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Text saved to: {filepath}")
        return str(filepath)

    def get_filepath(self, filename: str) -> str:
        """
        Get full path for a filename in the output directory.

        Args:
            filename: Filename

        Returns:
            Full path to the file
        """
        return str(self.output_dir / filename)


if __name__ == "__main__":
    # Test mode
    print("🧪 Local Publisher Test Mode")
    print("=" * 50)

    publisher = LocalPublisher()

    print(f"Output directory: {publisher.output_dir}")
    print()

    # Test HTML save
    html_content = "<!DOCTYPE html><html><body><h1>Test Report</h1></body></html>"
    html_path = publisher.save_html(html_content, "test.html")
    print(f"✅ HTML test: {html_path}")

    # Test JSON save
    test_articles = [
        {"title": "Test Article", "summary": "Test content"}
    ]
    json_path = publisher.save_json(test_articles, "2026-02-11", "test.json")
    print(f"✅ JSON test: {json_path}")
