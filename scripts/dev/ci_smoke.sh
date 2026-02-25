#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "[smoke] running pipeline e2e fake-data smoke"
python -m unittest tests.test_pipeline_e2e -v

echo "[smoke] validating observability summary contract"
python - <<'PY'
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from core.settings import (
    AppSettings, AISettings, RSSSettings, ReportSettings,
    CloudSettings, EmailSettings, PipelineSettings, LoggingSettings,
)
from daily_report_PRO_cloud import AI_Daily_Report

with tempfile.TemporaryDirectory() as tmp:
    output_dir = Path(tmp) / "reports"
    pipeline_dir = output_dir / ".pipeline"
    output_dir.mkdir(parents=True, exist_ok=True)

    project_root = Path.cwd()
    settings = AppSettings(
        ai=AISettings(api_key="dummy", base_url="https://api.deepseek.com", model="deepseek-chat"),
        rss=RSSSettings(rsshub_host="http://localhost:1200", proxy_url="", max_items_per_source=3, time_window_hours=24),
        report=ReportSettings(output_dir=str(output_dir), max_articles_in_report=3),
        cloud=CloudSettings(enabled=False),
        email=EmailSettings(enabled=False),
        pipeline=PipelineSettings(cache_dir=str(pipeline_dir), resume_from_cache=False, retry_count=0, retry_delay_seconds=0),
        logging=LoggingSettings(level="INFO"),
        sources_path=project_root / "config" / "sources.yaml",
        weights_path=project_root / "config" / "weights.yaml",
    )

    bot = AI_Daily_Report(settings)
    fake_items = [{"source": "OpenAI Blog", "title": "t", "link": "https://e", "summary": "s"}]

    with (
        patch.object(bot.collector, "collect_all", return_value=fake_items),
        patch.object(bot.analyzer, "analyze_single", return_value={
            "title": "t", "key_point": "k", "summary": "s", "source_url": "https://e",
            "source_name": "OpenAI Blog", "category": "技术", "sub_category": "模型",
            "country": "global", "importance_score": 8,
        }),
        patch("daily_report_PRO_cloud.time.sleep", return_value=None),
    ):
        bot.run()

    today = datetime.now().strftime("%Y-%m-%d")
    summary = json.loads((pipeline_dir / f"{today}_run_summary.json").read_text(encoding="utf-8"))
    obs = summary.get("observability_report", {})
    assert "rss_insights" in obs
    assert "pipeline_stats" in obs
    assert isinstance(obs.get("pipeline_stats", {}).get("top_error_codes", []), list)

print("[smoke] contract ok")
PY
