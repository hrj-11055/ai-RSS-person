#!/bin/bash
# AI RSS 项目 - 快速停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════╗${NC}"
echo -e "${RED}║   AI RSS 项目 - 快速停止              ║${NC}"
echo -e "${RED}╚══════════════════════════════════════╝${NC}"
echo -e "${YELLOW}⚠️  停止 Docker 服务...${NC}"
docker compose down

echo -e "${GREEN}✅ 已停止所有服务${NC}"
echo -e "${GREEN}══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  内存已释放                         ║${NC}"
echo -e "${GREEN}║  Docker 容器已全部关闭              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
