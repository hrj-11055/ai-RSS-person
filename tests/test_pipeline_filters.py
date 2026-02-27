"""
Pipeline post-rank filtering tests.

Focus:
1) Per-source daily cap (max 4)
2) Cross-day dedup against recent report JSON files
"""

import json
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from core.settings import (
    AISettings,
    AppSettings,
    CloudSettings,
    EmailSettings,
    LoggingSettings,
    PipelineSettings,
    RSSSettings,
    ReportSettings,
)
from daily_report_PRO_cloud import AI_Daily_Report


class TestPipelineFilters(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.tmpdir.name) / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline_dir = self.output_dir / ".pipeline"
        self.pipeline_dir.mkdir(parents=True, exist_ok=True)

        project_root = Path(__file__).resolve().parent.parent
        self.settings = AppSettings(
            ai=AISettings(api_key="test_key", base_url="https://api.deepseek.com", model="deepseek-chat"),
            rss=RSSSettings(
                rsshub_host="http://localhost:1200",
                proxy_url="",
                max_items_per_source=7,
                time_window_hours=24,
            ),
            report=ReportSettings(
                output_dir=str(self.output_dir),
                max_articles_in_report=12,
                local_target_dir="",
            ),
            cloud=CloudSettings(enabled=False),
            email=EmailSettings(enabled=False),
            pipeline=PipelineSettings(
                cache_dir=str(self.pipeline_dir),
                resume_from_cache=False,
                retry_count=0,
                retry_delay_seconds=0,
            ),
            logging=LoggingSettings(level="INFO"),
            sources_path=project_root / "config" / "sources.yaml",
            weights_path=project_root / "config" / "weights.yaml",
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write_yesterday_report(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "report_date": yesterday,
            "report_title": f"test-{yesterday}",
            "generated_at": datetime.now().isoformat(),
            "total_articles": 1,
            "articles": [
                {
                    "title": "Perplexity上线Computer功能，整合19个AI模型挑战传统金融终端",
                    "key_point": "历史事件",
                    "summary": "Perplexity 发布 Computer 功能，整合 19 个 AI 模型，挑战传统金融终端。",
                    "source_url": "https://example.com/history",
                    "source_name": "新智元",
                    "category": "技术",
                    "sub_category": "产品",
                    "country": "global",
                    "importance_score": 8,
                }
            ],
        }
        report_path = self.output_dir / f"{yesterday}.json"
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_post_rank_filters_source_cap_and_history_dedup(self):
        self._write_yesterday_report()
        bot = AI_Daily_Report(self.settings)

        ranked_candidates = [
            {
                "source": "量子位",
                "title": f"量子位独家快讯 {i}",
                "summary": f"这是量子位第 {i} 条新闻，内容彼此不同。",
                "link": f"https://example.com/qz-{i}",
                "score": 95 - i,
            }
            for i in range(1, 7)
        ]

        ranked_candidates.insert(
            0,
            {
                "source": "量子位",
                "title": "Perplexity 发布 Perplexity Computer：整合19个模型对标彭博终端",
                "summary": "Perplexity 发布 Computer 能力，整合 19 个模型，面向金融分析场景。",
                "link": "https://example.com/perplexity-new",
                "score": 99,
            },
        )

        ranked_candidates.extend(
            [
                {
                    "source": "36氪 AI",
                    "title": "36氪 报道 A",
                    "summary": "与其他新闻不重复。",
                    "link": "https://example.com/36kr-a",
                    "score": 80,
                },
                {
                    "source": "InfoQ AI",
                    "title": "InfoQ 报道 B",
                    "summary": "与其他新闻不重复。",
                    "link": "https://example.com/infoq-b",
                    "score": 79,
                },
            ]
        )

        today = datetime.now().strftime("%Y-%m-%d")
        final_items, history_dropped, source_cap_dropped = bot._post_process_ranked_items(
            ranked_candidates,
            date_str=today,
        )

        self.assertGreaterEqual(history_dropped, 1, "应至少过滤 1 条历史重复新闻")
        self.assertGreaterEqual(source_cap_dropped, 2, "量子位超过 4 条，应触发来源上限过滤")
        self.assertLessEqual(len(final_items), self.settings.report.max_articles_in_report)

        sources = Counter(item.get("source", "") for item in final_items)
        self.assertLessEqual(sources.get("量子位", 0), 4, "每来源每日最多 4 条")

        titles = {item.get("title", "") for item in final_items}
        self.assertNotIn(
            "Perplexity 发布 Perplexity Computer：整合19个模型对标彭博终端",
            titles,
            "与近三天历史重复的事件应被过滤",
        )


if __name__ == "__main__":
    unittest.main()
