#!/bin/bash
# RSSHub 启动脚本 - 自动获取 OrbStack bridge IP 并更新配置

echo "🔍 获取 OrbStack bridge100 IP..."

# 方法1: 获取 bridge100 的 IP
BRIDGE_IP=$(ifconfig bridge100 2>/dev/null | grep "inet " | awk '{print $2}')

# 方法2: 如果 bridge100 不存在，尝试 bridge100:av
if [ -z "$BRIDGE_IP" ]; then
    BRIDGE_IP=$(ifconfig | grep -A 3 "bridge100:" | grep "inet " | awk '{print $2}')
fi

# 方法3: 使用 networksetup
if [ -z "$BRIDGE_IP" ]; then
    BRIDGE_IP=$(networksetup -getinfo "OrbStack" 2>/dev/null | grep "IPv4 Address" | awk '{print $3}')
fi

if [ -z "$BRIDGE_IP" ]; then
    echo "❌ 无法获取 OrbStack bridge IP"
    echo "请手动获取并设置 PROXY_URI"
    exit 1
fi

echo "✅ 获取到 bridge IP: $BRIDGE_IP"

# 更新 docker-compose.yml 中的 PROXY_URI
sed -i.bak "s/PROXY_URI=http:\/\/[0-9.]*/PROXY_URI=http:\/\/$BRIDGE_IP/" docker-compose.yml

echo "🔄 重启 RSSHub..."
docker-compose -f docker-compose.yml restart rsshub

echo "✅ RSSHub 已启动，代理: $BRIDGE_IP:7897"
