#!/bin/bash
# AI 日报生成器 - macOS 版本
# 检查本地 RSSHub (npm 部署) 服务状态

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

# 检查 RSSHub 服务状态 (npm 部署，端口 1200)
echo -e "${YELLOW}[1/3] 检查 RSSHub 服务状态...${NC}"

if curl -s -o /dev/null -w "%{http_code}" http://localhost:1200 | grep -q "200"; then
    echo -e "${GREEN}✅ RSSHub 服务运行正常${NC} (http://localhost:1200)"
else
    echo -e "${RED}❌ RSSHub 服务未响应${NC}"
    echo -e "${YELLOW}⚠️  请启动 RSSHub: cd <rsshub目录> && npm start${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════╗${NC}"
echo ""

# 记录启动时间
START_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "${GREEN}🚀 开始时间: ${START_TIME}${NC}"
echo ""

# 运行主脚本
echo -e "${YELLOW}[2/3] 运行日报生成程序...${NC}"
echo ""
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

echo -e "${YELLOW}[3/3] 检查今日报告...${NC}"
TODAY=$(date +%Y-%m-%d)
REPORT_FILE="/Users/MarkHuang/ai-RSS-person/reports/${TODAY}.json"
if [ -f "$REPORT_FILE" ]; then
    ARTICLE_COUNT=$(python3 -c "import json; print(json.load(open('$REPORT_FILE')).get('total_articles', 0))" 2>/dev/null || echo "?")
    echo -e "${GREEN}✅ 报告已生成: $ARTICLE_COUNT 篇文章${NC}"
else
    echo -e "${YELLOW}⚠️  未找到今日报告文件${NC}"
fi

exit $EXIT_CODE
