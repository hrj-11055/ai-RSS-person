#!/bin/bash
# RSSHub 服务器启动脚本（npm/systemd/pm2 方式）

set -euo pipefail

PROJECT_DIR="/opt/ai-RSS-person"
ENV_FILE="${PROJECT_DIR}/.env"

get_env_value() {
    local key="$1"
    if [ -f "$ENV_FILE" ]; then
        grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true
    fi
}

run_cmd() {
    local cmd="$1"
    if [ -n "$cmd" ]; then
        bash -lc "$cmd"
        return $?
    fi
    return 1
}

echo "🚀 启动 RSSHub 服务..."

RSSHUB_START_CMD="$(get_env_value RSSHUB_START_CMD)"
RSSHUB_SERVICE_NAME="$(get_env_value RSSHUB_SERVICE_NAME)"
RSSHUB_PM2_NAME="$(get_env_value RSSHUB_PM2_NAME)"

if run_cmd "$RSSHUB_START_CMD"; then
    echo "✅ 已执行 RSSHUB_START_CMD"
elif [ -n "$RSSHUB_SERVICE_NAME" ] && systemctl list-unit-files | grep -q "^${RSSHUB_SERVICE_NAME}"; then
    systemctl start "$RSSHUB_SERVICE_NAME"
    echo "✅ 已启动 systemd 服务: $RSSHUB_SERVICE_NAME"
elif [ -n "$RSSHUB_PM2_NAME" ] && command -v pm2 >/dev/null 2>&1; then
    pm2 start "$RSSHUB_PM2_NAME" || pm2 restart "$RSSHUB_PM2_NAME"
    echo "✅ 已启动 pm2 进程: $RSSHUB_PM2_NAME"
else
    echo "❌ 无法确定 RSSHub 启动方式，请在 .env 配置 RSSHUB_START_CMD 或 RSSHUB_SERVICE_NAME"
    exit 1
fi

echo "⏳ 等待服务启动..."
sleep 5

max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f -s http://localhost:1200 > /dev/null 2>&1; then
        echo "✅ RSSHub 启动成功"
        echo "📍 访问地址: http://localhost:1200"
        exit 0
    fi
    attempt=$((attempt + 1))
    echo "⏳ 等待 RSSHub 就绪... ($attempt/$max_attempts)"
    sleep 2
done

echo "❌ RSSHub 启动失败"
exit 1
