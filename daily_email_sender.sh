#!/usr/bin/env python3
"""
邮件发送脚本 - JSON 转 Markdown 后发送邮件

流程：
1. 读取今日生成的 JSON 报告
2. 转换为 Markdown 格式
3. 调用 email_sender.py 发送邮件
"""

import os
import sys
import json
import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from core.utils import get_optional_env

# 加载环境变量
load_dotenv()

# 导入报告生成器和邮件发送器
from lib.report_generator import ReportGenerator
from email_sender import send_daily_report

# 配置
OUTPUT_DIR = get_optional_env("OUTPUT_DIR", "reports")


def main():
    """主函数"""
    # 获取今天的日期
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    json_filename = f"{today}.json"
    json_path = os.path.join(OUTPUT_DIR, json_filename)

    # 检查 JSON 文件是否存在
    if not os.path.exists(json_path):
        print(f"❌ 未找到今日报告文件: {json_path}")
        sys.exit(1)

    print(f"📄 读取报告: {json_path}")

    # 读取 JSON 报告
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data.get('articles', [])

    if not articles:
        print("❌ 报告中没有文章数据")
        sys.exit(1)

    print(f"📊 文章数量: {len(articles)}")

    # 生成 Markdown 报告
    print("📝 生成 Markdown 报告...")
    generator = ReportGenerator(output_dir=OUTPUT_DIR)
    md_path = generator.save_markdown(articles, f"{today}.md")

    print(f"✅ Markdown 报告已生成: {md_path}")

    # 发送邮件
    print("📧 发送邮件...")
    if send_daily_report(md_path):
        print("✅ 邮件发送成功！")
        sys.exit(0)
    else:
        print("❌ 邮件发送失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
