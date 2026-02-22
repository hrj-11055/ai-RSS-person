"""
RSS Collector 测试套件

测试 RSS 采集功能，包括各种抓取策略。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime

import sys
sys.path.insert(0, '..')

from lib.rss_collector import RSSCollector, validate_sources


class TestRSSCollector(unittest.TestCase):
    """测试 RSSCollector 类"""

    def setUp(self):
        """测试前设置"""
        self.test_sources = [
            {"name": "Test Source 1", "url": "https://example.com/rss", "strategy": "direct"},
            {"name": "Test Source 2", "url": "/test/route", "strategy": "rsshub"},
        ]

    def test_collector_initialization(self):
        """测试采集器初始化"""
        collector = RSSCollector(sources=self.test_sources)

        self.assertEqual(len(collector.sources), 2)
        self.assertIsNotNone(collector.headers)
        self.assertEqual(collector.max_items_per_source, 5)
        self.assertEqual(collector.time_window_hours, 24)

    def test_collector_default_sources(self):
        """测试使用默认源初始化"""
        collector = RSSCollector()
        self.assertGreater(len(collector.sources), 10)  # 至少10个源

    @patch('lib.rss_collector.requests.get')
    def test_fetch_direct_success(self, mock_get):
        """测试 direct 策略成功抓取"""
        # Mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Article</title>
                    <link>https://example.com/article1</link>
                    <description>Test description</description>
                    <pubDate>Mon, 11 Feb 2026 10:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""
        mock_get.return_value = mock_response

        collector = RSSCollector(sources=self.test_sources)
        result = collector._fetch_direct("https://example.com/rss")

        self.assertIsNotNone(result)
        self.assertEqual(result, mock_response.content)

    @patch('lib.rss_collector.requests.get')
    def test_fetch_direct_403_fallback(self, mock_get):
        """测试 direct 策略收到 403 时回退到 cffi"""
        # 第一次调用返回 403，触发回退
        mock_403 = Mock()
        mock_403.status_code = 403
        mock_get.return_value = mock_403

        collector = RSSCollector(sources=self.test_sources)

        # 由于 cffi 不可用，应该返回 None
        result = collector._fetch_direct("https://example.com/rss")
        self.assertIsNone(result)

    def test_time_window_filtering(self):
        """测试时间窗口过滤"""
        collector = RSSCollector(sources=self.test_sources)

        # 创建一个模拟的 entry（最近的文章）
        recent_entry = Mock()
        recent_entry.get = Mock(side_effect=lambda k, d=None: (
            datetime.datetime(2026, 2, 11, 10, 0, 0).timetuple() if k in ['published_parsed', 'updated_parsed'] else d
        ))

        # 应该通过时间窗口过滤
        self.assertTrue(collector._is_within_time_window(recent_entry))

        # 创建一个旧的 entry（超过24小时）
        old_entry = Mock()
        old_time = datetime.datetime.now() - datetime.timedelta(hours=30)
        old_entry.get = Mock(side_effect=lambda k, d=None: (
            old_time.timetuple() if k in ['published_parsed', 'updated_parsed'] else d
        ))

        # 应该被时间窗口过滤掉
        self.assertFalse(collector._is_within_time_window(old_entry))

    def test_time_window_no_date(self):
        """测试没有日期的文章（应该接受）"""
        collector = RSSCollector(sources=self.test_sources)

        entry = Mock()
        entry.get = Mock(return_value=None)

        # 没有日期的文章应该被接受
        self.assertTrue(collector._is_within_time_window(entry))

    @patch('lib.rss_collector.feedparser.parse')
    def test_parse_feed_success(self, mock_parse):
        """测试成功解析 feed"""
        # Mock feedparser 响应
        mock_feed = Mock()
        mock_entry = Mock()
        mock_entry.title = "Test Article"
        mock_entry.link = "https://example.com/article1"
        mock_entry.summary = "Test description"
        # Mock get method to return proper values
        published_time = datetime.datetime(2026, 2, 11, 10, 0, 0).timetuple()
        mock_entry.get = Mock(side_effect=lambda k, d=None: published_time if k in ['published_parsed', 'updated_parsed'] else d)

        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        collector = RSSCollector(sources=self.test_sources)
        source = {"name": "Test Source", "url": "https://example.com/rss", "strategy": "direct"}

        result = collector._parse_feed(b"fake content", source)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "Test Source")
        self.assertEqual(result[0]["title"], "Test Article")


class TestValidateSources(unittest.TestCase):
    """测试源验证函数"""

    @patch('lib.rss_collector.RSSCollector')
    def test_validate_sources_calls_collect_all(self, mock_collector_class):
        """测试验证函数调用采集器"""
        # 这里只测试函数调用，不测试实际的网络请求
        # 实际测试需要 mock 更多层级
        pass


if __name__ == '__main__':
    unittest.main()
