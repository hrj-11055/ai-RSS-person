#!/usr/bin/env python3
"""
每日邮件自动发送脚本
功能：
1. 检查reports目录下是否有新的JSON报告文件
2. 将JSON转换为Markdown格式
3. 发送邮件到指定收件人
"""

import os
import re
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_required_env(key: str) -> str:
    """获取必需的环境变量"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"缺少必需的环境变量: {key}")
    return value


def get_optional_env(key: str, default: str = "") -> str:
    """获取可选的环境变量"""
    return os.getenv(key, default)


def get_report_date_from_filename(filename: str) -> str:
    """
    从文件名中提取日期
    支持格式：2026-02-11.json 或 2026-02-11
    """
    # 正则表达式匹配 YYYY-MM-DD 格式
    pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    return None


def find_latest_json_file(reports_dir: str) -> str:
    """
    查找最新的JSON报告文件

    Args:
        reports_dir: 报告目录路径

    Returns:
        str: 最新JSON文件的完整路径，如果没有找到返回None
    """
    if not os.path.exists(reports_dir):
        print(f"❌ 报告目录不存在: {reports_dir}")
        return None

    # 正则表达式匹配日期格式JSON文件：YYYY-MM-DD.json
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.json$')

    json_files = []
    for filename in os.listdir(reports_dir):
        if pattern.match(filename):
            file_path = os.path.join(reports_dir, filename)
            # 获取文件修改时间
            mtime = os.path.getmtime(file_path)
            json_files.append((file_path, mtime, filename))

    if not json_files:
        print(f"❌ 在 {reports_dir} 目录中没有找到JSON报告文件")
        print(f"   期望格式：YYYY-MM-DD.json (如：2026-02-11.json)")
        return None

    # 按修改时间排序，获取最新的
    json_files.sort(key=lambda x: x[1], reverse=True)
    latest_file = json_files[0][0]
    latest_filename = json_files[0][2]

    print(f"✅ 找到最新JSON文件: {latest_filename}")
    print(f"   路径: {latest_file}")

    return latest_file


def json_to_markdown(json_file_path: str) -> str:
    """
    将JSON报告转换为Markdown格式

    Args:
        json_file_path: JSON文件路径

    Returns:
        str: 生成的Markdown文件路径
    """
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        report_date = data.get('report_date', 'unknown')
        report_title = data.get('report_title', 'AI日报')
        total_articles = data.get('total_articles', 0)
        articles = data.get('articles', [])

        # 生成Markdown内容
        md_lines = []
        md_lines.append(f"# {report_title}\n")
        md_lines.append(f"**生成时间**: {data.get('generated_at', 'unknown')}")
        md_lines.append(f"**文章总数**: {total_articles}篇\n")
        md_lines.append("---\n")

        for idx, article in enumerate(articles, 1):
            title = article.get('title', '无标题')
            key_point = article.get('key_point', '')
            summary = article.get('summary', '')
            source_url = article.get('source_url', '')
            source_name = article.get('source_name', '未知来源')
            category = article.get('category', '')
            sub_category = article.get('sub_category', '')
            country = article.get('country', '')
            importance_score = article.get('importance_score', 0)

            md_lines.append(f"## {idx}. {title}\n")
            md_lines.append(f"**关键点**: {key_point}\n")
            md_lines.append(f"**摘要**: {summary}\n")
            md_lines.append(f"**来源**: [{source_name}]({source_url})")
            md_lines.append(f"**分类**: {category} / {sub_category} | {country}")
            md_lines.append(f"**重要性**: ⭐ {importance_score}/10")
            md_lines.append("---\n")

        md_content = "\n".join(md_lines)

        # 保存为MD文件
        md_filename = f"{report_date}.md"
        md_file_path = os.path.join(os.path.dirname(json_file_path), md_filename)

        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"✅ Markdown文件已生成: {md_filename}")
        return md_file_path

    except Exception as e:
        print(f"❌ JSON转换失败: {str(e)}")
        return None


def send_email(md_file_path: str) -> bool:
    """
    调用邮件发送脚本

    Args:
        md_file_path: Markdown文件路径

    Returns:
        bool: 发送成功返回True
    """
    try:
        # 导入邮件发送模块
        import subprocess

        script_dir = os.path.dirname(os.path.abspath(__file__))
        email_sender_script = os.path.join(script_dir, 'email_sender.py')

        if not os.path.exists(email_sender_script):
            print(f"❌ 邮件发送脚本不存在: {email_sender_script}")
            return False

        # 调用邮件发送脚本
        print(f"📧 正在发送邮件...")
        result = subprocess.run(
            ['/Users/MarkHuang/miniconda3/bin/python3', email_sender_script, md_file_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✅ 邮件发送成功！")
            return True
        else:
            print(f"❌ 邮件发送失败:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ 发送邮件时出错: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 每日AI日报邮件发送任务")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 获取报告目录
    reports_dir = get_optional_env("OUTPUT_DIR", "reports")
    if not os.path.isabs(reports_dir):
        # 如果是相对路径，转换为绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(script_dir, reports_dir)

    print(f"📁 报告目录: {reports_dir}")
    print()

    # 步骤1: 查找最新的JSON文件
    print("📋 步骤1: 查找最新JSON文件...")
    latest_json = find_latest_json_file(reports_dir)
    if not latest_json:
        print("❌ 未找到JSON文件，任务终止")
        sys.exit(1)

    print()

    # 步骤2: 检查是否已有对应的MD文件
    json_filename = os.path.basename(latest_json)
    json_date = get_report_date_from_filename(json_filename)
    md_file_path = os.path.join(reports_dir, f"{json_date}.md")

    if os.path.exists(md_file_path):
        print(f"📄 Markdown文件已存在: {json_date}.md")
        print(f"   跳过转换步骤")
    else:
        # 步骤2: 转换JSON为MD
        print("📋 步骤2: 转换JSON为Markdown...")
        md_file_path = json_to_markdown(latest_json)
        if not md_file_path:
            print("❌ JSON转换失败，任务终止")
            sys.exit(1)

    print()

    # 步骤3: 发送邮件
    print("📋 步骤3: 发送邮件...")
    success = send_email(md_file_path)

    print()
    print("=" * 60)
    if success:
        print("✅ 任务执行成功！")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ 任务执行失败！")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
