"""
End-to-end pipeline test with fake data.

This test exercises the orchestrator flow:
collect -> deduplicate -> rank -> analyze -> local publish
while disabling external upload/email side effects.
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from core.settings import (
    AppSettings,
    AISettings,
    RSSSettings,
    ReportSettings,
    CloudSettings,
    EmailSettings,
    PipelineSettings,
    LoggingSettings,
)
from daily_report_PRO_cloud import AI_Daily_Report


class TestPipelineE2E(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.tmpdir.name) / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline_dir = self.output_dir / ".pipeline"

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
                max_articles_in_report=5,
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

    def test_fake_data_full_pipeline(self):
        bot = AI_Daily_Report(self.settings)

        fake_items = [
            {
                "source": "OpenAI Blog",
                "title": "OpenAI 发布 GPT-5",
                "link": "https://example.com/a1",
                "summary": "OpenAI 发布新模型",
            },
            {
                "source": "OpenAI Blog",
                "title": "OpenAI 发布 GPT-5（详细）",
                "link": "https://example.com/a2",
                "summary": "OpenAI 发布新模型 详细信息",
            },
            {
                "source": "TechCrunch AI",
                "title": "AI Startup raises funding",
                "link": "https://example.com/a3",
                "summary": "融资与商业化进展",
            },
        ]

        def fake_analyze(article):
            title = article.get("title", "")
            score = 9 if "GPT-5" in title else 6
            return {
                "title": title,
                "key_point": f"要点: {title}",
                "summary": f"摘要: {article.get('summary', '')}",
                "source_url": article.get("link", ""),
                "source_name": article.get("source", ""),
                "category": "技术",
                "sub_category": "大模型",
                "country": "global",
                "importance_score": score,
            }

        with (
            patch.object(bot.collector, "collect_all", return_value=fake_items),
            patch.object(bot.analyzer, "analyze_single", side_effect=fake_analyze),
            patch("daily_report_PRO_cloud.time.sleep", return_value=None),
        ):
            bot.run()

        today = datetime.now().strftime("%Y-%m-%d")
        output_json = self.output_dir / f"{today}.json"
        self.assertTrue(output_json.exists(), "应生成本地 JSON 报告")

        report = json.loads(output_json.read_text(encoding="utf-8"))
        self.assertIn("articles", report)
        self.assertGreaterEqual(len(report["articles"]), 2)
        self.assertGreaterEqual(
            report["articles"][0]["importance_score"],
            report["articles"][-1]["importance_score"],
            "文章应按 importance_score 降序",
        )

        # 阶段缓存产物
        self.assertTrue((self.pipeline_dir / f"{today}_collected.json").exists())
        self.assertTrue((self.pipeline_dir / f"{today}_deduped.json").exists())
        self.assertTrue((self.pipeline_dir / f"{today}_ranked.json").exists())
        self.assertTrue((self.pipeline_dir / f"{today}_analyzed.json").exists())
        self.assertTrue((self.pipeline_dir / f"{today}_state.json").exists())
        summary_path = self.pipeline_dir / f"{today}_run_summary.json"
        self.assertTrue(summary_path.exists(), "应生成运行统计 summary")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertIn("run_id", summary)
        self.assertIn("stage_success_rate", summary)
        self.assertIn("stages", summary)
        self.assertIn("observability_report", summary)
        obs = summary["observability_report"]
        self.assertIn("rss_insights", obs)
        self.assertIn("pipeline_stats", obs)
        self.assertIn("top_common_sources", obs["rss_insights"])
        self.assertIn("top_error_codes", obs["pipeline_stats"])


if __name__ == "__main__":
    unittest.main()
