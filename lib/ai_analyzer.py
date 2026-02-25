"""
AI 分析模块

从 daily_report_PRO_cloud.py 重构而来，使用 DeepSeek API
提供清晰的 AI 分析功能，输出结构化的 JSON 数据。

Author: AI-RSS-PERSON Team
Version: 2.0.0
"""

import json
import datetime
import logging
from typing import Dict, Optional, List
from pathlib import Path
from openai import OpenAI

# 导入共享工具
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import setup_logger
from core.utils.cost_tracker import CostTracker
from core.utils.constants import (
    DEFAULT_AI_MODEL,
    DEFAULT_AI_BASE_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
)

# 设置日志
logger = setup_logger(__name__)


class AIAnalyzer:
    """
    使用 DeepSeek API 的 AI 文章分析器。

    该类提供 RSS 文章的智能分析，包括提取关键洞察、分类和重要性评分。

    示例：
        >>> analyzer = AIAnalyzer()
        >>> article = {"title": "...", "summary": "...", "source": "...", "link": "..."}
        >>> result = analyzer.analyze_single(article)
        >>> print(result['title'])
    """

    # Prompt 模板作为类常量
    SUMMARY_PROMPT_TEMPLATE = """
你是由资深科技媒体人担任的《全球AI内参》主编。你的目标是从纷繁的信息中提炼高价值情报，供行业从业者和投资者阅读。

请阅读以下新闻数据：
【来源】：{source}
【原文标题】：{title}
【原文摘要】：{summary}

请输出一段 HTML 格式的中文快讯，严格遵守以下结构和要求：

1.  **<h3>中文标题</h3>**：
    * 要求：专业、简练但具有吸引力。避免震惊体，但要抓住痛点或热点。包含核心实体名（如公司、模型名）。
    * 风格参考：OpenAI再推新王炸，GPT-5参数细节曝光

2.  **<p>【新闻事实】</p>**：
    * 要求：用简练的中文概括新闻的核心内容（Who, What, When）。
    * 格式：如果内容较多，请使用 <ul><li> 列表形式，限制在 3 点以内。如果内容较少，使用一段话概括。重点词汇请使用 <strong> 标签加粗。

3.  **<p>【主编点评】</p>**：
    * 要求：不要复述新闻！必须提供增量信息。分析其对行业格局的影响、技术落地的难点、或者背后的商业逻辑。
    * 字数：100-150字，犀利、客观。

    输出示例格式：
    <h3>...</h3>
    <p><strong>速览：</strong>...</p>
    <p><strong>点评：</strong>...</p>
"""

    DETAILED_PROMPT_TEMPLATE = """
你是一位服务于顶级投资机构和科技高管的【AI情报分析师】。你的任务是撰写《全球AI内参》。
受众时间宝贵，他们不需要普通的新闻资讯，而是需要能辅助决策的【高价值情报】。

输入信息：
- 来源：{source}
- 原文标题：{title}
- 原文摘要：{summary}
- 原文链接：{link}

请按照以下标准输出 JSON 格式内容（必须是有效的 JSON，不要用 markdown 代码块包裹）：

字段说明：
1.  **title**（标题）：
    * 风格：极度冷静、专业。禁止使用感叹号。禁止使用"震惊"、"重磅"等营销词汇。
    * 结构：核心事件 + 关键数据/核心影响。
    * 字数：30字以内

2.  **key_point**（要点）：
    * 用一句话概括核心事实（Fact），控制在100字以内。
    * 必须包含具体的数字（如参数量、融资金额、性能提升百分比），去除所有形容词。

3.  **summary**（深度摘要）：
    * 详细阐述新闻事实和深度研判。
    * 不要复述新闻，要分析事件背后的"信号"。
    * 思考维度（任选其一）：
        * **商业竞争**：这动了谁的蛋糕？
        * **技术落地**：真正的瓶颈在哪里？
        * **长期趋势**：这是泡沫还是范式转移？
    * 字数：150字，直击要害。

4.  **source_url**：原文链接（直接使用输入的链接）

5.  **source_name**：来源名称（直接使用输入的来源）

6.  **category**（一级分类）：从以下选择其一
    - "技术"（技术突破、模型发布、算法创新）
    - "商业"（融资、并购、财报、商业模式）
    - "政策"（法规、监管、合规）
    - "产品"（产品发布、功能更新）
    - "研究"（学术论文、研究成果）
    - "观点"（行业领袖观点、访谈）

7.  **sub_category**（二级分类）：根据具体内容细分
    - 技术类：大模型、计算机视觉、自然语言处理、芯片硬件、开源项目
    - 商业类：融资并购、市场竞争、生态建设、价格策略
    - 政策类：数据隐私、内容监管、知识产权、国际合作
    - 产品类：企业服务、消费应用、开发者工具
    - 研究类：学术突破、基准测试、数据集发布
    - 观点类：行业预测、技术争议、伦理讨论

8.  **country**（地域）：从以下选择其一
    - "global"（全球/跨国）
    - "cn"（中国）

9.  **importance_score**（重要性评分）：0-10的整数
    * 9-10分：行业颠覆性事件（如GPT-4发布、OpenAI董事会风波）
    * 7-8分：重大产品发布、重要融资、政策重大变化
    * 5-6分：常规产品更新、中型融资、行业动态
    * 3-4分：观点文章、小型更新
    * 1-2分：一般性新闻

    输出示例：
    {{
        "title": "Anthropic 发布 Claude 3.5 Sonnet：代码能力超越 GPT-4o，价格下调 20%",
        "key_point": "Anthropic 发布 Claude 3.5 Sonnet，HumanEval 得分 92.0%，API 价格下调 20%，推理速度提升 2 倍。",
        "summary": "Anthropic 今日发布 Claude 3.5 Sonnet。基准测试显示，其在 HumanEval 代码生成任务中得分 92.0%，略高于 GPT-4o 的 90.2%。同时，API 调用价格较上一代 Opis 模型下调 20%，推理速度提升 2 倍。此举标志着大模型价格战进入白热化阶段。Claude 3.5 在代码与逻辑细分领域的特定优势，将直接冲击 GitHub Copilot 等辅助编程工具的市场格局。对于开发者而言，目前是混合使用模型的最佳窗口期，建议在代码生成场景优先切换至 Claude 3.5 以降低 Token 成本。",
        "source_url": "{link}",
        "source_name": "{source}",
        "category": "技术",
        "sub_category": "大模型",
        "country": "global" 或 "cn",
        "importance_score": 8
    }}

    重要：直接输出纯 JSON 文本，不要用 markdown 代码块（```json）包裹，确保格式正确可以被 json.loads() 解析。country 字段只能是 "global" 或 "cn"。
"""

    # 必需字段（用于验证）
    REQUIRED_FIELDS = [
        "title", "key_point", "summary", "source_url", "source_name",
        "category", "sub_category", "country", "importance_score"
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_AI_MODEL,
        timeout: int = 30
    ):
        """
        初始化 AI 分析器。

        参数：
            api_key: DeepSeek API 密钥（默认为 DEEPSEEK_API_KEY 环境变量）
            base_url: API 基础 URL（默认为 DEEPSEEK_BASE_URL 环境变量）
            model: 使用的模型名称
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("❌ DeepSeek API Key 未配置！请设置 DEEPSEEK_API_KEY")
        self.base_url = base_url or DEFAULT_AI_BASE_URL
        self.model = model
        self.timeout = timeout

        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # 成本追踪器
        self.cost_tracker = CostTracker()

    def analyze_single(
        self,
        article: Dict,
        prompt_type: str = "detailed"
    ) -> Optional[Dict]:
        """
        使用 AI 分析单篇文章。

        参数：
            article: 文章字典，包含：title、summary、source、link
            prompt_type: Prompt 类型（"summary" 或 "detailed"）

        返回：
            分析结果字典，如果分析失败则返回 None

        示例：
            >>> analyzer = AIAnalyzer()
            >>> article = {
            ...     "title": "OpenAI releases GPT-5",
            ...     "summary": "OpenAI announced...",
            ...     "source": "OpenAI Blog",
            ...     "link": "https://..."
            ... }
            >>> result = analyzer.analyze_single(article)
        """
        # 构建 Prompt
        prompt = self._build_prompt(article, prompt_type)

        try:
            # 调用 API
            response = self._call_api(prompt)
            if not response:
                return None

            # 解析响应
            content = response.choices[0].message.content

            # 追踪成本
            self.cost_tracker.add(response.usage)

            # 解析 JSON
            if prompt_type == "detailed":
                result = self._parse_json_response(content, article)
            else:
                # 对于 summary 类型，直接返回 HTML
                result = {"html_content": content}

            return result

        except Exception as e:
            logger.error(f"AI分析失败: {article.get('title', 'Unknown')[:50]}..., 错误: {str(e)[:100]}")
            return None

    def analyze_batch(
        self,
        articles: List[Dict],
        prompt_type: str = "detailed"
    ) -> List[Dict]:
        """
        批量分析多篇文章。

        参数：
            articles: 文章字典列表
            prompt_type: Prompt 类型（"summary" 或 "detailed"）

        返回：
            分析结果列表（可能包含 None，表示分析失败）
        """
        results = []
        total = len(articles)

        for i, article in enumerate(articles, 1):
            logger.info(f"[{i}/{total}] 处理: {article.get('title', 'Unknown')[:50]}...")
            result = self.analyze_single(article, prompt_type)
            results.append(result)

            # 添加小延迟以避免速率限制
            import time
            time.sleep(1)

        return results

    def _build_prompt(self, article: Dict, prompt_type: str) -> str:
        """
        根据文章数据构建 Prompt。

        参数：
            article: 文章字典
            prompt_type: Prompt 类型（"summary" 或 "detailed"）

        返回：
            格式化的 Prompt 字符串
        """
        template = self.DETAILED_PROMPT_TEMPLATE if prompt_type == "detailed" else self.SUMMARY_PROMPT_TEMPLATE

        # 为详细 prompt 添加时间戳
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')

        return template.format(
            source=article.get('source', 'Unknown'),
            title=article.get('title', 'Unknown'),
            summary=article.get('summary', ''),
            link=article.get('link', ''),
            timestamp=timestamp
        )

    def _call_api(self, prompt: str):
        """
        使用给定的 Prompt 调用 DeepSeek API。

        参数：
            prompt: Prompt 字符串

        返回：
            API 响应，失败则返回 None
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                timeout=self.timeout
            )
            return response
        except Exception as e:
            logger.error(f"API调用失败: {str(e)[:100]}")
            return None

    def _parse_json_response(self, content: str, article: Dict) -> Optional[Dict]:
        """
        解析并验证 AI 返回的 JSON 响应。

        参数：
            content: 原始响应内容
            article: 原始文章（用于错误消息）

        返回：
            解析和验证后的字典，解析失败则返回 None
        """
        # 检查内容
        if not content:
            logger.error(f"AI返回内容为空: {article.get('title', 'Unknown')[:50]}")
            return None

        content = content.strip()

        # 移除 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # 解析 JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {article.get('title', 'Unknown')[:50]}..., 错误: {str(e)[:100]}")
            logger.debug(f"Content preview: {content[:200]}")
            return None

        # 验证必需字段
        return self._validate_result(result, article)

    def _validate_result(self, result: Dict, article: Dict) -> Dict:
        """
        验证并为缺失字段添加默认值。

        参数：
            result: 解析后的结果字典
            article: 原始文章（用于错误消息）

        返回：
            验证后的结果字典
        """
        for field in self.REQUIRED_FIELDS:
            if field not in result:
                logger.warning(f"AI返回缺少字段: {field}，文章: {article.get('title', 'Unknown')[:50]}")
                # 添加默认值
                result[field] = self._get_default_value(field)

        return result

    def _get_default_value(self, field: str):
        """
        获取缺失字段的默认值。

        参数：
            field: 字段名

        返回：
            字段的默认值
        """
        defaults = {
            "importance_score": 5,
            "country": "global",
            "category": "技术",
            "sub_category": "未分类"
        }
        return defaults.get(field)

    def get_cost_report(self) -> str:
        """
        获取成本追踪报告。

        返回：
            格式化的成本报告字符串
        """
        return self.cost_tracker.report()

    def reset_cost_tracker(self):
        """重置成本追踪器。"""
        self.cost_tracker.reset()


if __name__ == "__main__":
    # 测试模式
    print("🧪 AI Analyzer 测试模式")
    print("=" * 50)

    analyzer = AIAnalyzer()

    # 测试文章
    test_article = {
        "title": "Test Article: AI Breakthrough",
        "summary": "This is a test summary about a new AI breakthrough that changes everything.",
        "source": "Test Source",
        "link": "https://example.com/test"
    }

    print(f"Testing with article: {test_article['title']}")
    print(f"API Key: {'✅ 已设置' if analyzer.api_key else '❌ 未设置'}")
    print(f"Base URL: {analyzer.base_url}")
    print(f"Model: {analyzer.model}")
    print()
    print("要运行完整分析，请在 .env 文件中设置 DEEPSEEK_API_KEY")
