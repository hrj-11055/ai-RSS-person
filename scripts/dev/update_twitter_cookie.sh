#!/bin/bash
#
# 更新 RSSHub Twitter Cookie 并重启容器
#
# 使用方法:
#   1. 从浏览器复制最新的 Twitter Cookie
#   2. 运行: ./update_twitter_cookie.sh
#   3. 粘贴 Cookie（按 Ctrl+D 结束输入）
#

set -e

DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_FILE="docker-compose.yml.backup"

echo "============================================================"
echo "🍪 Twitter Cookie 更新工具"
echo "============================================================"
echo ""

# 备份当前配置
echo "📦 备份当前配置..."
cp "$DOCKER_COMPOSE_FILE" "$BACKUP_FILE"
echo "✅ 已备份到 $BACKUP_FILE"
echo ""

# 获取新的 Cookie
echo "📋 请从浏览器复制最新的 Twitter Cookie"
echo "   访问 https://twitter.com → F12 → Network → Headers → cookie"
echo ""
echo "粘贴新的 Cookie（完成后按 Ctrl+D）："
echo ""

# 读取用户输入
NEW_COOKIE=$(cat)

if [ -z "$NEW_COOKIE" ]; then
    echo "❌ Cookie 为空，未更新"
    exit 1
fi

echo ""
echo "✅ 已读取 Cookie（长度: ${#NEW_COOKIE} 字符）"
echo ""

# 更新 docker-compose.yml 中的 TWITTER_COOKIE
echo "🔄 更新 $DOCKER_COMPOSE_FILE ..."

# 使用 sed 替换 TWITTER_COOKIE 的值
# macOS 和 Linux 的 sed 语法不同，需要判断
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|TWITTER_COOKIE=.*|TWITTER_COOKIE=$NEW_COOKIE|g" "$DOCKER_COMPOSE_FILE"
else
    # Linux
    sed -i "s|TWITTER_COOKIE=.*|TWITTER_COOKIE=$NEW_COOKIE|g" "$DOCKER_COMPOSE_FILE"
fi

echo "✅ 已更新 TWITTER_COOKIE"
echo ""

# 重启 RSSHub 容器
echo "🔄 重启 RSSHub 容器..."
docker-compose restart rsshub

echo ""
echo "⏳ 等待容器启动（5秒）..."
sleep 5

# 检查容器状态
if docker ps | grep -q "rss-person-rsshub"; then
    echo "✅ RSSHub 容器已启动"
    echo ""
    echo "============================================================"
    echo "🎉 更新完成！"
    echo "============================================================"
    echo ""
    echo "测试命令："
    echo "  python3 test_rsshub_sources.py"
    echo ""
else
    echo "❌ RSSHub 容器启动失败"
    echo "恢复备份..."
    cp "$BACKUP_FILE" "$DOCKER_COMPOSE_FILE"
    docker-compose restart rsshub
    echo "已恢复到之前的配置"
    exit 1
fi
