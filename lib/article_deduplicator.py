"""
文章去重模块

基于标题语义相似度进行新闻去重，当检测到重复新闻时，
保留权重较高的源的文章。

Author: AI-RSS-PERSON Team
Version: 1.0.0
"""

import logging
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import re

# 导入共享工具
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import setup_logger, get_optional_env
from core.config_manager import ConfigManager

# 设置日志
logger = setup_logger(__name__, get_optional_env("LOG_LEVEL", "INFO"))


class ArticleDeduplicator:
    """
    文章去重器

    使用标题语义相似度检测重复新闻，
    保留权重更高的源的文章。
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        config_manager: ConfigManager = None
    ):
        """
        初始化去重器

        Args:
            similarity_threshold: 相似度阈值，超过此值视为重复 (0-1)
            config_manager: 配置管理器，用于获取源权重
        """
        self.similarity_threshold = similarity_threshold
        self.config_manager = config_manager or ConfigManager()
        self.source_weights = self.config_manager.load_source_weights()

        # 编译一些正则表达式用于清理标题
        self.patterns_to_remove = [
            r'\|.*$',           # 移除 | 后的内容（通常是网站名）
            r'-.*$',            # 移除 - 后的内容
            r'【.*?】',          # 移除中文方括号内容
            r'\[.*?\]',         # 移除英文方括号内容
            r'（.*?）',          # 移除中文圆括号内容
            r'\(.*?\)',         # 移除英文圆括号内容
            r'[^\w\s\u4e00-\u9fff]',  # 只保留中文、英文、数字和空格
            r'\s+',             # 合并多个空格
        ]

    def deduplicate(
        self,
        articles: List[Dict],
        source_name_key: str = 'source',
        title_key: str = 'title'
    ) -> List[Dict]:
        """
        对文章列表进行去重

        Args:
            articles: 文章列表
            source_name_key: 源名称的字段名
            title_key: 标题的字段名

        Returns:
            去重后的文章列表
        """
        if not articles:
            return []

        logger.info(f"🔄 开始去重，原始文章数: {len(articles)}")

        # 按源权重排序（权重高的优先保留）
        sorted_articles = sorted(
            articles,
            key=lambda x: self._get_source_weight(
                x.get(source_name_key, 'Unknown')
            ),
            reverse=True
        )

        # 记录已处理的标题组
        processed_groups: List[List[Dict]] = []
        used_indices: Set[int] = set()

        for i, article in enumerate(sorted_articles):
            if i in used_indices:
                continue

            title = article.get(title_key, '')
            if not title:
                continue

            # 找到所有相似的文章
            similar_articles = [article]
            used_indices.add(i)

            for j in range(i + 1, len(sorted_articles)):
                if j in used_indices:
                    continue

                other_article = sorted_articles[j]
                other_title = other_article.get(title_key, '')

                if self._are_titles_similar(title, other_title):
                    similar_articles.append(other_article)
                    used_indices.add(j)

            # 在相似文章组中选择权重最高的
            if similar_articles:
                best = self._select_best_article(similar_articles, source_name_key)
                processed_groups.append(similar_articles)

                # 记录去重信息
                if len(similar_articles) > 1:
                    sources = [a.get(source_name_key, 'Unknown') for a in similar_articles]
                    best_source = best.get(source_name_key, 'Unknown')
                    logger.debug(
                        f"  🔄 去重: {len(similar_articles)}篇相似文章 "
                        f"-> 保留 [{best_source}] (权重: {self._get_source_weight(best_source)})"
                    )

        # 从每组中选择最佳文章
        result = []
        for group in processed_groups:
            best = self._select_best_article(group, source_name_key)
            result.append(best)

        removed_count = len(articles) - len(result)
        logger.info(f"✅ 去重完成: 移除 {removed_count} 篇重复文章，保留 {len(result)} 篇")

        return result

    def _get_source_weight(self, source_name: str) -> int:
        """获取源权重，默认为50"""
        return self.source_weights.get(source_name, 50)

    def _select_best_article(
        self,
        articles: List[Dict],
        source_name_key: str
    ) -> Dict:
        """
        从相似文章组中选择最佳文章

        选择标准：
        1. 源权重最高
        2. 标题最完整（长度适中）
        """
        # 按权重排序
        sorted_by_weight = sorted(
            articles,
            key=lambda x: self._get_source_weight(x.get(source_name_key, 'Unknown')),
            reverse=True
        )

        # 取权重最高的，如果有多个，选择标题长度适中的
        max_weight = self._get_source_weight(
            sorted_by_weight[0].get(source_name_key, 'Unknown')
        )
        top_weight_articles = [
            a for a in sorted_by_weight
            if self._get_source_weight(a.get(source_name_key, 'Unknown')) == max_weight
        ]

        if len(top_weight_articles) == 1:
            return top_weight_articles[0]

        # 选择标题长度适中的（避免过短或过长）
        top_weight_articles.sort(
            key=lambda x: len(x.get('title', '')),
            reverse=True
        )

        # 取中位数长度的
        mid_index = len(top_weight_articles) // 2
        return top_weight_articles[mid_index]

    def _are_titles_similar(self, title1: str, title2: str) -> bool:
        """
        判断两个标题是否相似

        使用多种策略：
        1. 完全匹配（去除标点符号后）
        2. 包含关系（一个标题包含另一个的核心词）
        3. 词汇重叠度
        """
        if not title1 or not title2:
            return False

        # 清理标题
        clean1 = self._clean_title(title1)
        clean2 = self._clean_title(title2)

        if not clean1 or not clean2:
            return False

        # 1. 完全匹配
        if clean1 == clean2:
            return True

        # 2. 包含关系（较短标题包含在较长标题中）
        if clean1 in clean2 or clean2 in clean1:
            return True

        # 3. 词汇重叠度
        similarity = self._calculate_similarity(clean1, clean2)
        return similarity >= self.similarity_threshold

    def _clean_title(self, title: str) -> str:
        """清理标题，移除干扰信息"""
        title = title.strip()

        # 移除常见模式
        for pattern in self.patterns_to_remove:
            title = re.sub(pattern, ' ', title)

        return title.strip().lower()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        使用词袋模型计算Jaccard相似度
        """
        # 分词（按空格分词，对中文需要额外处理）
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)

        if not words1 or not words2:
            return 0.0

        # Jaccard相似度
        set1 = set(words1)
        set2 = set(words2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def _tokenize(self, text: str) -> List[str]:
        """
        分词

        对中文按字符分词，对英文按单词分词
        """
        tokens = []

        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                tokens.append(char)
            elif char.isalnum():  # 英文或数字
                tokens.append(char.lower())
            elif char.isspace():
                continue

        return tokens


def deduplicate_articles(
    articles: List[Dict],
    similarity_threshold: float = 0.85,
    config_manager: ConfigManager = None
) -> List[Dict]:
    """
    便捷函数：对文章列表进行去重

    Args:
        articles: 文章列表
        similarity_threshold: 相似度阈值
        config_manager: 配置管理器

    Returns:
        去重后的文章列表
    """
    deduplicator = ArticleDeduplicator(
        similarity_threshold=similarity_threshold,
        config_manager=config_manager
    )
    return deduplicator.deduplicate(articles)


if __name__ == "__main__":
    # 测试代码
    test_articles = [
        {"title": "OpenAI发布GPT-5模型", "source_name": "机器之心", "link": "1"},
        {"title": "OpenAI发布GPT-5模型 | 人工智能新突破", "source_name": "量子位", "link": "2"},
        {"title": "OpenAI今天正式发布了GPT-5大语言模型", "source_name": "新智元", "link": "3"},
        {"title": "Google推出Gemini 2.0", "source_name": "36氪 AI", "link": "4"},
        {"title": "Google推出Gemini 2.0 - AI新纪元", "source_name": "AI前线", "link": "5"},
        {"title": "完全不同的新闻标题", "source_name": "少数派", "link": "6"},
    ]

    dedup = ArticleDeduplicator()
    result = dedup.deduplicate(test_articles)

    print(f"原始: {len(test_articles)} 篇")
    print(f"去重后: {len(result)} 篇")
    print("\n保留的文章:")
    for article in result:
        weight = dedup._get_source_weight(article["source_name"])
        print(f"  [{article['source_name']}] (权重:{weight}) {article['title']}")
