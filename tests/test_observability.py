"""
Basic observability tests.
"""

import re
import unittest

from core.utils.observability import RunMetrics, classify_error, create_run_id


class TestObservability(unittest.TestCase):
    def test_create_run_id_format(self):
        run_id = create_run_id()
        self.assertRegex(run_id, r"^run-\d{8}-\d{6}-[0-9a-f]{8}$")

    def test_classify_error_uses_root_cause(self):
        wrapped = RuntimeError("wrapped")
        wrapped.__cause__ = TimeoutError("timeout")
        severity, code = classify_error("upload", wrapped)
        self.assertEqual(severity, "HIGH")
        self.assertEqual(code, "E_UPLOAD_TIMEOUT")

    def test_run_metrics_summary(self):
        metrics = RunMetrics(run_id="run-test")
        metrics.start_stage("collect")
        metrics.end_stage_success("collect", attempts=1)
        metrics.start_stage("upload")
        metrics.end_stage_failure(
            "upload",
            attempts=2,
            error_code="E_UPLOAD_NETWORK",
            severity="HIGH",
            message="network down",
        )
        metrics.set_counter("collected_items", 3)
        summary = metrics.summary()
        self.assertEqual(summary["run_id"], "run-test")
        self.assertEqual(summary["stage_count"], 2)
        self.assertEqual(summary["stage_success_count"], 1)
        self.assertIn("collect", summary["stages"])
        self.assertEqual(summary["counters"]["collected_items"], 3)


if __name__ == "__main__":
    unittest.main()
