"""
Article Ranker 测试套件

测试文章排序和评分功能。
"""

import unittest

import sys
sys.path.insert(0, '..')

from article_ranker import ArticleRanker


class TestArticleRanker(unittest.TestCase):
    """测试 ArticleRanker 类"""

    def setUp(self):
        """测试前设置"""
        self.ranker = ArticleRanker()

        # 测试文章
        self.test_articles = [
            {
                "title": "OpenAI 发布 GPT-5",
                "summary": "OpenAI 今天宣布发布 GPT-5 模型，性能大幅提升",
                "source": "OpenAI Blog",
                "link": "https://openai.com/blog/gpt5"
            },
            {
                "title": "AI 市场分析报告",
                "summary": "2026年 AI 市场预测分析",
                "source": "TechCrunch",
                "link": "https://techcrunch.com/ai-market"
            },
            {
                "title": "普通新闻",
                "summary": "这是一条普通新闻",
                "source": "Generic News",
                "link": "https://example.com/news"
            },
        ]

    def test_ranker_initialization(self):
        """测试排序器初始化"""
        self.assertIsNotNone(self.ranker.source_weights)
        self.assertGreater(len(self.ranker.source_weights), 50)
        self.assertIsNotNone(self.ranker.high_weight_keywords)
        self.assertGreater(len(self.ranker.high_weight_keywords), 20)

    def test_source_authority_score(self):
        """测试源权威性评分"""
        # OpenAI Blog 源权重100，归一化到 0-60 后是 60
        article1 = {"title": "Test", "summary": "Test", "source": "OpenAI Blog"}
        openai_score = self.ranker._calculate_source_score(article1)
        self.assertEqual(openai_score, 60)

        # Generic News 源权重65，归一化后较低
        article2 = {"title": "Test", "summary": "Test", "source": "Generic News"}
        generic_score = self.ranker._calculate_source_score(article2)
        self.assertLess(generic_score, 20)

    def test_content_relevance_score(self):
        """测试内容相关性评分"""
        # 包含多个关键词（发布, gpt, model, 模型）应该得分较高
        article1 = {
            "title": "OpenAI 发布 GPT-5",
            "summary": "OpenAI 今天宣布发布 GPT-5 模型"
        }
        score1 = self.ranker._calculate_relevance_score(article1)
        # 匹配: gpt(1), 发布(2), model(1), 模型(1) = 5个关键词 = 20分
        self.assertGreaterEqual(score1, 15)

        # 普通新闻得分较低
        article2 = {
            "title": "普通新闻",
            "summary": "这是一条普通新闻"
        }
        score2 = self.ranker._calculate_relevance_score(article2)
        self.assertLess(score2, 5)

    def test_calculate_score(self):
        """测试综合评分计算"""
        article = {
            "title": "OpenAI 发布 GPT-5",
            "summary": "OpenAI 今天宣布发布 GPT-5 模型",
            "source": "OpenAI Blog"
        }

        score = self.ranker.calculate_score(article)

        # 验证分数在 0-100 范围内
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

        # OpenAI Blog (60分源权威) + 关键词匹配 (>15分) > 75
        self.assertGreater(score, 70)

    def test_rank_articles(self):
        """测试文章排序"""
        ranked = self.ranker.rank_articles(self.test_articles, top_n=3)

        # 验证返回的是排序后的列表
        self.assertEqual(len(ranked), 3)
        self.assertIn("score", ranked[0])

        # OpenAI Blog + GPT-5 应该排在第一
        self.assertEqual(ranked[0]["title"], "OpenAI 发布 GPT-5")

        # 分数应该递减
        self.assertGreaterEqual(ranked[0]["score"], ranked[1]["score"])
        self.assertGreaterEqual(ranked[1]["score"], ranked[2]["score"])

    def test_rank_articles_with_top_n(self):
        """测试限制返回文章数量"""
        ranked = self.ranker.rank_articles(self.test_articles, top_n=2)

        # 应该只返回前 2 篇文章
        self.assertEqual(len(ranked), 2)

    def test_rank_articles_empty_list(self):
        """测试空文章列表"""
        ranked = self.ranker.rank_articles([])
        self.assertEqual(len(ranked), 0)

    def test_high_weight_keywords(self):
        """测试关键词列表包含核心词汇"""
        # 验证关键词列表包含重要的 AI 术语（小写）
        keywords_str = " ".join(self.ranker.high_weight_keywords).lower()

        self.assertIn("gpt", keywords_str)
        self.assertIn("model", keywords_str)
        self.assertIn("claude", keywords_str)  # 关键词列表包含 claude，不包含 openai

    def test_source_weights_comprehensive(self):
        """测试源权重包含主要的 AI 公司"""
        # 验证源权重包含主要 AI 公司
        self.assertIn("OpenAI Blog", self.ranker.source_weights)
        self.assertIn("Google AI Blog", self.ranker.source_weights)
        self.assertIn("Anthropic AI", self.ranker.source_weights)


class TestScoringEdgeCases(unittest.TestCase):
    """测试评分边缘情况"""

    def setUp(self):
        """测试前设置"""
        self.ranker = ArticleRanker()

    def test_unknown_source(self):
        """测试未知源的评分"""
        article = {
            "title": "Some Article",
            "summary": "Some content",
            "source": "Completely Unknown Source"
        }

        score = self.ranker.calculate_score(article)
        # 未知源默认权重60，归一化后为0，但可能有关键词匹配
        # 所以分数应该是 >= 0
        self.assertGreaterEqual(score, 0)

    def test_article_without_title_or_summary(self):
        """测试缺少标题或摘要的文章"""
        article = {
            "source": "OpenAI Blog"
        }

        score = self.ranker.calculate_score(article)
        # 只有源权威性分数，没有内容相关性分数
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 60)  # 最高 60 分（只有源权威性）

    def test_multiple_keyword_matches(self):
        """测试多个关键词匹配"""
        article = {
            "title": "OpenAI 发布 GPT-5 模型，融资 10 亿美元",
            "summary": "OpenAI 今天的重大宣布",
            "source": "Generic News"
        }

        score = self.ranker.calculate_score(article)
        # 多个关键词匹配（发布, gpt, model, 模型, 融资）= 5个关键词 = 20分
        # Generic News 源权重65，归一化后为0
        # 总分 = 20分
        self.assertEqual(score, 20)

    def test_multi_source_event_boost(self):
        """测试多来源共同报道的排序加分"""
        single_source_article = {
            "title": "普通资讯",
            "summary": "无关键词",
            "source": "Completely Unknown Source",
            "event_source_count": 1,
        }
        multi_source_article = {
            "title": "普通资讯",
            "summary": "无关键词",
            "source": "Completely Unknown Source",
            "event_source_count": 4,
        }

        base_score = self.ranker.calculate_score(single_source_article)
        boosted_score = self.ranker.calculate_score(multi_source_article)

        self.assertEqual(base_score, 0)
        self.assertEqual(boosted_score, 9)
        self.assertGreater(boosted_score, base_score)


if __name__ == '__main__':
    unittest.main()
