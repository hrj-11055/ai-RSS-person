"""
文章排序模块

根据重要性和相关性对RSS文章进行智能排序。
支持从 YAML 配置文件加载权重和关键词。

Author: AI-RSS-PERSON Team
Version: 2.1.0
"""

from typing import List, Dict, Optional
from pathlib import Path

# 导入配置管理器
from core.config_manager import get_config_manager


class ArticleRanker:
    """文章排序器"""

    # 默认配置（当 YAML 文件不存在时使用）
    DEFAULT_KEYWORDS = [
        # AI模型相关
        'gpt', 'claude', 'gemini', 'llama', 'deepseek', 'transformer',
        'model', '模型',
        # 融资/商业相关
        'funding', 'investment', '融资', '投资', 'unicorn', 'acquisition',
        '收购', 'merger', 'ipo', '上市', 'billion', 'million',
        # 行业大事
        'ceo', 'founder', 'executive', '创始人', 'partnership', '合作',
        # 技术突破
        'research', 'paper', 'arxiv', '研究', '突破', 'benchmark',
        '性能', 'record', '首次',
        # 产品发布
        'product', '产品', 'feature', '功能', 'update', '更新',
        'announcement', '发布', 'launch', 'unveil',
    ]

    DEFAULT_SOURCE_WEIGHTS = {
        # 官方博客（最高权重）
        'OpenAI Blog': 100,
        'Google DeepMind Blog': 100,
        'Google AI Blog': 95,
        'Microsoft Research': 90,
        'Hugging Face': 95,
        'NVIDIA Blog': 90,
        'Anthropic AI': 100,
        'DeepSeek AI': 95,
        # 学术/权威媒体
        'Arxiv AI': 85,
        'MIT Technology Review': 80,
        # 顶级科技媒体
        'TechCrunch AI': 75,
        'The Verge AI': 75,
        'Ars Technica': 75,
        # AI 社区
        'Hacker News AI': 75,
        'Hacker News LLM': 75,
        # AI 领袖
        'Sam Altman': 95,
        'Geoffrey Hinton': 95,
        'Yann LeCun': 95,
        'Andrew Ng': 85,
        # 中文媒体
        '阮一峰博客': 90,
        '少数派': 75,
        '机器之心': 90,
        # 研究博客
        'Machine Learning Mastery': 70,
        'AWS ML Blog': 75,
        'KDnuggets Neural Networks': 70,
        # 技术博客
        'Simon Willison': 85,
        'Paul Graham': 90,
        'Mitchel H': 80,
        'Jeff Geerling': 75,
        'Daring Fireball': 75,
        'KREBs on Security': 80,
    }

    DEFAULT_SCORING_CONFIG = {
        'source_weight': 0.6,
        'content_weight': 0.4,
    }

    def __init__(self, use_config: bool = True, config_dir: Optional[str] = None):
        """
        初始化文章排序器

        Args:
            use_config: 是否从 YAML 配置文件加载权重
            config_dir: 配置文件目录
        """
        self.use_config = use_config

        if use_config:
            self.config_manager = get_config_manager()
            if config_dir:
                self.config_manager.config_dir = Path(config_dir)

            # 从配置文件加载
            self.source_weights = self.config_manager.load_source_weights() or self.DEFAULT_SOURCE_WEIGHTS
            self.high_weight_keywords = self.config_manager.load_keywords() or self.DEFAULT_KEYWORDS
            self.scoring_config = self.config_manager.load_scoring_config() or self.DEFAULT_SCORING_CONFIG
        else:
            # 使用默认配置
            self.source_weights = self.DEFAULT_SOURCE_WEIGHTS.copy()
            self.high_weight_keywords = self.DEFAULT_KEYWORDS.copy()
            self.scoring_config = self.DEFAULT_SCORING_CONFIG.copy()

    def calculate_score(self, item: Dict) -> float:
        """
        计算文章的综合得分

        评分维度:
        1. 来源权重 (默认 60%): 根据来源权威性
        2. 内容相关性 (默认 40%): 根据关键词匹配

        Args:
            item: RSS条目字典，必须包含 source, title, summary

        Returns:
            综合得分 (0-100)
        """
        score = 0.0

        # 1. 来源权重评分
        source_weight_percent = self.scoring_config.get('source_weight', 0.6)
        score += self._calculate_source_score(item) * source_weight_percent / 60 * 60

        # 2. 内容相关性评分
        content_weight_percent = self.scoring_config.get('content_weight', 0.4)
        score += self._calculate_relevance_score(item) * content_weight_percent / 40 * 40

        return round(score, 2)

    def _calculate_source_score(self, item: Dict) -> float:
        """
        计算来源权重得分 (0-60分)

        归一化处理: 将 source_weights 中的分数映射到 0-60 分
        """
        source = item.get('source', '')
        weight = self.source_weights.get(source, 60)  # 默认权重60

        # 归一化到 0-60 分
        # 假设最高权重100，最低权重60
        normalized = (weight - 60) / (100 - 60) * 60
        return max(0, min(60, normalized))

    def _calculate_relevance_score(self, item: Dict) -> float:
        """
        计算内容相关性得分 (0-40分)

        基于关键词匹配，每个关键词匹配得一定分数
        """
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        content = title + ' ' + summary

        matches = 0
        for keyword in self.high_weight_keywords:
            if keyword.lower() in content:
                matches += 1

        # 每匹配一个关键词得4分，最高40分
        return min(40, matches * 4)

    def rank_articles(self, articles: List[Dict], top_n: int = 20) -> List[Dict]:
        """
        对文章列表进行排序，返回前N篇

        Args:
            articles: 文章列表
            top_n: 返回前N篇，默认20

        Returns:
            排序后的文章列表（已添加 'score' 字段）
        """
        # 为每篇文章计算得分
        for article in articles:
            article['score'] = self.calculate_score(article)

        # 按得分降序排序
        sorted_articles = sorted(articles, key=lambda x: x['score'], reverse=True)

        # 只返回前 top_n 篇
        return sorted_articles[:top_n]

    def print_ranking_debug(self, articles: List[Dict], top_n: int = 10):
        """
        打印排序调试信息（前N篇的详细评分）

        Args:
            articles: 文章列表
            top_n: 打印前N篇
        """
        ranked = self.rank_articles(articles, top_n)

        print(f"\n{'='*80}")
        print(f"📊 文章排序结果 (Top {top_n})")
        print(f"{'='*80}\n")

        for i, article in enumerate(ranked, 1):
            print(f"{i}. [{article['score']:.1f}分] {article['title'][:60]}...")
            print(f"   来源: {article['source']}")
            print()

    def get_ranking_summary(self, articles: List[Dict]) -> str:
        """
        获取排序统计摘要

        Args:
            articles: 排序后的文章列表

        Returns:
            统计摘要字符串
        """
        if not articles:
            return "没有文章"

        total_score = sum(a.get('score', 0) for a in articles)
        avg_score = total_score / len(articles)

        sources = {}
        for article in articles:
            source = article['source']
            sources[source] = sources.get(source, 0) + 1

        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]

        summary = f"""
📊 排序统计:
- 总文章数: {len(articles)}
- 平均得分: {avg_score:.1f}
- 最高得分: {articles[0].get('score', 0):.1f}
- 最低得分: {articles[-1].get('score', 0):.1f}

📰 主要来源 (Top 5):
"""
        for source, count in top_sources:
            summary += f"  - {source}: {count}篇\n"

        return summary

    def add_source_weight(self, source: str, weight: int):
        """添加或更新源权重"""
        self.source_weights[source] = weight

    def add_keyword(self, keyword: str):
        """添加关键词"""
        if keyword not in self.high_weight_keywords:
            self.high_weight_keywords.append(keyword)

    def reload_config(self):
        """重新加载配置文件"""
        if self.use_config:
            self.source_weights = self.config_manager.load_source_weights() or self.DEFAULT_SOURCE_WEIGHTS
            self.high_weight_keywords = self.config_manager.load_keywords() or self.DEFAULT_KEYWORDS
            self.scoring_config = self.config_manager.load_scoring_config() or self.DEFAULT_SCORING_CONFIG
