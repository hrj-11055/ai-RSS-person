#!/bin/bash
# AI 日报生成器 - 防休眠包装脚本 (macOS)
# 使用 caffeinate 防止 Mac 在运行日报时进入休眠状态

set -e

# 项目目录
PROJECT_DIR="/Users/MarkHuang/ai-RSS-person"
LOG_DIR="$PROJECT_DIR/logs"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 记录开始时间
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "=========================================="
echo "   AI 日报生成器 (防休眠模式)"
echo "   开始时间: $START_TIME"
echo "=========================================="
echo ""
echo "📋 前置要求:"
echo "   1. RSSHub (npm) 服务运行在 http://localhost:1200"
echo "   2. Python 环境已配置"
echo ""

# 使用 caffeinate 防止系统休眠
# -s 参数: 防止系统在 AC 电源下休眠（最常用的选项）
# caffeinate 会一直等待直到命令完成
echo "🛡️  已启用 caffeinate 防休眠保护..."
echo ""

caffeinate -s "$PROJECT_DIR/scripts/mac/daily_report_with_docker_check.sh"

# 记录结束时间
END_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo ""
echo "=========================================="
echo "   完成时间: $END_TIME"
echo "=========================================="
