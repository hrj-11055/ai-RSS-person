#!/bin/bash
# 重新发送指定日期的报告到邮箱

REPORT_FILE="$1"

if [ -z "$REPORT_FILE" ]; then
    echo "用法: $0 <报告文件路径>"
    echo "示例: $0 reports/2026-02-15.md"
    exit 1
fi

if [ ! -f "$REPORT_FILE" ]; then
    echo "❌ 文件不存在: $REPORT_FILE"
    exit 1
fi

echo "📧 正在发送报告..."
echo "文件: $REPORT_FILE"

# 获取文件名和扩展
FILENAME=$(basename "$REPORT_FILE")
EXT="${FILENAME##*.}"

# 构建邮件主题
TODAY=$(date "+%Y-%m-%d")
EMAIL_SUBJECT="📊 AI 日报 - $TODAY"

echo "邮件主题: $EMAIL_SUBJECT"
echo ""

# 使用 Python 发送
/Users/MarkHuang/miniconda3/bin/python3 -c "
import sys
sys.path.insert(0, '/Users/MarkHuang/ai-RSS-person')

from email_sender import send_email, md_to_html

# 读取 Markdown 文件
with open('$REPORT_FILE', 'r', encoding='utf-8') as f:
    md_content = f.read()

# 转换为 HTML
html_content = md_to_html(md_content, f'$FILENAME')

# 发送邮件
subject = '$EMAIL_SUBJECT'
success = send_email(subject, html_content, md_content=md_content, md_filename='$FILENAME')

if success:
    print('✅ 邮件发送成功！')
else:
    print('❌ 邮件发送失败')
    exit(1)
"

echo ""
echo "✅ 完成"
