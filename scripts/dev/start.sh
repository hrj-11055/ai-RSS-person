#!/bin/bash
# AI RSS 项目 - 一键启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   AI RSS 项目 - 一键启动              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════╝${NC}"
echo -e "${GREEN}✅ 启动 Docker 服务...${NC}"
docker compose up -d

echo -e "${GREEN}📊 等待服务启动 (5秒)...${NC}"
sleep 5

echo -e "${GREEN}✅ 显示服务状态:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "${GREEN}══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  选择操作:                          ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════╣${NC}"
echo -e "${GREEN}1. 运行日报生成 (完成后自动关闭)     ║${NC}"
echo -e "${GREEN}2. 仅关闭服务                          ║${NC}"
echo -e "${GREEN}3. 保持运行                              ║${NC}"
echo -e "${GREEN}══════════════════════════════════════╝${NC}"
echo -ne "${YELLOW}请输入选项 (1/2/3): ${NC}"
read -r choice

case $choice in
    1)
        echo -e "${GREEN}🚀 运行日报生成...${NC}"
        /Users/MarkHuang/miniconda3/bin/python3 /Users/MarkHuang/ai-RSS-person/daily_report_PRO_cloud.py

        echo -e "${GREEN}✅ 日报生成完成${NC}"
        echo -e "${YELLOW}🛑 关闭 Docker 服务...${NC}"
        docker compose down
        echo -e "${GREEN}✅ 已关闭所有服务${NC}"
        ;;
    2)
        echo -e "${YELLOW}🛑 关闭 Docker 服务...${NC}"
        docker compose down
        echo -e "${GREEN}✅ 已关闭所有服务${NC}"
        ;;
    3)
        echo -e "${GREEN}✅ 服务保持运行${NC}"
        echo -e "${GREEN}使用以下命令手动关闭:${NC}"
        echo -e "${YELLOW}docker compose down${NC}"
        ;;
    *)
        echo -e "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac
