#!/bin/bash
# AI 日报生成器 - npm/systemd 版
# 确保 RSSHub 服务可访问后再执行日报生成

set -euo pipefail

SCRIPT_DIR="/Users/MarkHuang/ai-RSS-person"
ENV_FILE="${SCRIPT_DIR}/.env"
PYTHON_BIN="/Users/MarkHuang/miniconda3/bin/python3"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

get_env() {
  local key="$1"
  if [ -f "$ENV_FILE" ]; then
    grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true
  fi
}

run_if_set() {
  local cmd="$1"
  if [ -n "$cmd" ]; then
    bash -lc "$cmd"
    return $?
  fi
  return 1
}

start_rsshub_if_needed() {
  local start_cmd service_name pm2_name
  start_cmd="$(get_env RSSHUB_START_CMD)"
  service_name="$(get_env RSSHUB_SERVICE_NAME)"
  pm2_name="$(get_env RSSHUB_PM2_NAME)"

  if run_if_set "$start_cmd"; then
    return 0
  fi
  if [ -n "$service_name" ] && systemctl list-unit-files | grep -q "^${service_name}"; then
    systemctl start "$service_name"
    return 0
  fi
  if [ -n "$pm2_name" ] && command -v pm2 >/dev/null 2>&1; then
    pm2 start "$pm2_name" || pm2 restart "$pm2_name"
    return 0
  fi
  return 1
}

echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   AI 日报生成器 v2.0 (npm版)          ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════╣${NC}"

echo -e "${YELLOW}[1/3] 检查 RSSHub 服务状态...${NC}"
if curl -fsS --max-time 10 http://localhost:1200 >/dev/null 2>&1; then
  echo -e "${GREEN}✅ RSSHub 服务运行正常${NC}"
else
  echo -e "${YELLOW}⚠️ RSSHub 未响应，尝试自动启动...${NC}"
  if start_rsshub_if_needed; then
    sleep 5
  else
    echo -e "${RED}❌ 无法自动启动 RSSHub，请配置 RSSHUB_START_CMD 或 RSSHUB_SERVICE_NAME${NC}"
    exit 1
  fi
fi

if ! curl -fsS --max-time 10 http://localhost:1200 >/dev/null 2>&1; then
  echo -e "${RED}❌ RSSHub 仍不可访问${NC}"
  exit 1
fi

echo -e "${YELLOW}[2/3] 运行日报生成程序...${NC}"
"$PYTHON_BIN" "$SCRIPT_DIR/daily_report_PRO_cloud.py"
EXIT_CODE=$?

echo -e "${YELLOW}[3/3] 检查今日报告...${NC}"
TODAY=$(date +%Y-%m-%d)
REPORT_FILE="$SCRIPT_DIR/reports/${TODAY}.json"
if [ -f "$REPORT_FILE" ]; then
  ARTICLE_COUNT=$($PYTHON_BIN -c "import json; print(json.load(open('$REPORT_FILE')).get('total_articles', 0))" 2>/dev/null || echo "?")
  echo -e "${GREEN}✅ 报告已生成: $ARTICLE_COUNT 篇文章${NC}"
else
  echo -e "${YELLOW}⚠️ 未找到今日报告文件${NC}"
fi

exit $EXIT_CODE
