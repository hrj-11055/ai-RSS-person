#!/bin/bash
# AI-RSS-PERSON 健康检查脚本
# 检查今日报告与运行摘要（run_summary），输出动态稳定性指标

set -e

# ================= 配置区域 =================
PROJECT_DIR="/opt/ai-RSS-person"
ENV_FILE="${PROJECT_DIR}/.env"
LOG_FILE="${PROJECT_DIR}/logs/health-check.log"

# 中文源关键词（用于识别中文新闻）
CHINESE_PATTERNS="量子位|新智元|36氪|机器之心|极客公园|InfoQ|AI前线|智东西|钛媒体|虎嗅|甲子光年|少数派|阮一峰|逛逛GitHub|赛博禅心|夕小瑶|AIBase"

# 静态阈值（动态阈值会在此基础上调整）
MIN_TOTAL_ARTICLES=30
MIN_CHINESE_ARTICLES=10

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPORT_DIR="${PROJECT_DIR}/reports"
PIPELINE_DIR="${REPORT_DIR}/.pipeline"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

resolve_paths_from_env() {
    if [ -f "$ENV_FILE" ]; then
        local output_dir
        output_dir=$(grep -E '^OUTPUT_DIR=' "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true)
        local pipeline_cache_dir
        pipeline_cache_dir=$(grep -E '^PIPELINE_CACHE_DIR=' "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true)

        if [ -n "$output_dir" ]; then
            if [[ "$output_dir" = /* ]]; then
                REPORT_DIR="$output_dir"
            else
                REPORT_DIR="${PROJECT_DIR}/${output_dir}"
            fi
        fi

        if [ -n "$pipeline_cache_dir" ]; then
            if [[ "$pipeline_cache_dir" = /* ]]; then
                PIPELINE_DIR="$pipeline_cache_dir"
            else
                PIPELINE_DIR="${PROJECT_DIR}/${pipeline_cache_dir}"
            fi
        else
            PIPELINE_DIR="${REPORT_DIR}/.pipeline"
        fi
    fi
}

calc_recent_avg_articles() {
    local today="$1"
    find "$REPORT_DIR" -maxdepth 1 -name '*.json' -type f 2>/dev/null | grep -v "${today}\.json" | tail -n 7 | while read -r f; do
        jq '.total_articles // 0' "$f" 2>/dev/null || echo 0
    done | awk '{sum+=$1; count+=1} END {if (count>0) printf "%.2f", sum/count; else print "0"}'
}

check_run_summary() {
    local today="$1"
    local summary_file="${PIPELINE_DIR}/${today}_run_summary.json"

    if [ ! -f "$summary_file" ]; then
        log "⚠️ 未找到 run_summary: $summary_file"
        return 0
    fi

    local run_id
    run_id=$(jq -r '.run_id // "-"' "$summary_file" 2>/dev/null || echo "-")
    local success_rate
    success_rate=$(jq -r '.stage_success_rate // 0' "$summary_file" 2>/dev/null || echo 0)
    local total_duration
    total_duration=$(jq -r '.total_duration_ms // 0' "$summary_file" 2>/dev/null || echo 0)

    local avg_duration
    avg_duration=$(jq -r '.observability_report.pipeline_stats.avg_total_duration_ms // 0' "$summary_file" 2>/dev/null || echo 0)
    local sample_runs
    sample_runs=$(jq -r '.observability_report.pipeline_stats.sample_runs // 0' "$summary_file" 2>/dev/null || echo 0)

    log "🧭 run_id: $run_id"
    log "📈 阶段成功率: ${success_rate}%"
    log "⏱️ 总耗时: ${total_duration}ms (历史均值 ${avg_duration}ms, 样本 ${sample_runs})"

    if awk "BEGIN{exit !($success_rate < 100)}"; then
        send_alert "⚠️ 阶段成功率低于 100%: ${success_rate}%"
    fi

    if awk "BEGIN{exit !($sample_runs >= 3 && $avg_duration > 0 && $total_duration > $avg_duration * 1.5)}"; then
        log "⚠️ 本次耗时显著高于历史均值（>1.5x）"
        send_alert "⚠️ 本次耗时异常: ${total_duration}ms, 历史均值 ${avg_duration}ms"
    fi

    local top_errors
    top_errors=$(jq -r '.observability_report.pipeline_stats.top_error_codes[]?.error_code' "$summary_file" 2>/dev/null | head -n 3 | tr '\n' ',' | sed 's/,$//')
    if [ -n "$top_errors" ]; then
        log "🚨 Top 错误码: $top_errors"
        send_alert "⚠️ 发现错误码: $top_errors"
    else
        log "✅ 未发现错误码"
    fi

    local top_sources
    top_sources=$(jq -r '.observability_report.rss_insights.top_common_sources[]? | "\(.source):\(.count)"' "$summary_file" 2>/dev/null | head -n 5 | tr '\n' ',' | sed 's/,$//')
    if [ -n "$top_sources" ]; then
        log "📰 热门 RSS 源: $top_sources"
    fi
}

# 检查今日报告
check_today_report() {
    local today
    today=$(date +%Y-%m-%d)
    local report_file="${REPORT_DIR}/${today}.json"

    echo "=========================================="
    echo "   AI-RSS-PERSON 健康检查"
    echo "   日期: $today"
    echo "=========================================="
    echo ""

    if [ ! -f "$report_file" ]; then
        log "❌ 错误: 今日报告未生成"
        log "   预期路径: $report_file"
        send_alert "❌ AI日报未生成: $today"
        return 1
    fi

    log "✅ 今日报告已生成: $report_file"

    local article_count
    article_count=$(jq '.total_articles // 0' "$report_file" 2>/dev/null || echo 0)
    log "📊 文章总数: $article_count"

    local recent_avg
    recent_avg=$(calc_recent_avg_articles "$today")
    local dynamic_min
    dynamic_min=$(awk -v fixed="$MIN_TOTAL_ARTICLES" -v avg="$recent_avg" 'BEGIN{d=avg*0.5; if (d<fixed) d=fixed; printf "%d", d}')
    log "📐 动态文章阈值: $dynamic_min (近7次均值: $recent_avg)"

    if [ "$article_count" -lt "$dynamic_min" ]; then
        log "⚠️ 警告: 文章数量偏低 (当前=$article_count, 动态阈值=$dynamic_min)"
        send_alert "⚠️ 文章数量偏低: $article_count < $dynamic_min"
    fi

    local chinese_count
    chinese_count=$(jq "[.articles[] | select(.source | test(\"$CHINESE_PATTERNS\"))] | length" "$report_file" 2>/dev/null || echo 0)
    log "🇨🇳 中文新闻: $chinese_count"

    if [ "$chinese_count" -lt "$MIN_CHINESE_ARTICLES" ]; then
        log "⚠️ 警告: 中文新闻过少 (期望 ≥ $MIN_CHINESE_ARTICLES)"
        send_alert "⚠️ 中文新闻过少: $chinese_count (期望 ≥ $MIN_CHINESE_ARTICLES)"
    fi

    local generated_at
    generated_at=$(jq -r '.generated_at // "unknown"' "$report_file")
    log "⏰ 生成时间: $generated_at"

    log "📰 中文新闻来源:"
    jq -r ".articles[] | select(.source | test(\"$CHINESE_PATTERNS\")) | \"  - \(.source): \(.title[:50])\"" "$report_file" 2>/dev/null | head -20 | tee -a "$LOG_FILE"

    check_run_summary "$today"

    echo ""
    log "✅ 健康检查完成"
    return 0
}

# 发送告警（可选）
send_alert() {
    local message="$1"
    # 这里可以接入钉钉、企微、邮件等告警方式
    log "🚨 告警: $message"
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
        local next_run
        next_run=$(systemctl list-timers ai-rss-daily.timer --no-pager | awk 'NR==4 {print $1}')
        log "📅 下次执行: $next_run"
    else
        log "❌ 定时任务未运行"
    fi
}

show_help() {
    cat << '__HELP__'
用法: $0 [选项]

选项:
    --report-only     只检查报告，不检查服务状态
    --services-only   只检查服务状态
    --send-alert      发送告警（需要配置 WEBHOOK）
    -h, --help        显示帮助信息

示例:
    $0                # 完整检查
    $0 --report-only  # 只检查报告

__HELP__
}

main() {
    resolve_paths_from_env

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
