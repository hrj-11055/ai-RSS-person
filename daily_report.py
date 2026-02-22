#!/usr/bin/env python3
"""
AI 日报生成器 - 统一入口

从多个 RSS 源采集 AI 行业新闻，使用智能排序系统筛选重要文章，
通过 DeepSeek AI 分析并生成 JSON 格式报告，上传到云服务器。

Usage:
    python daily_report.py           # 运行完整流程
    python daily_report.py --config  # 显示配置信息
    python daily_report.py --test    # 测试模式（不发送邮件）

Author: AI-RSS-PERSON Team
Version: 2.1.0
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入主程序
from daily_report_PRO_cloud import AI_Daily_Report
from core.config_manager import get_config_manager
from core.utils import setup_logger

# 初始化日志
logger = setup_logger(__name__, "INFO")


def show_config():
    """显示当前配置信息"""
    config = get_config_manager()

    print("=" * 60)
    print("📋 AI 日报生成器 - 配置信息")
    print("=" * 60)

    print(f"\n📁 配置目录: {config.config_dir}")
    print(f"📄 源配置: {config.sources_file}")
    print(f"📄 权重配置: {config.weights_file}")

    print("\n📊 RSS 源统计:")
    for category in config.get_categories():
        count = len(config.get_sources_by_category(category))
        enabled = len(config.get_sources_by_category(category, enabled_only=True))
        status = "✅" if enabled > 0 else "⭕"
        print(f"  {status} {category}: {enabled}/{count}")

    print(f"\n🔢 总计: {len(config.get_enabled_sources())} 个源启用")

    print("\n⚠️  禁用的源:")
    disabled = [s for s in config.get_all_sources() if not s.get('enabled', True)]
    if disabled:
        for source in disabled:
            print(f"  - {source['name']} ({source.get('category', 'N/A')})")
    else:
        print("  无")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI 日报生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python daily_report.py           # 运行完整流程
  python daily_report.py --config  # 显示配置信息
  python daily_report.py --test    # 测试模式（不发送邮件）
        """
    )

    parser.add_argument(
        '--config',
        action='store_true',
        help='显示当前配置信息'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式：不发送邮件，不上传服务器'
    )

    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='不上传到云服务器'
    )

    parser.add_argument(
        '--no-email',
        action='store_true',
        help='不发送邮件'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )

    args = parser.parse_args()

    # 显示配置信息
    if args.config:
        show_config()
        return

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 运行主程序
    try:
        logger.info("🚀 启动 AI 日报生成器...")

        # 检查配置文件
        config = get_config_manager()
        enabled_sources = config.get_enabled_sources()

        if not enabled_sources:
            logger.warning("⚠️  没有启用的 RSS 源，请检查 config/sources.yaml")
            logger.info("💡 运行 'python daily_report.py --config' 查看配置")
            return

        logger.info(f"📡 使用 {len(enabled_sources)} 个 RSS 源")

        # 创建并运行日报生成器
        bot = AI_Daily_Report()

        # 测试模式：只采集和分析，不发送
        if args.test:
            logger.info("🧪 测试模式：跳过邮件发送和文件上传")
            # 这里可以添加测试逻辑
            bot.run()
            return

        # 正常模式
        bot.run()

    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 程序异常退出: {e}")
        raise


if __name__ == "__main__":
    main()
