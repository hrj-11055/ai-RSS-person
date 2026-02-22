"""
AI Analyzer 测试套件

测试 AI 分析功能，包括 API 调用、成本追踪等。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json

import sys
sys.path.insert(0, '..')

from lib.ai_analyzer import AIAnalyzer, CostTracker


class TestCostTracker(unittest.TestCase):
    """测试 CostTracker 类"""

    def setUp(self):
        """测试前设置"""
        self.tracker = CostTracker()

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tracker.total_input_tokens, 0)
        self.assertEqual(self.tracker.total_output_tokens, 0)

    def test_add_usage(self):
        """测试添加使用量"""
        mock_usage = Mock()
        mock_usage.prompt_tokens = 1000
        mock_usage.completion_tokens = 500

        self.tracker.add(mock_usage)

        self.assertEqual(self.tracker.total_input_tokens, 1000)
        self.assertEqual(self.tracker.total_output_tokens, 500)

    def test_add_multiple_usage(self):
        """测试多次添加使用量"""
        mock_usage1 = Mock()
        mock_usage1.prompt_tokens = 1000
        mock_usage1.completion_tokens = 500

        mock_usage2 = Mock()
        mock_usage2.prompt_tokens = 2000
        mock_usage2.completion_tokens = 1000

        self.tracker.add(mock_usage1)
        self.tracker.add(mock_usage2)

        self.assertEqual(self.tracker.total_input_tokens, 3000)
        self.assertEqual(self.tracker.total_output_tokens, 1500)

    def test_get_cost_report(self):
        """测试成本报告"""
        mock_usage = Mock()
        mock_usage.prompt_tokens = 1000
        mock_usage.completion_tokens = 500

        self.tracker.add(mock_usage)

        report = self.tracker.report()

        self.assertIn("本次消耗", report)
        self.assertIn("输入", report)
        self.assertIn("输出", report)
        self.assertIn("¥", report)

    def test_reset(self):
        """测试重置"""
        mock_usage = Mock()
        mock_usage.prompt_tokens = 1000
        mock_usage.completion_tokens = 500

        self.tracker.add(mock_usage)
        self.tracker.reset()

        self.assertEqual(self.tracker.total_input_tokens, 0)
        self.assertEqual(self.tracker.total_output_tokens, 0)


class TestAIAnalyzer(unittest.TestCase):
    """测试 AIAnalyzer 类"""

    def setUp(self):
        """测试前设置"""
        # 使用假的 API key 进行测试
        self.analyzer = AIAnalyzer(api_key="test_key")

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.analyzer.client)
        self.assertIsNotNone(self.analyzer.cost_tracker)
        self.assertEqual(self.analyzer.model, "deepseek-chat")

    def test_build_prompt_summary(self):
        """测试构建摘要 prompt"""
        article = {
            "title": "OpenAI 发布 GPT-5",
            "summary": "OpenAI 今天宣布发布 GPT-5 模型",
            "source": "OpenAI Blog"
        }

        prompt = self.analyzer._build_prompt(article, prompt_type="summary")

        self.assertIn("OpenAI 发布 GPT-5", prompt)
        self.assertIn("OpenAI Blog", prompt)

    def test_build_prompt_detailed(self):
        """测试构建详细分析 prompt"""
        article = {
            "title": "OpenAI 发布 GPT-5",
            "summary": "OpenAI 今天宣布发布 GPT-5 模型",
            "source": "OpenAI Blog"
        }

        prompt = self.analyzer._build_prompt(article, prompt_type="detailed")

        self.assertIn("OpenAI 发布 GPT-5", prompt)
        self.assertIn("category", prompt.lower())
        self.assertIn("importance", prompt.lower())

    @patch('lib.ai_analyzer.OpenAI')
    def test_parse_json_response_success(self, mock_openai):
        """测试解析 JSON 响应成功"""
        json_content = '''
        {
            "key_point": "这是一个重要的要点",
            "summary": "详细的摘要内容",
            "category": "技术",
            "sub_category": "大模型",
            "importance_score": 9
        }
        '''

        article = {"title": "Test Article"}
        result = self.analyzer._parse_json_response(json_content, article)

        self.assertIsNotNone(result)
        self.assertEqual(result["key_point"], "这是一个重要的要点")
        self.assertEqual(result["category"], "技术")
        self.assertEqual(result["importance_score"], 9)

    def test_parse_json_response_invalid_json(self):
        """测试解析无效 JSON"""
        invalid_json = "This is not valid JSON"

        article = {"title": "Test Article"}
        result = self.analyzer._parse_json_response(invalid_json, article)

        # 应该返回 None 或默认结构
        self.assertIsNone(result)

    def test_validate_result_missing_fields(self):
        """测试验证缺少字段的结果"""
        incomplete_result = {
            "key_point": "要点",
            # 缺少其他必需字段
        }

        article = {"title": "Test Article"}

        # 应该补充缺少的字段
        result = self.analyzer._validate_result(incomplete_result, article)

        self.assertIn("summary", result)
        self.assertIn("category", result)

    def test_validate_result_complete(self):
        """测试验证完整的结果"""
        complete_result = {
            "key_point": "重要要点",
            "summary": "详细摘要",
            "category": "技术",
            "sub_category": "大模型",
            "importance_score": 9
        }

        article = {"title": "Test Article"}

        result = self.analyzer._validate_result(complete_result, article)

        # 完整的结果应该保持不变
        self.assertEqual(result["key_point"], "重要要点")
        self.assertEqual(result["category"], "技术")

    @patch('lib.ai_analyzer.OpenAI')
    def test_analyze_single_mock(self, mock_openai):
        """测试分析单篇文章（mock API）"""
        # Mock API 响应
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "key_point": "重要要点",
            "summary": "详细摘要",
            "category": "技术",
            "sub_category": "大模型",
            "importance_score": 9
        })
        mock_response.usage.prompt_tokens = 1000
        mock_response.usage.completion_tokens = 500

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # 使用 mock client 重新初始化
        analyzer = AIAnalyzer(api_key="test_key")
        analyzer.client = mock_client

        article = {
            "title": "OpenAI 发布 GPT-5",
            "summary": "OpenAI 今天宣布发布 GPT-5 模型",
            "source": "OpenAI Blog"
        }

        result = analyzer.analyze_single(article)

        self.assertIsNotNone(result)
        self.assertEqual(result["key_point"], "重要要点")
        self.assertEqual(result["category"], "技术")


class TestPromptTemplates(unittest.TestCase):
    """测试 Prompt 模板"""

    def setUp(self):
        """测试前设置"""
        self.analyzer = AIAnalyzer(api_key="test_key")

    def test_summary_prompt_template(self):
        """测试摘要 prompt 模板"""
        self.assertIsNotNone(self.analyzer.SUMMARY_PROMPT_TEMPLATE)
        self.assertIn("{title}", self.analyzer.SUMMARY_PROMPT_TEMPLATE)

    def test_detailed_prompt_template(self):
        """测试详细分析 prompt 模板"""
        self.assertIsNotNone(self.analyzer.DETAILED_PROMPT_TEMPLATE)
        self.assertIn("{title}", self.analyzer.DETAILED_PROMPT_TEMPLATE)
        self.assertIn("category", self.analyzer.DETAILED_PROMPT_TEMPLATE.lower())

    def test_required_fields(self):
        """测试必需字段定义"""
        self.assertIn("key_point", self.analyzer.REQUIRED_FIELDS)
        self.assertIn("summary", self.analyzer.REQUIRED_FIELDS)
        self.assertIn("category", self.analyzer.REQUIRED_FIELDS)


if __name__ == '__main__':
    unittest.main()
