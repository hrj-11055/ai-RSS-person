#!/bin/bash
# RSSHub 服务器启动脚本
# 适用于 Linux 服务器环境

set -e

# 项目目录
PROJECT_DIR="/opt/ai-RSS-person"

# 切换到项目目录
cd "$PROJECT_DIR" || exit 1

echo "🚀 启动 RSSHub 服务..."

# 检查 docker-compose.yml 是否存在
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml 不存在"
    exit 1
fi

# 启动 RSSHub 和 Redis
docker-compose up -d rsshub redis

# 等待服务就绪
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
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
