"""
配置管理模块

从 YAML 文件加载 RSS 源和权重配置。

Author: AI-RSS-PERSON Team
Version: 2.1.0
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional

# 导入常量
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.utils.constants import STRATEGY_RSSHUB, STRATEGY_CFFI, STRATEGY_DIRECT, STRATEGY_NOPROXY

# 设置日志
from core.utils import setup_logger, get_optional_env
logger = setup_logger(__name__, get_optional_env("LOG_LEVEL", "INFO"))


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为项目根目录下的 config/
        """
        if config_dir is None:
            # 项目根目录
            project_root = Path(__file__).parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.sources_file = self.config_dir / "sources.yaml"
        self.weights_file = self.config_dir / "weights.yaml"

    def load_sources(self, enabled_only: bool = True) -> List[Dict]:
        """
        从 YAML 文件加载 RSS 源配置

        Args:
            enabled_only: 是否只返回启用的源

        Returns:
            源配置列表
        """
        if not self.sources_file.exists():
            logger.warning(f"配置文件不存在: {self.sources_file}")
            return []

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        sources = config.get('sources', [])

        # 转换策略名称
        strategy_map = {
            'direct': STRATEGY_DIRECT,
            'noproxy': STRATEGY_NOPROXY,
            'rsshub': STRATEGY_RSSHUB,
            'cffi': STRATEGY_CFFI,
        }

        # 转换为 RSSCollector 需要的格式
        result = []
        for source in sources:
            # 检查是否启用（enabled 字段存在且为 False 时禁用）
            is_enabled = source.get('enabled')
            if enabled_only and is_enabled is False:
                continue

            strategy = source.get('strategy', 'direct')
            mapped_strategy = strategy_map.get(strategy, strategy)

            result.append({
                'name': source['name'],
                'url': source['url'],
                'strategy': mapped_strategy,
                'category': source.get('category', ''),
                'enabled': is_enabled,  # 保留 enabled 字段
            })

        logger.info(f"从配置文件加载了 {len(result)} 个 RSS 源")
        return result

    def load_source_weights(self) -> Dict[str, int]:
        """
        从 YAML 文件加载源权重配置

        Returns:
            源名称 -> 权重的字典
        """
        if not self.weights_file.exists():
            logger.warning(f"配置文件不存在: {self.weights_file}")
            return {}

        with open(self.weights_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get('source_weights', {})

    def load_keywords(self) -> List[str]:
        """
        从 YAML 文件加载关键词列表

        Returns:
            关键词列表
        """
        if not self.weights_file.exists():
            logger.warning(f"配置文件不存在: {self.weights_file}")
            return []

        with open(self.weights_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get('keywords', [])

    def load_scoring_config(self) -> Dict:
        """
        从 YAML 文件加载评分配置

        Returns:
            评分配置字典
        """
        if not self.weights_file.exists():
            logger.warning(f"配置文件不存在: {self.weights_file}")
            return {
                'source_weight': 0.6,
                'content_weight': 0.4,
            }

        with open(self.weights_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get('scoring', {
            'source_weight': 0.6,
            'content_weight': 0.4,
        })

    def get_all_sources(self) -> List[Dict]:
        """
        获取所有源（包括禁用的）

        Returns:
            所有源配置列表
        """
        return self.load_sources(enabled_only=False)

    def get_enabled_sources(self) -> List[Dict]:
        """
        获取启用的源

        Returns:
            启用的源配置列表
        """
        return self.load_sources(enabled_only=True)

    def get_source_by_name(self, name: str) -> Optional[Dict]:
        """
        根据名称获取源配置

        Args:
            name: 源名称

        Returns:
            源配置字典，未找到返回 None
        """
        for source in self.get_all_sources():
            if source['name'] == name:
                return source
        return None

    def get_disabled_sources(self) -> List[Dict]:
        """
        获取禁用的源

        Returns:
            禁用的源配置列表
        """
        all_sources = self.get_all_sources()
        return [s for s in all_sources if not s.get('enabled', True)]

    def get_categories(self) -> List[str]:
        """
        获取所有源分类

        Returns:
            分类列表
        """
        categories = set()
        for source in self.get_all_sources():
            category = source.get('category', '未分类')
            if category:
                categories.add(category)
        return sorted(list(categories))

    def get_sources_by_category(self, category: str, enabled_only: bool = True) -> List[Dict]:
        """
        获取指定分类的源

        Args:
            category: 分类名称
            enabled_only: 是否只返回启用的源

        Returns:
            该分类下的源列表
        """
        sources = self.get_enabled_sources() if enabled_only else self.get_all_sources()
        return [s for s in sources if s.get('category') == category]

    def reload(self):
        """重新加载配置"""
        logger.info("重新加载配置文件...")


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例

    Returns:
        ConfigManager 实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == "__main__":
    # 测试代码
    config = get_config_manager()

    print("=" * 60)
    print("配置文件测试")
    print("=" * 60)

    print(f"\n📁 配置目录: {config.config_dir}")
    print(f"📄 源配置文件: {config.sources_file}")
    print(f"📄 权重配置文件: {config.weights_file}")

    print("\n📊 分类统计:")
    for category in config.get_categories():
        count = len(config.get_sources_by_category(category))
        enabled = len(config.get_sources_by_category(category, enabled_only=True))
        print(f"  - {category}: {enabled}/{count} 启用")

    print("\n✅ 启用的源:")
    for source in config.get_enabled_sources():
        print(f"  - {source['name']} ({source['strategy']})")

    print("\n⚠️  禁用的源:")
    for source in config.get_all_sources():
        if not source.get('enabled', True):
            print(f"  - {source['name']}")

    print("\n⚖️  源权重 (前10):")
    weights = config.load_source_weights()
    for name, weight in sorted(weights.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {name}: {weight}")

    print("\n🔑 关键词 (前15):")
    keywords = config.load_keywords()
    for kw in keywords[:15]:
        print(f"  - {kw}")
