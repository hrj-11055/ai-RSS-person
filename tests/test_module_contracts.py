"""
Module contract tests.

These tests validate key input/output contracts between modules:
- Collector output schema consumed by ranker/analyzer
- Ranker output schema consumed by analyzer
- Analyzer validated output schema consumed by publishers
"""

import json
import tempfile
import unittest
from pathlib import Path

from article_ranker import ArticleRanker
from lib.ai_analyzer import AIAnalyzer
from lib.publishers.local_publisher import LocalPublisher


class TestModuleContracts(unittest.TestCase):
    def test_collector_to_ranker_analyzer_contract(self):
        # Contract: collector emits source/title/link/summary as strings.
        collector_item = {
            "source": "OpenAI Blog",
            "title": "OpenAI 发布 GPT-5",
            "link": "https://example.com/post",
            "summary": "模型能力更新",
        }
        required_keys = {"source", "title", "link", "summary"}
        self.assertTrue(required_keys.issubset(set(collector_item.keys())))
        for key in required_keys:
            self.assertIsInstance(collector_item[key], str)

    def test_ranker_to_analyzer_contract(self):
        ranker = ArticleRanker(use_config=True)
        articles = [
            {
                "source": "OpenAI Blog",
                "title": "OpenAI 发布 GPT-5",
                "link": "https://example.com/a1",
                "summary": "模型发布",
            },
            {
                "source": "TechCrunch AI",
                "title": "AI Startup raises funding",
                "link": "https://example.com/a2",
                "summary": "融资新闻",
            },
        ]
        ranked = ranker.rank_articles(articles, top_n=2)
        self.assertEqual(len(ranked), 2)
        for item in ranked:
            self.assertIn("score", item)
            self.assertIsInstance(item["score"], (int, float))
            # Analyzer input contract
            self.assertIn("title", item)
            self.assertIn("summary", item)
            self.assertIn("source", item)
            self.assertIn("link", item)

    def test_analyzer_to_publisher_contract(self):
        analyzer = AIAnalyzer(api_key="test_key")
        raw_result = {
            "title": "OpenAI 发布 GPT-5",
            "key_point": "重点",
            "summary": "摘要",
            "source_url": "https://example.com/a1",
            "source_name": "OpenAI Blog",
            "category": "技术",
            "sub_category": "大模型",
            "country": "global",
            "importance_score": 9,
        }
        validated = analyzer._validate_result(raw_result, {"title": "T"})

        for field in analyzer.REQUIRED_FIELDS:
            self.assertIn(field, validated)

        with tempfile.TemporaryDirectory() as tmp:
            publisher = LocalPublisher(output_dir=tmp)
            out = publisher.save_json([validated], date_str="2026-02-25")
            payload = json.loads(Path(out).read_text(encoding="utf-8"))
            self.assertIn("articles", payload)
            self.assertEqual(len(payload["articles"]), 1)
            self.assertEqual(payload["articles"][0]["title"], validated["title"])


if __name__ == "__main__":
    unittest.main()
