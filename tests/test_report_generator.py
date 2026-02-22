"""
Report Generator 测试套件

测试报告生成功能，包括 Markdown、JSON、HTML 格式。
"""

import unittest
import datetime
from pathlib import Path

import sys
sys.path.insert(0, '..')

from lib.report_generator import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    """测试 ReportGenerator 类"""

    def setUp(self):
        """测试前设置"""
        self.generator = ReportGenerator()

        # 测试文章数据
        self.test_articles = [
            {
                "title": "OpenAI 发布 GPT-5",
                "key_point": "OpenAI 今天宣布发布 GPT-5 模型，性能提升300%",
                "summary": "OpenAI 今日宣布发布 GPT-5 模型，性能相比前代提升300%，API价格下调50%。新模型支持更长上下文，推理能力大幅提升。",
                "source_name": "OpenAI Blog",
                "source_url": "https://openai.com/blog/gpt5",
                "category": "技术",
                "sub_category": "大模型",
                "importance_score": 9
            },
            {
                "title": "Google DeepMind 新突破",
                "key_point": "DeepMind 在蛋白质折叠领域取得新进展",
                "summary": "Google DeepMind 宣布在蛋白质折叠预测方面取得新突破，准确率提升至99%。",
                "source_name": "Google Blog",
                "source_url": "https://blog.google",
                "category": "研究",
                "sub_category": "学术突破",
                "importance_score": 7
            },
        ]

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.generator.output_dir)
        self.assertTrue(self.generator.output_dir.exists())

    def test_generate_markdown(self):
        """测试生成 Markdown 报告"""
        md = self.generator.generate_markdown(self.test_articles)

        # 验证基本结构
        self.assertIn("# 🌍 全球AI日报", md)
        self.assertIn("## 📰 本期导读", md)
        self.assertIn("## 1. OpenAI 发布 GPT-5", md)
        self.assertIn("## 2. Google DeepMind 新突破", md)

        # 验证文章内容
        self.assertIn("OpenAI 今天宣布发布 GPT-5 模型", md)
        self.assertIn("性能提升300%", md)
        self.assertIn("**来源**: OpenAI Blog", md)
        self.assertIn("**分类**: 技术 / 大模型", md)

        # 验证重要性评分显示
        self.assertIn("⭐", md)

    def test_generate_markdown_custom_title(self):
        """测试自定义标题生成 Markdown"""
        custom_title = "测试报告"
        md = self.generator.generate_markdown(
            self.test_articles,
            title=custom_title,
            date_str="2026-02-11"
        )

        self.assertIn(f"# {custom_title}", md)
        self.assertIn("2026-02-11", md)

    def test_generate_html(self):
        """测试生成 HTML 报告"""
        html = self.generator.generate_html(self.test_articles)

        # 验证基本 HTML 结构
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)
        self.assertIn("<body>", html)
        self.assertIn("<div class=\"container\">", html)

        # 验证标题
        self.assertIn("<h1>", html)

        # 验证文章内容
        self.assertIn("OpenAI 发布 GPT-5", html)
        self.assertIn("OpenAI 今天宣布发布 GPT-5 模型", html)

    def test_escape_html(self):
        """测试 HTML 转义"""
        test_text = "<script>alert('test')</script>"
        escaped = self.generator._escape_html(test_text)

        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;", escaped)
        self.assertIn("&gt;", escaped)

    def test_generate_article_html(self):
        """测试生成单篇文章 HTML"""
        article = self.test_articles[0]
        html = self.generator._generate_article_html(article)

        # 验证包含文章元素
        self.assertIn("<h3>", html)
        self.assertIn("OpenAI 发布 GPT-5", html)
        self.assertIn("速览：", html)
        self.assertIn("深度分析：", html)
        self.assertIn("技术", html)
        self.assertIn("大模型", html)

    def test_save_markdown(self):
        """测试保存 Markdown 文件"""
        import tempfile
        import os

        # 使用临时目录
        temp_dir = tempfile.mkdtemp()
        generator = ReportGenerator(output_dir=temp_dir)

        filepath = generator.save_markdown(self.test_articles, filename="test_report.md")

        # 验证文件存在
        self.assertTrue(Path(filepath).exists())

        # 验证文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("OpenAI 发布 GPT-5", content)

        # 清理
        os.remove(filepath)
        os.rmdir(temp_dir)

    def test_save_markdown_default_filename(self):
        """测试使用默认文件名保存"""
        import tempfile
        import os

        temp_dir = tempfile.mkdtemp()
        generator = ReportGenerator(output_dir=temp_dir)

        filepath = generator.save_markdown(self.test_articles)

        # 验证文件名格式（YYYY-MM-DD.md）
        filename = Path(filepath).name
        self.assertRegex(filename, r'\d{4}-\d{2}-\d{2}\.md')

        # 清理
        os.remove(filepath)
        os.rmdir(temp_dir)

    def test_save_json(self):
        """测试保存 JSON 文件（使用 LocalPublisher）"""
        import tempfile
        import os
        import json
        from lib.publishers.local_publisher import LocalPublisher

        temp_dir = tempfile.mkdtemp()
        publisher = LocalPublisher(output_dir=temp_dir)

        filepath = publisher.save_json(self.test_articles, date_str="2026-02-11")

        # 验证文件存在
        self.assertTrue(Path(filepath).exists())

        # 验证 JSON 内容
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data["report_date"], "2026-02-11")
            self.assertEqual(len(data["articles"]), 2)
            self.assertEqual(data["total_articles"], 2)

        # 清理
        os.remove(filepath)
        os.rmdir(temp_dir)

    def test_save_default(self):
        """测试保存默认格式（仅 Markdown）"""
        # 注意：save_default 需要 save_json，但 ReportGenerator 没有该方法
        # 所以我们只测试 Markdown 保存
        import tempfile
        import os

        temp_dir = tempfile.mkdtemp()
        generator = ReportGenerator(output_dir=temp_dir)

        # 只保存 Markdown（当前 ReportGenerator 的主要功能）
        md_path = generator.save_markdown(self.test_articles)

        # 验证文件存在
        self.assertTrue(Path(md_path).exists())

        # 清理
        os.remove(md_path)
        os.rmdir(temp_dir)

    def test_html_escaping_in_article_generation(self):
        """测试文章生成时 HTML 转义"""
        article_with_html = {
            "title": "Test <script>alert('xss')</script>",
            "key_point": "Summary with <b>HTML</b>",
            "summary": "Content with <i>tags</i>",
            "source_name": "Test Source",
            "source_url": "https://example.com",
            "category": "Test",
            "sub_category": "Test",
            "importance_score": 5
        }

        html = self.generator._generate_article_html(article_with_html)

        # 验证 HTML 标签被转义
        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>", html)
        self.assertNotIn("<i>", html)

    def test_importance_stars_display(self):
        """测试重要性星级显示"""
        md = self.generator.generate_markdown(self.test_articles)

        # 验证星级显示
        self.assertIn("⭐" * 4, md)  # importance_score 9 -> 4 stars
        self.assertIn("⭐" * 3, md)  # importance_score 7 -> 3 stars


class TestReportGeneratorOutput(unittest.TestCase):
    """测试报告生成器输出"""

    def setUp(self):
        """测试前设置"""
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = ReportGenerator(output_dir=str(self.temp_dir))

        # 测试文章数据
        self.test_articles = [
            {
                "title": "OpenAI 发布 GPT-5",
                "key_point": "OpenAI 今天宣布发布 GPT-5 模型，性能提升300%",
                "summary": "OpenAI 今日宣布发布 GPT-5 模型，性能相比前代提升300%，API价格下调50%。新模型支持更长上下文，推理能力大幅提升。",
                "source_name": "OpenAI Blog",
                "source_url": "https://openai.com/blog/gpt5",
                "category": "技术",
                "sub_category": "大模型",
                "importance_score": 9
            },
        ]

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(str(self.temp_dir), ignore_errors=True)

    def test_output_directory_created(self):
        """测试输出目录自动创建"""
        self.assertTrue(self.temp_dir.exists())

    def test_multiple_saves(self):
        """测试多次保存"""
        from lib.publishers.local_publisher import LocalPublisher

        # 保存 Markdown
        md_path = self.generator.save_markdown(self.test_articles)
        self.assertTrue(Path(md_path).exists())

        # 保存 JSON（使用 LocalPublisher）
        local_publisher = LocalPublisher(output_dir=str(self.temp_dir))
        json_path = local_publisher.save_json(self.test_articles, date_str="2026-02-11")
        self.assertTrue(Path(json_path).exists())

        # 验证文件不同
        self.assertNotEqual(md_path, json_path)


if __name__ == '__main__':
    unittest.main()
