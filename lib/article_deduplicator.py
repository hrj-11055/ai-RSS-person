"""
文章去重模块

基于标题语义相似度进行新闻去重，当检测到重复新闻时，
保留权重较高的源的文章。

Author: AI-RSS-PERSON Team
Version: 1.0.0
"""

import logging
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode

# 导入共享工具
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import setup_logger
from core.config_manager import ConfigManager

# 设置日志
logger = setup_logger(__name__)


class ArticleDeduplicator:
    """
    文章去重器

    使用标题语义相似度检测重复新闻，
    保留权重更高的源的文章。
    """

    def __init__(
        self,
        similarity_threshold: float = 0.72,
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
                if self._are_articles_similar(article, other_article, title_key=title_key):
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
            result.append(self._annotate_event_coverage(best, group, source_name_key))

        # 第二阶段：独立统计“多源同报”覆盖，不依赖是否已被去重合并
        result = self._enrich_event_coverage(
            deduplicated=result,
            original_articles=articles,
            source_name_key=source_name_key,
            title_key=title_key,
        )

        removed_count = len(articles) - len(result)
        logger.info(f"✅ 去重完成: 移除 {removed_count} 篇重复文章，保留 {len(result)} 篇")

        return result

    @staticmethod
    def _annotate_event_coverage(best_article: Dict, group: List[Dict], source_name_key: str) -> Dict:
        """在去重后的保留文章上标记同事件被多少来源共同报道。"""
        annotated = dict(best_article)

        sources: list[str] = []
        for item in group:
            source = (
                item.get(source_name_key)
                or item.get("source")
                or item.get("source_name")
                or "Unknown"
            )
            source = str(source).strip()
            if source:
                sources.append(source)

        unique_sources = list(dict.fromkeys(sources))
        annotated["event_source_count"] = max(1, len(unique_sources))
        annotated["event_sources"] = unique_sources
        annotated["event_duplicate_count"] = max(0, len(group) - 1)
        return annotated

    def _enrich_event_coverage(
        self,
        deduplicated: List[Dict],
        original_articles: List[Dict],
        source_name_key: str,
        title_key: str,
    ) -> List[Dict]:
        """
        用更宽松的事件相似规则统计“多源同报”覆盖数。

        目的：即使文章没有在第一阶段被真正合并，也能在排序时获得多源共同报道加分。
        """
        enriched: List[Dict] = []

        for item in deduplicated:
            current_sources = list(item.get("event_sources", [])) or [self._extract_source(item, source_name_key)]
            source_order = dict.fromkeys([s for s in current_sources if s])
            related_article_count = 0

            for candidate in original_articles:
                if self._are_articles_related_for_coverage(item, candidate, title_key=title_key):
                    related_article_count += 1
                    source = self._extract_source(candidate, source_name_key)
                    if source:
                        source_order.setdefault(source, None)

            annotated = dict(item)
            merged_sources = list(source_order.keys())
            source_count = max(int(annotated.get("event_source_count", 1) or 1), len(merged_sources))
            annotated["event_sources"] = merged_sources
            annotated["event_source_count"] = max(1, source_count)
            annotated["event_article_count"] = max(related_article_count, int(annotated.get("event_article_count", 0) or 0))
            annotated["event_duplicate_count"] = max(0, annotated["event_source_count"] - 1)
            enriched.append(annotated)

        return enriched

    @staticmethod
    def _extract_source(item: Dict, source_name_key: str) -> str:
        return (
            str(
                item.get(source_name_key)
                or item.get("source")
                or item.get("source_name")
                or "Unknown"
            ).strip()
        )

    def _are_articles_related_for_coverage(self, article1: Dict, article2: Dict, title_key: str = "title") -> bool:
        """宽松版同事件判定，用于统计多源覆盖数，不用于直接删文。"""
        title1 = self._clean_title(article1.get(title_key, ""))
        title2 = self._clean_title(article2.get(title_key, ""))
        if not title1 or not title2:
            return False

        sim = self._char_similarity(title1, title2)
        overlap = self._char_overlap_ratio(title1, title2)
        common = self._longest_common_substring_len(title1, title2)

        nums1 = self._extract_numbers(title1)
        nums2 = self._extract_numbers(title2)
        has_number_overlap = bool(nums1 and nums2 and (nums1 & nums2))

        if sim >= 0.70 and common >= 8:
            return True

        if has_number_overlap and common >= 6 and (sim >= 0.30 or overlap >= 0.55):
            return True

        return False

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

        # 直接使用字符相似度（SequenceMatcher）
        return self._char_similarity(clean1, clean2) >= self.similarity_threshold

    def _are_articles_similar(self, article1: Dict, article2: Dict, title_key: str = "title") -> bool:
        """判断两篇文章是否属于同一事件（字符相似度主导）。"""
        title1 = article1.get(title_key, "")
        title2 = article2.get(title_key, "")
        if not title1 or not title2:
            return False

        # URL 规范化后一致，直接判定重复
        url1 = self._canonicalize_url(article1.get("link", "") or article1.get("url", ""))
        url2 = self._canonicalize_url(article2.get("link", "") or article2.get("url", ""))
        if url1 and url1 == url2:
            return True

        clean1 = self._clean_title(title1)
        clean2 = self._clean_title(title2)
        if not clean1 or not clean2:
            return False

        title_char_sim = self._char_similarity(clean1, clean2)
        if title_char_sim >= self.similarity_threshold:
            return True

        # 中等字符相似 + 数字重合 + 公共连续片段足够长，也视为同一事件。
        # 这可以覆盖“同一融资/估值事件，不同媒体不同写法”场景。
        nums1 = self._extract_numbers(clean1)
        nums2 = self._extract_numbers(clean2)
        has_number_overlap = bool(nums1 and nums2 and (nums1 & nums2))
        common_substring_len = self._longest_common_substring_len(clean1, clean2)
        if title_char_sim >= 0.43 and has_number_overlap and common_substring_len >= 6:
            return True

        return False

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

    @staticmethod
    def _char_similarity(text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()

    @staticmethod
    def _char_overlap_ratio(text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        counter1 = Counter(text1)
        counter2 = Counter(text2)
        inter = sum((counter1 & counter2).values())
        base = min(len(text1), len(text2))
        if base == 0:
            return 0.0
        return inter / base

    @staticmethod
    def _longest_common_substring_len(text1: str, text2: str) -> int:
        if not text1 or not text2:
            return 0
        match = SequenceMatcher(None, text1, text2).find_longest_match(0, len(text1), 0, len(text2))
        return int(match.size)

    @staticmethod
    def _overlap_ratio(left: Set[str], right: Set[str]) -> float:
        if not left or not right:
            return 0.0
        base = min(len(left), len(right))
        if base == 0:
            return 0.0
        return len(left & right) / base

    def _extract_keywords(self, text: str) -> Set[str]:
        """抽取事件关键词（英文词组、数字词、中文词段）。"""
        keywords: Set[str] = set()

        for token in re.findall(r"[a-z0-9][a-z0-9+._-]{1,}", text.lower()):
            if len(token) >= 3:
                keywords.add(token)

        for token in re.findall(r"[\u4e00-\u9fff]{2,}", text):
            if len(token) >= 2:
                # 对中文词段做 2-gram，提升改写标题的重叠召回
                for i in range(len(token) - 1):
                    keywords.add(token[i:i + 2])

        stopwords = {
            "ai", "news", "blog", "today", "update", "发布", "宣布", "公司",
            "模型", "产品", "功能", "平台", "支持", "推出", "上线", "新闻",
        }
        return {k for k in keywords if k not in stopwords}

    @staticmethod
    def _extract_numbers(text: str) -> Set[str]:
        return set(re.findall(r"\d+(?:\.\d+)?", text))

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        if not url:
            return ""
        try:
            parsed = urlparse(url.strip())
            if not parsed.scheme or not parsed.netloc:
                return ""
            query_pairs = [
                (k, v)
                for k, v in parse_qsl(parsed.query, keep_blank_values=False)
                if not (k.startswith("utm_") or k in {"spm", "from", "ref", "fbclid", "gclid"})
            ]
            query = urlencode(sorted(query_pairs))
            normalized = parsed._replace(
                scheme=parsed.scheme.lower(),
                netloc=parsed.netloc.lower(),
                fragment="",
                query=query,
            )
            return urlunparse(normalized)
        except Exception:
            return ""

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
