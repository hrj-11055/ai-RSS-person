#!/bin/bash
# AI RSS 项目 - 一键启动脚本（npm/systemd/pm2 版本）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
PYTHON_BIN="${PYTHON_BIN:-/Users/MarkHuang/miniconda3/bin/python3}"

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

start_rsshub() {
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

stop_rsshub() {
  local stop_cmd service_name pm2_name
  stop_cmd="$(get_env RSSHUB_STOP_CMD)"
  service_name="$(get_env RSSHUB_SERVICE_NAME)"
  pm2_name="$(get_env RSSHUB_PM2_NAME)"

  if run_if_set "$stop_cmd"; then
    return 0
  fi
  if [ -n "$service_name" ] && systemctl list-unit-files | grep -q "^${service_name}"; then
    systemctl stop "$service_name" || true
    return 0
  fi
  if [ -n "$pm2_name" ] && command -v pm2 >/dev/null 2>&1; then
    pm2 stop "$pm2_name" || true
    return 0
  fi
  return 1
}

echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   AI RSS 项目 - 一键启动 (npm版)     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════╝${NC}"

echo -e "${YELLOW}🔍 检查并启动 RSSHub 服务...${NC}"
if start_rsshub; then
  echo -e "${GREEN}✅ RSSHub 启动命令已执行${NC}"
else
  echo -e "${YELLOW}⚠️ 未找到 RSSHub 启动配置（请设置 RSSHUB_START_CMD 或 RSSHUB_SERVICE_NAME）${NC}"
fi

echo -e "${GREEN}📊 等待服务启动 (3秒)...${NC}"
sleep 3

if curl -fsS --max-time 10 http://localhost:1200 >/dev/null 2>&1; then
  echo -e "${GREEN}✅ RSSHub 可访问: http://localhost:1200${NC}"
else
  echo -e "${RED}❌ RSSHub 不可访问${NC}"
fi

echo -e "${GREEN}══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  选择操作:                          ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════╣${NC}"
echo -e "${GREEN}1. 运行日报生成 (完成后尝试停止RSSHub)║${NC}"
echo -e "${GREEN}2. 仅停止 RSSHub 服务                 ║${NC}"
echo -e "${GREEN}3. 保持运行                            ║${NC}"
echo -e "${GREEN}══════════════════════════════════════╝${NC}"
echo -ne "${YELLOW}请输入选项 (1/2/3): ${NC}"
read -r choice

case $choice in
  1)
    echo -e "${GREEN}🚀 运行日报生成...${NC}"
    "$PYTHON_BIN" "$SCRIPT_DIR/daily_report_PRO_cloud.py"
    echo -e "${GREEN}✅ 日报生成完成${NC}"
    echo -e "${YELLOW}🛑 尝试停止 RSSHub 服务...${NC}"
    stop_rsshub || true
    ;;
  2)
    echo -e "${YELLOW}🛑 停止 RSSHub 服务...${NC}"
    stop_rsshub || true
    ;;
  3)
    echo -e "${GREEN}✅ 服务保持运行${NC}"
    ;;
  *)
    echo -e "${RED}❌ 无效选项${NC}"
    exit 1
    ;;
esac
