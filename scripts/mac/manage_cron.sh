#!/bin/bash
# Mac 定时任务管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="$SCRIPT_DIR/com.aireport.daily.plist"
LOG_DIR="$SCRIPT_DIR/logs"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

case "$1" in
    install)
        echo "📦 安装每日日报定时任务..."
        # 复制 plist 文件到 LaunchAgents 目录
        cp "$PLIST_FILE" ~/Library/LaunchAgents/
        # 加载任务
        launchctl load ~/Library/LaunchAgents/com.aireport.daily.plist
        echo "✅ 定时任务已安装！"
        echo "⏰ 将在每天早上 7:00 运行"
        echo ""
        echo "📋 任务流程："
        echo "   1. 收集 RSS 文章 → 排序 → AI 分析"
        echo "   2. 生成 Markdown 报告 (YYYY-MM-DD.md)"
        echo "   3. 生成 JSON 数据 (YYYY-MM-DD.json)"
        echo "   4. 上传 JSON 到云服务器"
        echo "   5. 发送邮件（Markdown 作为附件）"
        echo ""
        echo "📝 常用命令："
        echo "   ./manage_cron.sh status    - 查看任务状态"
        echo "   ./manage_cron.sh logs      - 查看运行日志"
        echo "   ./manage_cron.sh test      - 手动运行一次"
        echo "   ./manage_cron.sh uninstall - 卸载定时任务"
        ;;

    uninstall)
        echo "🗑️  卸载定时任务..."
        launchctl unload ~/Library/LaunchAgents/com.aireport.daily.plist 2>/dev/null
        rm ~/Library/LaunchAgents/com.aireport.daily.plist 2>/dev/null
        echo "✅ 定时任务已卸载"
        ;;

    status)
        echo "📊 任务状态："
        echo ""
        launchctl list | grep com.aireport.daily && echo "✅ 已安装 (7:00 AM)" || echo "❌ 未安装"
        ;;

    logs)
        echo "📋 最近20行日志："
        echo "==================== stdout.log ===================="
        tail -20 "$LOG_DIR/stdout.log" 2>/dev/null || echo "暂无日志"
        echo ""
        echo "==================== stderr.log ===================="
        tail -20 "$LOG_DIR/stderr.log" 2>/dev/null || echo "暂无日志"
        ;;

    test)
        echo "🧪 手动运行完整流程..."
        cd "$SCRIPT_DIR"
        /Users/MarkHuang/miniconda3/bin/python3 daily_report_PRO_cloud.py
        ;;

    test-email)
        echo "🧪 测试邮件发送（需要先生成报告）..."
        cd "$SCRIPT_DIR"
        /Users/MarkHuang/miniconda3/bin/python3 daily_email_sender.sh
        ;;

    edit)
        echo "✏️  编辑定时配置文件..."
        vim "$PLIST_FILE"
        echo "⚠️  修改后需要重新安装："
        echo "   ./manage_cron.sh uninstall"
        echo "   ./manage_cron.sh install"
        ;;

    *)
        echo "========================================"
        echo "   AI-RSS-PERSON 定时任务管理"
        echo "========================================"
        echo ""
        echo "基本操作："
        echo "  ./manage_cron.sh install   - 安装定时任务 (7:00 AM)"
        echo "  ./manage_cron.sh uninstall - 卸载定时任务"
        echo ""
        echo "查看状态："
        echo "  ./manage_cron.sh status    - 查看任务状态"
        echo "  ./manage_cron.sh logs      - 查看运行日志"
        echo ""
        echo "测试功能："
        echo "  ./manage_cron.sh test      - 手动运行完整流程"
        echo "  ./manage_cron.sh test-email - 测试邮件发送"
        echo ""
        echo "编辑配置："
        echo "  ./manage_cron.sh edit      - 编辑定时配置"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📋 任务流程（7:00 AM 执行）："
        echo "   ① 收集 RSS 文章（27 源）"
        echo "   ② 双重评分排序（源权威性 + 内容相关性）"
        echo "   ③ AI 分析（DeepSeek API）"
        echo "   ④ 生成 Markdown 报告 → 保存本地"
        echo "   ⑤ 生成 JSON 数据 → 上传云服务器"
        echo "   ⑥ 转换为 Markdown → 发送邮件"
        echo ""
        echo "⚠️  使用前请配置 .env 文件："
        echo "   - DEEPSEEK_API_KEY（必需）"
        echo "   - CLOUD_SERVER_*（云服务器上传）"
        echo "   - EMAIL_*（邮件发送）"
        echo ""
        ;;
esac
