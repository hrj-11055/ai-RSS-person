#!/bin/bash
# 更新 .env 中 Twitter Cookie 字段并重启 RSSHub（npm/systemd/pm2）

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

get_env() {
  local key="$1"
  if [ -f "$ENV_FILE" ]; then
    grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true
  fi
}

set_env() {
  local key="$1"
  local value="$2"
  touch "$ENV_FILE"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i '' "s|^${key}=.*$|${key}=${value}|" "$ENV_FILE" 2>/dev/null || sed -i "s|^${key}=.*$|${key}=${value}|" "$ENV_FILE"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
  fi
}

extract_field() {
  local cookie="$1"
  local field="$2"
  echo "$cookie" | sed 's/; /;/g' | tr ';' '\n' | sed 's/^ *//;s/ *$//' | grep -E "^${field}=" | head -n1 | cut -d '=' -f2-
}

restart_rsshub() {
  local restart_cmd service_name pm2_name
  restart_cmd="$(get_env RSSHUB_RESTART_CMD)"
  service_name="$(get_env RSSHUB_SERVICE_NAME)"
  pm2_name="$(get_env RSSHUB_PM2_NAME)"

  if [ -n "$restart_cmd" ]; then
    bash -lc "$restart_cmd"
    return
  fi
  if [ -n "$service_name" ] && systemctl list-unit-files | grep -q "^${service_name}"; then
    systemctl restart "$service_name"
    return
  fi
  if [ -n "$pm2_name" ] && command -v pm2 >/dev/null 2>&1; then
    pm2 restart "$pm2_name"
    return
  fi
  echo "⚠️ 未配置 RSSHub 重启命令（RSSHUB_RESTART_CMD / RSSHUB_SERVICE_NAME）"
}

echo "============================================================"
echo "🍪 Twitter Cookie 更新工具（npm版）"
echo "============================================================"

echo "请粘贴完整 Cookie（包含 auth_token 和 ct0，结束后 Ctrl+D）："
RAW_COOKIE="$(cat)"

if [ -z "$RAW_COOKIE" ]; then
  echo "❌ Cookie 为空"
  exit 1
fi

AUTH_TOKEN="$(extract_field "$RAW_COOKIE" auth_token)"
CT0="$(extract_field "$RAW_COOKIE" ct0)"

if [ -z "$AUTH_TOKEN" ] || [ -z "$CT0" ]; then
  echo "❌ 无法从 Cookie 中提取 auth_token/ct0"
  exit 1
fi

set_env "TWITTER_AUTH_TOKEN" "$AUTH_TOKEN"
set_env "TWITTER_CT0" "$CT0"

echo "✅ 已更新 .env 中 TWITTER_AUTH_TOKEN / TWITTER_CT0"

restart_rsshub
sleep 3

if curl -fsS --max-time 20 "http://localhost:1200/twitter/user/OpenAI" >/dev/null 2>&1; then
  echo "✅ Twitter 路由验证成功"
else
  echo "⚠️ Twitter 路由验证失败（可能是临时限流/认证问题）"
fi
