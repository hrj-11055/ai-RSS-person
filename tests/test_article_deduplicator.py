import unittest

from lib.article_deduplicator import ArticleDeduplicator


class TestArticleDeduplicator(unittest.TestCase):
    def test_deduplicate_same_event_paraphrase(self):
        dedup = ArticleDeduplicator(similarity_threshold=0.85)
        items = [
            {
                "source": "OpenAI Blog",
                "title": "OpenAI 获 1100 亿美元融资，投前估值达 7300 亿美元",
                "summary": "OpenAI 完成新一轮私募融资，金额 1100 亿美元。",
                "link": "https://example.com/openai-funding-1",
            },
            {
                "source": "TechCrunch AI",
                "title": "ChatGPT周活跃用户达9亿，OpenAI完成1100亿美元私募融资",
                "summary": "消息称 OpenAI 以 7300 亿美元估值完成融资。",
                "link": "https://example.com/openai-funding-2",
            },
            {
                "source": "InfoQ AI",
                "title": "Perplexity 发布 Computer 产品：整合多模型能力于单一系统",
                "summary": "这是另一条不相关新闻。",
                "link": "https://example.com/perplexity-computer",
            },
        ]

        result = dedup.deduplicate(items, source_name_key="source")
        self.assertEqual(len(result), 2, "同一事件的改写标题应被合并")

    def test_deduplicate_canonical_url(self):
        dedup = ArticleDeduplicator(similarity_threshold=0.95)
        items = [
            {
                "source": "OpenAI Blog",
                "title": "OpenAI 发布新公告",
                "summary": "",
                "link": "https://openai.com/news/a?id=1&utm_source=x",
            },
            {
                "source": "The Verge AI",
                "title": "OpenAI 发布新公告（转述）",
                "summary": "",
                "link": "https://openai.com/news/a?id=1&utm_source=y",
            },
        ]

        result = dedup.deduplicate(items, source_name_key="source")
        self.assertEqual(len(result), 1, "URL 仅 query 跟踪参数不同应视为重复")

    def test_event_coverage_metadata(self):
        dedup = ArticleDeduplicator(similarity_threshold=0.85)
        items = [
            {
                "source": "OpenAI Blog",
                "title": "OpenAI 发布新模型",
                "summary": "官方发布详情",
                "link": "https://example.com/openai-release",
            },
            {
                "source": "TechCrunch AI",
                "title": "OpenAI 发布新模型（解读）",
                "summary": "媒体跟进报道",
                "link": "https://example.com/openai-release?utm_source=tc",
            },
            {
                "source": "InfoQ AI",
                "title": "另一条独立新闻",
                "summary": "不重复",
                "link": "https://example.com/other-news",
            },
        ]

        result = dedup.deduplicate(items, source_name_key="source")
        self.assertEqual(len(result), 2)
        max_coverage = max(item.get("event_source_count", 1) for item in result)
        self.assertEqual(max_coverage, 2, "合并后的事件应标记来源数量")
        merged_item = max(result, key=lambda x: x.get("event_source_count", 1))
        self.assertIn("OpenAI Blog", merged_item.get("event_sources", []))
        self.assertIn("TechCrunch AI", merged_item.get("event_sources", []))

    def test_loose_coverage_for_multi_source_event(self):
        dedup = ArticleDeduplicator(similarity_threshold=0.85)
        items = [
            {
                "source": "InfoQ AI",
                "title": "史诗级输血！亚马逊、英伟达、软银联手投出1100亿美元，OpenAI估值冲上7300亿美元",
                "summary": "",
                "link": "https://example.com/openai-funding-infoq",
            },
            {
                "source": "量子位",
                "title": "OpenAI最新融资1100亿美元！英伟达亚马逊软银都抢到船票了",
                "summary": "",
                "link": "https://example.com/openai-funding-qbit",
            },
            {
                "source": "The Verge AI",
                "title": "OpenAI获1100亿美元新融资，亚马逊、英伟达、软银参投",
                "summary": "",
                "link": "https://example.com/openai-funding-verge",
            },
            {
                "source": "MIT News AI",
                "title": "MIT实验室发布新型水下导航算法",
                "summary": "",
                "link": "https://example.com/mit-underwater",
            },
        ]

        result = dedup.deduplicate(items, source_name_key="source")
        self.assertGreaterEqual(len(result), 3)
        multi_source_items = [x for x in result if x.get("event_source_count", 1) >= 2]
        self.assertGreaterEqual(len(multi_source_items), 2, "融资事件应被标记为多源同报")


if __name__ == "__main__":
    unittest.main()
