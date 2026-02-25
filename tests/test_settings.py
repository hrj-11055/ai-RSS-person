"""
Settings loading and validation tests.
"""

import os
import unittest
from unittest.mock import patch

from core.settings import load_settings, validate_settings, clear_settings


class TestSettings(unittest.TestCase):
    def setUp(self):
        clear_settings()

    def tearDown(self):
        clear_settings()

    @patch.dict(
        os.environ,
        {
            "DEEPSEEK_API_KEY": "test_key",
            "EMAIL_ENABLED": "false",
            "UPLOAD_ENABLED": "false",
            "MAX_ITEMS_PER_SOURCE": "",
            "MAX_ARTICLES_IN_REPORT": "",
        },
        clear=False,
    )
    def test_yaml_overrides_constants_when_env_missing(self):
        settings = load_settings()
        # core/config.yaml 中 rss.max_items_per_source = 5
        self.assertEqual(settings.rss.max_items_per_source, 5)
        # core/config.yaml 中 ranking.max_articles_in_report = 20
        self.assertEqual(settings.report.max_articles_in_report, 20)

    @patch.dict(
        os.environ,
        {
            "DEEPSEEK_API_KEY": "test_key",
            "MAX_ITEMS_PER_SOURCE": "11",
            "MAX_ARTICLES_IN_REPORT": "33",
            "EMAIL_ENABLED": "false",
            "UPLOAD_ENABLED": "false",
        },
        clear=False,
    )
    def test_env_overrides_yaml(self):
        settings = load_settings()
        self.assertEqual(settings.rss.max_items_per_source, 11)
        self.assertEqual(settings.report.max_articles_in_report, 33)

    @patch.dict(
        os.environ,
        {
            "DEEPSEEK_API_KEY": "",
            "EMAIL_ENABLED": "false",
            "UPLOAD_ENABLED": "false",
        },
        clear=False,
    )
    def test_validate_missing_required_api_key(self):
        settings = load_settings()
        with self.assertRaises(ValueError):
            validate_settings(settings)

    @patch.dict(
        os.environ,
        {
            "DEEPSEEK_API_KEY": "test_key",
            "UPLOAD_ENABLED": "true",
            "UPLOAD_METHOD": "http",
            "HTTP_UPLOAD_URL": "",
            "EMAIL_ENABLED": "false",
        },
        clear=False,
    )
    def test_validate_http_upload_requires_url(self):
        settings = load_settings()
        with self.assertRaises(ValueError):
            validate_settings(settings)

    @patch.dict(
        os.environ,
        {
            "DEEPSEEK_API_KEY": "test_key",
            "STAGE_RETRY_COUNT": "2",
            "RESUME_FROM_CACHE": "false",
            "EMAIL_ENABLED": "false",
            "UPLOAD_ENABLED": "false",
        },
        clear=False,
    )
    def test_type_conversion(self):
        settings = load_settings()
        self.assertEqual(settings.pipeline.retry_count, 2)
        self.assertFalse(settings.pipeline.resume_from_cache)


if __name__ == "__main__":
    unittest.main()
