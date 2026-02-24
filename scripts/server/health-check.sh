#!/bin/bash
# AI-RSS-PERSON 健康检查脚本
# 检查今日报告是否生成，统计文章数量和中文新闻数量

set -e

# ================= 配置区域 =================
PROJECT_DIR="/opt/ai-RSS-person"
REPORT_DIR="${PROJECT_DIR}/reports"
LOG_FILE="${PROJECT_DIR}/logs/health-check.log"

# 中文源关键词（用于识别中文新闻）
CHINESE_PATTERNS="量子位|新智元|36氪|机器之心|极客公园|InfoQ|AI前线|智东西|钛媒体|虎嗅|甲子光年|少数派|阮一峰|逛逛GitHub|赛博禅心|夕小瑶|AIBase"

# 阈值配置
MIN_TOTAL_ARTICLES=30      # 最低文章总数
MIN_CHINESE_ARTICLES=10    # 最低中文新闻数

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查今日报告
check_today_report() {
    TODAY=$(date +%Y-%m-%d)
    REPORT_FILE="${REPORT_DIR}/${TODAY}.json"

    echo "=========================================="
    echo "   AI-RSS-PERSON 健康检查"
    echo "   日期: $TODAY"
    echo "=========================================="
    echo ""

    # 检查报告文件是否存在
    if [ ! -f "$REPORT_FILE" ]; then
        log "❌ 错误: 今日报告未生成"
        log "   预期路径: $REPORT_FILE"
        send_alert "❌ AI日报未生成: $TODAY"
        return 1
    fi

    log "✅ 今日报告已生成: $REPORT_FILE"

    # 检查文章总数
    ARTICLE_COUNT=$(jq '.total_articles // 0' "$REPORT_FILE" 2>/dev/null || echo 0)
    log "📊 文章总数: $ARTICLE_COUNT"

    if [ "$ARTICLE_COUNT" -lt "$MIN_TOTAL_ARTICLES" ]; then
        log "⚠️  警告: 文章数量过少 (期望 ≥ $MIN_TOTAL_ARTICLES)"
    fi

    # 检查中文新闻数量
    CHINESE_COUNT=$(jq "[.articles[] | select(.source | test(\"$CHINESE_PATTERNS\"))] | length" "$REPORT_FILE" 2>/dev/null || echo 0)
    log "🇨🇳 中文新闻: $CHINESE_COUNT"

    if [ "$CHINESE_COUNT" -lt "$MIN_CHINESE_ARTICLES" ]; then
        log "⚠️  警告: 中文新闻过少 (期望 ≥ $MIN_CHINESE_ARTICLES)"
        send_alert "⚠️ 中文新闻过少: $CHINESE_COUNT (期望 ≥ $MIN_CHINESE_ARTICLES)"
    fi

    # 检查报告生成时间
    GENERATED_AT=$(jq -r '.generated_at // "unknown"' "$REPORT_FILE")
    log "⏰ 生成时间: $GENERATED_AT"

    # 列出中文新闻来源
    echo ""
    log "📰 中文新闻来源:"
    jq -r ".articles[] | select(.source | test(\"$CHINESE_PATTERNS\")) | \"  - \(.source): \(.title[:50])\"" "$REPORT_FILE" 2>/dev/null | head -20 | tee -a "$LOG_FILE"

    echo ""
    log "✅ 健康检查完成"
    return 0
}

# 发送告警（可选）
send_alert() {
    local MESSAGE="$1"
    # 这里可以接入钉钉、企微、邮件等告警方式
    # 示例: 钉钉机器人
    # curl -X POST "$DINGTALK_WEBHOOK" -H "Content-Type: application/json" \
    #     -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"$MESSAGE\"}}"

    log "🚨 告警: $MESSAGE"
}

# 检查 RSSHub 状态
check_rsshub() {
    echo ""
    log "🔍 检查 RSSHub 状态..."

    if curl -f -s http://localhost:1200 > /dev/null 2>&1; then
        log "✅ RSSHub 运行正常"
    else
        log "❌ RSSHub 无法访问"
        return 1
    fi
}

# 检查定时任务状态
check_timer() {
    echo ""
    log "🔍 检查定时任务状态..."

    if systemctl is-active --quiet ai-rss-daily.timer; then
        log "✅ 定时任务运行中"
        # 查看下次执行时间
        NEXT_RUN=$(systemctl list-timers ai-rss-daily.timer --no-pager | awk 'NR==4 {print $1}')
        log "📅 下次执行: $NEXT_RUN"
    else
        log "❌ 定时任务未运行"
    fi
}

# 显示使用帮助
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
    --report-only     只检查报告，不检查服务状态
    --services-only   只检查服务状态
    --send-alert      发送告警（需要配置 WEBHOOK）
    -h, --help        显示帮助信息

示例:
    $0                # 完整检查
    $0 --report-only  # 只检查报告

EOF
}

# ================= 主流程 =================
main() {
    case "${1:-}" in
        --report-only)
            check_today_report
            ;;
        --services-only)
            check_rsshub
            check_timer
            ;;
        --send-alert)
            send_alert "测试告警"
            ;;
        -h|--help)
            show_help
            ;;
        *)
            check_today_report
            check_rsshub
            check_timer
            ;;
    esac
}

main "$@"
