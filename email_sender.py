#!/usr/bin/env python3
"""
qq邮箱邮件发送脚本
支持发送Markdown格式的AI日报
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr, formatdate
from datetime import datetime
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


def send_email(
    subject: str,
    html_content: str,
    md_content: str = None,
    md_filename: str = None
) -> bool:
    """
    发送邮件（支持HTML和附件）

    Args:
        subject: 邮件主题
        html_content: HTML格式邮件正文
        md_content: Markdown附件内容（可选）
        md_filename: Markdown附件文件名（可选）

    Returns:
        bool: 发送成功返回True，失败返回False
    """
    try:
        # 从环境变量获取配置
        smtp_server = get_required_env("SMTP_SERVER")
        smtp_port = int(get_required_env("SMTP_PORT"))
        sender_email = get_required_env("SENDER_EMAIL")
        sender_password = get_required_env("SENDER_PASSWORD")
        receiver_email = get_required_env("RECEIVER_EMAIL")
        cc_email = get_optional_env("CC_EMAIL")
        bcc_email = get_optional_env("BCC_EMAIL")

        # 创建邮件对象
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = formataddr(["AI日报机器人", sender_email])
        msg["To"] = receiver_email
        msg["Date"] = formatdate(localtime=True)

        # 设置抄送和密送
        if cc_email:
            msg["Cc"] = cc_email
        if bcc_email:
            msg["Bcc"] = bcc_email

        # 添加HTML正文
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # 如果提供Markdown内容，添加为附件
        if md_content and md_filename:
            md_part = MIMEApplication(md_content.encode("utf-8"))
            md_part.add_header(
                "Content-Disposition",
                "attachment",
                filename=md_filename
            )
            msg.attach(md_part)

        # 构建收件人列表（包含抄送和密送）
        recipients = [receiver_email]
        if cc_email:
            recipients.extend([email.strip() for email in cc_email.split(",")])
        if bcc_email:
            recipients.extend([email.strip() for email in bcc_email.split(",")])

        # 连接SMTP服务器并发送
        print(f"📧 正在连接SMTP服务器: {smtp_server}:{smtp_port}")

        if smtp_port == 465:
            # SSL连接
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
        else:
            # TLS连接
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())

        print("✅ 邮件发送成功！")
        print(f"📮 收件人: {receiver_email}")
        if cc_email:
            print(f"📋 抄送: {cc_email}")
        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False


def md_to_html(md_content: str, title: str) -> str:
    """
    将Markdown内容转换为简单的HTML格式

    Args:
        md_content: Markdown内容
        title: 邮件标题

    Returns:
        str: HTML内容
    """
    # 简单的Markdown到HTML转换
    html_lines = []
    html_lines.append("<!DOCTYPE html>")
    html_lines.append("<html><head>")
    html_lines.append("<meta charset='utf-8'>")
    html_lines.append("<style>")
    html_lines.append("body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }")
    html_lines.append("h1 { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }")
    html_lines.append("h2 { color: #1d4ed8; margin-top: 30px; }")
    html_lines.append("h3 { color: #1e40af; }")
    html_lines.append("a { color: #2563eb; text-decoration: none; }")
    html_lines.append("a:hover { text-decoration: underline; }")
    html_lines.append("strong { color: #1e3a8a; }")
    html_lines.append("code { background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', 'Courier New', monospace; }")
    html_lines.append("pre { background: #1f2937; color: #f9fafb; padding: 15px; border-radius: 5px; overflow-x: auto; }")
    html_lines.append("pre code { background: transparent; padding: 0; }")
    html_lines.append("blockquote { border-left: 4px solid #3b82f6; padding-left: 15px; color: #6b7280; margin: 15px 0; }")
    html_lines.append("hr { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }")
    html_lines.append(".article { border-left: 3px solid #e5e7eb; padding-left: 15px; margin: 20px 0; }")
    html_lines.append(".meta { color: #6b7280; font-size: 14px; margin-top: 10px; }")
    html_lines.append("</style>")
    html_lines.append("</head><body>")

    # 添加标题
    html_lines.append(f"<h1>{title}</h1>")

    # 处理Markdown内容
    lines = md_content.split("\n")
    in_code_block = False
    in_article = False

    for line in lines:
        # 跳过开头的标题行（已经添加过了）
        if line.startswith("# ") and not in_code_block:
            continue

        # 空行
        if not line:
            if in_article:
                html_lines.append("</div>")
                in_article = False
            html_lines.append("<br>")
            continue

        # 代码块
        if line.startswith("```"):
            if in_code_block:
                html_lines.append("</pre></code>")
                in_code_block = False
            else:
                html_lines.append("<pre><code>")
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(f"<code>{line}</code>")
            continue

        # 一级标题
        if line.startswith("# ") and not in_code_block:
            if in_article:
                html_lines.append("</div>")
                in_article = False
            title_text = line[2:].strip()
            html_lines.append(f"<h1>{title_text}</h1>")
            continue

        # 二级标题（文章标题）
        if line.startswith("## ") and not in_code_block:
            if in_article:
                html_lines.append("</div>")
            title_text = line[3:].strip()
            # 提取序号和标题
            html_lines.append(f"<h2>{title_text}</h2>")
            html_lines.append("<div class='article'>")
            in_article = True
            continue

        # 三级标题
        if line.startswith("### ") and not in_code_block:
            title_text = line[4:].strip()
            html_lines.append(f"<h3>{title_text}</h3>")
            continue

        # 加粗文本
        line = line.replace("**", "<strong>").replace("**", "</strong>") if "**" in line else line

        # 链接 [text](url)
        while "[" in line and "](" in line:
            start = line.find("[")
            end = line.find("]")
            url_start = line.find("](", end)
            url_end = line.find(")", url_start)

            if start >= 0 and end > start and url_start > end and url_end > url_start:
                text = line[start+1:end]
                url = line[url_start+2:url_end]
                link = f'<a href="{url}">{text}</a>'
                line = line[:start] + link + line[url_end+1:]
            else:
                break

        # 分隔线
        if line.strip() == "---":
            if in_article:
                html_lines.append("</div>")
                in_article = False
            html_lines.append("<hr>")
            continue

        # 普通段落
        if line.startswith("**") and ":" in line:
            # 这是一个字段行（如 **关键点**: xxx）
            line = f"<p><strong>{line}</strong></p>"
        elif line.startswith("**来源**:") or line.startswith("**分类**:") or line.startswith("**重要性**:") or line.startswith("**发布时间**:"):
            # 元数据行
            line = f"<div class='meta'>{line}</div>"
        else:
            line = f"<p>{line}</p>"

        html_lines.append(line)

    if in_article:
        html_lines.append("</div>")

    html_lines.append("<hr>")
    html_lines.append("<p style='color: #6b7280; font-size: 12px;'>本邮件由AI自动生成</p>")
    html_lines.append("</body></html>")

    return "\n".join(html_lines)


def send_daily_report(md_file_path: str) -> bool:
    """
    发送每日AI日报

    Args:
        md_file_path: Markdown文件路径

    Returns:
        bool: 发送成功返回True
    """
    try:
        # 读取Markdown文件
        with open(md_file_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 提取标题（第一行）
        first_line = md_content.split("\n")[0]
        title = first_line.replace("# ", "").strip()

        # 生成邮件主题（添加日期）
        today = datetime.now().strftime("%Y-%m-%d")
        email_subject = f"📊 {title} ({today})"

        # 转换为HTML
        html_content = md_to_html(md_content, title)

        # 提取文件名作为附件名
        md_filename = os.path.basename(md_file_path)

        # 发送邮件
        return send_email(
            subject=email_subject,
            html_content=html_content,
            md_content=md_content,
            md_filename=md_filename
        )

    except Exception as e:
        print(f"❌ 发送日报失败: {str(e)}")
        return False


if __name__ == "__main__":
    import sys

    # 获取日志级别
    log_level = get_optional_env("LOG_LEVEL", "INFO")

    if len(sys.argv) > 1:
        # 命令行指定MD文件
        md_file = sys.argv[1]
    else:
        # 默认发送今天生成的最新MD文件
        reports_dir = get_optional_env("OUTPUT_DIR", "reports")
        today = datetime.now().strftime("%Y-%m-%d")

        # 查找今天的MD文件
        md_files = [
            f for f in os.listdir(reports_dir)
            if f.endswith(".md") and today in f
        ]

        if not md_files:
            print(f"❌ 未找到今天({today})的MD报告文件")
            sys.exit(1)

        # 使用最新的文件
        md_files.sort(reverse=True)
        md_file = os.path.join(reports_dir, md_files[0])

    print(f"📄 准备发送报告: {md_file}")

    # 发送邮件
    if send_daily_report(md_file):
        print("✅ 日报发送成功！")
        sys.exit(0)
    else:
        print("❌ 日报发送失败！")
        sys.exit(1)
