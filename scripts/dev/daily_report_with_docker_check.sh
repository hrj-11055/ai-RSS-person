#!/bin/bash
# AI 日报生成器 - 带Docker检查
# 确保RSSHub和Redis服务在运行前启动

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   AI 日报生成器 v2.0                    ║${NC}"
echo -e "${GREEN}║   RSS-PERSON Project                      ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════╣${NC}"
echo ""

# 检查Docker服务状态
echo -e "${YELLOW}[1/5] 检查 Docker 服务状态...${NC}"

# 检查关键容器
RSSHUB_RUNNING=$(docker ps -q -f name=rss-person-rsshub)
REDIS_RUNNING=$(docker ps -q -f name=rss-person-redis)

if [ -z "$RSSHUB_RUNNING" ] || [ -z "$REDIS_RUNNING" ]; then
    echo -e "${RED}❌ Docker 服务未运行${NC}"
    echo -e "${YELLOW}⚠️  启动必要的 Docker 服务...${NC}"

    # 启动服务
    docker compose up -d > /dev/null 2>&1

    # 等待服务启动
    echo -e "${YELLOW}⏳ 等待服务启动 (5秒)...${NC}"
    sleep 5

    # 验证服务状态
    if docker ps -q -f name=rss-person-rsshub && docker ps -q -f name=rss-person-redis; then
        echo -e "${GREEN}✅ Docker 服务已启动${NC}"
    else
        echo -e "${RED}❌ Docker 服务启动失败${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Docker 服务运行正常${NC}"
    echo -e "    RSSHub: $(docker ps -q -f name=rss-person-rsshub > /dev/null && echo "运行中" || echo "未运行")"
    echo -e "    Redis:   $(docker ps -q -f name=rss-person-redis > /dev/null && echo "运行中" || echo "未运行")"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════╗${NC}"
echo ""

# 记录启动时间
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "${GREEN}🚀 开始时间: ${START_TIME}${NC}"
echo ""

# 运行主脚本
/Users/MarkHuang/miniconda3/bin/python3 /Users/MarkHuang/ai-RSS-person/daily_report_PRO_cloud.py

EXIT_CODE=$?

# 记录结束时间
END_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo ""
echo -e "${GREEN}╠══════════════════════════════════════╣${NC}"
echo -e "${GREEN}║   完成时间: ${END_TIME}                ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════╣${NC}"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 日报生成成功${NC}"
else
    echo -e "${RED}❌ 日报生成失败 (退出码: $EXIT_CODE)${NC}"
fi

exit $EXIT_CODE
