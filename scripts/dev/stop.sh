#!/bin/bash
# AI RSS 项目 - 快速停止脚本（npm/systemd/pm2 版本）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

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

echo -e "${RED}╔════════════════════════════════════╗${NC}"
echo -e "${RED}║   AI RSS 项目 - 快速停止 (npm版)     ║${NC}"
echo -e "${RED}╚══════════════════════════════════════╝${NC}"

echo -e "${YELLOW}⚠️  停止 RSSHub 服务...${NC}"
if stop_rsshub; then
  echo -e "${GREEN}✅ RSSHub 已停止${NC}"
else
  echo -e "${YELLOW}⚠️ 未找到 RSSHub 停止配置（请设置 RSSHUB_STOP_CMD 或 RSSHUB_SERVICE_NAME）${NC}"
fi
